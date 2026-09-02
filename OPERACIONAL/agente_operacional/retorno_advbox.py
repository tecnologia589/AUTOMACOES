"""
Fecha a tarefa no ADVBOX:
  - Cria nova tarefa (publicacao) atribuida de volta a quem pediu, com o resultado
  - Sinaliza "FEITO" + inclui link do Drive do documento gerado
    (regra: sempre incluir links nos comments)
  - From = AGENTE_IA_ID (retorno aparece em nome da propria CORBELINO.IA)
  - Em caso de sucesso, grava um marcador maquina-legivel ([CORBELINOIA-FEITO #id])
    que permite a CORBELINO.IA detectar, em varreduras futuras, que a tarefa ja foi
    feita - sem refazer o trabalho (ver `ja_concluida_no_advbox`).
  - Notifica via WhatsApp cada destinatario (resolve "tarefa fantasma" no ADVBOX)
"""
import logging
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'INTEGRACOES'))
from advbox_integration import criar_publicacao, listar_tarefas  # noqa
from atendedireito_integration import enviar_texto_por_telefone  # noqa

from .config import (
    AGENTE_IA_ID, TASK_TYPE_ACOMPANHAMENTO, USER_PHONES,
    NOTIFICAR_WHATSAPP, MARCADOR_CONCLUSAO,
)

log = logging.getLogger('agente_op.retorno')


# ============================================================
# IDEMPOTENCIA VIA ADVBOX (fonte da verdade)
# ============================================================
# Campos textuais de um post/publicacao onde o comentario pode aparecer na leitura
# (criamos com 'comments'; o GET /posts costuma devolver em 'notes').
_CAMPOS_TEXTO_POST = ('notes', 'comments', 'comment', 'task', 'description', 'title', 'text', 'body')


def _texto_post(post: dict) -> str:
    """Concatena os campos textuais de um post para busca do marcador de conclusao."""
    partes = []
    for c in _CAMPOS_TEXTO_POST:
        v = post.get(c)
        if isinstance(v, str) and v.strip():
            partes.append(v)
    return '\n'.join(partes)


def _marcador_feito(task_id) -> str:
    """Marcador embutido no comentario de retorno (ex.: '[CORBELINOIA-FEITO #12345]')."""
    return f'[{MARCADOR_CONCLUSAO} #{task_id}]'


def ja_concluida_no_advbox(task_id, lawsuit_id) -> bool:
    """
    Idempotencia consultando o proprio ADVBOX (sobrevive a restart, troca de maquina
    ou perda do cache local).

    Antes de (re)executar uma tarefa, a CORBELINO.IA varre os andamentos/publicacoes do
    processo. Se encontrar o marcador de conclusao que ela mesma deixou referenciando
    esta tarefa original (ex.: "[CORBELINOIA-FEITO #12345]"), retorna True -> nao refazer.

    Sem lawsuit_id nao da pra varrer o processo: retorna False e deixa o cache local
    decidir.
    """
    if not lawsuit_id:
        return False
    alvo = re.compile(rf'{re.escape(MARCADOR_CONCLUSAO)}\s*#\s*{int(task_id)}\b', re.IGNORECASE)
    try:
        posts = listar_tarefas(lawsuit_id=lawsuit_id)
    except Exception as e:
        log.warning(f'[{task_id}] nao consegui varrer andamentos do processo {lawsuit_id}: {e}')
        return False  # em duvida, deixa seguir (o cache local ainda protege)
    for p in posts:
        if alvo.search(_texto_post(p)):
            log.info(f'[{task_id}] marcador de conclusao encontrado no processo '
                     f'{lawsuit_id} - tarefa ja feita pela CORBELINO.IA, nao sera refeita')
            return True
    return False


