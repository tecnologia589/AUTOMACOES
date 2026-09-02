---
name: jurimetria
description: Análise de probabilidade de êxito de um processo (jurimetria) — cruza a tese e as matérias do caso com o perfil decisório do magistrado e os precedentes contra o mesmo réu, e entrega relatório premium no Drive. Use também para triagem/cobrança de processos (priorização por probabilidade).
trigger: /jurimetria
---

# Skill: Jurimetria (Probabilidade de Êxito)

Metodologia do escritório para estimar a chance de um processo e gerar o relatório
no padrão visual premium. **Sempre seguir estes passos, nesta ordem.**
Aplica-se tanto à preparação de audiência quanto à **triagem/cobrança de processos**
(priorizar e precificar casos pela probabilidade de êxito).

## Princípio inegociável
**NUNCA fabricar sentenças, números de processo, jurisprudência ou estatística.**
Se uma fonte estiver indisponível, dizer isso com transparência e seguir com o que é
verificável. Probabilidades são **prognóstico profissional**, não estatística — rotular como tal.

## Passo 1 — Ler a íntegra do processo
Reunir e ler TODAS as peças disponíveis (Drive + local):
petição inicial, **contestação**, **réplica** (revela a defesa e as provas dela),
rol de testemunhas, despachos/atas, documentos (holerites, cartões, CTPS, TRCT, CCTs).
- Buscar no Drive: `search_files` por `title contains '<cliente>'` e `fullText contains '<cliente>'`.
- Ler docx/PDF via `read_file_content`; arquivos grandes caem em tool-results → ler em chunks.
- A **réplica** costuma ser a peça-ouro: mapeia a contestação e as "provas que a defesa entregou".

## Passo 2 — Identificar o(a) magistrado(a) e confirmar quem sentencia
- Achar o nome na **ata de audiência / despacho** (não em petição, que traz "Exmo. Sr. Juiz").
- Conferir a lotação atual no portal de transparência do tribunal competente (TRT/TJ da região).
- **Atenção:** audiência inicial (Central de Iniciais) pode ter juiz diferente de quem
  preside a instrução/sentença na Vara. Confirmar quem efetivamente julgará.

## Passo 3 — Perfil decisório do magistrado (com honestidade)
- Tentar: JusBrasil / Escavador. **Acesso automatizado costuma retornar HTTP 403** —
  registrar a limitação. Sentenças de 1º grau não são indexadas por juiz em buscadores.
- Se houver login do escritório (JusBrasil Premium / PJe), o usuário pode exportar as
  sentenças; aí sim classificar pró-autor / pró-réu com base no texto real.
- **Sem dados confiáveis, não inventar perfil.** Quando há confissão documental ou admissão
  em audiência, o resultado depende pouco do perfil — registrar isso.

## Passo 4 — Precedentes contra o mesmo réu (mesmo tribunal)
Buscar no Drive/JusBrasil casos análogos contra a MESMA empresa/grupo (mesmas teses).
Levantar o resultado real de cada um (procedente/improcedente/parcial). É o sinal mais
preditivo depois da prova dos autos.

## Passo 5 — Cruzar tese × matéria → probabilidade por pedido
Para cada pedido, estimar a chance (faixa ou %) com base em:
força probatória (confissão documental > prova a produzir), jurisprudência consolidada
(súmulas/OJs/temas), e os precedentes do Passo 4. Marcar Alta/Média/Baixa.

## Passo 6 — Veredito global, cenários e recomendações
- Probabilidade do **núcleo do pedido** + cenário provável vs. adverso.
- Fatores que sobem/descem a chance (ex.: admissão em audiência ↑; réu em Recuperação Judicial ↓).
- Recomendações práticas para a instrução / próxima fase.

## Passo 7 — Gerar relatório premium e subir no Drive
Montar HTML no padrão visual premium do escritório (capa dark+dourado, Montserrat, seções
numeradas, blocos coloridos, tabela de probabilidades) e converter/subir com o helper testado:

```bash
python UTILS/relatorio_pdf_drive.py "saidas/<cliente> - Analise Probabilidade.html" --title "ANALISE DE PROBABILIDADE - <CLIENTE>"
# para atualizar mantendo o mesmo link:
python UTILS/relatorio_pdf_drive.py "saidas/<cliente> - Analise.html" --update <FILE_ID>
```

O helper (`UTILS/relatorio_pdf_drive.py`) faz HTML→PDF (Chrome/Edge headless, preserva
cores) → upload no Drive com link compartilhável. Rodar `--selftest` valida todos os caminhos.

## Para cobrança / triagem de processos
Ao avaliar uma carteira para cobrança ou priorização, rodar os Passos 1–5 de forma enxuta
e ordenar os processos pela probabilidade do núcleo do pedido — focar esforço/cobrança nos
de maior chance e sinalizar os de risco (ex.: réu em Recuperação Judicial).

## Ver também
- Roteiro de audiência: mesmo padrão visual premium (perguntas preposto/testemunhas).
- O subagente Revisora de Controladoria valida a jurisprudência citada antes do uso.
