# Agente Operacional CORBELINO_ADVOGADOS (CORBELINO.IA)

Agente autonomo que recebe tarefas do ADVBOX (atribuidas ao usuario-agente **CORBELINO.IA**) via webhook disparado pela N8N, produz o resultado (peca juridica, notificacao de cliente, resposta operacional) e devolve a tarefa para quem pediu com o link do documento.

## Fluxo

```
Equipe do escritorio
   |
   v  (atribui tarefa a CORBELINO.IA no ADVBOX)
ADVBOX  ----polling/webhook---->  N8N
                                    |
                                    v  POST /tarefa {task_id}
                            Agente Operacional (FastAPI)
                                    |
                                    v
                    +---------------+---------------+
                    |               |               |
              peca juridica   notificar cliente  movimentacao
              (Opus +          (Atende Direito)   (Sonnet)
               POP cacheado)
                    |               |               |
                    +---------------+---------------+
                                    |
                                    v
                          Drive (salva doc) + ADVBOX (devolve tarefa)
```

## Deteccao de tipo

A partir do campo `task` + `notes` da tarefa:

- **peca**: inicial, contestacao, replica, razoes finais, recurso ordinario/especial, contrarrazoes, embargos, manifestacao, memoriais
- **assinatura**: enviar documento ao ZapSign para assinatura
- **consultar_assinatura**: consultar status de assinatura no ZapSign
- **sync_assinados**: baixar documentos assinados do ZapSign para o Drive
- **notificacao**: notificar cliente, whatsapp, avisar cliente
- **movimentacao**: fallback para qualquer outro tipo

## Variaveis de ambiente (config/.env)

Veja `config/.env.example`. As principais para o agente:

```
ANTHROPIC_API_KEY=
ADVBOX_API_TOKEN=
ZAPSIGN_API_TOKEN=
ATENDE_DIREITO_TOKEN=
AGENTE_OP_TOKEN=<token_forte_para_N8N>
AGENTE_OP_PORT=8787
ADVBOX_USER_AGENTE=<id do usuario-agente CORBELINO.IA no ADVBOX>
ADVBOX_TASK_TYPE_ACOMPANHAMENTO=<id do tipo de tarefa para retornos>
ESCRITORIO_ASSINATURA=Dr. Paulo Alexandre Soares Corbelino - OAB/MT 33.267 - Cáceres/MT
ESCRITORIO_EMAIL_RESPONSAVEL=
```

Os papeis funcionais (RESPONSAVEL / OPERACIONAL / FINANCEIRO) sao lidos de `config/equipe.py`.

## Timbrado

O escritorio deve fornecer o timbrado DELE em **`config/timbrado_modelo.docx`** (com cabecalho, logo e rodape proprios). O motor de formatacao abre esse arquivo como base, limpa o corpo e insere a peca. Sem o timbrado, a geracao de pecas falha com erro explicito.

## Deploy local

```bash
cd "CORBELINO_ADVOGADOS"
pip install fastapi uvicorn anthropic pypdf python-docx
uvicorn OPERACIONAL.agente_operacional.webhook:app --host 0.0.0.0 --port 8787
```

Expor externamente para a N8N via tunnel (Cloudflare Tunnel, ngrok, etc).

## Configuracao N8N (passo a passo)

Workflow pronto para importar: [`n8n_workflow.json`](n8n_workflow.json).

### 1. Importar workflow
- N8N -> Workflows -> menu "..." -> Import from File -> selecionar `n8n_workflow.json`

### 2. Substituir placeholders nos nodos
- **ADVBOX: listar tarefas** -> header `Authorization` -> trocar `SEU_ADVBOX_TOKEN_AQUI` pelo valor de `ADVBOX_API_TOKEN` do `.env`
- **So CORBELINO.IA pendente** -> trocar `SEU_ADVBOX_USER_AGENTE` pelo ID do usuario-agente no ADVBOX
- **Disparar Agente Operacional** -> header `Authorization` -> trocar `SEU_AGENTE_OP_TOKEN_AQUI` pelo valor de `AGENTE_OP_TOKEN` do `.env`
- Se a N8N nao roda na mesma maquina do agente, trocar `http://127.0.0.1:8787/tarefa` pela URL publica do tunnel

