# Guia de Instalação — Agentes Corbelino no Claude.ai

Este guia mostra como instalar os agentes do Dr. **Paulo Alexandre Soares Corbelino** (Corbelino Advogados Associados) como **Projects** no Claude.ai (https://claude.ai).

## Agentes disponíveis nesta pasta

### Custom Instructions (Projects do Claude.ai)

| Arquivo | Para que serve | Quando usar |
|---|---|---|
| `corbelino-previdenciario.md` | **Generalista previdenciário** — diagnóstico, estratégia, recursos, intercorrentes, recursos administrativos. | Quando o caso ainda não está pronto para a inicial — análise, planejamento, dúvida estratégica. |
| `corbelino-iniciais.md` | **Especialista em petições iniciais** — estrutura completa, fundamentação densa, quesitos. | Quando já tem o caso fechado e precisa **redigir a inicial**. |
| `corbelino-quesitos.md` | **Especialista em quesitos** — perícia médica e estudo socioeconômico. | Quando o juiz designa perícia e precisa juntar quesitos (ou complementar / impugnar laudo). |
| `corbelino-trabalhista.md` | **Direito do Trabalho** — vínculo, verbas rescisórias, horas extras, rescisão indireta, dano moral trabalhista. ⚠️ base genérica, ainda não calibrada com material real do Dr. Paulo. | Casos trabalhistas (lado do trabalhador). |
| `corbelino-bancario.md` | **Bancário/Consumidor** — parecer de viabilidade + ação revisional/defensiva (juros, tarifas, capitalização, busca e apreensão). ⚠️ base genérica, ainda não calibrada. | Contratos bancários pra analisar ou já em disputa. |

> **Boas práticas:** crie **um Project separado para cada agente**. Cada um tem foco diferente e responde melhor isolado.

### Skills empacotadas (Claude.ai)

Skills ficam disponíveis na conta inteira (não só em um Project) — o Claude as invoca automaticamente conforme o pedido. Para empacotar, abra um chat **novo** no Claude.ai (Chrome ou app) e **cole o prompt abaixo**. O Claude responde com um pacote pronto para instalação.

| Arquivo (prompt) | Nome da skill que será criada | Quando o Claude vai invocar sozinho |
|---|---|---|
| `prompt-criar-skill-previdenciario.md` | `previdenciario-corbelino` | Pedidos de diagnóstico, estratégia, recurso administrativo, peça intercorrente. |
| `prompt-criar-skill-iniciais.md` | `iniciais-previdenciarias-corbelino` | Pedido de redação de petição inicial previdenciária. |
| `prompt-criar-skill-quesitos.md` | `quesitos-corbelino` | Pedido de quesitos para perícia médica ou estudo socioeconômico. |
| `prompt-criar-skill-timbrado.md` | `timbrado-corbelino` | Toda vez que uma das outras 3 skills (ou eu) precisar gerar um DOCX no papel timbrado oficial. |

> **Ordem de instalação:** instale `timbrado-corbelino` **primeiro**. As outras 3 skills tentam chamá-la quando vão gerar DOCX. Antes de instalar, suba no seu Drive o arquivo `TIMBRADO_CORBELINO.docx` (cabeçalho/rodapé oficiais do escritório).

**Por que ter os dois formatos?**
- **Custom Instructions** dá controle máximo dentro de um Project (e permite subir base de conhecimento dedicada).
- **Skill** funciona em qualquer conversa da conta do Dr. Paulo, e é invocada automaticamente quando ele pede algo que se encaixe na descrição.

Recomendo usar os **dois em paralelo**: Projects pra trabalhar casos complexos com base de conhecimento dedicada; Skills pra produtividade do dia a dia ("monta quesitos pra esse caso", "redige uma inicial LOAS-PCD").

## Pré-requisitos

- Conta Claude.ai do Dr. Paulo Alexandre
- **Plano Claude Pro ou Max** (Projects não estão disponíveis no plano Free)

## Passo a passo

### 1. Criar os Projects

Para **cada agente**, repita:

1. Abra https://claude.ai
2. No menu lateral esquerdo, clique em **"Projects"**
3. Clique em **"+ Create Project"** (canto superior direito)
4. Preencha conforme a tabela abaixo:

| Arquivo `.md` | Nome do Project | Descrição |
|---|---|---|
| `corbelino-previdenciario.md` | **Corbelino Prev — Previdenciário** | Assistente previdenciária do Dr. Paulo Alexandre Soares Corbelino (OAB/MT 33.267) — diagnóstico, estratégia, recursos, peças intercorrentes. |
| `corbelino-iniciais.md` | **Corbelino Prev — Iniciais** | Especialista em redigir petições iniciais previdenciárias no padrão do Dr. Paulo Alexandre (Corbelino Advogados Associados). |
| `corbelino-quesitos.md` | **Corbelino Prev — Quesitos** | Especialista em elaborar quesitos médicos e socioeconômicos para perícias previdenciárias do JEF Cáceres-MT (Corbelino Advogados Associados). |
| `corbelino-trabalhista.md` | **Corbelino Trab — Trabalhista** | Assistente trabalhista do Dr. Paulo Alexandre Soares Corbelino (OAB/MT 33.267) — vínculo, verbas, horas extras, rescisão indireta, dano moral trabalhista. |
| `corbelino-bancario.md` | **Corbelino Banc — Bancário** | Assistente em direito bancário/consumidor do Dr. Paulo Alexandre Soares Corbelino (OAB/MT 33.267) — parecer de viabilidade e ação revisional/defensiva. |

5. Clique em **"Create"**

### 2. Configurar as instruções (Custom Instructions)

Para cada Project:

1. Dentro do Project, clique em **"⚙️ Set Instructions"** (ou "Custom Instructions" — o nome muda conforme a versão)
2. Abra o arquivo `.md` correspondente desta pasta
3. **Pule as primeiras linhas** entre `---` (o bloco frontmatter, com `name:` / `description:` / `model:`)
4. Cole **todo o resto do arquivo** — começando pelo primeiro `# Título`
5. Clique em **"Save"**

### 3. Subir base de conhecimento (recomendado)

Em cada Project, clique em **"+ Add knowledge"** e suba:

**Para o Corbelino Prev — Iniciais (prioridade alta):**
- **Petições iniciais modelo** do Dr. Paulo (DOCX/PDF) — calibra tom e estrutura
- **Papel timbrado** do escritório
- **Quesitos** que ele já usa em perícias
- **Súmulas TNU 29, 48, 149** e precedentes preferidos (TRF1, TRF4, TNU, STJ, STF)

**Para o Corbelino Prev — Previdenciário (generalista):**
- **Modelos de recursos administrativos** (Junta / Conselho Pleno)
- **Modelos de cumprimento de exigência** (Meu INSS)
- **Procuração, contrato de honorários e declaração de hipossuficiência** (modelos)
- **Ficha do cliente** padrão

> Essencial mínimo em ambos: **timbrado** + **uma inicial dele já protocolada** (qualquer benefício).

### 4. Testar

**Corbelino Prev — Iniciais:**
> "Cliente menor, 6 anos, CID F84 (TEA), DER 15/03/2026, NB 176393591, indeferido por 'não atende ao critério de deficiência'. Família: mãe (serviços gerais, ~R$ 1.200) + 2 irmãos. Estamos em Pontes Lacerda. Monta a inicial LOAS-PCD."

Esperado: pergunta o que falta antes de redigir; ao redigir, segue a estrutura completa (endereçamento JEF Cáceres, tabelas com NB/DER/motivo, doutrina Canotilho/Sarlet/Jorge Miranda, Súmulas TNU 29 e 48, quesitos no fim); termina com "Inicial pronta para revisão do Dr. Paulo. Não protocolei."

**Corbelino Prev — Previdenciário (generalista):**
> "Cliente teve auxílio-doença cessado em 10/04/2026. CID M51 (hérnia de disco lombar). Tem laudo do ortopedista atestando incapacidade. CNIS mostra última contribuição em 02/2026 como motorista. Qual a estratégia? Recurso administrativo ou ação?"

Esperado: aplica a Estrutura de Análise Padrão (11 seções), aponta opções e gestão de risco.

**Corbelino Prev — Quesitos:**
> "Mesmo caso do Gleison (TEA + TDAH, 6 anos, BPC-PCD). Juiz designou perícia médica e estudo social. Monta os dois blocos de quesitos."

Esperado: 14 quesitos médicos no padrão Dr. Paulo + bloco BPC-PCD criança + 12 quesitos socioeconômicos; assinatura ao final; encerra com "Quesitos prontos para revisão do Dr. Paulo."

## Variação para Claude Code (avançado — opcional)

Se o Dr. Paulo quiser usar o agente **dentro do Claude Code** (CLI) como subagente, basta copiar o arquivo `corbelino-previdenciario.md` para `.claude/agents/` no repositório dele — o frontmatter (`---`) é mantido. O Claude Code reconhece automaticamente.

---

## Manutenção

- **Atualizar o agente:** edite `corbelino-previdenciario.md` e cole novamente nas Custom Instructions.
- **Adicionar nova peça modelo:** suba na knowledge base do Project — o agente passa a usar imediatamente.
- **Bug ou ajuste fino:** abra um chamado com o time PAB (Weverton).
