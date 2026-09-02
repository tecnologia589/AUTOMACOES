"""
Handler generico para tarefas que nao sao peca juridica nem notificacao.
Exemplos: 'anotar movimentacao X', 'solicitar documento Y', 'verificar publicacao Z'.

Estrategia: pede ao Claude para produzir um parecer/resposta baseado no contexto
e devolve na tarefa como resumo - NAO altera ADVBOX alem do retorno (regra:
'nunca modificar ADVBOX sem autorizacao explicita').
"""
import logging

from ..config import ESCRITORIO_NOME
from ..llm_client import triagem
from .base import montar_bloco_contexto

log = logging.getLogger('agente_op.movimentacao')


def executar(tipo_tarefa: str, instrucao: str, contexto: dict) -> dict:
    bloco = montar_bloco_contexto(contexto)
    prompt = f"""
Voce e assistente operacional do escritorio {ESCRITORIO_NOME}.

A equipe atribuiu a seguinte tarefa ao agente (CORBELINO.IA):

TIPO: {tipo_tarefa}
INSTRUCAO: {instrucao or '(sem instrucao adicional)'}

CONTEXTO:
{bloco}

TAREFA:
- Interprete o que foi pedido.
- Produza uma resposta objetiva e pratica.
- Se precisar que um humano autorize algo no ADVBOX, indique claramente qual acao e porque.
- NAO modifique nada no ADVBOX por conta propria.
- Se identificar que a tarefa deveria ter sido classificada como peca juridica ou notificacao de cliente,
  informe isso no inicio da resposta.

Retorne a resposta formatada para ser colada no comment da tarefa.
""".strip()

    try:
        resposta = triagem(prompt)
    except Exception as e:
        return {
            'sucesso': False,
            'titulo': 'FALHA AO PROCESSAR TAREFA',
            'resumo': 'Nao foi possivel processar a tarefa automaticamente.',
            'detalhes': str(e),
        }

    return {
        'sucesso': True,
        'titulo': tipo_tarefa or 'TAREFA OPERACIONAL',
        'resumo': resposta,
    }
