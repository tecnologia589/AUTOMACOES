"""
Orquestrador principal.
Recebe um task_id do ADVBOX, carrega contexto e despacha para o handler correto.

Inclui idempotencia: se a mesma task_id chegar duas vezes (polling do N8N),
a segunda execucao e ignorada.
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from threading import Lock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'INTEGRACOES'))
from advbox_integration import _request as advbox_request  # noqa

from .config import AGENTE_IA_ID, LOG_DIR
from .context_loader import carregar_contexto
from .retorno_advbox import entregar_resultado, registrar_erro, ja_concluida_no_advbox
from .handlers import (
    peca_juridica, notificar_cliente, movimentacao,
    enviar_assinatura, sincronizar_assinados, consultar_assinatura,
)

log = logging.getLogger('agente_op.orchestrator')

# ============================================================
# IDEMPOTENCIA - cache de tarefas ja processadas
# ============================================================
_CACHE_FILE = LOG_DIR / 'tarefas_processadas.json'
_cache_lock = Lock()


def _carregar_cache():
    if not _CACHE_FILE.exists():
        return {}
    try:
        return json.loads(_CACHE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _salvar_cache(cache):
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')


def _ja_processada(task_id):
    """True se ja terminou OU se esta em processamento ha menos de 10 min."""
    from datetime import timedelta
    with _cache_lock:
        cache = _carregar_cache()
        entrada = cache.get(str(task_id))
        if not entrada:
            return False
        if entrada.get('status') == 'em_processamento':
            try:
                quando = datetime.fromisoformat(entrada['quando'])
                if datetime.now() - quando < timedelta(minutes=10):
                    return True
                return False  # travou ha mais de 10 min, permite reprocessar
            except Exception:
                return True
        return True


def _marcar_em_processamento(task_id):
    """Marca a tarefa como em processamento - bloqueia execucoes paralelas."""
    with _cache_lock:
        cache = _carregar_cache()
        cache[str(task_id)] = {
            'status': 'em_processamento',
            'quando': datetime.now().isoformat(timespec='seconds'),
            'resumo': '',
        }
        _salvar_cache(cache)


def _marcar_processada(task_id, status, resumo=''):
    with _cache_lock:
        cache = _carregar_cache()
        cache[str(task_id)] = {
            'status': status,
            'quando': datetime.now().isoformat(timespec='seconds'),
            'resumo': resumo[:200],
        }
        _salvar_cache(cache)


# Palavras-chave para deteccao de tipo (tipo da tarefa OU texto do comment)
PECAS = [
    'inicial', 'peticao inicial',
    'contestacao', 'contestação',
    'replica', 'réplica',
    'razoes finais', 'razões finais', 'razoes', 'razões',
    'recurso ordinario', 'recurso ordinário',
    'recurso especial', 'recurso extraordinario', 'recurso extraordinário',
    'contrarrazoes', 'contrarrazões',
    'embargos', 'manifestacao', 'manifestação',
    'memoriais', 'peticao', 'petição',
    'reanalise', 'reanálise', 'analise de peca', 'análise de peça',
    'pecas processuais', 'peças processuais',
    'desconsideracao', 'desconsideração',
    'parecer', 'minuta',
]
NOTIFICACOES = [
    'notificar cliente', 'notificar', 'whatsapp', 'atende direito',
    'avisar cliente', 'comunicar cliente',
]
ASSINATURAS = [
    'zapsign', 'zap sign', 'assinar', 'assinatura', 'assinaturas',
    'carregar contrato', 'enviar para assinar', 'enviar para assinatura',
    'subir no zapsign', 'subir no zap', 'subir contrato', 'assinatura eletronica',
    'assinatura eletrônica', 'assinatura digital',
]
CONSULTAR_ASSINATURA = [
    'consultar zapsign', 'status zapsign', 'status da assinatura',
    'verificar assinatura', 'checar assinatura', 'ver assinatura',
    'status do contrato', 'situacao da assinatura', 'situação da assinatura',
]
SYNC_ASSINADOS = [
    'sincronizar assinados', 'sincronizar zapsign', 'puxar zapsign',
    'baixar assinados', 'sync zapsign', 'sync assinados',
    'atualizar assinados', 'pegar assinados',
]


def _normaliza(s):
    return (s or '').lower().replace('ç', 'c').replace('ã', 'a').replace('á', 'a')\
        .replace('é', 'e').replace('ê', 'e').replace('í', 'i').replace('ó', 'o')\
        .replace('ô', 'o').replace('ú', 'u').strip()


def detectar_tipo(tarefa):
    """Detecta a categoria da acao:
    'sync_assinados' | 'consultar_assinatura' | 'assinatura' | 'peca' | 'notificacao' | 'movimentacao'.
    """
    campos = [tarefa.get('task'), tarefa.get('notes')]
    texto = _normaliza(' '.join(str(c) for c in campos if c))
    # Consultar/sync tem prioridade pois sao subtipos de assinatura
    if any(p in texto for p in SYNC_ASSINADOS):
        return 'sync_assinados'
    if any(p in texto for p in CONSULTAR_ASSINATURA):
        return 'consultar_assinatura'
    # assinatura vem antes de peca pois costuma vir junto com palavras de "peca" tipo "contrato"
    if any(p in texto for p in ASSINATURAS):
        return 'assinatura'
    if any(p in texto for p in PECAS):
        return 'peca'
    if any(p in texto for p in NOTIFICACOES):
        return 'notificacao'
    return 'movimentacao'


def buscar_tarefa(task_id):
    """
    Busca a tarefa no ADVBOX. GET individual /posts/{id} retorna 401 (limitacao da API),
    entao usa listagem. O agente tem poucas tarefas pendentes, geralmente cabe no per_page=200.
    """
    r = advbox_request('GET', '/posts', params={'per_page': 200})
    posts = r.get('data', []) if isinstance(r, dict) else (r or [])
    for p in posts:
        if str(p.get('id')) == str(task_id):
            return p
    return None


def _agente_pendente(tarefa):
    """True se o agente (CORBELINO.IA) esta nos destinatarios e ainda nao completou."""
    for u in tarefa.get('users', []):
        if u.get('user_id') == AGENTE_IA_ID and not u.get('completed'):
            return True
    return False


def _co_destinatarios(tarefa):
    """Retorna lista de user_ids dos demais destinatarios (excluindo o agente).
    Sao essas pessoas que recebem o resultado de volta.
    FALLBACK: se a tarefa so tem o agente, devolve para o responsavel operacional configurado."""
    from .config import OPERACIONAL_ID, RESPONSAVEL_ID
    co = [u.get('user_id') for u in tarefa.get('users', [])
            if u.get('user_id') and u.get('user_id') != AGENTE_IA_ID]
    if not co:
        fallback = OPERACIONAL_ID or RESPONSAVEL_ID
        if fallback:
            log.info(f'co_destinatarios vazio - aplicando fallback para {fallback}')
            co = [fallback]
        else:
            log.warning('co_destinatarios vazio e nenhum fallback configurado em config/equipe.py')
    return co


def processar_tarefa(task_id: int, tarefa: dict = None):
    """Entry point chamado pelo webhook em background.
    Se tarefa for fornecida (n8n manda completa), pula o GET; senao busca."""
    if _ja_processada(task_id):
        log.info(f'[{task_id}] Ja processada anteriormente (ou em processamento), ignorando')
        return

    # Lock: marca como em processamento ANTES de comecar (evita execucoes paralelas)
    _marcar_em_processamento(task_id)
    log.info(f'[{task_id}] Iniciando processamento')
    try:
        if not tarefa:
            tarefa = buscar_tarefa(task_id)
        if not tarefa:
            log.warning(f'[{task_id}] Tarefa nao encontrada no ADVBOX')
            _marcar_processada(task_id, 'nao_encontrada')
            return

        # Valida destinatario: o agente precisa estar em users[] com completed=null
        if not _agente_pendente(tarefa):
            log.info(f'[{task_id}] Ignorada: CORBELINO.IA nao e destinataria pendente')
            _marcar_processada(task_id, 'ignorada_destinatario')
            return

        co_destinatarios = _co_destinatarios(tarefa)
        lawsuit_id = tarefa.get('lawsuits_id') or tarefa.get('lawsuit_id')
        instrucao = tarefa.get('notes') or ''
        tipo_tarefa = tarefa.get('task') or ''

        log.info(f'[{task_id}] co_destinatarios={co_destinatarios} '
                 f'lawsuit={lawsuit_id} tipo="{tipo_tarefa}"')

        # Idempotencia via ADVBOX (alem do cache local): antes de executar, varre os
        # andamentos do processo. Se o agente ja registrou "feito com link" para
        # esta tarefa, nao refaz - sobrevive a restart/troca de maquina/perda do cache.
        if ja_concluida_no_advbox(task_id, lawsuit_id):
            log.info(f'[{task_id}] Ja concluida pela CORBELINO.IA no ADVBOX - ignorando (nao refaz)')
            _marcar_processada(task_id, 'ja_concluida_advbox')
            return

        categoria = detectar_tipo(tarefa)
        log.info(f'[{task_id}] categoria detectada: {categoria}')

        contexto = carregar_contexto(
            lawsuit_id=lawsuit_id,
            tipo_tarefa=tipo_tarefa,
            instrucao=instrucao,
            categoria=categoria,
            tarefa_advbox=tarefa,
        )

        if categoria == 'sync_assinados':
            resultado = sincronizar_assinados.executar(tipo_tarefa, instrucao, contexto)
        elif categoria == 'consultar_assinatura':
            resultado = consultar_assinatura.executar(tipo_tarefa, instrucao, contexto)
        elif categoria == 'assinatura':
            resultado = enviar_assinatura.executar(tipo_tarefa, instrucao, contexto)
        elif categoria == 'peca':
            resultado = peca_juridica.executar(tipo_tarefa, instrucao, contexto)
        elif categoria == 'notificacao':
            resultado = notificar_cliente.executar(tipo_tarefa, instrucao, contexto)
        else:
            resultado = movimentacao.executar(tipo_tarefa, instrucao, contexto)

        entregar_resultado(task_id, co_destinatarios, lawsuit_id, resultado)
        _marcar_processada(task_id, 'sucesso' if resultado.get('sucesso') else 'erro_handler',
                           resultado.get('titulo', ''))
        log.info(f'[{task_id}] Concluido')

    except Exception as e:
        log.exception(f'[{task_id}] Falha: {e}')
        try:
            t = tarefa if isinstance(tarefa, dict) else {}
            registrar_erro(task_id, _co_destinatarios(t),
                           t.get('lawsuits_id') or t.get('lawsuit_id'), str(e))
        except Exception:
            pass
        _marcar_processada(task_id, 'excecao', str(e)[:200])
