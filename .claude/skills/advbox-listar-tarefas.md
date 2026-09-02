---
name: advbox-listar-tarefas
description: Lista e filtra tarefas do ADVBOX via API (GET /posts)
trigger: /advbox-listar-tarefas
---

# Skill: Listar Tarefas ADVBOX

Endpoint NOVO — ainda não implementado como função dedicada no `advbox_integration.py`.

## Endpoint: GET /posts

**URL:** `https://app.advbox.com.br/api/v1/posts`
**Auth:** Bearer Token

## Filtros disponíveis (todos opcionais)
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `user_id` | string | ID exato do responsável |
| `user_name` | string | Nome do responsável (busca parcial, case-insensitive) |
| `task_id` | string | ID do tipo de tarefa |
| `lawsuit_id` | string | ID do processo |
| `id` | integer | ID de uma tarefa específica |
| `date_start` | string | Data início da tarefa (YYYY-MM-DD) — **usar com date_end** |
| `date_end` | string | Data fim da tarefa (YYYY-MM-DD) — **usar com date_start** |
| `created_start` | string | Data início criação (YYYY-MM-DD) — **usar com created_end** |
| `created_end` | string | Data fim criação (YYYY-MM-DD) — **usar com created_start** |
| `deadline_start` | string | Prazo início (YYYY-MM-DD) — **usar com deadline_end** |
| `deadline_end` | string | Prazo fim (YYYY-MM-DD) — **usar com deadline_start** |
| `completed_start` | string | Conclusão início (YYYY-MM-DD) — **usar com completed_end** |
| `completed_end` | string | Conclusão fim (YYYY-MM-DD) — **usar com completed_start** |
| `limit` | integer | Itens por página (default 1000, range 1-100 recomendado) |
| `offset` | integer | Posição inicial (default 0) |

## ATENÇÃO: Lógica de status nos filtros
- **Sem filtros**: retorna TODAS (pendentes + concluídas)
- **Com `user_name` ou `user_id`**: retorna APENAS pendentes daquele usuário
- **Com `lawsuit_id`**: retorna APENAS pendentes daquele processo
- **Com `completed_start/end`**: retorna APENAS concluídas no período

## Pares de data DEVEM ser completos
Usar `date_start` sem `date_end` faz o filtro ser ignorado. Sempre enviar o par.

## Response (200)
```json
{
  "offset": 0, "limit": 100, "totalCount": 532,
  "data": [{
    "id": 123456789,
    "date": "2025-05-12 00:00:00",
    "date_deadline": null,
    "task": "AUDIÊNCIA PRELIMINAR",
    "reward": 0,
    "notes": "Comparecer à audiência...",
    "local": null,
    "lawsuits_id": 1234567,
    "created_at": "2025-05-12 15:47:45",
    "lawsuit": {
      "id": 1234567,
      "process_number": "0001234-56.2025.8.26.0100",
      "protocol_number": null,
      "customers": [{"customer_id": 123, "name": "João Silva", "identification": null}]
    },
    "users": [{
      "user_id": 163,
      "name": "Maria Oliveira",
      "completed": null,
      "important": 1,
      "urgent": 0
    }]
  }]
}
```

## Exemplo de uso
```python
from INTEGRACOES.advbox_integration import _request

# Tarefas pendentes de um responsável (por nome)
tarefas = _request('GET', '/posts', params={'user_name': 'PAULO', 'limit': 50})

# Tarefas de um processo
tarefas = _request('GET', '/posts', params={'lawsuit_id': '12345'})

# Tarefas com prazo esta semana
tarefas = _request('GET', '/posts', params={
    'deadline_start': '2026-04-14',
    'deadline_end': '2026-04-20',
})

# Tarefas concluídas no mês
tarefas = _request('GET', '/posts', params={
    'completed_start': '2026-04-01',
    'completed_end': '2026-04-30',
})
```

## IDs de usuários
Resolver os IDs pelos papéis em `config/equipe.py` (carregados do `config/.env`).
Não usar IDs hardcoded.

## Erros
- **400**: Formato de data inválido
- **401**: Token inválido
