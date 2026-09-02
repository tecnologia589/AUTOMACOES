"""
Processador LLM para geracao de Peticao Inicial Trabalhista.
Usa a CORBELINO.IA (Claude) para analisar documentos e gerar a peca completa.
"""
import anthropic
import json
import os
import sys


# ============================================================
# DADOS DO ESCRITORIO (lidos do ambiente, com defaults CORBELINO_ADVOGADOS)
# ============================================================
ESCRITORIO_NOME = os.getenv('ESCRITORIO_NOME', 'Corbelino Advogados Associados')
ESCRITORIO_ADVOGADO = os.getenv('ESCRITORIO_ADVOGADO', 'Dr. Paulo Alexandre Soares Corbelino')
ESCRITORIO_OAB = os.getenv('ESCRITORIO_OAB', 'OAB/MT 33.267')
ESCRITORIO_CIDADE = os.getenv('ESCRITORIO_CIDADE', 'Cáceres/MT')
ESCRITORIO_ENDERECO = os.getenv('ESCRITORIO_ENDERECO', '')  # cliente preenche no onboarding


def classificar_documentos(textos: dict) -> dict:
    """
    Recebe dict {nome_arquivo: texto_extraido} e classifica cada documento.
    Retorna dict com categorias: transcricao, cnh, rg, ctps, cadastro, outros.
    """
    classificado = {
        'transcricao': [],
        'cnh': [],
        'rg': [],
        'ctps': [],
        'cadastro': [],
        'comprovante_endereco': [],
        'outros': [],
    }

    for nome, texto in textos.items():
        nome_upper = nome.upper()
        texto_upper = texto[:2000].upper()

        if any(k in nome_upper for k in ['TRANSCRI', 'REUNIAO', 'REUNIÃO', 'AUDIO', 'ÁUDIO']):
            classificado['transcricao'].append((nome, texto))
        elif any(k in nome_upper for k in ['CNH', 'HABILITACAO', 'HABILITAÇÃO']):
            classificado['cnh'].append((nome, texto))
        elif any(k in texto_upper for k in ['HABILITACAO', 'HABILITAÇÃO', 'CATEGORIA', 'PERMISSAO', 'CNH']):
            classificado['cnh'].append((nome, texto))
        elif any(k in nome_upper for k in ['RG', 'IDENTIDADE']):
            classificado['rg'].append((nome, texto))
        elif any(k in nome_upper for k in ['CTPS', 'CARTEIRA DE TRABALHO', 'TRABALHO']):
            classificado['ctps'].append((nome, texto))
        elif any(k in nome_upper for k in ['CADASTRO', 'FICHA', 'DADOS']):
            classificado['cadastro'].append((nome, texto))
        elif any(k in nome_upper for k in ['COMPROVAN', 'ENDERECO', 'ENDEREÇO', 'RESIDENC']):
            classificado['comprovante_endereco'].append((nome, texto))
        elif any(k in texto_upper for k in ['RECLAMANTE', 'ADVOGADO', 'REUNIAO', 'DEPOIMENTO']):
            classificado['transcricao'].append((nome, texto))
        else:
            classificado['outros'].append((nome, texto))

    return classificado


def checar_completude(classificado: dict) -> list:
    """
    Verifica documentos encontrados vs necessarios.
    Retorna lista de documentos faltantes.
    """
    necessarios = {
        'transcricao': 'Transcricao da reuniao inicial',
        'cadastro': 'Cadastro/ficha do cliente (dados pessoais)',
    }
    desejaveis = {
        'cnh': 'CNH do cliente',
        'ctps': 'Carteira de Trabalho (CTPS)',
        'comprovante_endereco': 'Comprovante de endereco',
    }

    faltantes = []
    for cat, desc in necessarios.items():
        if not classificado.get(cat):
            faltantes.append(f'[NECESSARIO] {desc}')

    for cat, desc in desejaveis.items():
        if not classificado.get(cat):
            faltantes.append(f'[DESEJAVEL] {desc}')

    return faltantes


