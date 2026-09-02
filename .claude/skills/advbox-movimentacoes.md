---
name: advbox-movimentacoes
description: Consulta movimentações processuais e cria movimentações manuais no ADVBOX
trigger: /advbox-movimentacoes
---

# Skill: Movimentações Processuais ADVBOX

Endpoints NOVOS — ainda não implementados no `advbox_integration.py`.

## 1. Últimas movimentações (todos os processos)

### GET /last_movements

**URL:** `https://app.advbox.com.br/api/v1/last_movements`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `lawsuit_id` | integer | Filtrar por processo específico |
| `process_number` | string | Filtrar por número CNJ |
| `protocol_number` | string | Filtrar por protocolo |
| `date_start` | string | Início do período (YYYY-MM-DD) — usar com date_end |
| `date_end` | string | Fim do período (YYYY-MM-DD) — usar com date_start |

**Paginação:** limit=100 (default), offset=0

**Response:**
```json
{
  "offset": 0, "limit": 100, "totalCount": 250,
  "data": [{
    "lawsuit_id": 12345,
    "date": "2025-02-15",
    "title": "PETIÇÃO INTERMEDIÁRIA",
    "header": "TJSP - Tribunal de Justiça de São Paulo",
    "process_number": "0001234-56.2024.8.26.0100",
    "protocol_number": null,
    "customers": "João Silva, Maria Santos"
  }]
}
```

## 2. Movimentações de um processo

### GET /movements/{lawsuit_id}

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `origin` | string | Filtrar: `"TRIBUNAL"` ou `"MANUAL"` |

**Response:** Mesmo formato do /last_movements (array de movimentações)
**204:** Sem movimentações encontradas

## 3. Criar movimentação manual

### POST /lawsuits/movement

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| `lawsuit_id` | integer | Sim | Deve existir e pertencer ao escritório |
| `date` | string | Sim | **DD/MM/YYYY** (diferente dos outros endpoints!) |
| `description` | string | Sim | **Mínimo 10 caracteres** |

**Response 201:** `{"success": true, "lawsuits_id": 123}`

## Exemplo de uso
```python
from INTEGRACOES.advbox_integration import _request

# Últimas movimentações dos últimos 7 dias
movs = _request('GET', '/last_movements', params={
    'date_start': '2026-04-07',
    'date_end': '2026-04-14',
})

# Movimentações de um processo específico (só tribunal)
movs = _request('GET', f'/movements/{lawsuit_id}', params={'origin': 'TRIBUNAL'})

# Criar movimentação manual
resultado = _request('POST', '/lawsuits/movement', json_data={
    'lawsuit_id': 12345,
    'date': '14/04/2026',
    'description': 'Petição inicial protocolada no sistema PJe',
})
```

## ATENÇÃO: Formatos de data diferentes!
- GET endpoints: **YYYY-MM-DD**
- POST /lawsuits/movement: **DD/MM/YYYY**

## IMPORTANTE
- Consultas são livres — não precisam de autorização
- Criar movimentação manual REQUER autorização explícita
- description mínimo 10 caracteres
