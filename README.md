# Corbelino Advogados Associados — Central de Automacoes

Plataforma de automacao juridica do escritorio **Corbelino Advogados Associados**
(Dr. Paulo Alexandre Soares Corbelino — OAB/MT 33.267 — Cáceres/MT e Pontes
Lacerda/MT).

Areas de atuacao: **Previdenciario** (foco original — BPC/LOAS, aposentadorias,
beneficios por incapacidade, revisoes), **Trabalhista** (expansao, lado do
trabalhador) e **Bancario/Defesa do Consumidor** (expansao — parecer de
viabilidade + acao revisional/defensiva).

> **A IA nunca protocola.** Toda peca gerada por estas automacoes e para revisao
> humana do Dr. Paulo Alexandre antes de qualquer protocolo.

## Agentes juridicos de IA

Este repositorio inclui 5 agentes juridicos prontos em `agentes_claude/` (e
copiados como subagentes do Claude Code em `.claude/agents/`):

| Agente | Area | Status |
|---|---|---|
| `corbelino-previdenciario.md` | Previdenciario — generalista (diagnostico, estrategia, recursos) | ✅ Calibrado com material real do Dr. Paulo |
| `corbelino-iniciais.md` | Previdenciario — peticoes iniciais | ✅ Calibrado com material real do Dr. Paulo |
| `corbelino-quesitos.md` | Previdenciario — quesitos de pericia | ✅ Calibrado com material real do Dr. Paulo |
| `corbelino-trabalhista.md` | Trabalhista (lado do trabalhador) | ⚠️ Base generica — pendente calibracao com pecas reais |
| `corbelino-bancario.md` | Bancario / defesa do consumidor | ⚠️ Base generica — pendente calibracao com pecas reais |

Os agentes de **Trabalhista** e **Bancario** foram montados com o playbook
juridico padrao da area (CLT/CDC + jurisprudencia consolidada), mas ainda nao
tem o tom, as teses preferidas e a estrutura reais do Dr. Paulo. Assim que ele
enviar 1-2 peticoes ja protocoladas em cada area, os arquivos devem ser refeitos
puxando o estilo real — no mesmo processo usado para calibrar o previdenciario a
partir da peticao-modelo "LOAS Indeferido — MENOR". Ver
`agentes_claude/GUIA_INSTALACAO_CLAUDE_AI.md` para instalar como Projects/Skills
no Claude.ai.

## Frentes de automacao (engenharia completa)

Alem dos agentes juridicos, este repositorio traz o mesmo motor de automacao
usado pelos demais escritorios parceiros — adaptado para o Corbelino Advogados
Associados:

| Squad | O que faz | Comando-chave |
|-------|-----------|---------------|
| **INTAKE** | Intake comercial: analisa o caso (IA), gera Ficha/Contrato/Procuracao/Declaracao, envia para assinatura e cadastra no ADVBOX (se configurado) | `python INTAKE/main.py ...` |
| **FINANCEIRO** | Fechamento mensal, conciliacao Asaas×ADVBOX e cobranca semanal por WhatsApp (se configurado) | `python FINANCEIRO/fechamento_mensal.py MM/YYYY` |
| **OPERACIONAL** | Tarefas, processos, prazos e geracao de peticoes; agente CORBELINO.IA (webhook) | `python OPERACIONAL/main.py tarefas` |
| **SYNC** | Sincroniza documentos assinados (ZapSign → Drive) | `python SYNC/sync_assinados.py` |

> **Nenhuma credencial de sistema foi recebida ainda** (ADVBOX, Asaas, ZapSign,
> Atende Direito, Google Drive) — nem confirmacao de quais desses sistemas o
> escritorio realmente usa. Ate serem confirmados/preenchidos, INTAKE/
> FINANCEIRO/SYNC ponta-a-ponta nao funcionam; o que roda hoje sao os agentes de
> IA (produzir pecas sobre documentos soltos). Ver `docs/ONBOARDING.md`.

## Instalacao rapida

```bash
# 1. Ambiente
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
playwright install chromium    # para geracao de PDF

# 2. Configuracao
copy config\.env.example config\.env   # (macOS/Linux: cp config/.env.example config/.env)
# preencher TODOS os campos conforme docs/ONBOARDING.md (nada vem preenchido)
# coloque config/credentials.json (Google Cloud) na pasta config/

# 3. Teste
python OPERACIONAL/main.py tarefas
```

> **Antes de rodar em producao, leia `docs/ONBOARDING.md`** — ele lista, passo a
> passo, todas as credenciais e IDs que ainda precisam ser preenchidos. As
> automacoes rodam de forma segura/neutra enquanto algo nao estiver configurado
> (nada e enviado/lancado sem credencial).

## Estrutura
Ver `CLAUDE.md` para a arvore completa e as regras de cada squad.

## Seguranca
- Segredos ficam **somente** em `config/.env` (nunca versionado — ver `.gitignore`).
- Nenhuma credencial vem pre-preenchida neste repositorio.
