# Prompt para o Claude CRIAR a skill "Quesitos Previdenciários"

> Cole exatamente isso no Claude (Claude.ai — Chrome ou app) e ele empacota a skill pra você instalar.

---

Use seu skill creator (ou sua capacidade de criar skills) para empacotar uma skill chamada **"quesitos-corbelino"**, instalável no meu Claude.ai.

**Função:** elaborar **quesitos previdenciários** (perícia médica e/ou estudo socioeconômico) sob medida para cada caso do escritório **CORBELINO ADVOGADOS ASSOCIADOS** (Dr. **PAULO ALEXANDRE SOARES CORBELINO** — **OAB/MT 33.267**, Cáceres / Pontes Lacerda — MT), no padrão dele, prontos para juntar à inicial, ao requerimento administrativo ou à manifestação intercorrente.

**Description da skill (pro modelo invocar certo):** "Elabora quesitos previdenciários (perícia médica e/ou estudo socioeconômico) calibrados ao caso — BPC-PCD (incluindo criança com TEA/TDAH), BPC-idoso, auxílio-doença, invalidez, acidente, aposentadoria especial, isenção de IR por doença grave. Usa os quesitos-modelo do Dr. Paulo Alexandre Soares Corbelino (Corbelino Advogados Associados, OAB/MT 33.267) como referência. Use sempre que o usuário precisar de quesitos para perícia médica ou estudo social em ação previdenciária."

**Quando invocada, a skill deve fazer:**

1. **Antes de redigir, perguntar** (não inventar):
   - **Tipo de quesito:** médico, socioeconômico, ou os dois?
   - **Benefício pleiteado:** BPC-PCD / BPC-idoso / auxílio-doença / aposentadoria por invalidez / acidente / aposentadoria especial / isenção de IR por doença grave / outro.
   - **Quem responde?** perito médico judicial / assistente social judicial / perito administrativo do INSS.
   - **Estágio processual:** inicial (junta com a PI), intercorrente (após designação da perícia), impugnação ao laudo, complementação.
   - **Dados do segurado:** nome, idade, escolaridade, profissão. Se menor: representante + idade do menor.
   - **Doença/lesão e CID-10** com fonte (laudo, prontuário, receituário). Quem laudou.
   - **DID** (data início da doença) e **DII** (data início da incapacidade) pretendidas.
   - **Documentos médicos disponíveis** (laudos, exames, prontuário, atestados, receituários, relatórios terapêuticos).
   - **Composição familiar e renda per capita** (essencial para BPC).
   - **Barreiras** à participação social/educacional/comunicacional/atitudinal (relevante para BPC-PCD).
   - **Indeferimento administrativo:** transcrição literal do motivo do INSS + tese principal da inicial.
   - **Outros profissionais envolvidos** (fonoaudiólogo, psicólogo, fisioterapeuta, terapeuta ocupacional — comum em LOAS-PCD criança).
   - **Nexo causal** com atividade laboral, acidente ou esforço físico.

2. **Consultar a base de conhecimento** do Dr. Paulo no Drive (quando integrada):
   - Modelos de quesitos dele — em especial os anexados à peça `Loas Def Indeferido - MENOR.docx` (14 quesitos médicos do padrão).
   - Pasta do cliente atual — laudos, exames, prontuário, receituários, CADÚnico.
   - Petição inicial já redigida do caso, para alinhar quesitos à tese.

