"""
Integração com API LegalMail - Corbelino Advogados Associados

O escritório Corbelino Advogados Associados já usa o ADVBOX (não o LegalMail) como sistema jurídico -
ver INTEGRACOES/advbox_integration.py. Este módulo fica disponível como integração
GENÉRICA/opcional, herdada do núcleo compartilhado, caso o escritório venha a usar o
LegalMail no futuro. Cobre a API pública do LegalMail: consulta de processos,
intimações capturadas (DJEN/tribunais), partes, peticionamento eletrônico (inicial e
intermediária) com upload de PDF/timbrado, e protocolo. NÃO USAR sem confirmar antes
com o escritório se ele realmente usa o LegalMail.

API Base: https://app.legalmail.com.br
Doc oficial (Scalar/OpenAPI): https://app.legalmail.com.br/api/docs
Spec bruta: https://app.legalmail.com.br/assets/docs/openapi.yaml

AUTENTICAÇÃO
    Diferente do ADVBOX (Bearer header), o LegalMail usa `api_key` como
    QUERY STRING PARAM em toda requisição. A chave é criada no Painel da API
    da plataforma (Configurações > Painel da API) e fica em LEGALMAIL_API_KEY
    no .env.

COBRANÇA / CRÉDITOS
    O consumo da API é pago com créditos do workspace (créditos de assinatura
    + recarga avulsa). Só respostas 2xx são cobradas. O endpoint de intimações
    (listar_intimacoes) é cobrado POR REQUISIÇÃO (~R$0,05), não por item — evite
    laços/polling. Use `consultar_saldo()` para acompanhar o saldo.

RATE LIMIT E ANTI-POLLING
    120 requisições/min. Repetir a MESMA consulta em intervalo curto aciona um
    sistema de bloqueio progressivo (a API detecta "polling" e pune com bloqueios
    crescentes, de 5 a 15+ minutos). Para intimações em tempo real, prefira
    webhook (não coberto aqui) em vez de consultar em laço.

FLUXO DE PETICIONAMENTO (resumo)
    Inicial (nova ação):
      1. criar_processo_inicial(...)              -> idpeticoes, idprocessos
      2. atualizar_processo_inicial(idpeticoes, ...)  (comarca/classe/assunto/
         valorCausa etc. - OBRIGATÓRIO antes do protocolo; campos variam por
         tribunal/sistema, ver `regra.validations` na resposta do passo 1)
      3. enviar_arquivo_principal(idpeticoes, idprocessos, caminho_pdf)
      4. enviar_anexo(idpeticoes, tipo_documento_id, caminho_pdf)  (opcional)
      5. protocolar_inicial(idpeticoes, idprocessos, fk_peca, fk_certificado, ...)

    Intermediária (petição em processo já existente):
      1. criar_peticao_intermediaria(fk_processo, fk_certificado, ...) -> idpeticoes
      2. enviar_arquivo_principal(idpeticoes, idprocessos, caminho_pdf)
      3. enviar_anexo(...)  (opcional)
      4. protocolar_intermediaria(idpeticoes, idprocessos, fk_peca, solicitantes, ...)

    Peças/PDF só são aceitas em PDF. O timbrado do escritório (config/timbrado_modelo.docx)
    deve ser convertido para PDF antes do upload - ver OPERACIONAL/gerar_peticao.py.
"""
import os
import sys
import time
import requests


BASE_URL = 'https://app.legalmail.com.br'


def _api_key():
    key = os.getenv('LEGALMAIL_API_KEY')
    if not key:
        print('ERRO: LEGALMAIL_API_KEY nao encontrado no .env')
        sys.exit(1)
    return key


