---
name: advbox-criar-cliente
description: Cadastra novo cliente no ADVBOX via API (POST /customers)
trigger: /advbox-criar-cliente
---

# Skill: Cadastrar Cliente no ADVBOX

Usa `python -c` para chamar a função `cadastrar_cliente` do módulo `INTEGRACOES/advbox_integration.py`.

## Endpoint: POST /customers

**URL:** `https://app.advbox.com.br/api/v1/customers`
**Auth:** Bearer Token (config/.env → ADVBOX_API_TOKEN)

## Campos obrigatórios
| Campo API | Tipo | Descrição |
|-----------|------|-----------|
| `users_id` | integer | ID do usuário responsável (buscar via settings) |
| `customers_origins_id` | integer | ID da origem do contato (buscar via settings) |
| `name` | string | Nome completo do cliente |

## Campos opcionais
| Campo API | Tipo | Formato/Validação |
|-----------|------|-------------------|
| `email` | string | Email válido |
| `identification` | string | CPF/CNPJ — validado algoritmicamente, bloqueia duplicados |
| `phone` | string | Telefone fixo |
| `cellphone` | string | Celular |
| `birthdate` | string | **YYYY-MM-DD** (não DD/MM/YYYY!) |
| `gender` | string | M ou F |
| `occupation` | string | Profissão |
| `document` | string | RG (campo livre) |
| `street` | string | Rua/endereço |
| `region` | string | Bairro |
| `city` | string | Cidade |
| `state` | string | UF (2 letras) |
| `country` | string | Ex: BRASIL |
| `postalcode` | string | **DEVE ter hífen: 99999-999** (sem hífen é rejeitado) |
| `number_ctps` | string | Número CTPS |
| `number_pis` | string | Número PIS |
| `number_cid` | string | CID |
| `notes` | string | Observações |

## Regras do escritório
1. Antes de cadastrar, SEMPRE buscar por CPF para evitar duplicidade
2. Origem padrão: buscar "INDICACAO" nas settings
3. Responsável padrão: primeiro usuário das settings (ou especificado)
4. CPF formato: XXX.XXX.XXX-XX
5. CEP DEVE ter hífen: 88800-000 (não 88800000)
6. Data nascimento converter DD/MM/YYYY → YYYY-MM-DD antes de enviar

## Exemplo de uso via código
```python
from INTEGRACOES.advbox_integration import cadastrar_cliente
resultado = cadastrar_cliente({
    'nome': 'JOÃO DA SILVA',
    'cpf': '123.456.789-00',
    'email': 'joao@email.com',
    'telefone': '(48) 98888-7777',
    'data_nascimento': '15/05/1990',
    'profissao': 'OPERADOR',
    'rua': 'Rua Exemplo, 123',
    'bairro': 'Centro',
    'cidade': 'São Paulo',
    'estado': 'SC',
    'cep': '88800-000',
})
```

## Respostas
- **201**: `{"success": true, "customers_id": 12345678}`
- **400**: CPF duplicado, campo inválido, CEP sem hífen
- **401**: Token inválido
- **429**: Rate limit (500 POST/dia)

## IMPORTANTE
- Nunca cadastrar sem autorização explícita do usuário
- Nunca inventar dados — se falta informação, perguntar
- Se cliente já existe (CPF duplicado), retornar o ID existente