def gerar_peticao_inicial(classificado: dict) -> dict:
    """
    Envia os documentos classificados para o Claude gerar a peticao inicial completa.
    Retorna dict com: nome_cliente, empresa, peticao_texto, faltantes.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERRO: ANTHROPIC_API_KEY nao encontrada no .env")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Montar contexto ENXUTO - so documentos essenciais para a peticao
    # Prioridade: transcricao e cadastro sao obrigatorios, ctps e cnh complementam
    # NAO mandar: procuracao, contrato, declaracao, prints (nao agregam pra peticao)
    categorias_essenciais = ['transcricao', 'cadastro', 'ctps', 'cnh', 'comprovante_endereco']
    contexto = ""
    MAX_CHARS = 80000  # Limite enxuto para economizar tokens
    chars_usados = 0

    # Filtrar documentos que NAO sao uteis pra peticao
    excluir_nomes = ['PROCURA', 'CONTRATO', 'DECLARAC', 'HIPOSSUF', 'HONORAR']

    for cat in categorias_essenciais:
        docs = classificado.get(cat, [])
        for nome, texto in docs:
            # Pular documentos que ja foram gerados (nao sao insumo)
            if any(exc in nome.upper() for exc in excluir_nomes):
                print(f"  Pulando (nao essencial): {nome}")
                continue
            texto_limitado = texto[:12000]
            if chars_usados + len(texto_limitado) > MAX_CHARS:
                print(f"  AVISO: Limite de contexto atingido, pulando {nome}")
                continue
            contexto += f"\n\n=== DOCUMENTO: {nome} (tipo: {cat}) ===\n{texto_limitado}"
            chars_usados += len(texto_limitado)

    print(f"  Contexto: {chars_usados:,} caracteres enviados para a CORBELINO.IA")

    faltantes = checar_completude(classificado)

    aviso_faltantes = ""
    if faltantes:
        aviso_faltantes = "\n\nDOCUMENTOS FALTANTES (destaque na peca onde a informacao esta incompleta):\n"
        aviso_faltantes += "\n".join(f"- {f}" for f in faltantes)

    system_prompt = f'''Voce e CORBELINO.IA, advogada senior com 20 anos de experiencia pratica em direito processual trabalhista, e trabalha em conjunto com o(a) advogado(a) responsavel do {ESCRITORIO_NOME}, {ESCRITORIO_ADVOGADO}, inscrito(a) na {ESCRITORIO_OAB}. Voces formam um time vitorioso.

Voce e redatora criteriosa: sem prolixidade, escreve em terceira pessoa com o impeto de quem e detentor do direito. Sua redacao e coesa, profissional, atinente as regras processuais e faticas. Se refere as partes pelo polo que ocupa na acao (O Reclamante, a Reclamada). Domina a CLT, CPC, CC, CDC, Constituicao Federal, Lei do Motorista (13.103/2015) e normas dos tribunais.

TAREFA: Voce recebera documentos de um caso trabalhista (transcricao de reuniao, documentos pessoais, cadastro, etc.). Deve gerar uma PETICAO INICIAL TRABALHISTA completa e pronta para protocolar.

============================================================
PADROES DE FORMATACAO DO ESCRITORIO (OBRIGATORIOS - NAO CONFUNDIR)
============================================================
- Fonte: Montserrat, corpo 11pt
- Alinhamento do corpo do texto: JUSTIFICADO (sempre)
- Espacamento entre linhas: 1,5
- Recuo da primeira linha: 7 (a esquerda)
- Titulos com NUMERAL ALFANUMERICO em negrito (I., II., III., IV., V., I.1., II.1., A), B), etc.): **JUSTIFICADOS**, NUNCA centralizados. Sao titulos de secao dentro do texto, em negrito, mas alinhados com o corpo (justificados).
- Unicos elementos CENTRALIZADOS na peca: o enderecamento ao juizo (EXCELENTISSIMO...), o nome da acao (RECLAMATORIA TRABALHISTA), o "Nestes termos / pede deferimento", a data/local e a assinatura. Mais nada.
- Citacoes de lei/jurisprudencia: recuo 4cm a esquerda, italico, sem recuo de primeira linha.
- NAO confundir: secao "I. DOS FATOS", "II. DO DIREITO", "III. DOS PEDIDOS", "IV. DO VALOR DA CAUSA", "V. DOS REQUERIMENTOS FINAIS" sao NEGRITO + JUSTIFICADO, NAO centralizados.

Retorne ESTRITAMENTE um objeto JSON valido com estas chaves:

1. "nome_cliente": nome completo do reclamante
2. "empresa": nome da empresa reclamada
3. "tipo_acao": tipo da acao (ex: Reclamatoria Trabalhista)
4. "documentos_faltantes": lista de documentos/informacoes que faltam
5. "peticao": texto COMPLETO da peticao inicial, estruturada assim:

EXCELENTISSIMO(A) SENHOR(A) JUIZ(A) DO TRABALHO DA ___ VARA DO TRABALHO DE [CIDADE/UF]
(unico elemento centralizado aqui - o enderecamento ao juizo)

[qualificacao completa do reclamante com todos os dados pessoais disponíveis - justificado, recuo 7]

vem, respeitosamente, perante Vossa Excelencia, por intermedio de seu(sua) advogado(a), {ESCRITORIO_ADVOGADO}, inscrito(a) na {ESCRITORIO_OAB}, com escritorio profissional em {ESCRITORIO_CIDADE} [COMPLETAR: endereco profissional completo], propor a presente

RECLAMATORIA TRABALHISTA
(centralizado em negrito - nome da acao)

em face de [EMPRESA], [qualificacao da empresa se disponivel], pelos fatos e fundamentos a seguir expostos.

I. DOS FATOS
(NEGRITO + JUSTIFICADO, NAO centralizado)
[Narrativa cronologica dos fatos baseada EXCLUSIVAMENTE nos documentos fornecidos - justificado, recuo 7, espacamento 1,5]

II. DO DIREITO
(NEGRITO + JUSTIFICADO, NAO centralizado)
[Fundamentacao juridica com artigos da CLT, CF, Lei 13.103/2015, etc.]
[Cada direito violado deve ter sua propria subsecao com fundamentacao - subsecoes tipo II.1., II.2. tambem em negrito + justificado]

III. DOS PEDIDOS
(NEGRITO + JUSTIFICADO, NAO centralizado)
[Lista numerada de TODOS os pedidos cabiveis com base nos fatos]

IV. DO VALOR DA CAUSA
(NEGRITO + JUSTIFICADO, NAO centralizado)
[Estimativa fundamentada]

V. DOS REQUERIMENTOS FINAIS
(NEGRITO + JUSTIFICADO, NAO centralizado)
[Requerimentos processuais: citacao, provas, justica gratuita, etc.]

Nestes termos,
pede deferimento.
(centralizado)

{ESCRITORIO_CIDADE}, [data de hoje].
(centralizado)

{ESCRITORIO_ADVOGADO}
{ESCRITORIO_OAB}
(centralizado)

REGRAS CRITICAS:
1. NAO invente fatos. Use APENAS o que consta nos documentos.
2. Onde faltar informacao, use [COMPLETAR: descricao do que falta] como placeholder.
3. A peticao deve ser EXTENSA e COMPLETA, pronta para protocolar.
4. FORMATACAO: corpo JUSTIFICADO, recuo 7, espacamento 1,5. Titulos de secao com numeral alfanumerico (I., II., III., IV., V., A), B)) sao NEGRITO + JUSTIFICADO - NUNCA centralizados. So centralizar: enderecamento, nome da acao, encerramento, data e assinatura.
5. Cite artigos de lei especificos e aplicaveis.
6. Na qualificacao, se faltar algum dado pessoal, use [COMPLETAR].
7. NAO use hifens para listar. Use numeracao ou letras.

RETORNE APENAS O JSON. Nao inclua texto, introducoes ou blocos ```json markdown.'''

    print("  Enviando documentos para analise da CORBELINO.IA (Claude)...")
    print("  Gerando peticao inicial completa...")

    try:
        # Usar streaming para evitar timeout em requisicoes longas
        texto_resp = ""
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=32768,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Analise os documentos abaixo e gere a peticao inicial trabalhista completa.{aviso_faltantes}\n\n{contexto}"
            }]
        ) as stream:
            for text in stream.text_stream:
                texto_resp += text

        texto_resp = texto_resp.strip()
        if texto_resp.startswith("```json"):
            texto_resp = texto_resp[7:]
        if texto_resp.startswith("```"):
            texto_resp = texto_resp[3:]
        if texto_resp.endswith("```"):
            texto_resp = texto_resp[:-3]

        try:
            dados = json.loads(texto_resp)
        except json.JSONDecodeError:
            # JSON truncado — tentar extrair os campos manualmente
            print("  AVISO: JSON truncado, extraindo campos manualmente...")
            import re
            dados = {}
            # Extrair nome_cliente
            m = re.search(r'"nome_cliente"\s*:\s*"([^"]+)"', texto_resp)
            if m:
                dados['nome_cliente'] = m.group(1)
            # Extrair empresa
            m = re.search(r'"empresa"\s*:\s*"([^"]+)"', texto_resp)
            if m:
                dados['empresa'] = m.group(1)
            # Extrair tipo_acao
            m = re.search(r'"tipo_acao"\s*:\s*"([^"]+)"', texto_resp)
            if m:
                dados['tipo_acao'] = m.group(1)
            # Extrair peticao (tudo entre "peticao": " e o final)
            m = re.search(r'"peticao"\s*:\s*"(.*)', texto_resp, re.DOTALL)
            if m:
                peticao_raw = m.group(1)
                # Remover aspas final e chave se existir
                peticao_raw = re.sub(r'"\s*,?\s*\}?\s*$', '', peticao_raw)
                # Decodificar escapes JSON
                peticao_raw = peticao_raw.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                dados['peticao'] = peticao_raw

        dados['faltantes_detectados'] = faltantes
        return dados

    except json.JSONDecodeError:
        print("ERRO: A IA nao retornou JSON valido.")
        print("Resposta recebida:")
        print(texto_resp[:500])
        sys.exit(1)
    except Exception as e:
        print(f"ERRO de conexao com a IA: {e}")
        sys.exit(1)