3. **Gerar lista numerada de quesitos** em blocos, conforme o caso:

   ### A) Quesitos ao Perito Médico
   **Núcleo fixo (14 quesitos do padrão do Dr. Paulo):**
   1. Idade e grau de escolaridade do(a) periciando(a).
   2. Deficiência/moléstia/doença e CID.
   3. Incapacidade para atividades laborais habituais ou outra qualquer.
   4. Incapacidade parcial ou total.
   5. Incapacidade permanente ou temporária.
   6. Desde quando se encontra incapacitado(a) — DII.
   7. Incapacidade para a vida independente (Súmula 29/TNU).
   8. Interferência em atividades rotineiras (afazeres domésticos, carregar peso, abaixar-se, deambular, permanecer em pé/sentado).
   9. Limitações para a vida — tipos.
   10. Fase evolutiva (descompensada) ou estabilizada (residual).
   11. Decorre de agravamento da doença.
   12. Impossibilita retorno ao mercado de trabalho — temporária ou permanente; se temporária, estimativa.
   13. Outra especialidade médica do Sr. Perito (essencial quando exigir especialista).
   14. Estimativa de custo mensal de tratamento (consultas, exames, medicamentos).

   **Blocos complementares (incluir conforme o caso):**
   - **BPC-PCD** (criança e adulto): impedimentos de longo prazo (≥ 2 anos), barreiras (sociais, atitudinais, educacionais, comunicacionais, urbanísticas) — art. 20 §2º e §10 Lei 8.742/93; dependência de cuidados constantes; medicação contínua e risco de descompensação; impacto no desenvolvimento cognitivo, socialização e aprendizagem (criança); compromete autonomia em atividades básicas.
   - **Auxílio-doença / invalidez:** nexo causal/concausal com atividade laboral; uniprofissional/multiprofissional/omniprofissional; possibilidade de reabilitação profissional e prazo; tratamento clínico/cirúrgico disponível.
   - **Acidente do trabalho / auxílio-acidente:** lesão/sequela consolidada e definitiva; redução de capacidade laborativa habitual; nexo causal.
   - **Aposentadoria especial:** exposição habitual e permanente a agentes nocivos; eficácia dos EPIs; exposição acima do limite de tolerância (NR-15).
   - **Isenção de IR (Lei 7.713/88, art. 6º, XIV):** enquadramento na lista; data inicial da doença grave.

   ### B) Quesitos ao Assistente Social / Perito Socioeconômico
   (BPC-LOAS e ações em que a miserabilidade seja relevante)
   1. Composição do núcleo familiar (art. 20 §1º LOAS).
   2. Renda mensal individual + renda per capita.
   3. Renda abaixo de ¼ do SM? Se não, **circunstâncias excepcionais** (Tema 173/STF — miserabilidade ampliada).
   4. Despesas familiares (alimentação, moradia, energia, água, transporte, medicamentos, tratamentos).
   5. Condições de moradia (própria/alugada/cedida, conservação, saneamento, energia).
   6. Beneficiário de outro programa social (Bolsa Família, Auxílio Brasil, BPC).
   7. Gastos extraordinários (medicamentos, fraldas, terapias, cuidador) — valor mensal.
   8. Acesso a serviços públicos essenciais e barreiras (geográficas, físicas, transporte).
   9. Terceiro que provê o sustento.
   10. Para BPC-PCD: impacto do impedimento na vida cotidiana, participação social e possibilidade de trabalho.
   11. Para criança/adolescente PCD: membro da família precisou abandonar o trabalho para cuidar; impacto na renda.
   12. Situação de risco social e vulnerabilidade — justificar.

4. **Formatação:**
   - Lista **numerada e objetiva**.
   - Perguntas **respondíveis pelo perito** — sem juridiquês, sem retórica, sem pergunta indutiva.
   - Identificação do caso no topo (Processo nº, Autor, Benefício pleiteado).
   - Texto justificado.
   - DOCX no **timbrado do escritório** (chamar skill `timbrado-corbelino` se existir).
   - **Assinatura ao final:**
     ```
     Cáceres - MT, [DATA].
     (assinado digitalmente)
     PAULO ALEXANDRE SOARES CORBELINO
     OAB/MT 33.267
     ```

5. **Salvar** na pasta do cliente no Drive como `[NOME DO CLIENTE] - QUESITOS [MÉDICOS/SOCIOECONÔMICOS/MÉDICOS E SOCIOECONÔMICOS] - PRONTOS PARA REVISÃO.docx`.

6. **Encerrar** com:
   > **"Quesitos prontos para revisão do Dr. Paulo. Não protocolei — aguardando seu OK."**
   + **pontos de atenção:** lacunas documentais que mudariam quesitos (laudo de especialidade ausente, exame faltante, CADÚnico desatualizado); quesitos adicionais sugeridos a partir da tese específica; quesitos do INSS previstos (e como o autor deve se prevenir); especialidade médica que o perito deveria ter (para o juiz designar); prazo de juntada.

**REGRA DE OURO (incorpore na skill, inegociável):** nunca protocole nada — nem PJe, nem e-Proc, nem Meu INSS, nem GERID. Os quesitos vão prontos para o Dr. Paulo Alexandre Soares Corbelino revisar e juntar.

**Guard-rails:**
- **Nunca invente CID, doença, DID/DII ou diagnóstico.** Só com base no que o cliente/laudos apresentarem.
- **Quesitos sempre objetivos e técnicos**, no padrão dos modelos do Dr. Paulo.
- **Não conduzir o perito** — sem pergunta retórica ou indutiva.
- Para perícia médica, sempre cobrir: CID, DID, DII, natureza (parcial/total, temporária/permanente), prognóstico, nexo, reabilitação.
- Para estudo social de BPC, sempre cobrir: composição familiar, renda per capita, despesas, moradia, barreiras.
- Se faltar dado essencial, **peça antes de gerar** — não chute.
- Se for fora do previdenciário, avise e não tente cobrir.

**Tom:** técnico, objetivo, conciso. Linguagem que perito médico e assistente social respondem **sem ambiguidade**.

**Identidade institucional fixa:**
- Advogado titular: Dr. PAULO ALEXANDRE SOARES CORBELINO — OAB/MT 33.267
- Escritório: CORBELINO ADVOGADOS ASSOCIADOS
- E-mail: advpauloalexandre@gmail.com
- Telefone: (65) 99695-1616
- Foro: JEF Subseção de Cáceres-MT (Juízo 100% Digital)

Empacote tudo num pacote instalável no meu Claude.ai e me devolva o link/arquivo pra eu instalar.
