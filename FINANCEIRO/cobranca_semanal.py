"""
Cobranca semanal - Corbelino Advogados Associados
Puxa boletos vencidos + a vencer no Asaas e envia PDF + lembrete via Atende Direito.

Uso:
  python FINANCEIRO/cobranca_semanal.py
  python FINANCEIRO/cobranca_semanal.py --dias-aviso 7
  python FINANCEIRO/cobranca_semanal.py --apenas-relatorio
  python FINANCEIRO/cobranca_semanal.py --teste-numero 48999990000
  python FINANCEIRO/cobranca_semanal.py --somente-vencidas

Regras:
- OVERDUE: tom de cobranca
- PENDING a vencer: tom de lembrete
- Um cliente pode ter N boletos -> envia 1 mensagem resumo + N PDFs
- Sem telefone ou sem contato no Atende Direito -> entra no relatorio de PENDENTES

Listas de clientes (cadastro do escritorio):
- clientes_nao_cobrar.txt : clientes que NAO devem ser cobrados (um por linha)
- clientes_negociar.txt    : clientes com abertura para negociacao (um por linha)
>>> TODO (onboarding): preencher essas listas conforme as politicas do escritorio.
    Comecam vazias.
"""
import os
import sys
import argparse
import time
from datetime import date, datetime
from collections import defaultdict

# Adicionar raiz do projeto ao path para importar INTEGRACOES
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from dotenv import load_dotenv
load_dotenv(os.path.join(RAIZ, 'config', '.env'))

from INTEGRACOES import asaas_integration as asaas
from INTEGRACOES import atendedireito_integration as ad
from INTEGRACOES import advbox_integration as advbox


ARQUIVO_EXCLUSOES = os.path.join(os.path.dirname(__file__), 'clientes_nao_cobrar.txt')
ARQUIVO_NEGOCIAR = os.path.join(os.path.dirname(__file__), 'clientes_negociar.txt')

# Identidade do escritorio (via env, com defaults neutros).
ESCRITORIO_NOME = os.getenv('ESCRITORIO_NOME', 'Corbelino Advogados Associados')
ESCRITORIO_TELEFONE = os.getenv('ESCRITORIO_TELEFONE', '')
ESCRITORIO_EMAIL = os.getenv('ESCRITORIO_EMAIL_FINANCEIRO', '')
ESCRITORIO_CIDADE = os.getenv('ESCRITORIO_CIDADE', 'Cáceres/MT e Pontes Lacerda/MT')
ESCRITORIO_SITE = os.getenv('ESCRITORIO_SITE', '')

# Cache de andamentos por customer_id Asaas (evita refetch dentro da execucao)
_andamento_cache = {}


def _assinatura():
    """Bloco de assinatura padrao do escritorio (campos vazios sao omitidos)."""
    linhas = [f"*Equipe {ESCRITORIO_NOME}*"]
    contato = " | ".join([p for p in (ESCRITORIO_TELEFONE, ESCRITORIO_EMAIL) if p])
    if contato:
        linhas.append(contato)
    if ESCRITORIO_CIDADE:
        linhas.append(ESCRITORIO_CIDADE)
    if ESCRITORIO_SITE:
        linhas.append(ESCRITORIO_SITE)
    return "\n".join(linhas)


# ============================================================
# LISTAS DE CLIENTES (exclusao e negociacao)
# ============================================================

