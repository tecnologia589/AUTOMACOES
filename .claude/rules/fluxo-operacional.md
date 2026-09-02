# Fluxo Operacional - Corbelino Advogados Associados

## Ordem de Execucao do Intake

1. **Reuniao inicial** - Advogado preenche o cadastro do cliente (CADASTRO_CLIENTE.txt)
2. **Coleta de documentos** - CNH/RG, comprovante de endereco, CTPS e demais
3. **Rodar automacao** - `python INTAKE/main.py "TRANSCRICAO.pdf" "DOC_PESSOAL.pdf" "CADASTRO.txt"`
4. **Analise da IA** (etapa 1) - Analise tecnica completa do caso
5. **Extracao de dados** (etapa 2) - Questionario + dados pessoais
6. **Criar pasta** - NOME DO CLIENTE (subpastas padrao)
7. **Gerar Ficha** - Documento guia com analise e dados
8. **Gerar Contrato** - Honorarios advocaticios preenchido
9. **Gerar Procuracao** - Ad judicia preenchida
10. **Gerar Declaracao** - Hipossuficiencia preenchida

## POP - Procedimento Operacional Padrao (Pos-Automacao)
1. Revisar documentos gerados
2. Vincular no ZapSign para assinatura digital
3. Cadastrar cliente no ADVBOX
4. Computar prazos (PFI e PF)
5. Enviar resumo da contratacao ao cliente
6. Cobrar documentos faltantes

## Regras gerais
- Pecas geradas pela IA sao SEMPRE para revisao do advogado antes de protocolar.
- Nunca alterar dados no ADVBOX sem autorizacao explicita (consulta livre).
- Nunca criar pasta/arquivo no Drive sem autorizacao explicita.
