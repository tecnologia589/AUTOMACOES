---
name: advbox-publicacoes
description: Consulta publicações de um processo no ADVBOX (GET /publications)
trigger: /advbox-publicacoes
---

# Skill: Publicações de Processo ADVBOX

Endpoint NOVO — ainda não implementado no `advbox_integration.py`.

## Endpoint: GET /publications/{lawsuit_id}

**URL:** `https://app.advbox.com.br/api/v1/publications/{lawsuit_id}`
**Auth:** Bearer Token

## Path parameter
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `lawsuit_id` | integer | ID do processo |

## Response (200)
```json
{
  "data": [{
    "process_number": "1234567-89.2024.8.00.0000",
    "protocol_number": null,
    "start": "2025-01-15 00:00:00",
    "date_deadline": null,
    "local": null,
    "created_at": "2025-01-14 10:30:00",
    "author": "João Silva",
    "responsible": "Maria Santos",
    "customers": "Cliente A, Cliente B",
    "publication": "Intimação para apresentação de documentos",
    "date": "2025-01-15"
  }]
}

```

## Campos da response
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `process_number` | string/null | Número CNJ |
| `protocol_number` | string/null | Protocolo |
| `start` | datetime/null | Data início (YYYY-MM-DD HH:MM:SS) |
| `date_deadline` | date/null | Prazo (YYYY-MM-DD) |
| `local` | string/null | Local |
| `created_at` | datetime | Data criação |
| `author` | string | Autor |
| `responsible` | string | Responsável |
| `customers` | string | Clientes (separados por vírgula) |
| `publication` | string | Texto da publicação |
| `date` | date | Data da publicação (YYYY-MM-DD) |

## Exemplo de uso
```python
from INTEGRACOES.advbox_integration import _request
pubs = _request('GET', f'/publications/{lawsuit_id}')
for pub in pubs.get('data', []):
    print(f"{pub['date']} - {pub['publication']}")
    print(f"  Responsável: {pub['responsible']}")
    if pub['date_deadline']:
        print(f"  PRAZO: {pub['date_deadline']}")
```

## Regras do escritório
- A controladoria acompanha as PUBLICAÇÕES (não as tarefas)
- Consulta livre — não precisa de autorização
- 404 se processo não existe

## Erros
- **401**: Token inválido
- **404**: Processo não encontrado