def _notificar_whatsapp(task_id, destinatarios, titulo, link_doc):
    """Envia WhatsApp para cada destinatario interno avisando que a peca esta pronta.
    Resolve o problema de 'tarefa fantasma' no ADVBOX (nao da pra concluir via API)."""
    if not NOTIFICAR_WHATSAPP:
        return
    enviados = []
    pulados = []
    telefones_unicos = set()  # nao enviar 2x pro mesmo numero
    for uid in destinatarios:
        tel = USER_PHONES.get(uid, '').strip()
        if not tel:
            pulados.append(f'user_id={uid} (sem telefone)')
            continue
        if tel in telefones_unicos:
            pulados.append(f'user_id={uid} (telefone duplicado)')
            continue
        telefones_unicos.add(tel)

        link_tarefa = f'https://app.advbox.com.br/0?t={task_id}'
        msg = (
            f'CORBELINO.IA - peca pronta\n\n'
            f'{titulo}\n\n'
        )
        if link_doc:
            msg += f'Documento: {link_doc}\n\n'
        msg += (
            f'Tarefa original: {link_tarefa}\n'
            f'Apos revisar, conclua manualmente no ADVBOX.'
        )

        try:
            ok = enviar_texto_por_telefone(tel, msg)
            if ok:
                enviados.append(f'{uid}->{tel}')
            else:
                pulados.append(f'user_id={uid} (envio falhou)')
        except Exception as e:
            pulados.append(f'user_id={uid} (excecao: {e})')

    if enviados:
        log.info(f'[{task_id}] WhatsApp enviado para: {enviados}')
    if pulados:
        log.info(f'[{task_id}] WhatsApp pulado: {pulados}')


def _prazo_amanha():
    d = datetime.now() + timedelta(days=1)
    return d.strftime('%Y-%m-%d')


def _tipo_tarefa_padrao():
    """Tipo ACOMPANHAMENTO (settings['tasks'] do ADVBOX), configurado no .env."""
    return TASK_TYPE_ACOMPANHAMENTO


def entregar_resultado(task_id, destinatarios, lawsuit_id, resultado: dict):
    """
    destinatarios: list[int] - co-destinatarios da tarefa original
    resultado = {
        'sucesso': bool,
        'titulo': str,
        'resumo': str,
        'doc_link': str | None,
        'doc_nome': str | None,
        'detalhes': str | None,
    }
    """
    if not destinatarios:
        log.warning(f'[{task_id}] sem co-destinatarios, nao posso devolver tarefa')
        return

    titulo = resultado.get('titulo') or 'RESULTADO AGENTE OPERACIONAL'
    resumo = resultado.get('resumo') or ''
    link = resultado.get('doc_link')
    nome = resultado.get('doc_nome')
    detalhes = resultado.get('detalhes') or ''
    sucesso = bool(resultado.get('sucesso'))
    status_icone = 'FEITO' if sucesso else 'ATENCAO'

    linhas = [
        f'[{status_icone}] {titulo}',
        '',
        resumo,
    ]
    if link:
        linhas += ['', f'Documento: {nome or "arquivo"}', f'Link: {link}']
    if detalhes:
        linhas += ['', '--- detalhes ---', detalhes]
    if sucesso:
        # Marcador maquina-legivel: assinala que ESTA tarefa ja foi feita pela CORBELINO.IA.
        # Nas varreduras seguintes, `ja_concluida_no_advbox` acha isto e nao refaz.
        linhas += ['', _marcador_feito(task_id)]
    linhas += [
        '',
        '=' * 50,
        f'>> APOS REVISAO, FAVOR CONCLUIR A TAREFA ORIGINAL #{task_id} NO ADVBOX <<',
        '(A API do ADVBOX ainda nao permite conclusao automatica via integracao)',
        '=' * 50,
    ]
    comments = '\n'.join(linhas)

    tipo_id = _tipo_tarefa_padrao()
    if not tipo_id:
        log.warning(f'[{task_id}] tipo de tarefa padrao nao configurado '
                    f'(ADVBOX_TASK_TYPE_ACOMPANHAMENTO), usando 1')
        tipo_id = 1

    try:
        criar_publicacao(
            lawsuit_id=lawsuit_id,
            task_id=tipo_id,
            guest_ids=list(destinatarios),
            comments=comments,
            from_id=AGENTE_IA_ID,     # retorno do agente aparece como da propria CORBELINO.IA
            date_deadline=_prazo_amanha(),
            urgent=False,
        )
        log.info(f'[{task_id}] retorno entregue para users {destinatarios}')
    except Exception as e:
        log.exception(f'[{task_id}] falha ao criar retorno: {e}')
        return  # se falhou criar tarefa, nao manda WhatsApp

    # Notifica via WhatsApp - resolve "tarefa fantasma" no ADVBOX
    _notificar_whatsapp(task_id, destinatarios, titulo, link)


def registrar_erro(task_id, destinatarios, lawsuit_id, msg_erro: str):
    """Notifica falha de execucao."""
    resultado = {
        'sucesso': False,
        'titulo': 'FALHA NA EXECUCAO AUTOMATICA',
        'resumo': 'O agente operacional nao conseguiu concluir a tarefa.',
        'detalhes': msg_erro[:2000],
    }
    entregar_resultado(task_id, destinatarios, lawsuit_id, resultado)
