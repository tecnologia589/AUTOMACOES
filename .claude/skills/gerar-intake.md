---
name: gerar-intake
description: Gera o intake completo de um novo cliente - ficha, contrato, procuracao e declaracao
trigger: /intake
---

# Skill: Gerar Intake Completo

## Uso
```
python INTAKE/main.py "TRANSCRICAO.pdf" "DOC_PESSOAL.pdf" "CADASTRO_CLIENTE.txt"
```

## Aceita multiplos documentos extras
```
python INTAKE/main.py "TRANSCRICAO.pdf" "DOC_PESSOAL.pdf" "CTPS.pdf" "COMPROVANTE.pdf" "CADASTRO.txt"
```

## Formatos aceitos
- `.pdf` - Transcricoes, CNH/RG, CTPS, comprovantes (com OCR automatico)
- `.txt` - Cadastro do cliente preenchido na reuniao
- `.docx` - Fichas ou documentos Word

## O que gera automaticamente
1. Pasta do cliente (com subpastas padrao)
2. Ficha do Cliente (analise da IA + questionario + dados pessoais)
3. Contrato de Honorarios
4. Procuracao ad judicia
5. Declaracao de Hipossuficiencia

## Passo a passo para o operador
1. Preencher `CADASTRO_CLIENTE.txt` durante a reuniao
2. Salvar transcricao como PDF
3. Coletar documento pessoal do cliente (CNH/RG em PDF)
4. Rodar o comando acima
5. Revisar documentos gerados no Google Drive
