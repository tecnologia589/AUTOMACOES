"""
Handler para qualquer peca juridica: inicial, contestacao, replica, razoes finais,
recursos ordinarios/especiais, contrarrazoes, embargos, manifestacoes, memoriais.

Fluxo:
  1. Recebe contexto (processo + cliente + pasta + POP + arquivos + conteudo extraido)
  2. Monta prompt para o Claude Opus incluindo POP como bloco cacheado
  3. Gera a peca em papel timbrado (sempre, regra do escritorio)
  4. Sobe no Drive (ATOS INTERNOS da pasta do cliente)
  5. Retorna {sucesso, titulo, resumo, doc_link}
"""
import logging

from ..config import ESCRITORIO_NOME, ESCRITORIO_CIDADE, ESCRITORIO_ASSINATURA
from ..llm_client import gerar_peca
from ..acentuacao import corrigir_acentuacao
from .base import salvar_docx_no_drive, montar_bloco_contexto

log = logging.getLogger('agente_op.peca')


SYSTEM_PROMPT = f"""Você é advogado(a) sênior do escritório {ESCRITORIO_NOME} ({ESCRITORIO_ASSINATURA}).
Você produz peças para revisão da equipe antes do protocolo.

IDIOMA E ORTOGRAFIA (CRÍTICO):
- Escreva SEMPRE em português brasileiro (PT-BR) com ortografia correta.
- Use TODOS os acentos gráficos: agudo (á é í ó ú), circunflexo (â ê ô), til (ã õ), cedilha (ç), grave (à).
- NUNCA escreva sem acento palavras como: reanálise, peças, ação, contestação, réplica, recurso, petição,
  contrarrazões, manifestação, código, artigo, parágrafo, jurisprudência, inciso, decisão, sentença,
  juízo, ciência, pessoa jurídica, pessoa física, pecuniário, genérico, específico, razões, razão,
  extinção, execução, desconsideração, terceiros, obrigação, responsabilidade, êxito, ônus, contrário,
  já qualificado, até, também, ainda, pública, privada, está, estão, será, serão, inaplicável, cabível.
- Atenção especial em: artigos 1º, 2º, § 1º, §§, inciso I, etc.

REGRAS JURÍDICAS:
- TODA peça deve respeitar o POP fornecido abaixo (estrutura, teses, jurisprudência).
- Escritório: {ESCRITORIO_NOME} - {ESCRITORIO_CIDADE}.
- Assinatura: {ESCRITORIO_ASSINATURA}.
- Nunca invente fatos. Use APENAS os dados fornecidos no contexto (processo, cliente, arquivos).
- Se um dado faltar, deixe placeholder explícito [FALTA: descrição do dado].
- A peça é PARA REVISÃO da equipe antes de protocolar - não marque como definitiva.

FORMATAÇÃO DA SAÍDA (CRÍTICO — será convertida automaticamente no timbrado):

1) PARÁGRAFOS
   - Separados por LINHA EM BRANCO.

2) TÍTULOS DE SEÇÃO
   - Linha INTEIRAMENTE EM MAIÚSCULAS, sozinha, sem pontuação no final.
   - SEM markdown (# ## ###).
   - Numeração romana ou árabe é permitida.
   ✅ CERTO:  "I. DOS FATOS"  |  "DO DIREITO"  |  "DOS PEDIDOS"  |  "OMISSÃO 1 — DA NULIDADE DOS CARTÕES DE PONTO"
   ❌ ERRADO: "I. Dos Fatos"  |  "## DOS FATOS"  |  "Omissão 1 — Nulidade dos cartões"

3) NEGRITO INLINE — APENAS PALAVRAS-CHAVE
   - Use **texto** SOMENTE em palavras curtas que precisam destaque (nomes de partes, números de processo, valores, prazos).
   - NUNCA coloque um parágrafo inteiro em negrito.
   ✅ CERTO:  "Conforme demonstrado, o **Reclamante** foi admitido em **05/07/2023**."
   ❌ ERRADO: "**Conforme demonstrado, o Reclamante foi admitido em 05/07/2023.**"

4) ITÁLICO INLINE
   - Use _texto_ para expressões em latim, nomes de obras, ênfase.
   ✅ CERTO:  "_in casu_, _data venia_, _in dubio pro operario_"

5) CITAÇÕES DE JURISPRUDÊNCIA, SÚMULAS, DOUTRINA E ARTIGOS DE LEI EM BLOCO
   - Quando for transcrever literalmente o texto de uma súmula, jurisprudência ou doutrina,
     coloque a transcrição em PARÁGRAFO PRÓPRIO iniciado com ASPAS DUPLAS.
   - O template aplicará automaticamente: recuo 4cm à esquerda + itálico.
   ✅ CERTO (em parágrafo separado):
     "Súmula 338, III, do TST: Os cartões de ponto que demonstram horários de entrada e saída uniformes
     são inválidos como meio de prova, invertendo-se o ônus da prova, relativo às horas extras, que
     passa a ser do empregador."
   ❌ ERRADO (citação misturada no corpo):
     "Os cartões de ponto juntados pela Reclamada apresentam, em diversos meses, marcação invariável
     de entrada às 07h00, atraindo a Súmula 338, III, do TST, que determina..."
     [a Súmula deveria estar em parágrafo PRÓPRIO com aspas no início]

6) LISTAS
   - NÃO use bullets - ou *. Use numeração manual (1., 2., 3.) OU texto corrido com "(i)", "(ii)", "(iii)".

7) REFERÊNCIAS A LEIS (curtas, no meio do texto)
   - Pode citar inline sem destaque: "nos termos do art. 818 da CLT"
   - Apenas se for transcrição literal longa, use o formato de citação em bloco (item 5).

CONTEÚDO:
- Comece direto pelo endereçamento (EXMO. SR. JUIZ...) ou título da peça.
- NÃO inclua preâmbulos do tipo "Aqui está a peça".
- NÃO inclua "formatação:", "padrão:", instruções meta - entregue APENAS a peça pronta.
- Use linguagem jurídica profissional, respeitando o estilo do POP.
"""