def _request(method, path, params=None, json_data=None, files=None, retries=2):
    """Faz request à API LegalMail. api_key é sempre injetada na query string."""
    url = f'{BASE_URL}{path}'
    params = dict(params or {})
    params['api_key'] = _api_key()

    for tentativa in range(retries + 1):
        try:
            resp = requests.request(
                method, url, params=params, json=json_data, files=files, timeout=60
            )
            if resp.status_code == 429:
                corpo = resp.json() if resp.text else {}
                wait = int(resp.headers.get('Retry-After', corpo.get('retry_after_seconds', 15)))
                print(f'  LegalMail rate limit / anti-polling: {corpo.get("message", "")}. Aguardando {wait}s...')
                time.sleep(wait)
                continue
            if resp.status_code == 402:
                print('  LegalMail: saldo de creditos insuficiente para esta requisicao.')
                return None
            resp.raise_for_status()
            return resp.json() if resp.text else {}
        except requests.exceptions.HTTPError:
            print(f'  LegalMail API erro ({resp.status_code}): {resp.text[:500]}')
            if tentativa < retries and resp.status_code >= 500:
                time.sleep(3)
                continue
            raise
        except requests.exceptions.RequestException as e:
            print(f'  LegalMail conexao falhou: {e}')
            if tentativa < retries:
                time.sleep(3)
                continue
            raise
    return None


# ============================================================
# SALDO / CRÉDITOS
# ============================================================

def consultar_saldo():
    """Saldo de créditos do workspace (assinatura + recarga)."""
    return _request('GET', '/api/v1/balance')


# ============================================================
# INTIMAÇÕES (publicações capturadas - DJEN/tribunais)
# Cobrado por requisição (~R$0,05). NAO usar em laço/polling curto -
# ver aviso de anti-polling no cabeçalho do módulo.
# ============================================================

def listar_intimacoes(data_captura_inicio=None, data_captura_fim=None,
                       data_disponibilizacao_inicio=None, data_disponibilizacao_fim=None,
                       processo=None, partes=None, tipo=None, fonte=None, tribunal=None,
                       destinatario=None, destinatario_id=None, termo=None, teor=None,
                       prazo_status=None, id=None, ordenar_por='id', ordem='desc',
                       offset=0, limit=50):
    """
    Lista intimações capturadas no workspace (tela "Intimações" da plataforma).
    `prazo_status`: pendente | cumprido | excedido.
    Para rotina diária, filtre por data_captura_inicio/fim e pagine com offset.
    """
    params = {k: v for k, v in dict(
        data_captura_inicio=data_captura_inicio, data_captura_fim=data_captura_fim,
        data_disponibilizacao_inicio=data_disponibilizacao_inicio,
        data_disponibilizacao_fim=data_disponibilizacao_fim,
        processo=processo, partes=partes, tipo=tipo, fonte=fonte, tribunal=tribunal,
        destinatario=destinatario, destinatario_id=destinatario_id, termo=termo, teor=teor,
        prazo_status=prazo_status, id=id, ordenar_por=ordenar_por, ordem=ordem,
        offset=offset, limit=limit,
    ).items() if v is not None}
    return _request('GET', '/api/v1/notices', params=params)


def listar_intimacoes_pendentes_hoje(data=None):
    """Atalho: intimações com prazo pendente capturadas numa data (padrão hoje, formato YYYY-MM-DD)."""
    if not data:
        from datetime import date
        data = date.today().isoformat()
    return listar_intimacoes(data_captura_inicio=data, data_captura_fim=data,
                              prazo_status='pendente', ordenar_por='data_captura', ordem='asc')


# ============================================================
# PROCESSOS (lawsuit)
# ============================================================

def listar_processos(usuario_id=None, oab=None, oab_uf=None, offset=0, limit=50):
    """Lista processos do workspace (id, numero, classe). Filtra por usuario_id OU oab+oab_uf."""
    params = {k: v for k, v in dict(
        usuario_id=usuario_id, oab=oab, oab_uf=oab_uf, offset=offset, limit=limit,
    ).items() if v is not None}
    return _request('GET', '/api/v1/lawsuit/all', params=params)


def buscar_processos(**filtros):
    """Busca avançada de processos (filtros conforme /api/v1/lawsuit/search - ver doc oficial)."""
    return _request('GET', '/api/v1/lawsuit/search', params=filtros)


def resumo_processos(**filtros):
    """Resumo/contadores de processos do workspace."""
    return _request('GET', '/api/v1/lawsuit/summary', params=filtros)


def detalhe_processo(idprocessos):
    """Detalhe completo de um processo pelo id."""
    return _request('GET', '/api/v1/lawsuit/detail', params={'idprocessos': idprocessos})


def excluir_processo(idprocessos):
    return _request('POST', '/api/v1/lawsuit/delete', params={'idprocessos': idprocessos})


