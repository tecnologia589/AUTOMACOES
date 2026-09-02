"""
Webhook FastAPI chamado pela N8N.

N8N monitora tarefas ADVBOX atribuidas ao usuario-agente (CORBELINO.IA) e dispara:
  POST /tarefa  { "task_id": 12345 }  Authorization: Bearer <AGENTE_OP_TOKEN>

O webhook retorna 202 imediatamente e processa em background.

Rodar:
  cd "CORBELINO_ADVOGADOS"
  uvicorn OPERACIONAL.agente_operacional.webhook:app --host 0.0.0.0 --port 8787
"""
import logging
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException

from .config import AGENTE_OP_TOKEN, LOG_DIR
from .orchestrator import processar_tarefa

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'agente_{datetime.now():%Y-%m}.log', encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger('agente_op')

app = FastAPI(title='Agente Operacional CORBELINO_ADVOGADOS', version='1.0')


def _auth(authorization: str):
    if not AGENTE_OP_TOKEN:
        raise HTTPException(500, 'AGENTE_OP_TOKEN nao configurado em config/.env')
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Authorization ausente')
    if authorization.split(' ', 1)[1] != AGENTE_OP_TOKEN:
        raise HTTPException(401, 'Token invalido')


@app.get('/healthcheck')
def healthcheck():
    return {'status': 'ok', 'servico': 'agente_operacional_corbelino_advogados'}


@app.post('/tarefa', status_code=202)
def receber_tarefa(payload: dict, bg: BackgroundTasks, authorization: str = Header(None)):
    _auth(authorization)
    # Aceita 3 formatos:
    #   {"task": {...}}       -> tarefa completa do ADVBOX (preferido)
    #   {"task_id": 123}      -> so o ID, agente busca depois
    #   {...campos da tarefa} -> tarefa direto no payload root
    tarefa_completa = payload.get('task')
    if not tarefa_completa and 'id' in payload and ('users' in payload or 'task' in payload):
        tarefa_completa = payload
    task_id = (tarefa_completa or {}).get('id') or payload.get('task_id') or payload.get('id')
    if not task_id:
        raise HTTPException(400, 'task_id ou task obrigatorio no payload')
    log.info(f'Tarefa {task_id} recebida via webhook (completa={bool(tarefa_completa)})')
    bg.add_task(processar_tarefa, int(task_id), tarefa_completa)
    return {'status': 'aceito', 'task_id': task_id}
