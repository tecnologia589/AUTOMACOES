# Onboarding — Corbelino Advogados Associados

Checklist de configuracao. Faca **na ordem**. Marque cada item ao concluir.
Todo o preenchimento acontece em `config/.env` (copie de `config/.env.example`),
em `config/equipe.py` e em `config/regras_financeiras.py`.

---

## 0. O que ja se sabe

- **Nome / marca:** Corbelino Advogados Associados.
- **Advogado responsavel:** Dr. Paulo Alexandre Soares Corbelino — OAB/MT 33.267.
- **E-mail:** advpauloalexandre@gmail.com. Telefone: (65) 99695-1616.
- **Areas:** Previdenciario (foco original — BPC/LOAS, aposentadorias, beneficios
  por incapacidade, revisoes) e expansao para Trabalhista e Bancario/Defesa do
  Consumidor.
- **Abrangencia geografica:** Cáceres/MT e Pontes Lacerda/MT.
- **Sistema juridico:** NAO CONFIRMADO. Nao ha nenhuma informacao de que o
  escritorio use ADVBOX ou qualquer outro software de gestao — confirmar com o
  Dr. Paulo Alexandre antes de configurar `INTEGRACOES/advbox_integration.py`.
- **CRM/atendimento/cobranca:** NAO CONFIRMADO. Nenhuma ferramenta informada.
- **Agentes juridicos de IA:** ja existem e estao calibrados/prontos em
  `agentes_claude/`:
  - `corbelino-previdenciario.md`, `corbelino-iniciais.md`, `corbelino-quesitos.md`
    — calibrados com material REAL do Dr. Paulo Alexandre (peticao-modelo e base
    de conhecimento previdenciaria dele).
  - `corbelino-trabalhista.md`, `corbelino-bancario.md` — bases genericas de boa
    qualidade (playbook padrao da area), AINDA sem material real dele nessas 2
    areas. Ver `agentes_claude/README.md` / `GUIA_INSTALACAO_CLAUDE_AI.md`.
- **Timbrado:** AINDA NAO RECEBIDO.

## 1. Credenciais de API (config/.env)

Nenhuma credencial foi recebida ate a criacao deste repositorio. Confirmar com o
Dr. Paulo Alexandre, uma a uma:

- [ ] **ANTHROPIC_API_KEY** — chave da API Claude (console.anthropic.com).
- [ ] **ADVBOX_API_TOKEN** — SE o escritorio usar ADVBOX (a confirmar).
- [ ] **ASAAS_API_TOKEN** — SE usar Asaas para cobranca (a confirmar).
- [ ] **ZAPSIGN_API_TOKEN** — SE for usar assinatura digital via ZapSign.
- [ ] **ATENDE_DIREITO_TOKEN** — SE for usar CRM/WhatsApp Atende Direito.
- [ ] **Google Cloud** — coloque o JSON de credenciais em `config/credentials.json`
      (Service Account ou OAuth) e, se OAuth, gere o `token.json` no 1o uso.

## 2. Identidade do escritorio (config/.env)

Ja vem com os defaults do Corbelino Advogados Associados. Confira/ajuste:
- [x] ESCRITORIO_NOME / NOME_ESCRITORIO = Corbelino Advogados Associados
- [ ] ESCRITORIO_CNPJ — nao recebido.
- [x] ESCRITORIO_ADVOGADO = Dr. Paulo Alexandre Soares Corbelino
- [x] ESCRITORIO_OAB = OAB/MT 33.267
- [x] ESCRITORIO_CIDADE / CIDADE_FORO = Cáceres/MT e Pontes Lacerda/MT
- [ ] ESCRITORIO_ENDERECO — endereco fisico do escritorio, nao recebido.
- [x] ESCRITORIO_TELEFONE = (65) 99695-1616, ESCRITORIO_EMAIL =
      advpauloalexandre@gmail.com
- [ ] ADVOGADO_RESPONSAVEL_EMAIL — confirmar se e o mesmo e-mail institucional
      acima ou um pessoal diferente, para signatario padrao (ZapSign/ADVBOX).

## 3. Usuarios ADVBOX (config/.env + config/equipe.py)

SE o escritorio usar ADVBOX, no painel ADVBOX > Usuarios, pegue os IDs e preencha:
- [ ] **ADVBOX_USER_RESPONSAVEL** — ID do Dr. Paulo Alexandre Soares Corbelino.
- [ ] ADVBOX_USER_OPERACIONAL — ID de quem recebe tarefas operacionais.
- [ ] ADVBOX_USER_FINANCEIRO — ID de quem lanca transacoes financeiras.
- [ ] ADVBOX_USER_FROM — ID do usuario que "assina" as tarefas (/posts).
- [ ] ADVBOX_USER_AGENTE — ID da conta-agente (CORBELINO.IA) que recebe as
      tarefas do robo.
- [ ] ADVBOX_TASK_TYPE_ACOMPANHAMENTO — ID do tipo de tarefa de acompanhamento.
- [ ] (Opcional) ADVBOX_USERS_MAP = "ID:NOME,ID:NOME" para exibir nomes nos
      relatorios.

## 4. Google Drive / Docs (config/.env)

Crie no Drive do escritorio e cole os IDs:
- [ ] GOOGLE_TEMPLATE_ID — Google Doc da Ficha-molde.
- [ ] GOOGLE_PASTA_RECLAMANTE — pasta raiz onde nascem as pastas de cliente.
- [ ] GOOGLE_SHEETS_CONTRATOS_ID (+ GOOGLE_PLANILHA_CONTRATOS / GOOGLE_ABA_CONTRATOS)
      — planilha de numeracao de contratos.
