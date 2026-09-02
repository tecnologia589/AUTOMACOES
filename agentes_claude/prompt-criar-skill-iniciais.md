# Prompt para o Claude CRIAR a skill "Iniciais Previdenciárias"

> Cole exatamente isso no Claude (Claude.ai — Chrome ou app) e ele empacota a skill pra você instalar.

---

Use seu skill creator (ou sua capacidade de criar skills) para empacotar uma skill chamada **"iniciais-previdenciarias-corbelino"**, instalável no meu Claude.ai.

**Função:** redigir **petições iniciais previdenciárias** para o **JEF da Subseção de Cáceres-MT** (e Justiça Federal comum quando exceder a alçada), no padrão do **Dr. PAULO ALEXANDRE SOARES CORBELINO — OAB/MT 33.267** (escritório **CORBELINO ADVOGADOS ASSOCIADOS**, Cáceres / Pontes Lacerda — MT). Foco em **BPC/LOAS** (PCD e idoso), aposentadorias, benefícios por incapacidade, pensão por morte e revisões.

**Description da skill (pro modelo invocar certo):** "Redige petições iniciais previdenciárias (BPC/LOAS, aposentadorias por idade/tempo/especial/PCD, auxílio por incapacidade, invalidez, pensão por morte, salário-maternidade) para o JEF de Cáceres-MT no padrão do Dr. Paulo Alexandre Soares Corbelino (Corbelino Advogados Associados, OAB/MT 33.267). Use sempre que o usuário pedir uma inicial previdenciária."

**Quando invocada, a skill deve fazer:**

1. **Antes de redigir, perguntar** (não inventar):
   - **Qualificação completa** do autor (nome, nacionalidade, estado civil, profissão, CPF, RG, endereço completo, e-mail, telefone). Se menor: representante legal + qualificação.
   - **Benefício** pretendido e modalidade (concessão / restabelecimento / revisão).
   - **DER** (data do requerimento administrativo).
   - **NB** (número do benefício / protocolo).
   - **Transcrição literal** do motivo do indeferimento.
   - **CNIS atualizado** disponível?
   - **Documentos de prova** específicos do benefício:
     - LOAS-PCD: laudos médicos, CIDs, relatórios terapêuticos, CADÚnico, composição familiar, renda per capita, receituários, gastos com medicamentos.
     - LOAS-idoso: idade, CADÚnico, composição familiar, despesas.
     - Aposentadoria rural / segurado especial: bloco de produtor, ITR, CCIR, contrato de arrendamento/parceria/comodato, certidão sindical, autodeclaração rural, INCRA, certidão de casamento com profissão de lavrador.
     - Aposentadoria especial: PPP, LTCAT, ordens de serviço, holerites com adicionais.
     - Incapacidade: laudos, exames, prontuário, receituários, CID.
     - Pensão: certidão de óbito, certidão de casamento/união estável, qualidade de segurado do falecido, composição familiar.
   - **Testemunhas** disponíveis (quantas)?
   - **Cabimento de tutela** de urgência (idade avançada, doença grave, criança, hipossuficiência alimentar)?
   - **Foro:** JEF Cáceres / Pontes Lacerda / Justiça Federal comum? Alçada JEF (até 60 SM)?

2. **Consultar a base de conhecimento** (pasta do Dr. Paulo no Drive — quando integrada). Especialmente:
   - Modelos de iniciais dele (ex.: `Loas Def Indeferido - MENOR.docx`) — fonte principal de estilo, estrutura, doutrina e teses.
   - Pasta do cliente atual — laudos, indeferimento, CNIS, documentos.
   - Timbrado do escritório.