### 3. Ativar workflow
- Toggle "Active" no canto superior direito

### Como funciona
- A cada 2 minutos: N8N consulta `GET /posts?per_page=200`
- Filtra apenas tarefas com o usuario-agente como destinatario pendente
- Para cada tarefa: dispara `POST /tarefa` no agente
- O agente faz **idempotencia interna** (`logs/tarefas_processadas.json`) e **via ADVBOX** (marcador no processo), entao tarefas ja processadas sao ignoradas mesmo se vierem novamente no polling
- O agente retorna 202 imediatamente; processamento real roda em background

### Cache de idempotencia
- Arquivo: `OPERACIONAL/agente_operacional/logs/tarefas_processadas.json`
- Para reprocessar uma tarefa, basta remover o ID do arquivo

## Seguranca

- Webhook protegido por Bearer token (`AGENTE_OP_TOKEN`)
- Retorno no ADVBOX sempre com `from = usuario-agente (CORBELINO.IA)`
- Agente NUNCA altera dados do ADVBOX, apenas **cria** a tarefa de retorno
- Todos os documentos gerados ficam marcados como "PARA REVISAO" da equipe

## Logs

`OPERACIONAL/agente_operacional/logs/agente_<YYYY-MM>.log`

## Arquivos

- `webhook.py` - FastAPI (endpoint `/tarefa` + `/healthcheck`)
- `orchestrator.py` - detecta tipo e despacha
- `context_loader.py` - puxa processo, cliente, pasta Drive, POP
- `llm_client.py` - wrapper Anthropic (Opus para pecas, Sonnet para triagem)
- `retorno_advbox.py` - cria tarefa de retorno + idempotencia via ADVBOX
- `template_engine.py` - aplica o timbrado e a formatacao do escritorio
- `escritorio_format.py` - motor de formatacao fiel (margens, fonte, recuo, citacoes)
- `peca_escritorio_engine.py` - geracao de peca com DNA do escritorio (skills /peca-escritorio e /formatar-escritorio)
- `acentuacao.py` - safety net de acentuacao PT-BR
- `handlers/peca_juridica.py` - gera qualquer peca usando POP
- `handlers/notificar_cliente.py` - mensagem WhatsApp via Atende Direito
- `handlers/enviar_assinatura.py` - envia documento ao ZapSign
- `handlers/consultar_assinatura.py` - consulta status de assinatura
- `handlers/sincronizar_assinados.py` - baixa assinados do ZapSign para o Drive
- `handlers/movimentacao.py` - fallback operacional
- `config.py` - IDs e constantes (lidos do .env / equipe.py)
- `REFERENCIAS/` - DNA de escrita + pecas-modelo PROPRIAS do escritorio

## Onboarding (checklist)

1. Preencher `config/.env` com as credenciais do escritorio (ADVBOX, ZapSign, Atende Direito, Anthropic).
2. Definir o ID do usuario-agente (`ADVBOX_USER_AGENTE`) e o tipo de tarefa de retorno (`ADVBOX_TASK_TYPE_ACOMPANHAMENTO`).
3. Preencher os IDs da equipe em `config/equipe.py`.
4. Colocar o timbrado do escritorio em `config/timbrado_modelo.docx`.
5. Depositar 1-2 pecas-modelo PROPRIAS em `REFERENCIAS/` e preencher `REFERENCIAS/DNA_TOM_ESCRITA.md`.
6. Importar e ativar o workflow no N8N.
7. Testar com 1 tarefa real atribuida ao usuario-agente.