def atribuir_processo(idprocessos, usuario_id):
    return _request('POST', '/api/v1/lawsuit/assign', params={'idprocessos': idprocessos, 'usuario_id': usuario_id})


def arquivar_processo(idprocessos):
    return _request('POST', '/api/v1/lawsuit/archive', params={'idprocessos': idprocessos})


def definir_sistema_tribunal(idprocessos, sistema):
    """Define o sistema (pje/projudi/esaj/eproc) do processo quando o tribunal tem mais de um."""
    return _request('POST', '/api/v1/lawsuit/court-system', params={'idprocessos': idprocessos, 'sistema': sistema})


def autos_processo(idprocessos, **filtros):
    """Lista os autos/documentos do processo."""
    params = dict(filtros)
    params['idprocessos'] = idprocessos
    return _request('GET', '/api/v1/lawsuit/case-files', params=params)


def url_movimentacao(idprocessos, **params_extra):
    params = dict(params_extra)
    params['idprocessos'] = idprocessos
    return _request('GET', '/api/v1/lawsuit/docket-entry/url', params=params)


def atualizar_autos(idprocessos, **dados):
    dados = dict(dados)
    dados['idprocessos'] = idprocessos
    return _request('POST', '/api/v1/lawsuit/case-files/update', json_data=dados)


def solicitar_download_autos(idprocessos, **dados):
    dados = dict(dados)
    dados['idprocessos'] = idprocessos
    return _request('POST', '/api/v1/lawsuit/case-files/download/request', json_data=dados)


def status_download_autos(hash_download):
    return _request('GET', '/api/v1/lawsuit/case-files/download/status', params={'hash': hash_download})


# --- Campos customizados do processo ---

def upsert_campo_customizado(idprocessos, chave, valor):
    return _request('POST', '/api/v1/lawsuit/custom_fields/upsert',
                     json_data={'idprocessos': idprocessos, 'chave': chave, 'valor': valor})


def listar_campos_customizados(idprocessos):
    return _request('GET', '/api/v1/lawsuit/custom_fields/all', params={'idprocessos': idprocessos})


def obter_campo_customizado(idprocessos, chave):
    return _request('GET', '/api/v1/lawsuit/custom_fields/get', params={'idprocessos': idprocessos, 'chave': chave})


def editar_campo_customizado(idprocessos, chave, valor):
    return _request('PUT', '/api/v1/lawsuit/custom_fields/edit',
                     json_data={'idprocessos': idprocessos, 'chave': chave, 'valor': valor})


def excluir_campo_customizado(idprocessos, chave):
    return _request('DELETE', '/api/v1/lawsuit/custom_fields/delete', params={'idprocessos': idprocessos, 'chave': chave})


# ============================================================
# IMPORTAÇÃO DE PROCESSOS (uploads - avulsa ou lote)
# ============================================================

def classes_de_importacao():
    """Classes processuais aceitas para pedido de importação (uploads/classes)."""
    return _request('GET', '/api/v1/uploads/classes')


def sistemas_permitidos_para_numero(numero, tribunal=None):
    """Sistemas de tribunal compatíveis com um número de processo (uploads/allowed-systems)."""
    params = {'numero': numero}
    if tribunal:
        params['tribunal'] = tribunal
    return _request('GET', '/api/v1/uploads/allowed-systems', params=params)


def solicitar_importacao_processos(pedidos):
    """
    Solicita importação de processo(s) já existente(s) no tribunal.
    `pedidos`: lista de dicts {numero, tribunal, sistema, classe_id, certificado_id}.
    Passo a passo: classes_de_importacao() -> classe_id; sistemas_permitidos_para_numero() -> sistema;
    listar_certificados() -> certificado_id.
    """
    return _request('POST', '/api/v1/uploads/request', json_data={'pedidos': pedidos})


def status_importacao(hash_pedido):
    return _request('GET', '/api/v1/uploads/status', params={'hash': hash_pedido})


def cancelar_importacao(hash_pedido):
    return _request('POST', '/api/v1/uploads/cancel', params={'hash': hash_pedido})


# ============================================================
# CERTIFICADOS DIGITAIS
# ============================================================

def listar_certificados():
    """Certificados digitais ativos do workspace (necessários p/ protocolar)."""
    return _request('GET', '/api/v1/workspace/certificates')


