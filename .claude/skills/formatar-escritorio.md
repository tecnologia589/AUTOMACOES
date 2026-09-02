---
name: formatar-escritorio
description: Aplica formatacao fiel do escritorio (Montserrat 11pt, recuo 7cm, citacoes 10pt italico, timbrado do escritorio) em texto bruto ou arquivo .docx existente. Sem chamar IA.
trigger: /formatar-escritorio
---

# Skill: Formatar Escritorio - aplica so a formatacao (sem IA)

## Quando usar

Quando ja existe um texto de peca redigido (manualmente ou por outra ferramenta) e
voce so quer aplicar a FORMATACAO oficial do escritorio + timbrado:

- Peca redigida em texto pela equipe e precisa do polish final
- Migrar peca de outra fonte para o padrao do escritorio
- Reformatar uma peca antiga
- Aplicar correcao de formatacao sem mexer no conteudo

Para gerar peca NOVA com IA, use `/peca-escritorio`.

## O que essa skill faz

1. Le texto bruto (.txt ou .docx convertido) com marcacao simples:
   - Linhas em branco separam paragrafos
   - Numeracao I., I.I., a), b) detecta titulos/subtitulos
   - Linha comecando com aspa (") vira citacao
   - `**texto**` -> negrito inline
   - `_texto_` -> italico inline
   - Marcadores markdown `#`, `##`, `###` sao limpos automaticamente
2. Renderiza no timbrado do escritorio com formatacao FIEL:
   - Margens 3 / 1.6 / 3 / 3 cm
   - Montserrat 11pt (corpo)
   - Citacoes em 10pt italico, recuo esquerdo 4cm
   - Recuo 1a linha 7cm literais
   - Espacamento 1.5
   - Nome da peca centralizado bold
   - Titulos de secao com travessao longo "–" (nao hifen)

## Como invocar

```python
import sys
sys.path.insert(0, 'OPERACIONAL/agente_operacional')
from peca_escritorio_engine import formatar_no_timbrado

# Le seu texto bruto (de onde quiser)
texto = open('minha_peca_bruta.txt', encoding='utf-8').read()

# Aplica formatacao + salva
out = formatar_no_timbrado(texto, 'CLIENTE - Peticao Inicial.docx')
print(f'Peca formatada: {out}')
```

Ou diretamente o formatador puro:

```python
import sys
sys.path.insert(0, 'OPERACIONAL/agente_operacional')
import escritorio_format as PF

PF.gerar_peca(texto, 'output.docx')
```

## Especificacoes aplicadas

| Item | Valor |
|---|---|
| Pagina | A4 (21 x 29.7 cm) |
| Margens | top 3 / bottom 1.6 / left 3 / right 3 cm |
| Fonte | Montserrat |
| Corpo | 11 pt |
| Citacoes (jurisprudencia/sumula) | 10 pt italico |
| Espacamento linha | 1.5 |
| Recuo 1a linha (corpo + pedidos) | 7 cm literais |
| Recuo esquerdo citacoes | 4 cm |
| space_before / space_after | None |
| Alinhamento padrao | Justificado |

## Estrutura detectada automaticamente

- "EXCELENTISSIMO..." -> enderecamento (justify, bold, sem recuo)
- "RECLAMATORIA TRABALHISTA" / "CONTESTACAO" / "REPLICA" -> nome da peca (CENTER, bold)
- "I - ...", "II - ...", "I.I - ..." -> titulo de secao (justify, bold, travessao longo)
- "a) ...", "b) ..." em meio de paragrafo -> subtitulo (justify, bold)
- "a) ...", "b) ..." na secao V/PEDIDOS -> pedido (justify, recuo 7cm)
- Linha comecando com aspa -> citacao (10pt italico, recuo esquerdo 4cm)

## Boas praticas relacionadas

- Obrigatorio gerar no timbrado do escritorio
- Recuo 1a linha 7cm literais
- Assinatura padrao: Dr. Paulo Alexandre Soares Corbelino — OAB/MT 33.267 — Cáceres/MT
