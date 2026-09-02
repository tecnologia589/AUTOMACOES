---
name: advbox-historico
description: Consulta histórico de tarefas de um processo no ADVBOX (GET /history)
trigger: /advbox-historico
---

# Skill: Histórico de Tarefas de Processo ADVBOX

Endpoint NOVO — ainda não implementado no `advbox_integration.py`.

## Endpoint: GET /history/{lawsuit_id}

**URL:** `https://app.advbox.com.br/api/v1/history/{lawsuit_id}`
**Auth:** Bearer Token

## Path parameter
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `lawsuit_id` | integer | ID do processo |

## Query parameter
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `status` | string | Filtrar: `"pending"` ou `"completed"` (sem filtro = todas) |

## ATENÇÃO
- Este endpoint **NÃO suporta paginação** (limit/offset não funcionam)
- Retorna TODAS as tarefas de uma vez
- Processo inexistente retorna array vazio (não 404)

## Response (200)
```json
{
  "status": "all",
  "data": [{
    "process_number": "0001234-56.2024.8.26.0100",
    "protocol_number": "PROT-12345",
    "task": "AUDIÊNCIA",
    "reward": 1500,
    "start": "2026-02-15 10:00:00",
    "date_deadline": "2026-02-15 12:00:00",
    "comments": "Audiência de conciliação",
    "local": "Sala 301",
    "created_at": "2026-01-10 14:30:00",
    "author": "JOÃO SILVA",
    "responsible": "MARIA SANTOS",
    "customers": "PEDRO OLIVEIRA"
  }]
}
```

## Campos da response
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `process_number` | string/null | Número CNJ |
| `protocol_number` | string/null | Protocolo |
| `task` | string | Tipo de tarefa |
| `reward` | number | Pontuação |
| `start` | datetime | Data início (YYYY-MM-DD HH:MM:SS) |
| `date_deadline` | string/null | Prazo |
| `comments` | string | Descrição/observações |
| `local` | string/null | Local |
| `created_at` | datetime | Data criação |
| `author` | string | Quem criou |
| `responsible` | string | Responsável |
| `customers` | string | Clientes envolvidos |

## Exemplo de uso
```python
from INTEGRACOES.advbox_integration import _request

# Todas as tarefas do processo
historico = _request('GET', f'/history/{lawsuit_id}')

# Apenas pendentes
pendentes = _request('GET', f'/history/{lawsuit_id}', params={'status': 'pending'})

# Apenas concluídas
concluidas = _request('GET', f'/history/{lawsuit_id}', params={'status': 'completed'})
```

## Erros
- **401**: Token inválido
- **404**: Processo não encontrado (retorna array vazio)
