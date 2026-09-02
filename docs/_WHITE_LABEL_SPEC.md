# Identidade & Spec — Corbelino Advogados Associados

> Documento-guia interno. Toda peça de código/documentação deste repositório deve
> refletir SOMENTE a identidade do Corbelino Advogados Associados.
> Regra de ouro: **zero menção a qualquer outro escritório, pessoa ou cliente que
> não seja do Corbelino Advogados Associados.** Nenhuma credencial, token, ID de
> Drive/ADVBOX, timbrado ou regra de negócio de terceiros pode existir neste
> repositório.

## 1. Identidade do escritório

| Campo | Valor |
|-------|-------|
| Nome / marca | Corbelino Advogados Associados |
| Advogado responsável | Dr. Paulo Alexandre Soares Corbelino |
| OAB (responsável) | OAB/MT 33.267 |
| Cidade / Foro | Cáceres/MT e Pontes Lacerda/MT |
| Telefone | (65) 99695-1616 |
| E-mail | advpauloalexandre@gmail.com |
| Áreas | Previdenciário (BPC/LOAS, aposentadorias, benefícios por incapacidade — foco original e mais calibrado), Trabalhista (expansão) e Bancário/Defesa do Consumidor (expansão) |
| Abrangência geográfica | Cáceres/MT e Pontes Lacerda/MT |
| Sistema jurídico em uso | **Não confirmado.** Nenhuma informação recebida sobre ADVBOX ou qualquer outro sistema de gestão jurídica — a confirmar no onboarding. |
| CRM/atendimento | **Não confirmado.** Nenhuma ferramenta contratada foi informada. |
| Agente de IA | CORBELINO.IA |
| Timbrado | **Ainda não recebido.** `config/timbrado_modelo.docx` precisa ser fornecido pelo escritório (ver `config/timbrado_modelo.LEIA-ME.txt`). |

## 2. Credenciais → status neste onboarding

Diferente de outros onboardings, **nenhuma credencial real foi recebida ainda**.
`config/.env.example` vem 100% vazio (exceto identidade textual — nome, OAB, e-mail
e telefone, que já são conhecidos):

```
ANTHROPIC_API_KEY=
ADVBOX_API_TOKEN=
ASAAS_API_TOKEN=
ZAPSIGN_API_TOKEN=
ATENDE_DIREITO_TOKEN=
GOOGLE_APPLICATION_CREDENTIALS=config/credentials.json
AGENTE_OP_TOKEN=
AGENTE_OP_PORT=8787
```

- IDs de pasta do Drive → vazios.
- IDs de usuário do ADVBOX → vazios, dependentes de confirmação se o escritório usa ADVBOX.

## 3. Equipe / usuários → config central

Nunca hardcodar pessoas; usar `config/equipe.py` (ou env) com placeholders:

```python
USUARIOS_ADVBOX = {
    "RESPONSAVEL": None,   # TODO: ID ADVBOX do Dr. Paulo Alexandre Soares Corbelino (se houver ADVBOX)
    "OPERACIONAL": None,   # ID de quem recebe tarefas operacionais
    "FINANCEIRO": None,
}
USUARIO_PADRAO_TAREFAS = "RESPONSAVEL"  # campo 'from' das tarefas /posts
```

## 4. Regras de negócio → configuráveis (vêm VAZIAS)

Cadastrar no onboarding, em `config/regras_financeiras.py`:
- Comissões (rótulo, sufixos, percentual, exclusões) — o escritório atua com um único
  advogado responsável; não há indicação de estrutura de comissionamento até o momento.
- Exceções de faturamento / clientes que não contam como receita.
- Provisão / reserva de lucro (default 0).
- Listas `clientes_nao_cobrar.txt` / `clientes_negociar.txt` (vazias).

## 5. Formatação de peças

- Motor de formatação padrão: Montserrat 11pt, justificado, espaçamento 1,5,
  recuo de 1ª linha 7cm, citações recuadas em itálico (padrão PAB — confirmar
  com o Dr. Paulo Alexandre se mantém ou tem preferência própria).
- Timbrado: `config/timbrado_modelo.docx` — **ainda não recebido**.
- Assinatura padrão das peças: **Dr. Paulo Alexandre Soares Corbelino — OAB/MT
  33.267 — Cáceres/MT**.
- O "DNA de escrita" para Previdenciário já está embutido nos agentes
  `agentes_claude/corbelino-previdenciario.md`, `corbelino-iniciais.md` e
  `corbelino-quesitos.md` (calibrados com material real do Dr. Paulo Alexandre).
  Trabalhista e Bancário ainda usam bases genéricas — ver `README.md`.

## 6. Estrutura de pastas (clientes)

Convenção: `{NOME DO CLIENTE}/ATOS INTERNOS/ DOCUMENTOS DO CLIENTE/ PASTA DO CLIENTE`.
IDs de Drive ficam em env (vazios).

## 7. Checklist de aceitação (passa só se TODOS = OK)

- [x] Nenhuma referência a outro escritório/pessoa/cliente que não seja do
      Corbelino Advogados Associados (verificado por varredura antes do commit
      inicial — este repositório partiu de um template de outro cliente e todos
      os resíduos de identidade foram removidos, incluindo dados pessoais como
      CPF/RG e endereços que pertenciam ao template original).
- [x] Nenhum token de terceiro no `.env.example` — todos os campos de credencial
      vêm vazios.
- [x] Assinatura e foro = Dr. Paulo Alexandre Soares Corbelino / Cáceres-Pontes
      Lacerda-MT.
- [x] OAB preenchida (OAB/MT 33.267).
- [x] `requirements.txt` idêntico ao núcleo funcional (herdado do template, não alterado).