def cadastrar_certificado(**dados):
    return _request('POST', '/api/v1/certificate', json_data=dados)


# ============================================================
# SISTEMAS DE TRIBUNAL
# ============================================================

def requisitos_sistema_tribunal(**filtros):
    return _request('GET', '/api/v1/courts-systems/requirements', params=filtros)


def listar_sistemas_tribunal(**filtros):
    return _request('GET', '/api/v1/courts-systems', params=filtros)


def cadastrar_sistema_tribunal(**dados):
    return _request('POST', '/api/v1/courts-systems', json_data=dados)


def atualizar_sistema_tribunal(**dados):
    return _request('PUT', '/api/v1/courts-systems', json_data=dados)


def excluir_sistema_tribunal(**filtros):
    return _request('DELETE', '/api/v1/courts-systems', params=filtros)


# ============================================================
# PARTES (party)
# ============================================================

def listar_partes(offset=0, limit=50):
    return _request('GET', '/api/v1/party', params={'offset': offset, 'limit': limit})


def buscar_partes(**filtros):
    return _request('GET', '/api/v1/party/search', params=filtros)


def cadastrar_parte(**dados):
    """
    Cadastra uma parte (cliente/réu). Campos comuns: nome, documento (CPF/CNPJ), email,
    celular, rg, orgao, endereco_* , profissao, estado_civil, nacionalidade etc.
    """
    return _request('POST', '/api/v1/party', json_data=dados)


def atualizar_parte(id_parte, **dados):
    dados = dict(dados)
    dados['id'] = id_parte
    return _request('PUT', '/api/v1/party', json_data=dados)


def excluir_parte(id_parte):
    return _request('DELETE', '/api/v1/party', params={'id': id_parte})


def profissoes():
    return _request('GET', '/api/v1/party/professions')


def orgaos_emissores():
    return _request('GET', '/api/v1/party/issuing-agencies')


# ============================================================
# PETIÇÃO INICIAL (complaint)
# ============================================================

def criar_processo_inicial(itens):
    """
    Cria petição(ões) inicial(is). `itens`: dict único ou lista de dicts com
    tribunal (obrig.), instancia (obrig.: '1'|'2'|'recursal'), sistema (opcional se
    o tribunal só tiver um), idpoloativo/idpolopassivo (id ou lista de ids de partes),
    ufTribunal (só se não inferível). Retorna, por item aceito, idpeticoes/idprocessos
    e `regra.validations` com os campos que faltam preencher via atualizar_processo_inicial.
    """
    return _request('POST', '/api/v1/complaint', json_data=itens)


def atualizar_processo_inicial(idpeticoes, **dados):
    """
    PASSO OBRIGATÓRIO antes do protocolo. Preenche os campos exigidos pelo
    tribunal/sistema (comarca, classe, assunto, competencia, area, rito, valorCausa,
    atividade economica etc. - variam por tribunal). Pedidos da petição (gratuidade,
    liminar, sigilo, prioridade...) vão agrupados em dados['pedidos'] = {...}.
    """
    return _request('PUT', '/api/v1/complaint', params={'idpeticoes': idpeticoes}, json_data=dados)


def listar_peticoes_iniciais(**filtros):
    return _request('GET', '/api/v1/complaint', params=filtros)


def excluir_peticao_inicial(idpeticoes):
    return _request('DELETE', '/api/v1/complaint', params={'idpeticoes': idpeticoes})


def protocolar_inicial(idpeticoes, idprocessos, fk_peca, fk_certificado,
                        data_protocolo=None, fk_documento_auxiliar=None, nivel_sigilo_peticao=None):
    """
    Protocola a petição inicial (já com arquivo principal anexado via enviar_arquivo_principal
    e campos obrigatórios preenchidos via atualizar_processo_inicial).
    fk_documento_auxiliar e nivel_sigilo_peticao são OBRIGATÓRIOS quando o sistema é eProc.
    """
    params = {k: v for k, v in dict(
        idpeticoes=idpeticoes, idprocessos=idprocessos, fk_peca=fk_peca,
        fk_certificado=fk_certificado, data_protocolo=data_protocolo,
        fk_documento_auxiliar=fk_documento_auxiliar, nivel_sigilo_peticao=nivel_sigilo_peticao,
    ).items() if v is not None}
    return _request('POST', '/api/v1/complaint/send', params=params)


