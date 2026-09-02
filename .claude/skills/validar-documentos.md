---
name: validar-documentos
description: Valida se todos os campos obrigatorios foram preenchidos nos documentos gerados
trigger: /validar
---

# Skill: Validar Documentos

## Uso
Apos gerar o intake, rodar validacao:
```
/validar [link-do-documento]
```

## Checklist automatico
- Verifica se todos os placeholders {{}} foram substituidos
- Confirma dados pessoais presentes (CPF, RG, endereco)
- Valida formatacao (fonte Montserrat, 11pt)
- Confere consistencia entre documentos (mesmo CPF em todos)
- Identifica campos vazios que precisam preenchimento manual

## Resultado
- Lista de campos OK
- Lista de campos faltantes
- Sugestoes de correcao