- [ ] Modelos e pastas dos documentos do intake (preencher os pares com e sem
      _ID iguais): GOOGLE_TEMPLATE_CONTRATO(_ID) / GOOGLE_PASTA_CONTRATO(_ID),
      GOOGLE_TEMPLATE_PROCURACAO(_ID) / GOOGLE_PASTA_PROCURACAO(_ID),
      GOOGLE_TEMPLATE_DECLARACAO(_ID) / GOOGLE_PASTA_DECLARACAO(_ID).
- [ ] Financeiro: DRIVE_PASTA_FECHAMENTO_ID, DRIVE_PASTA_FINANCEIRO_ID,
      DRIVE_PLANILHA_HISTORICO_ID, DRIVE_PLANILHA_RESULTADO_ID.
- [ ] DRIVE_PASTA_CLIENTES_ID — usada pelo handler de sincronizacao de assinados.

## 5. Regras financeiras (config/regras_financeiras.py)

Vem VAZIO de proposito (sem comissao nenhuma calculada). O escritorio tem um
unico advogado responsavel — nao ha indicacao ate agora de estrutura de
comissionamento com terceiros. Cadastrar apenas se/quando isso for definido:
- [ ] **COMISSOES** — para cada comissionado: rotulo, sufixos na descricao do
      Asaas, percentual, advbox_customers_id, exclusoes e (se for o caso)
      lista_fechada.
- [ ] **ADVBOX_FINANCEIRO** — banco/centro de custo/categoria para lancar
      comissoes.
- [ ] **EXCLUIR_FATURAMENTO** — clientes que nao contam como receita (se houver).
- [ ] **PERCENTUAL_PROVISAO_LUCRO** — se o escritorio usa provisao/reserva
      (default 0).

## 6. Listas de cobranca (FINANCEIRO/)

- [ ] `clientes_nao_cobrar.txt` — um cliente por linha (quem NUNCA recebe
      cobranca).
- [ ] `clientes_negociar.txt` — clientes em negociacao/acordo.

## 7. Padrao de pecas / timbrado

- [ ] `config/timbrado_modelo.docx` — AINDA NAO RECEBIDO. O escritorio precisa
      enviar o .docx oficial (logo + cabecalho/rodape) — ver
      `config/timbrado_modelo.LEIA-ME.txt` para o formato exigido.
- [ ] Confirmar margens (o motor aplica o padrao PAB 3cm/1,6cm/3cm/3cm por
      default — confirmar se o escritorio usa o mesmo).
- [x] Agentes juridicos ja calibrados para Previdenciario (ver secao 0) —
      cobrem o "DNA de escrita" real do Dr. Paulo Alexandre para essa area sem
      depender de `OPERACIONAL/agente_operacional/REFERENCIAS/`.
- [ ] **Trabalhista e Bancario:** pedir 1-2 pecas ja protocoladas em cada area
      para recalibrar `agentes_claude/corbelino-trabalhista.md` e
      `corbelino-bancario.md` puxando o estilo real (mesmo processo usado no
      previdenciario a partir da peticao-modelo "LOAS Indeferido — MENOR").

## 8. Agente Operacional (CORBELINO.IA)

- [ ] AGENTE_OP_TOKEN — defina um token forte (autentica o webhook).
- [ ] AGENTE_OP_PORT — porta do servidor (default 8787).
- [ ] (Opcional) AGENTE_OP_USER_PHONES — JSON {"<id_advbox>":"<telefone>"} para
      notificacao WhatsApp ao concluir tarefa.
- [ ] Suba o servico: `OPERACIONAL/agente_operacional/iniciar_servicos.bat`
      (Windows) ou `.sh` (macOS/Linux). Testar com `verificar_servicos` e parar
      com `parar_servicos`.
- [ ] Configure o gatilho/n8n (`n8n_workflow.json`) apontando para a URL do
      webhook e usando o AGENTE_OP_TOKEN.
- [ ] Para rodar 24/7, avaliar deploy em VPS (`docs/DEPLOY_VPS.md`, systemd) —
      decidir com o escritorio se sera VPS propria ou compartilhada.

## 9. Agendamentos

- [ ] SYNC de assinados 3x/dia: `SYNC/sync_assinados.bat` (Windows) / `.sh`
      (macOS/Linux). Agendar via Task Scheduler (Windows) ou cron/launchd
      (macOS/Linux).
- [ ] (Opcional) Cobranca semanal: agendar `FINANCEIRO/cobranca_semanal.py` do
      mesmo jeito.

---

### Verificacao final

- [ ] `python OPERACIONAL/main.py tarefas` lista tarefas do ADVBOX sem erro
      (depende de ADVBOX_API_TOKEN + ADVBOX_USER_RESPONSAVEL preenchidos, e de
      confirmar que o escritorio usa ADVBOX).
- [ ] `python FINANCEIRO/fechamento_mensal.py MM/YYYY --sem-lancar` roda o
      fechamento (modo seguro) — depende das regras financeiras (secao 5).
- [ ] Um intake de teste gera os 4 documentos no timbrado real (apos o timbrado
      ser recebido) e envia para assinatura/ADVBOX conforme definido.
- [ ] Testar os 5 agentes juridicos em `agentes_claude/` — ver
      `GUIA_INSTALACAO_CLAUDE_AI.md` para instalar como Projects no Claude.ai.