# --- Dados de referência para petição inicial (todos GET, sem parâmetro extra na maioria) ---

def comarcas(**filtros):
    return _request('GET', '/api/v1/complaint/district', params=filtros)


def atividades_economicas(**filtros):
    return _request('GET', '/api/v1/complaint/economic-activities', params=filtros)


def tipos_processo(**filtros):
    return _request('GET', '/api/v1/complaint/process-types', params=filtros)


def competencias(**filtros):
    return _request('GET', '/api/v1/complaint/specialties', params=filtros)


def anos_eleitorais(**filtros):
    return _request('GET', '/api/v1/complaint/election-years', params=filtros)


def orgaos_julgadores(**filtros):
    return _request('GET', '/api/v1/complaint/judging-bodies', params=filtros)


def areas(**filtros):
    return _request('GET', '/api/v1/complaint/areas', params=filtros)


def ritos(**filtros):
    return _request('GET', '/api/v1/complaint/procedures', params=filtros)


def tipos_justica(**filtros):
    return _request('GET', '/api/v1/complaint/justice-types', params=filtros)


def classes_processuais(**filtros):
    return _request('GET', '/api/v1/complaint/classes', params=filtros)


def assuntos(**filtros):
    return _request('GET', '/api/v1/complaint/subjects', params=filtros)


def motivos_prioridade_legal(**filtros):
    return _request('GET', '/api/v1/complaint/legal-priority-reasons', params=filtros)


def motivos_isencao_custas(**filtros):
    return _request('GET', '/api/v1/complaint/court-fee-waiver-reasons', params=filtros)


# ============================================================
# PETIÇÃO INTERMEDIÁRIA (pleading)
# ============================================================

def criar_peticao_intermediaria(fk_processo, fk_certificado, tutela_antecipada=None,
                                 custas_recolhidas=None, numero_guia=None, tipo=None):
    """
    Cria petição intermediária num processo já existente. `tipo` (opcional):
    'habilitacao_nos_autos' (só PJe), 'quesitos_parte_autora' ou
    'quesitos_complementares' (só eProc). Sem `tipo` = intermediária normal.
    Retorna idpeticoes (usar em enviar_arquivo_principal/protocolar_intermediaria).
    """
    dados = {k: v for k, v in dict(
        fk_processo=fk_processo, fk_certificado=fk_certificado,
        tutela_antecipada=tutela_antecipada, custas_recolhidas=custas_recolhidas,
        numero_guia=numero_guia, tipo=tipo,
    ).items() if v is not None}
    return _request('POST', '/api/v1/pleading', json_data=dados)


def intimacoes_pendentes_cumprimento(idprocessos):
    """Intimações pendentes de cumprimento no processo (para vincular à petição intermediária)."""
    return _request('GET', '/api/v1/pleading/notices-to-comply', params={'idprocessos': idprocessos})


def requerentes_disponiveis(idprocessos):
    """Partes do processo disponíveis como solicitantes (polo ativo/passivo) da intermediária."""
    return _request('GET', '/api/v1/pleading/requesters', params={'idprocessos': idprocessos})


def protocolar_intermediaria(idpeticoes, idprocessos, solicitantes, fk_peca=None,
                              data_protocolo=None, fk_documento_auxiliar=None,
                              nivel_sigilo_peticao=None, intimacoes=None,
                              declaracao_mandato_apresentado=None, protesto_mandato_oportuno=None):
    """
    Protocola a petição intermediária.
    `solicitantes` (OBRIGATÓRIO, lista): [{"id": <id_parte>, "polo": "ativo"|"passivo"}]
    ou [{"polo": "outros", "nome": "..."}] (nome obrigatório em TRT/TJRJ+dcp).
    `fk_peca` obrigatório para intermediária normal (dispensado em quesitos, já
    definida na criação). `intimacoes`: lista de ids a marcar como cumpridas.
    fk_documento_auxiliar e nivel_sigilo_peticao são obrigatórios quando o sistema é eProc.
    """
    params = {k: v for k, v in dict(
        idpeticoes=idpeticoes, idprocessos=idprocessos, fk_peca=fk_peca,
        data_protocolo=data_protocolo, fk_documento_auxiliar=fk_documento_auxiliar,
        nivel_sigilo_peticao=nivel_sigilo_peticao,
    ).items() if v is not None}
    body = {'solicitantes': solicitantes}
    if intimacoes is not None:
        body['intimacoes'] = intimacoes
    if declaracao_mandato_apresentado is not None:
        body['declaracao_mandato_apresentado'] = declaracao_mandato_apresentado
    if protesto_mandato_oportuno is not None:
        body['protesto_mandato_oportuno'] = protesto_mandato_oportuno
    return _request('POST', '/api/v1/pleading/send', params=params, json_data=body)


