---
description: Executa o intake completo de um novo cliente
---

# Comando: Intake

Gera automaticamente todos os documentos de um novo cliente.

## Prerequisitos
1. `CADASTRO_CLIENTE.txt` preenchido com dados da reuniao
2. Transcricao da reuniao em PDF
3. Documento pessoal do cliente (CNH ou RG) em PDF

## Execucao
```bash
python INTAKE/main.py "TRANSCRICAO.pdf" "DOC_PESSOAL.pdf" "CADASTRO_CLIENTE.txt"
```

## Resultado esperado
- Pasta criada com o NOME DO CLIENTE (subpastas padrao)
- Ficha do Cliente com analise completa da IA
- Contrato de Honorarios preenchido
- Procuracao ad judicia preenchida
- Declaracao de Hipossuficiencia preenchida

## Proximos passos (manual)
1. Revisar todos os documentos
2. Vincular no ZapSign
3. Cadastrar no ADVBOX
4. Computar prazos
5. Enviar ao cliente
