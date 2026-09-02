# Regras de Compliance Juridica - Corbelino Advogados Associados

## Campos Obrigatorios por Documento

### Ficha do Cliente (DOCUMENTO GUIA)
A ficha e o documento principal. Deve ser preenchida PRIMEIRO.
Todos os demais documentos sao gerados a partir dos dados da ficha.

### Dados que devem vir de documentos pessoais (CNH, RG)
- Nome completo
- CPF
- RG e orgao emissor
- Nacionalidade
- Data de nascimento

### Dados que devem vir do cadastro/reuniao
- Telefone
- Email
- Endereco completo
- Estado civil
- Profissao
- Parte contraria / empresa reclamada
- Indicante
- Origem

## Validacoes Criticas
- CPF deve estar no formato XXX.XXX.XXX-XX
- Datas no formato DD/MM/YYYY
- Endereco deve ter: rua, numero, bairro, cidade, estado, CEP
- Nunca inventar dados - se nao tem, deixar o placeholder

## Direitos Previdenciarios a Validar (area principal - Dr. Paulo Alexandre)
- Tempo de contribuicao / carencia (RGPS e RPPS)
- Averbacao de periodos (CTC, vinculos, tempo rural)
- Enquadramento em regras de transicao (EC 103/2019)
- Aposentadoria especial - exposicao a agente nocivo, PPP/LTCAT
- Aposentadoria do professor - tempo de magisterio, funcoes equiparadas
- Previdencia rural - inicio de prova material + prova testemunhal
- Beneficio por incapacidade / avaliacao biopsicossocial (quando aplicavel)
- Revisao de RMI, buraco negro, indice de correcao

## Direitos Trabalhistas a Validar (area de expansao - base generica, ver agentes_claude/corbelino-trabalhista.md)
- Reconhecimento de vinculo empregaticio
- Verbas rescisorias (aviso previo, ferias + 1/3, 13o, FGTS + 40%)
- Horas extras, intervalo intrajornada/interjornada
- Rescisao indireta
- Equiparacao salarial, adicionais (insalubridade, periculosidade)
- Dano moral trabalhista

## Direito Bancario / Defesa do Consumidor a Validar (area de expansao - base generica, ver agentes_claude/corbelino-bancario.md)
- Juros abusivos, capitalizacao indevida, tarifas nao pactuadas
- Venda casada / seguros embutidos sem consentimento claro
- Busca e apreensao (financiamento de veiculo) - defesa
- Parecer de viabilidade OBRIGATORIO antes de qualquer acao revisional/defensiva

> Observacao: o escritorio atua em tres frentes - Previdenciario (foco original,
> ja calibrado), Trabalhista e Bancario/Consumidor (expansao, bases genericas
> pendentes de calibracao com pecas reais do Dr. Paulo Alexandre). Ajustar o rol
> de verificacao conforme a area do caso. Abrangencia geografica: Cáceres/MT e
> Pontes Lacerda/MT.