# ============================================================
# ANEXOS / ARQUIVO PRINCIPAL (comum a inicial e intermediária)
# Somente PDF é aceito em ambos os endpoints.
# ============================================================

def enviar_arquivo_principal(idpeticoes, idprocessos, caminho_pdf):
    """Upload do PDF principal da petição (peça gerada, já em papel timbrado)."""
    with open(caminho_pdf, 'rb') as f:
        return _request('POST', '/api/v1/complaintsandpleadings/file',
                         params={'idpeticoes': idpeticoes, 'idprocessos': idprocessos},
                         files={'file': f})


def enviar_anexo(idpeticoes, fk_documentos_tipos, caminho_pdf, descricao_outros=None):
    """
    Upload de anexo complementar (PDF). `fk_documentos_tipos` conforme
    tipos_de_anexo(idpeticoes). `descricao_outros` só quando o tipo é "Outros".
    """
    data = {}
    if descricao_outros:
        data['descricao_outros'] = descricao_outros
    with open(caminho_pdf, 'rb') as f:
        return _request('POST', '/api/v1/complaintsandpleadings/attachments',
                         params={'idpeticoes': idpeticoes, 'fk_documentos_tipos': fk_documentos_tipos},
                         json_data=None, files={'file': f, **{k: (None, v) for k, v in data.items()}})


def tipos_de_anexo(idpeticoes=None):
    params = {'idpeticoes': idpeticoes} if idpeticoes else {}
    return _request('GET', '/api/v1/complaintsandpleadings/attachment/types', params=params)


def listar_anexos(idpeticoes):
    return _request('GET', '/api/v1/complaintsandpleadings/attachments/list', params={'idpeticoes': idpeticoes})


def tribunais_disponiveis(**filtros):
    return _request('GET', '/api/v1/complaintsandpleadings/courts', params=filtros)


def tipos_de_peca(**filtros):
    """Peças disponíveis (fk_peca) por tribunal/sistema/evento - usado no protocolo."""
    return _request('GET', '/api/v1/complaintsandpleadings/types', params=filtros)


def status_peticoes(**filtros):
    return _request('POST', '/api/v1/complaintsandpleadings/status', json_data=filtros)


# ============================================================
# USUÁRIOS DO WORKSPACE
# ============================================================

def listar_usuarios():
    return _request('GET', '/api/v1/users')


def cadastrar_usuario(**dados):
    return _request('POST', '/api/v1/users', json_data=dados)


def atualizar_usuario(**dados):
    return _request('PUT', '/api/v1/users', json_data=dados)


def excluir_usuario(id_usuario):
    return _request('DELETE', '/api/v1/users', params={'id': id_usuario})


# ============================================================
# DOCUMENTOS / MODELOS
# ============================================================

def listar_documentos(**filtros):
    return _request('GET', '/api/v1/docs', params=filtros)


def enviar_documento(caminho_arquivo, **params_extra):
    with open(caminho_arquivo, 'rb') as f:
        return _request('POST', '/api/v1/docs', params=params_extra, files={'file': f})


def excluir_documento(id_documento):
    return _request('DELETE', '/api/v1/docs', params={'id': id_documento})


def baixar_documento(id_documento):
    return _request('GET', '/api/v1/docs/download', params={'id': id_documento})


def listar_modelos_documento(**filtros):
    return _request('GET', '/api/v1/docs/models', params=filtros)


def excluir_modelo_documento(id_modelo):
    return _request('DELETE', '/api/v1/docs/models', params={'id': id_modelo})


# ============================================================
# PROTOCOLOS (filings)
# ============================================================

def listar_protocolos(**filtros):
    """Histórico de protocolos realizados (petições enviadas) no workspace."""
    return _request('GET', '/api/v1/filings', params=filtros)
