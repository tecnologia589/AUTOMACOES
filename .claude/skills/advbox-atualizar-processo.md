---
name: advbox-atualizar-processo
description: Atualiza processo existente no ADVBOX via API (PUT /lawsuits/{id})
trigger: /advbox-atualizar-processo
---

# Skill: Atualizar Processo no ADVBOX

Endpoint NOVO — ainda não implementado no `advbox_integration.py`. Chamar direto via `_request`.

## Endpoint: PUT /lawsuits/{id}

**URL:** `https://app.advbox.com.br/api/v1/lawsuits/{id}`
**Auth:** Bearer Token

## Path parameter
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | integer | ID do processo a atualizar |

## Campos atualizáveis (todos opcionais — enviar só o que mudar)
| Campo API | Tipo | Validação |
|-----------|------|-----------|
| `users_id` | string | ID do responsável |
| `stages_id` | string | Fase processual (auto-atualiza `step`) |
| `type_lawsuits_id` | string | Tipo de processo (auto-atualiza `group`) |
| `process_number` | string | CNJ validado — enviar `""` para limpar |
| `protocol_number` | string | Protocolo |
| `folder` | string | Máximo 30 caracteres |
| `date` | string | YYYY-MM-DD |
| `notes` | string | Observações |
| `fees_expec` | integer | Honorários esperados (R$) |
| `fees_money` | integer | Honorários recebidos (R$) |
| `contingency` | integer | Contingência (R$) |
| `status_closure` | string | Data encerramento YYYY-MM-DD — `""` para limpar |
| `exit_production` | string | Saída produção YYYY-MM-DD — `""` para limpar |
| `exit_execution` | string | Saída execução YYYY-MM-DD — `""` para limpar |

## Regras do escritório
1. Nunca alterar ADVBOX sem autorização explícita
2. Enviar APENAS os campos que mudam — os demais ficam inalterados
3. Para limpar campos de data, enviar string vazia `""`
4. `folder` máximo 30 caracteres
5. Datas sempre YYYY-MM-DD

## Exemplo de uso
```python
from INTEGRACOES.advbox_integration import _request
# Mudar fase e adicionar número do processo
resultado = _request('PUT', f'/lawsuits/{lawsuit_id}', json_data={
    'stages_id': '300001',
    'process_number': '0001234-56.2026.5.12.0001',
    'notes': 'Distribuído em 14/04/2026',
})
```

## Casos de uso comuns
- Atualizar fase (NEGOCIAÇÃO → INICIAL → RECURSAL)
- Adicionar número CNJ após distribuição
- Registrar encerramento (status_closure)
- Atualizar honorários
- Mudar responsável

## Respostas
- **200**: `{"success": true, "lawsuits_id": "1234567"}`
- **400**: Body vazio, folder > 30 chars, CNJ inválido, data inválida
- **401**: Token inválido
- **404**: Processo não encontrado ou sem permissão

## IMPORTANTE
- Nunca atualizar processo sem autorização explícita
- Sempre confirmar qual campo será alterado antes de executar
