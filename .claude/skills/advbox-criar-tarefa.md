---
name: advbox-criar-tarefa
description: Cria tarefa/publicação no ADVBOX via API (POST /posts)
trigger: /advbox-criar-tarefa
---

# Skill: Criar Tarefa no ADVBOX

Usa `python -c` para chamar a função `criar_publicacao` do módulo `INTEGRACOES/advbox_integration.py`.

## Endpoint: POST /posts

**URL:** `https://app.advbox.com.br/api/v1/posts`
**Auth:** Bearer Token

## Campos obrigatórios
| Campo API | Tipo | Descrição |
|-----------|------|-----------|
| `from` | **string** | ID do criador da tarefa — **SEMPRE o usuário responsável padrão** (`<ADVBOX_USER_RESPONSAVEL>`, vem do `config/.env` / `config/equipe.py`) |
| `guests` | array<integer> | IDs dos responsáveis (mínimo 1, sem duplicados) |
| `tasks_id` | **string** | ID do tipo de tarefa (buscar via settings) |
| `lawsuits_id` | **string** | ID do processo associado |
| `start_date` | string | Data início — aceita YYYY-MM-DD ou DD/MM/YYYY |

## Campos opcionais
| Campo API | Tipo | Descrição |
|-----------|------|-----------|
| `start_time` | string | Hora início HH:MM |
| `end_date` | string | Data término YYYY-MM-DD ou DD/MM/YYYY |
| `end_time` | string | Hora término HH:MM (requer end_date) |
| `date_deadline` | string | Prazo YYYY-MM-DD ou DD/MM/YYYY |
| `local` | string | Local da tarefa |
| `comments` | string | Descrição detalhada — **mínimo 10 caracteres** |
| `urgent` | boolean | Flag urgente |
| `important` | boolean | Flag importante |
| `display_schedule` | boolean | Exibir na agenda |

## Regras do escritório
1. **`from` SEMPRE o usuário responsável padrão** (`<ADVBOX_USER_RESPONSAVEL>`) — configurado no `config/equipe.py` / `config/.env`, nunca um ID hardcoded
2. **`from` é STRING**, não integer
3. `comments` deve ter no mínimo 10 caracteres
4. Sempre incluir links do Google Drive nos comments quando disponíveis
5. Tarefas de peças geradas são PARA REVISÃO do advogado responsável antes de protocolar
6. API detecta e bloqueia tarefas duplicadas
7. Nunca criar tarefa sem autorização explícita

## IDs de usuários
Não usar IDs hardcoded. Resolver os IDs pelos papéis definidos em `config/equipe.py`
(carregados do `config/.env` no onboarding):
- `<ADVBOX_USER_RESPONSAVEL>` — advogado responsável (Dr. Paulo Alexandre Soares Corbelino)
- `<ADVBOX_USER_OPERACIONAL>` — quem recebe tarefas operacionais
- `<ADVBOX_USER_FINANCEIRO>` — financeiro

## Tipos de tarefa comuns (verificar IDs via settings)
- ACOMPANHAMENTO
- AUDIÊNCIA
- PETIÇÃO
- PRAZO FATAL

## Exemplo de uso via código
```python
from INTEGRACOES.advbox_integration import criar_publicacao
from config.equipe import USUARIOS_ADVBOX

resultado = criar_publicacao(
    lawsuit_id=12345,
    task_id='100',                                  # ID do tipo de tarefa
    guest_ids=[USUARIOS_ADVBOX['OPERACIONAL']],     # responsável operacional
    comments='Revisar contrato gerado - https://drive.google.com/...',
    from_id=str(USUARIOS_ADVBOX['RESPONSAVEL']),    # usuário responsável (string!)
    date_deadline='2026-04-20',
    urgent=True,
)
```

## Respostas
- **200**: `{"success": true, "posts_id": 180922743}`
- **400**: Campos faltando, data inválida, tarefa duplicada, guests vazio
- **401**: Token inválido
- **429**: Rate limit (500 POST/dia)

## IMPORTANTE
- Nunca criar tarefa sem autorização explícita do usuário
- Sempre confirmar processo, responsáveis e prazo antes de criar