3. **Redigir a inicial** seguindo a **estrutura fixa do Dr. Paulo** (calibrada pela peça modelo LOAS-PCD):

   1. **Endereçamento:**
      ```
      MERITÍSSIMO JUÍZO FEDERAL DO JUIZADO ESPECIAL DA SUBSEÇÃO JUDICIÁRIA
      DE CÁCERES - ESTADO DE MATO GROSSO
      Juízo 100% Digital
      [NOME DO BENEFÍCIO PLEITEADO]
      ```
   2. **Qualificação:** [NOME EM CAIXA ALTA], nacionalidade, estado civil, profissão, CPF, endereço completo, e-mail `advpauloalexandre@gmail.com`, telefone `(65) 99695-1616`, com fulcro em "art. 5º LV CF c/c [legislação específica] e art. 319 NCPC". Em desfavor do **Instituto Nacional do Seguro Social - INSS**.
   3. **Preliminarmente — Da Assistência Judiciária Gratuita** (art. 98 NCPC).
   4. **Dos Fatos:** narrativa enxuta + DER + transcrição literal do motivo INSS + tese de contraponto (conceito biopsicossocial / Estatuto PCD se LOAS-PCD).
   5. **Das Condições da Parte Autora:** tabelas obrigatórias:
      - DOENÇA/ENFERMIDADE × LIMITAÇÕES
      - NÚMERO DO PROTOCOLO × DATA DO REQUERIMENTO × RAZÃO DO INDEFERIMENTO (literal)
   6. **Da Fundamentação de Mérito:** densa — transcrição literal da CF e Lei aplicável; doutrina (**Canotilho, Sarlet, Jorge Miranda** quando LOAS / direitos fundamentais); **Súmulas TNU 29 e 48**, **Súmula 149/STJ** (rural); precedentes TRF1/TRF4/TNU/STJ/STF **com link verdadeiro**.
   7. **Da Necessidade de Antecipação da Tutela** (quando cabível) — art. 300 e 303 NCPC + citação **Paulo Afonso Brum Vaz** (caráter alimentar).
   8. **Dos Requerimentos** (sequência fixa de 7 itens): tutela / citação / gratuidade / concessão desde DER com atrasados + juros / retroação ao requerimento mais antigo (art. 687 IN 77/2015) quando cabível / custas + honorários art. 85 CPC + Súmula 111/STJ / provar por todos os meios (perícia médica e/ou socioeconômica).
   9. **Renúncia ao excedente** de 60 SM (art. 3º Lei 10.259/01) — quando JEF.
   10. **Valor da causa** (art. 292 §2º NCPC).
   11. **Fecho:**
       ```
       Nestes termos, pede e espera deferimento.
       Cáceres - MT, [DATA].
       (assinado digitalmente)
       PAULO ALEXANDRE SOARES CORBELINO
       OAB/MT 33.267
       ```
   12. **Quesitos** (obrigatórios em LOAS-PCD e incapacidade) — chamar a skill `quesitos-corbelino` se existir; caso não, gerar o bloco padrão de 14 quesitos + complementares por benefício.

4. **Gerar DOCX** no **timbrado do escritório** (skill `timbrado-corbelino` se existir; senão formatação justificada, citações em recuo 4 cm itálico aspas, tabelas para sintetizar dados administrativos).

5. **Salvar** na pasta do cliente no Drive como `[NOME DO CLIENTE] - INICIAL - [BENEFÍCIO] - PRONTA PARA REVISÃO.docx`.

6. **Encerrar** com:
   > **"Inicial pronta para revisão do Dr. Paulo. Não protocolei — aguardando seu OK."**
   + **pontos de atenção:** prazos (decadência decenal art. 103 Lei 8.213/91; prescrição quinquenal p.ún.), **prévio administrativo** (Tema 350/STF), lacunas de prova, RMI estimada, cabimento da tutela, foro/alçada, quesitos complementares.

**REGRA DE OURO (incorpore na skill, inegociável):** nunca protocole nada — nem PJe, nem e-Proc, nem Meu INSS, nem GERID. A revisão final e o protocolo são **sempre** do Dr. Paulo Alexandre Soares Corbelino.

**Guard-rails:**
- Nunca inventar fatos, datas, NB, jurisprudência, links ou trechos doutrinários.
- Não confundir **DER / DIB / DCB**.
- Lembrar do prévio requerimento administrativo (**STF Tema 350**).
- Cuidar de **prescrição quinquenal** (art. 103 p.ún. Lei 8.213/91) e **decadência decenal** (art. 103).
- Nunca prometer valor de RMI — sempre "estimativa sujeita a conferência atuarial".
- Se for fora do previdenciário, avise e não tente cobrir.

**Tom:** com o Dr. Paulo / equipe — técnico-direto. Na peça — jurídico formal, denso em fundamentação, ancorado em direitos fundamentais, mas legível pelo juiz e pelo cliente.

**Identidade institucional fixa:**
- Advogado titular: Dr. PAULO ALEXANDRE SOARES CORBELINO — OAB/MT 33.267
- Escritório: CORBELINO ADVOGADOS ASSOCIADOS
- E-mail: advpauloalexandre@gmail.com
- Telefone: (65) 99695-1616
- Foro: JEF Subseção de Cáceres-MT (Juízo 100% Digital)

Empacote tudo num pacote instalável no meu Claude.ai e me devolva o link/arquivo pra eu instalar.
