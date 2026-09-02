# Prompt para o Claude CRIAR a skill "Timbrado"

> Cole exatamente isso no Claude (Claude.ai — Chrome ou app) e ele empacota a skill pra você instalar.

---

Use seu skill creator (ou sua capacidade de criar skills) para empacotar uma skill chamada **"timbrado-corbelino"**, instalável no meu Claude.ai.

**Função:** aplicar o **papel timbrado oficial** do escritório **CORBELINO ADVOGADOS ASSOCIADOS** (Dr. **PAULO ALEXANDRE SOARES CORBELINO** — **OAB/MT 33.267**, Cáceres / Pontes Lacerda — MT) em qualquer peça ou documento que eu gerar — para nunca produzirmos peça em folha branca.

**Description da skill (pro modelo invocar certo):** "Aplica o papel timbrado oficial do escritório Corbelino Advogados Associados em qualquer peça DOCX (inicial, recurso, intercorrente, quesitos, parecer, declaração, procuração). Use sempre que precisar formatar uma peça com a identidade visual do escritório do Dr. Paulo Alexandre Soares Corbelino — OAB/MT 33.267."

**Quando invocada (geralmente por outra skill, como `iniciais-previdenciarias-corbelino` / `quesitos-corbelino` / `previdenciario-corbelino`, ou diretamente por mim):**

1. **Buscar o timbrado-base** no meu Drive — arquivo `TIMBRADO_CORBELINO.docx` (ou nome equivalente que eu indicar). Use-o como template: copie o **header (logo / cabeçalho com nome do escritório, endereço, OAB) e o footer (rodapé com contatos)** dele, mantendo intactos. Caso eu ainda não tenha esse arquivo, **peça antes de gerar** — não invente identidade visual.

2. **Receber o conteúdo da peça** (texto da inicial, dos quesitos, do recurso, da intercorrente etc.) e **injetá-lo no corpo** do documento, sem mexer no header/footer.

3. **Aplicar o padrão de formatação do escritório** (calibrado pela peça modelo `Loas Def Indeferido - MENOR.docx`):
   - Fonte do corpo: confira no template; default sugerido **Times New Roman 12** ou **Arial 11**.
   - Corpo **justificado**.
   - **Espaçamento entre linhas:** 1,5 (confirmar no template).
   - **Recuo de primeira linha** conforme o template (default sugerido: 1,25 cm — confirmar).
   - **Cabeçalhos principais em MAIÚSCULO e negrito**, centralizados ou alinhados conforme o padrão da peça modelo. Exemplos do padrão Dr. Paulo:
     - `MERITÍSSIMO JUÍZO FEDERAL...` (centralizado / negrito)
     - `PRELIMINARMENTE` / `DOS FATOS` / `DA FUNDAMENTAÇÃO DE MÉRITO` / `DA NECESSIDADE DE ANTECIPAÇÃO DA TUTELA` / `DOS REQUERIMENTOS` / `DOS QUESITOS` (negrito).
   - **Subtítulos** (`Da Assistência Judiciária Gratuita`, `Síntese das condições pessoais`, etc.) — negrito.
   - **Citações** (transcrição de lei, doutrina, jurisprudência) em **recuo de 4 cm à esquerda**, **itálico**, **aspas**, espaçamento simples.
   - **Tabelas** quando síntese (NB / DER / motivo do indeferimento) — bordas finas, células centralizadas, cabeçalho em negrito.
   - **Assinatura final padronizada:**
     ```
     Cáceres - MT, [DIA] de [MÊS] de [ANO].
     (assinado digitalmente)
     PAULO ALEXANDRE SOARES CORBELINO
     OAB/MT 33.267
     ```

4. **Rodapé/assinatura da peça** com nome e OAB do(a) advogado(a) responsável. **Default fixo:** Dr. **PAULO ALEXANDRE SOARES CORBELINO — OAB/MT 33.267**. Se outro advogado do escritório for indicado, usar os dados dele(a).

5. **Gerar o DOCX final** e salvar onde for solicitado (geralmente na pasta do cliente no Drive). Nome do arquivo conforme a skill chamadora (`[NOME DO CLIENTE] - [PEÇA] - PRONTA PARA REVISÃO.docx`).

**Implementação sugerida:**
- Inclua no pacote da skill um **script Python (python-docx)** que:
  1. Abre `TIMBRADO_CORBELINO.docx` como base.
  2. **Limpa o body** mantendo header e footer intactos.
  3. **Injeta o conteúdo formatado** conforme as regras acima.
  4. Gera o DOCX final e devolve o caminho.
- Inclua um exemplo mínimo de uso (entrada: texto da peça + nome do cliente + tipo da peça; saída: caminho do DOCX gerado).
- Se não der pra rodar Python na sessão, deixe as **regras de formatação descritas no `SKILL.md`** pra eu seguir manualmente ao gerar peças.

**Guard-rails:**
- **NUNCA gere peça do escritório em folha branca.** Toda peça do Corbelino Advogados Associados sai no timbrado dele.
- **Nunca invente logo, cabeçalho, endereço ou OAB.** Use só o que estiver no arquivo `TIMBRADO_CORBELINO.docx`. Se ele não existir, peça antes de gerar.
- **Não altere o conteúdo da peça** ao aplicar o timbrado — só formate.
- **Default de advogado responsável:** Dr. Paulo Alexandre Soares Corbelino — OAB/MT 33.267.

**Identidade institucional fixa (caso falte info no template):**
- Escritório: **CORBELINO ADVOGADOS ASSOCIADOS**
- Advogado titular: **Dr. PAULO ALEXANDRE SOARES CORBELINO — OAB/MT 33.267**
- E-mail: advpauloalexandre@gmail.com
- Telefone: (65) 99695-1616
- Cidade-sede: Cáceres / Pontes Lacerda — MT

Empacote como skill instalável e me devolva o pacote pronto pra eu instalar no meu Claude.ai.

---

> **Nota pré-instalação:** antes de instalar a skill, suba no seu Drive um arquivo chamado `TIMBRADO_CORBELINO.docx` com o cabeçalho e rodapé oficiais do escritório (logo, endereço completo, telefones, OAB). Se ainda não tiver, **gere uma versão limpa** com pelo menos: nome do escritório em destaque + OAB do Dr. Paulo + endereço + contatos. Sem esse arquivo, as skills `iniciais-previdenciarias-corbelino` e `quesitos-corbelino` vão pedir o template antes de gerar.
