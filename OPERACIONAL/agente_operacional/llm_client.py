"""
Wrapper Anthropic SDK com prompt caching para o POP (conteudo estatico por peca).
Regra: pecas juridicas usam Opus.
"""
import logging
from anthropic import Anthropic

from .config import (
    ANTHROPIC_API_KEY, LLM_MODEL_PECA, LLM_MODEL_TRIAGEM,
    LLM_MAX_TOKENS, LLM_THINKING_BUDGET,
)

log = logging.getLogger('agente_op.llm')
_client = None


def client():
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError('ANTHROPIC_API_KEY ausente em config/.env')
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def gerar_peca(system_prompt: str, pop_texto: str, user_prompt: str,
               thinking: bool = True) -> str:
    """
    Gera peca juridica usando Opus com:
      - system prompt (instrucoes do escritorio)
      - POP como bloco cacheado (economiza em geracoes repetidas)
      - prompt do usuario com contexto variavel
      - extended thinking (se thinking=True)
    """
    system = [
        {'type': 'text', 'text': system_prompt},
    ]
    if pop_texto:
        system.append({
            'type': 'text',
            'text': f'\n\n=== POP (Procedimento Operacional Padrao) ===\n{pop_texto}',
            'cache_control': {'type': 'ephemeral'},
        })

    kwargs = {
        'model': LLM_MODEL_PECA,
        'max_tokens': LLM_MAX_TOKENS,
        'system': system,
        'messages': [{'role': 'user', 'content': user_prompt}],
    }
    if thinking:
        kwargs['thinking'] = {'type': 'enabled', 'budget_tokens': LLM_THINKING_BUDGET}

    resp = client().messages.create(**kwargs)
    partes = [b.text for b in resp.content if getattr(b, 'type', None) == 'text']
    usage = getattr(resp, 'usage', None)
    if usage:
        log.info(
            f'LLM tokens in={usage.input_tokens} out={usage.output_tokens} '
            f'cache_read={getattr(usage, "cache_read_input_tokens", 0)} '
            f'cache_write={getattr(usage, "cache_creation_input_tokens", 0)}'
        )
    return '\n'.join(partes).strip()


def triagem(user_prompt: str, system_prompt: str = '') -> str:
    """Chamadas rapidas e baratas (Sonnet) para mensagens curtas ou classificacao."""
    kwargs = {
        'model': LLM_MODEL_TRIAGEM,
        'max_tokens': 2000,
        'messages': [{'role': 'user', 'content': user_prompt}],
    }
    if system_prompt:
        kwargs['system'] = system_prompt
    resp = client().messages.create(**kwargs)
    return ''.join(b.text for b in resp.content if getattr(b, 'type', None) == 'text').strip()
