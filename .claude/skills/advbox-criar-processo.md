---
name: advbox-criar-processo
description: Cadastra novo processo no ADVBOX via API (POST /lawsuits)
trigger: /advbox-criar-processo
---

# Skill: Cadastrar Processo no ADVBOX

Usa `python -c` para chamar a função `cadastrar_processo` do módulo `INTEGRACOES/advbox_integration.py`.

## Endpoint: POST /lawsuits

**URL:** `https://app.advbox.com.br/api/v1/lawsuits`
**Auth:** Bearer Token

## Campos obrigatórios
| Campo API | Tipo | Descrição |
|-----------|------|-----------|
| `users_id` | string/integer | ID do responsável (buscar via settings) |
| `customers_id` | array<integer> | Array de IDs de clientes (mínimo 1) |
| `stages_id` | string/integer | ID da fase processual (buscar via settings) |
| `type_lawsuits_id` | string/integer | ID do tipo de processo (buscar via settings) |

## Campos opcionais
| Campo API | Tipo | Validação |
|-----------|------|-----------|
| `process_number` | string | Formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO — validado contra base oficial |
| `protocol_number` | string | Número de protocolo livre |
| `folder` | string | **Máximo 30 caracteres** |
| `date` | string | YYYY-MM-DD |
| `notes` | string | Observações detalhadas |
| `fees_expec` | integer | Honorários esperados (R$) |
| `fees_money` | integer | Honorários recebidos (R$) |
| `contingency` | integer | Valor de contingência (R$) |
| `status_closure` | string | Data encerramento YYYY-MM-DD |
| `exit_production` | string | Data saída produção YYYY-MM-DD |
| `exit_execution` | string | Data saída execução YYYY-MM-DD |

## Regras do escritório
1. Tipo padrão: TRABALHISTA (buscar ID via settings) — o escritório atua também em Cível e Empresarial; ajustar o tipo conforme a área
2. Fase inicial padrão: NEGOCIAÇÃO (buscar ID via settings)
3. O cliente DEVE existir antes — cadastrar via /advbox-criar-cliente primeiro
4. `folder` truncar em 30 caracteres
5. `process_number` só enviar se tiver número CNJ válido

## Exemplo de uso via código
```python
from INTEGRACOES.advbox_integration import cadastrar_processo
resultado = cadastrar_processo(
    cliente_id=12345678,
    dados_processo={
        'pasta': 'SILVA x TRANSPORTES ABC',
        'notas': 'Reclamação trabalhista - horas extras e verbas rescisórias',
        'honorarios_esperados': 15000,
    }
)
```

## Respostas
- **201**: `{"success": true, "lawsuits_id": 12358596}`
- **400**: Cliente não pertence à conta, fase inválida, CNJ inválido, folder > 30 chars
- **401**: Token inválido
- **429**: Rate limit

## IMPORTANTE
- Nunca criar processo sem autorização explícita
- Verificar se o cliente já está cadastrado antes
- group e step são derivados automaticamente de type_lawsuits_id e stages_id