def _carregar_lista(arquivo):
    if not os.path.isfile(arquivo):
        return set(), []
    ids, nomes = set(), []
    with open(arquivo, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue
            if linha.startswith('cus_'):
                ids.add(linha)
            else:
                nomes.append(linha.upper())
    return ids, nomes


def carregar_exclusoes():
    return _carregar_lista(ARQUIVO_EXCLUSOES)


def carregar_negociar():
    return _carregar_lista(ARQUIVO_NEGOCIAR)


def _match_lista(customer_id, nome, lista):
    ids, nomes = lista
    if customer_id in ids:
        return True
    nome_upper = (nome or '').upper()
    return any(n in nome_upper for n in nomes)


def cliente_excluido(customer_id, nome, exclusoes):
    return _match_lista(customer_id, nome, exclusoes)


def cliente_negociar(customer_id, nome, negociar):
    return _match_lista(customer_id, nome, negociar)


# ============================================================
# HELPERS DE FORMATACAO
# ============================================================

def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_data(iso_date):
    """'2026-04-12' -> '12/04/2026'"""
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return iso_date


def dias_atraso(iso_date):
    """Dias de atraso a partir de hoje. Negativo = dias que faltam."""
    try:
        venc = datetime.strptime(iso_date, "%Y-%m-%d").date()
        return (date.today() - venc).days
    except Exception:
        return 0


# ============================================================
# ANDAMENTO PROCESSUAL (ADVBOX)
# ============================================================

def obter_andamento_cliente(asaas_customer_id, cpf, max_processos=3, max_movs=3):
    """
    Busca processos do cliente no ADVBOX (match por CPF) e formata texto
    com as ultimas movimentacoes de cada processo ativo.

    Retorna string formatada (vazia se nao encontrar nada).
    """
    if asaas_customer_id in _andamento_cache:
        return _andamento_cache[asaas_customer_id]

    cpf_limpo = ''.join(c for c in (cpf or '') if c.isdigit())
    if not cpf_limpo:
        _andamento_cache[asaas_customer_id] = ''
        return ''

    try:
        clientes_advbox = advbox.buscar_cliente(cpf=cpf_limpo)
    except Exception as e:
        print(f"   AVISO: erro ao buscar cliente ADVBOX: {e}")
        _andamento_cache[asaas_customer_id] = ''
        return ''

    if not clientes_advbox:
        _andamento_cache[asaas_customer_id] = ''
        return ''

    cliente_advbox_id = clientes_advbox[0].get('id')
    try:
        processos = advbox.buscar_processo(cliente_id=cliente_advbox_id)
    except Exception as e:
        print(f"   AVISO: erro ao buscar processos ADVBOX: {e}")
        _andamento_cache[asaas_customer_id] = ''
        return ''

    if not processos:
        _andamento_cache[asaas_customer_id] = ''
        return ''

    ativos = [p for p in processos if not p.get('archived')] or processos

    blocos = []
    for proc in ativos[:max_processos]:
        lawsuit_id = proc.get('id')
        proc_num = (proc.get('process_number') or proc.get('protocol_number')
                    or proc.get('folder') or 'sem numero')
        # Filtra so movs do TRIBUNAL para nao vazar notas internas (origin=MANUAL)
        try:
            movs = advbox.listar_movimentacoes_processo(lawsuit_id, origin='TRIBUNAL')
        except Exception as e:
            print(f"   AVISO: erro ao buscar movs do processo {lawsuit_id}: {e}")
            continue

        if not movs:
            continue

        movs_sorted = sorted(movs, key=lambda m: m.get('date', ''), reverse=True)
        linhas = []
        for m in movs_sorted[:max_movs]:
            data = fmt_data(m.get('date', ''))
            titulo = (m.get('title') or 'Movimentacao').strip()
            if len(titulo) > 140:
                titulo = titulo[:137] + '...'
            linhas.append(f"  - {data}: {titulo}")

        if linhas:
            blocos.append(f"*Processo:* {proc_num}\n" + "\n".join(linhas))

    if not blocos:
        resultado = ''
    else:
        resultado = ("\n\n*ANDAMENTO DO(S) SEU(S) PROCESSO(S):*\n\n"
                     + "\n\n".join(blocos))

    _andamento_cache[asaas_customer_id] = resultado
    return resultado


# ============================================================
# MONTAGEM DE MENSAGEM
# ============================================================

def _primeiro_nome(nome_cliente):
    """Extrai primeiro nome util, ignorando prefixos como ESPOLIO, RESIDENCIAL etc."""
    if not nome_cliente:
        return "Cliente"
    limpo = nome_cliente.split('_')[0]
    partes = limpo.split()
    prefixos_genericos = {'ESPOLIO', 'ESPÓLIO', 'RESIDENCIAL', 'CONDOMINIO',
                          'CONDOMÍNIO', 'EMPRESA', 'ASSOCIACAO', 'ASSOCIAÇÃO'}
    if len(partes) >= 2 and partes[0].upper() in prefixos_genericos:
        return f"{partes[0].title()} {partes[1].title()}"
    return partes[0].title() if partes else "Cliente"


def montar_mensagem(nome_cliente, boletos, modo='cobranca', andamento=''):
    """
    Mensagem padrao do escritorio.
    - modo 'lembrete'  : tom amigavel para cliente em dia (sem palavras de cobranca)
    - modo 'cobranca'  : regularizacao de pendencia financeira
    - modo 'negociacao': cobranca + abertura para parcelamento
    Inclui bloco de andamento processual (ADVBOX) antes do fechamento.
    """
    primeiro_nome = _primeiro_nome(nome_cliente)
    total = sum(b.get('value', 0) for b in boletos)

    # Bloco de boletos: 1 ou varios
    if len(boletos) == 1:
        b = boletos[0]
        venc_txt = f"com vencimento em {fmt_data(b['dueDate'])}."
        valor_txt = fmt_moeda(b['value'])
    elif modo == 'lembrete':
        linhas = []
        for b in sorted(boletos, key=lambda x: x.get('dueDate', '')):
            linhas.append(f"  - {fmt_data(b['dueDate'])} - {fmt_moeda(b['value'])}")
        venc_txt = "com os seguintes vencimentos:\n" + "\n".join(linhas)
        valor_txt = fmt_moeda(total)
    else:
        linhas = []
        for b in sorted(boletos, key=lambda x: x.get('dueDate', '')):
            dias = dias_atraso(b['dueDate'])
            if b['_situacao'] == 'VENCIDA' and dias > 0:
                sit = f"vencido ha {dias} dia(s)"
            elif b['_situacao'] == 'A_VENCER' and dias < 0:
                sit = f"vence em {-dias} dia(s)"
            else:
                sit = b['_situacao'].lower()
            linhas.append(f"  - {fmt_data(b['dueDate'])} - "
                          f"{fmt_moeda(b['value'])} ({sit})")
        venc_txt = "com os seguintes vencimentos:\n" + "\n".join(linhas)
        valor_txt = fmt_moeda(total)

    # Lembrete amigavel (cliente em dia) - sem tom de cobranca
    if modo == 'lembrete':
        msg = (
            f"*Lembrete de Honorarios - {ESCRITORIO_NOME}*\n\n"
            f"Ola, {primeiro_nome}! Tudo bem?\n\n"
            f"Passando para lembrar, com carinho, do(s) seu(s) honorario(s) "
            f"advocaticio(s) contratado(s) junto ao {ESCRITORIO_NOME}, {venc_txt}\n\n"
            f"Valor: *{valor_txt}*"
            f"{andamento or ''}\n\n"
            f"Segue o boleto em anexo para facilitar o pagamento. Caso ja tenha "
            f"efetuado o pagamento, por gentileza desconsidere este lembrete.\n\n"
            f"Seguimos a disposicao para qualquer duvida e agradecemos pela "
            f"confianca no nosso trabalho.\n\n"
            f"Atenciosamente,\n"
            f"{_assinatura()}"
        )
        return msg

    bloco_neg = ""
    if modo == 'negociacao':
        bloco_neg = (
            "\n\nSabemos que o momento pode estar dificil. Estamos abertos a "
            "conversar sobre parcelamento ou condicoes especiais para voce "
            "regularizar a situacao."
        )

    msg = (
        f"*Assunto: Regularizacao de Pendencia Financeira*\n\n"
        f"Prezado(a) {primeiro_nome},\n\n"
        f"Esperamos que esteja bem.\n\n"
        f"Identificamos em nosso controle financeiro que ha valor pendente "
        f"referente ao(s) honorario(s) contratado(s) junto ao {ESCRITORIO_NOME}, "
        f"{venc_txt}\n\n"
        f"Sabemos que imprevistos podem ocorrer e estamos a disposicao para "
        f"auxiliar na regularizacao, inclusive avaliando alternativas de "
        f"pagamento, caso necessario. Nosso objetivo e manter o atendimento "
        f"juridico com a mesma qualidade e continuidade, prezando sempre "
        f"pela transparencia e respeito mutuo."
        f"{bloco_neg}\n\n"
        f"Valor em aberto: *{valor_txt}*"
        f"{andamento or ''}\n\n"
        f"Pedimos, por gentileza, que realize o pagamento, evitando suspensao "
        f"do atendimento ou eventuais encargos contratuais.\n\n"
        f"Segue o boleto para pagamento.\n\n"
        f"Em caso de duvidas, entre em contato conosco, nossa equipe esta a "
        f"disposicao para auxiliar.\n\n"
        f"Atenciosamente,\n"
        f"{_assinatura()}"
    )
    return msg


# ============================================================
# PROCESSAMENTO
# ============================================================

def agrupar_por_cliente(cobrancas):
    """Agrupa cobrancas por customer_id."""
    grupos = defaultdict(list)
    for c in cobrancas:
        grupos[c['customer']].append(c)
    return grupos


def processar_cliente(customer_id, boletos, args, exclusoes, negociar):
    """
    Processa um cliente: busca dados, monta mensagem, envia.

    Retorna dict com resultado: {status, motivo, nome, telefone, qtd_boletos, valor_total}
    """
    cliente = asaas.obter_cliente(customer_id)
    if not cliente:
        return {'status': 'erro', 'motivo': 'cliente Asaas nao encontrado',
                'customer_id': customer_id}

    nome = cliente.get('name') or '(sem nome)'
    telefone = cliente.get('mobilePhone') or cliente.get('phone') or ''
    valor_total = sum(b.get('value', 0) for b in boletos)

    base = {
        'status': 'pendente',
        'nome': nome,
        'telefone': telefone,
        'qtd_boletos': len(boletos),
        'valor_total': valor_total,
        'situacoes': [b['_situacao'] for b in boletos],
    }

    # Exclusoes manuais (clientes_nao_cobrar.txt)
    if cliente_excluido(customer_id, nome, exclusoes):
        base['status'] = 'excluido'
        base['motivo'] = 'na lista de exclusoes'
        return base

    if not telefone or telefone == '0000000000':
        base['status'] = 'sem_telefone'
        base['motivo'] = 'cliente sem telefone cadastrado no Asaas'
        return base

    # Filtro de teste
    if args.teste_numero:
        tel_teste = ''.join(c for c in args.teste_numero if c.isdigit())
        tel_cliente = ''.join(c for c in telefone if c.isdigit())
        if tel_teste not in tel_cliente and tel_cliente not in tel_teste:
            return None  # skip silencioso

    print(f"\n[{base['qtd_boletos']} boleto(s)] {nome} - {telefone} - total {fmt_moeda(valor_total)}")

    # Buscar andamento processual no ADVBOX (sempre, mesmo em modo relatorio)
    cpf_cliente = cliente.get('cpfCnpj', '')
    andamento = obter_andamento_cliente(customer_id, cpf_cliente)
    base['andamento'] = bool(andamento)

    # Modo relatorio: nao envia, so simula
    if args.apenas_relatorio:
        base['status'] = 'simulado'
        return base

    # Buscar contato no Atende Direito
    contato = ad.buscar_contato_por_telefone(telefone)
    if not contato:
        base['status'] = 'sem_contato_ad'
        base['motivo'] = 'telefone nao encontrado no Atende Direito'
        print(f"   AVISO: telefone nao encontrado no Atende Direito")
        return base

    user_ns = contato.get('user_ns')
    print(f"   Contato AD: {contato.get('name', '')} ({user_ns})")

    # Enviar mensagem de texto com resumo + andamento processual
    if getattr(args, 'lembrete', False):
        modo = 'lembrete'
    else:
        modo = 'negociacao' if cliente_negociar(customer_id, nome, negociar) else 'cobranca'
    base['modo'] = modo
    mensagem = montar_mensagem(nome, boletos, modo=modo, andamento=andamento)
    if not ad.enviar_mensagem_texto(user_ns, mensagem):
        base['status'] = 'erro_envio_texto'
        base['motivo'] = 'falha ao enviar texto'
        return base
    print(f"   Texto enviado")
    time.sleep(1.5)

    # Enviar PDFs (um por boleto)
    enviados = 0
    for b in boletos:
        url_pdf = b.get('bankSlipUrl')
        if not url_pdf:
            print(f"   AVISO: boleto {b['id']} sem bankSlipUrl")
            continue
        desc = b.get('description', 'Boleto')[:80]
        legenda = f"{desc} - Venc {fmt_data(b['dueDate'])} - {fmt_moeda(b['value'])}"
        if ad.enviar_arquivo(user_ns, url_pdf, legenda=legenda, tipo='file'):
            enviados += 1
            print(f"   PDF enviado: {b['id']}")
        else:
            print(f"   ERRO ao enviar PDF: {b['id']}")
        time.sleep(1.5)

    base['status'] = 'enviado' if enviados == len(boletos) else 'parcial'
    base['pdfs_enviados'] = enviados
    return base


# ============================================================
# RELATORIO DETALHADO
# ============================================================

def gerar_relatorio_detalhado(grupos, exclusoes, negociar, force_modo=None):
    """
    Gera texto de relatorio detalhado: para cada cliente que SERIA cobrado,
    mostra dados, boletos, e a mensagem que seria enviada.

    force_modo: se definido (ex: 'lembrete'), sobrepoe o modo de todos os clientes.

    Retorna o texto completo.
    """
    linhas = []
    linhas.append("=" * 78)
    linhas.append(f"RELATORIO DETALHADO DE COBRANCA - {ESCRITORIO_NOME}")
    linhas.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("=" * 78)

    para_cobrar = []
    excluidos = []
    sem_telefone = []

    for customer_id, boletos in grupos.items():
        cliente = asaas.obter_cliente(customer_id)
        if not cliente:
            continue
        nome = cliente.get('name') or '(sem nome)'
        telefone = cliente.get('mobilePhone') or cliente.get('phone') or ''

        cpf = cliente.get('cpfCnpj', '')
        info = {
            'customer_id': customer_id,
            'nome': nome,
            'telefone': telefone,
            'cpf': cpf,
            'email': cliente.get('email', ''),
            'boletos': boletos,
            'total': sum(b.get('value', 0) for b in boletos),
            'modo': force_modo or ('negociacao' if cliente_negociar(customer_id, nome, negociar) else 'cobranca'),
            'andamento': obter_andamento_cliente(customer_id, cpf),
        }

        if cliente_excluido(customer_id, nome, exclusoes):
            excluidos.append(info)
        elif not telefone or telefone == '0000000000':
            sem_telefone.append(info)
        else:
            para_cobrar.append(info)

    # Ordenar por valor total desc
    para_cobrar.sort(key=lambda x: -x['total'])

    # Secao 1: clientes para cobrar
    linhas.append(f"\n\n{'#' * 78}")
    linhas.append(f"# CLIENTES QUE SERAO COBRADOS: {len(para_cobrar)}")
    linhas.append(f"{'#' * 78}\n")

    for i, info in enumerate(para_cobrar, 1):
        vencidas = [b for b in info['boletos'] if b['_situacao'] == 'VENCIDA']
        a_vencer = [b for b in info['boletos'] if b['_situacao'] == 'A_VENCER']

        linhas.append("-" * 78)
        linhas.append(f"[{i}/{len(para_cobrar)}] {info['nome']}")
        linhas.append("-" * 78)
        linhas.append(f"Customer ID : {info['customer_id']}")
        linhas.append(f"Telefone    : {info['telefone']}")
        linhas.append(f"CPF/CNPJ    : {info['cpf']}")
        if info['email']:
            linhas.append(f"Email       : {info['email']}")
        linhas.append(f"Total aberto: {fmt_moeda(info['total'])}")
        linhas.append(f"Boletos     : {len(info['boletos'])} "
                      f"({len(vencidas)} vencidos + {len(a_vencer)} a vencer)")

        linhas.append("\nBOLETOS:")
        for b in sorted(info['boletos'], key=lambda x: x.get('dueDate', '')):
            situacao = b['_situacao']
            dias = dias_atraso(b['dueDate'])
            if situacao == 'VENCIDA' and dias > 0:
                sit_txt = f"VENCIDO ha {dias} dia(s)"
            elif situacao == 'A_VENCER' and dias < 0:
                sit_txt = f"a vencer em {-dias} dia(s)"
            else:
                sit_txt = situacao
            desc = (b.get('description') or '').strip()[:70]
            linhas.append(f"  - {fmt_data(b['dueDate'])} | {fmt_moeda(b['value']):>14s} "
                          f"| {sit_txt:<22s} | {desc}")

        tag_modo = " [NEGOCIACAO]" if info['modo'] == 'negociacao' else ""
        tag_and = " +ANDAMENTO" if info.get('andamento') else " (sem andamento ADVBOX)"
        linhas.append(f"\nMENSAGEM QUE SERA ENVIADA{tag_modo}{tag_and}:")
        linhas.append("  " + "v" * 60)
        msg = montar_mensagem(info['nome'], info['boletos'],
                              modo=info['modo'], andamento=info.get('andamento', ''))
        for ln in msg.split('\n'):
            linhas.append(f"  {ln}")
        linhas.append("  " + "^" * 60)
        linhas.append(f"\n+ {len(info['boletos'])} PDF(s) do boleto anexos (bankSlipUrl)")
        linhas.append("")

    # Secao 2: excluidos
    if excluidos:
        linhas.append(f"\n\n{'#' * 78}")
        linhas.append(f"# CLIENTES EXCLUIDOS (nao serao cobrados): {len(excluidos)}")
        linhas.append(f"{'#' * 78}\n")
        for info in excluidos:
            linhas.append(f"  - {info['nome']} - {len(info['boletos'])} boleto(s) "
                          f"- {fmt_moeda(info['total'])}")

    # Secao 3: sem telefone
    if sem_telefone:
        linhas.append(f"\n\n{'#' * 78}")
        linhas.append(f"# SEM TELEFONE (precisa cadastrar no Asaas): {len(sem_telefone)}")
        linhas.append(f"{'#' * 78}\n")
        for info in sem_telefone:
            linhas.append(f"  - {info['nome']} - {len(info['boletos'])} boleto(s) "
                          f"- {fmt_moeda(info['total'])}")

    # Totais
    total_cobrar = sum(c['total'] for c in para_cobrar)
    total_exc = sum(c['total'] for c in excluidos)
    total_sem = sum(c['total'] for c in sem_telefone)

    linhas.append(f"\n\n{'=' * 78}")
    linhas.append("TOTAIS")
    linhas.append("=" * 78)
    linhas.append(f"  A cobrar      : {len(para_cobrar):3d} cliente(s) - "
                  f"{fmt_moeda(total_cobrar)}")
    linhas.append(f"  Excluidos     : {len(excluidos):3d} cliente(s) - "
                  f"{fmt_moeda(total_exc)}")
    linhas.append(f"  Sem telefone  : {len(sem_telefone):3d} cliente(s) - "
                  f"{fmt_moeda(total_sem)}")
    linhas.append(f"  TOTAL GERAL   : {len(para_cobrar)+len(excluidos)+len(sem_telefone):3d} "
                  f"cliente(s) - {fmt_moeda(total_cobrar+total_exc+total_sem)}")

    return "\n".join(linhas)


# ============================================================
# RELATORIO
# ============================================================

def imprimir_relatorio(resultados, args):
    print("\n" + "=" * 70)
    print("RELATORIO FINAL")
    print("=" * 70)

    por_status = defaultdict(list)
    for r in resultados:
        if r:
            por_status[r['status']].append(r)

    ordem = ['enviado', 'simulado', 'parcial', 'excluido', 'sem_telefone',
             'sem_contato_ad', 'erro_envio_texto', 'erro']
    for status in ordem:
        itens = por_status.get(status, [])
        if not itens:
            continue
        print(f"\n[{status.upper()}] {len(itens)} cliente(s):")
        for r in itens:
            nome = r.get('nome', '?')[:40]
            tel = r.get('telefone', '')
            qtd = r.get('qtd_boletos', 0)
            valor = r.get('valor_total', 0)
            motivo = f" ({r.get('motivo')})" if r.get('motivo') else ''
            print(f"  - {nome:40s} {tel:15s} {qtd}x {fmt_moeda(valor):>15s}{motivo}")

    # Totais
    total_clientes = sum(len(v) for v in por_status.values())
    total_valor = sum(r.get('valor_total', 0) for r in resultados if r)
    total_enviados = len(por_status.get('enviado', [])) + len(por_status.get('parcial', []))

    print("\n" + "-" * 70)
    print(f"Total de clientes processados: {total_clientes}")
    print(f"Valor total em aberto: {fmt_moeda(total_valor)}")
    if args.apenas_relatorio:
        print(f"MODO RELATORIO - nada foi enviado")
    else:
        print(f"Mensagens enviadas: {total_enviados}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description=f"Cobranca semanal - {ESCRITORIO_NOME}")
    parser.add_argument('--dias-aviso', type=int, default=7,
                        help='Dias antes do vencimento para avisar (default 7)')
    parser.add_argument('--apenas-relatorio', action='store_true',
                        help='Nao envia mensagens, so mostra o que seria feito')
    parser.add_argument('--teste-numero', type=str, default=None,
                        help='Envia apenas para esse telefone (para teste)')
    parser.add_argument('--somente-vencidas', action='store_true',
                        help='Ignora a vencer, cobra so as OVERDUE')
    parser.add_argument('--somente-a-vencer', action='store_true',
                        help='Ignora vencidas, cobra so as PENDING dos proximos N dias')
    parser.add_argument('--detalhado', action='store_true',
                        help='Imprime e salva relatorio detalhado por cliente (preview das mensagens)')
    parser.add_argument('--todas-pendentes', action='store_true',
                        help='Puxa TODAS cobrancas OVERDUE+PENDING (ignora --dias-aviso)')
    parser.add_argument('--lembrete', action='store_true',
                        help='Forca tom de LEMBRETE amigavel para todos (cliente em dia)')
    args = parser.parse_args()

    print("=" * 70)
    print(f"COBRANCA SEMANAL - {ESCRITORIO_NOME}")
    print(f"Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"Modo: {'RELATORIO (sem envio)' if args.apenas_relatorio else 'ENVIO REAL'}")
    if args.teste_numero:
        print(f"TESTE: apenas telefone {args.teste_numero}")
    print("=" * 70)

    # 1. Puxar Asaas
    if args.somente_vencidas:
        print("\nBuscando cobrancas OVERDUE...")
        cobrancas = asaas.listar_cobrancas(status='OVERDUE')
        for c in cobrancas:
            c['_situacao'] = 'VENCIDA'
    elif args.somente_a_vencer:
        from datetime import timedelta
        hoje = date.today()
        limite = hoje + timedelta(days=args.dias_aviso)
        print(f"\nBuscando cobrancas PENDING entre {hoje} e {limite}...")
        cobrancas = asaas.listar_cobrancas(
            status='PENDING',
            due_date_ge=hoje.isoformat(),
            due_date_le=limite.isoformat(),
        )
        for c in cobrancas:
            c['_situacao'] = 'A_VENCER'
    elif args.todas_pendentes:
        print("\nBuscando TODAS cobrancas em aberto (OVERDUE + PENDING)...")
        vencidas = asaas.listar_cobrancas(status='OVERDUE')
        a_vencer = asaas.listar_cobrancas(status='PENDING')
        for c in vencidas:
            c['_situacao'] = 'VENCIDA'
        for c in a_vencer:
            c['_situacao'] = 'A_VENCER'
        cobrancas = vencidas + a_vencer
    else:
        cobrancas = asaas.listar_cobrancas_abertas(dias_ate_vencer=args.dias_aviso)

    if not cobrancas:
        print("\nNenhuma cobranca em aberto. Nada a fazer.")
        return

    print(f"\n{len(cobrancas)} cobranca(s) a processar.")

    # 2. Agrupar por cliente
    grupos = agrupar_por_cliente(cobrancas)
    print(f"Agrupado em {len(grupos)} cliente(s).")

    # 3. Carregar exclusoes/negociacao e processar cada cliente
    exclusoes = carregar_exclusoes()
    negociar = carregar_negociar()
    if exclusoes[0] or exclusoes[1]:
        print(f"Exclusoes: {len(exclusoes[0])} id(s) + {len(exclusoes[1])} nome(s)")
    if negociar[0] or negociar[1]:
        print(f"Negociacao: {len(negociar[0])} id(s) + {len(negociar[1])} nome(s)")

    # Modo detalhado: gera preview completo e encerra (nao envia nada)
    if args.detalhado:
        print("\nGerando relatorio detalhado...")
        texto = gerar_relatorio_detalhado(grupos, exclusoes, negociar,
                                          force_modo='lembrete' if args.lembrete else None)
        print(texto)
        arq = os.path.join(os.path.dirname(__file__),
                           f"relatorio_cobranca_{date.today().isoformat()}.txt")
        with open(arq, 'w', encoding='utf-8') as f:
            f.write(texto)
        print(f"\n\nRelatorio salvo em: {arq}")
        return

    resultados = []
    for i, (customer_id, boletos) in enumerate(grupos.items(), 1):
        print(f"\n[{i}/{len(grupos)}] Customer {customer_id}")
        try:
            r = processar_cliente(customer_id, boletos, args, exclusoes, negociar)
            if r:
                resultados.append(r)
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuario.")
            break
        except Exception as e:
            print(f"   ERRO: {e}")
            resultados.append({
                'status': 'erro', 'customer_id': customer_id,
                'motivo': str(e),
                'valor_total': sum(b.get('value', 0) for b in boletos),
            })
        # Pausa entre clientes (rate limit Atende Direito)
        if not args.apenas_relatorio:
            time.sleep(2)

    # 4. Relatorio
    imprimir_relatorio(resultados, args)


if __name__ == '__main__':
    main()
