---
name: peca-escritorio
description: Gera peca juridica completa (PI, contestacao, replica, recurso) com o DNA de escrita do escritorio + formatacao fiel ao timbrado. Usa Opus + amostras reais do escritorio + jurisprudencia.
trigger: /peca-escritorio
---

# Skill: Peca Escritorio - Producao de pecas no padrao do escritorio

## Quando usar

Sempre que precisar produzir uma peca processual em nome do escritorio
(PI, contestacao, replica, recurso ordinario, recurso de revista, contrarrazoes, embargos,
manifestacoes, parecer juridico, agravo).

Use esta skill em vez de gerar texto neutro de IA com `template_engine.py`.

## O que essa skill faz

1. Carrega 1-2 pecas REAIS do escritorio como amostras de estilo (depositadas em `REFERENCIAS/`)
2. Carrega o DNA de escrita do escritorio (arquivo `REFERENCIAS/DNA_TOM_ESCRITA.md`)
3. Chama Opus (streaming + retry de rede) com system prompt assertivo aplicando:
   - Vocabulario-marca do escritorio (ex.: "cristalino", "Excelencia,", "Ademais", "Outrossim")
   - Estrutura: narrativa cinematografica + calculo aritmetico + ementa em bloco
   - Tese subsidiaria sempre + ataque a ma-fe explicito
4. Limpa marcadores markdown
5. Renderiza no timbrado do escritorio com formatacao FIEL:
   - Montserrat 11pt (citacoes 10pt italico)
   - Recuo 1a linha 7cm literais
   - Margens 3/1.6/3/3 cm
   - Citacoes com recuo esquerdo 4cm
   - Espacamento 1.5

## Como invocar

### A) Python direto (em script de cliente):

```python
import sys
from pathlib import Path
sys.path.insert(0, 'OPERACIONAL/agente_operacional')
from peca_escritorio_engine import produzir_peca

dados_caso = """
Cliente: [nome completo, CPF, RG, nacionalidade, endereco, telefone]
Parte contraria: [nome empresa, CNPJ, endereco]
Vinculo: [periodo, salario formal vs real, funcao]
Fatos relevantes:
  - [lista de fatos do caso]
Provas em poder do cliente:
  - [holerites, extratos, registros, etc]
Contrato: CT XXX/AAAA
Enderecamento: Vara do Trabalho de [comarca]
Valor da causa estimado: R$ XXX.XXX
"""

# Opcional: incluir jurisprudencia verificada e/ou esqueleto de outra peca
out = produzir_peca(
    dados_caso=dados_caso,
    output_path='CLIENTE - Peticao Inicial.docx',
    tipo_peca='PETICAO INICIAL',
    jurisprudencia=open('jurisprudencia.md').read(),  # opcional
    esqueleto=open('modelo.txt').read(),              # opcional
    incluir_amostras=True,                            # default
)
print(f'Peca gerada: {out}')
```

### B) Pelo agente operacional (CORBELINO.IA)

Adicionar nova categoria `peca_escritorio` no agente (mesma logica das outras categorias),
que invoca `peca_escritorio_engine.produzir_peca()` com os dados recebidos do card.

## Estrutura de arquivos

```
OPERACIONAL/agente_operacional/
├── escritorio_format.py         # formatador fiel (Montserrat 11, recuo 7cm, etc)
├── peca_escritorio_engine.py    # engine: gera texto Opus + formata
├── timbrado_modelo.docx         # timbrado do escritorio (cabecalho/logo/rodape)
└── REFERENCIAS/
    ├── DNA_TOM_ESCRITA.md       # expressoes-marca + regras de tom do escritorio
    ├── PECA_REF_01.docx         # peca-modelo real (cliente deposita)
    ├── PECA_REF_02.docx
    ├── peca_ref_01.txt          # versao texto pra alimentar Opus
    └── peca_ref_02.txt
```

## Resultado esperado (peca formatada)

- Texto integral no timbrado do escritorio
- Montserrat (corpo 11pt | citacoes 10pt italico)
- Paragrafos com recuo de 1a linha 7cm literais
- Margens 3.0 / 1.6 / 3.0 / 3.0 cm
- Vocabulario-marca do escritorio aplicado (vocativos, conectivos)
- Jurisprudencia verificada incluida em bloco

## Assinatura padrao das pecas

Dr. Paulo Alexandre Soares Corbelino — OAB/MT 33.267 — Cáceres/MT

## Boas praticas relacionadas

- Sempre usar Opus para producao de pecas juridicas
- Toda peca gerada no timbrado do escritorio (nunca em folha branca)
- Recuo de 1a linha 7cm literais
- A peca segue para a Revisora de Controladoria antes do protocolo