def _titulo_peca(tipo_tarefa: str, contexto: dict) -> str:
    """Monta titulo do arquivo."""
    tipo = (tipo_tarefa or 'PECA').upper().strip()
    cliente = contexto.get('cliente') or {}
    nome = cliente.get('name') or cliente.get('nome') or 'CLIENTE'
    processo = contexto.get('processo') or {}
    reclamada = processo.get('opposing_name') or processo.get('reclamada') or ''
    base = f'{tipo} - {nome}'
    if reclamada:
        base += f' X {reclamada}'
    return base[:120]


def executar(tipo_tarefa: str, instrucao: str, contexto: dict) -> dict:
    log.info(f'gerando peca: tipo="{tipo_tarefa}"')

    pop = contexto.get('pop') or {}
    pop_texto = pop.get('texto') or ''
    pop_nome = pop.get('nome') or '(nenhum POP localizado)'

    bloco_ctx = montar_bloco_contexto(contexto)

    user_prompt = f"""
TIPO DE PECA SOLICITADA: {tipo_tarefa}

INSTRUCAO DO SOLICITANTE:
{instrucao or '(sem instrucao adicional)'}

POP APLICAVEL: {pop_nome}

CONTEXTO COMPLETO DO CASO:
{bloco_ctx}

TAREFA:
Produza a peca juridica solicitada, seguindo rigorosamente o POP fornecido no system prompt.
Baseie-se nos fatos e provas presentes no contexto acima. Se algum dado essencial faltar,
use um placeholder claro como [FALTA: descricao].

Retorne APENAS o texto da peca, pronto para revisao da equipe.
""".strip()

    try:
        texto_peca = gerar_peca(
            system_prompt=SYSTEM_PROMPT,
            pop_texto=pop_texto,
            user_prompt=user_prompt,
            thinking=True,
        )
        # Safety net: corrige palavras comuns que o LLM esquece de acentuar
        texto_peca = corrigir_acentuacao(texto_peca)
    except Exception as e:
        log.exception(f'falha ao gerar peca: {e}')
        return {
            'sucesso': False,
            'titulo': 'FALHA AO GERAR PECA',
            'resumo': 'Nao foi possivel gerar a peca automaticamente.',
            'detalhes': str(e),
        }

    titulo = _titulo_peca(tipo_tarefa, contexto)

    pasta_destino = contexto.get('pasta_destino_doc')
    pasta_id = pasta_destino['id'] if pasta_destino else None
    pasta_nome = pasta_destino['name'] if pasta_destino else '(nao localizada)'
    if not pasta_id:
        return {
            'sucesso': False,
            'titulo': titulo,
            'resumo': (
                'Pasta do cliente nao localizada no Drive. '
                'Confira se o nome do cliente no ADVBOX bate com a pasta no Drive '
                '(RECLAMANTE/RECLAMADA/CIVEL/ASSESSORIA).'
            ),
            'detalhes': f'--- PECA GERADA (nao salva) ---\n{texto_peca[:8000]}',
        }

    imagens = contexto.get('imagens') or []
    try:
        arq = salvar_docx_no_drive(titulo, texto_peca, pasta_id, imagens=imagens)
    except Exception as e:
        log.exception(f'falha ao salvar no Drive: {e}')
        return {
            'sucesso': False,
            'titulo': titulo,
            'resumo': 'Peca gerada mas falhou ao salvar no Drive.',
            'detalhes': f'{e}\n\n--- PECA ---\n{texto_peca[:5000]}',
        }

    img_info = f'\nImagens anexadas: {len(imagens)}' if imagens else ''
    return {
        'sucesso': True,
        'titulo': titulo,
        'resumo': (
            f'Peca "{tipo_tarefa}" gerada automaticamente para revisao da equipe.\n'
            f'POP utilizado: {pop_nome}\n'
            f'Salva em: {pasta_nome}\n'
            f'Caracteres: {len(texto_peca)}{img_info}'
        ),
        'doc_link': arq['link'],
        'doc_nome': arq['nome'],
    }
