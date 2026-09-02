"""
Engine central para producao de pecas juridicas no padrao do escritorio.

Combina:
  1. Geracao de conteudo com Opus (DNA de escrita do escritorio) -> gerar_texto_peca()
  2. Aplicacao de formatacao fiel (escritorio_format) -> formatar_no_timbrado()
  3. Helper completo end-to-end -> produzir_peca()

O DNA de tom e as pecas-modelo do escritorio ficam em REFERENCIAS/:
  - DNA_TOM_ESCRITA.md  (regras de tom/estilo - o escritorio preenche)
  - 1-2 pecas-modelo PROPRIAS em .txt (o motor aprende o estilo a partir delas)

Usado por skills:
  - /peca-escritorio (gerar peca do zero)
  - /formatar-escritorio (so aplicar formatacao em texto existente)
"""
import os
import sys
import time
from pathlib import Path

# Importa o formatador irmao
sys.path.insert(0, str(Path(__file__).parent))
import escritorio_format as PF

import anthropic
from dotenv import load_dotenv

# Carrega .env do diretorio raiz do projeto
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / 'config' / '.env')

REFERENCIAS_DIR = Path(__file__).parent / 'REFERENCIAS'

# Assinatura padrao das pecas (configuravel no .env).
ESCRITORIO_ASSINATURA = os.getenv(
    'ESCRITORIO_ASSINATURA',
    'Dr. Paulo Alexandre Soares Corbelino - OAB/MT 33.267 - Cáceres/MT',
)
ESCRITORIO_NOME = os.getenv('ESCRITORIO_NOME', 'Corbelino Advogados Associados')

# Modelo usado para producao de pecas (regra do escritorio: Opus).
MODELO_PECA = os.getenv('LLM_MODEL_PECA', 'claude-opus-4-6')


# ============================================================
# CARREGADORES DE CONTEXTO (amostras + DNA)
# ============================================================

def carregar_dna_escritorio():
    """Retorna o documento de DNA de tom (md) - usado como instrucao para o Opus.
    O escritorio preenche REFERENCIAS/DNA_TOM_ESCRITA.md no onboarding."""
    path = REFERENCIAS_DIR / 'DNA_TOM_ESCRITA.md'
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8')


def carregar_amostras_escritorio(max_chars_cada=15000):
    """Carrega texto truncado das pecas-modelo PROPRIAS do escritorio (.txt em REFERENCIAS/).
    O escritorio deposita 1-2 pecas reais DELE ali para o motor aprender o estilo."""
    if not REFERENCIAS_DIR.exists():
        return []
    amostras = []
    for arq in sorted(REFERENCIAS_DIR.glob('*.txt')):
        try:
            texto = arq.read_text(encoding='utf-8')
        except Exception:
            continue
        if texto.strip():
            amostras.append((arq.stem, texto[:max_chars_cada]))
    return amostras


# ============================================================
# SYSTEM PROMPT PADRAO
# ============================================================

SYSTEM_PROMPT_ESCRITORIO = f"""Voce escreve pecas processuais COMO ADVOGADO(A) SENIOR do escritorio {ESCRITORIO_NOME}.

Sua missao: produzir pecas que pareçam AUTENTICAMENTE escritas pelo escritorio - aderentes
ao DNA de escrita e as pecas-modelo fornecidas como referencia (quando houver). Nao texto
neutro de IA, mas pecas com a personalidade, vocabulario e tom do escritorio.

REGRAS ABSOLUTAS:

1. TOM E ESTILO: siga rigorosamente o DNA de escrita do escritorio (bloco de regras) e as
   pecas-modelo de referencia fornecidas. Se nao houver DNA/amostras, use tom formal-classico,
   tecnico e assertivo.

2. PARTES: trate as partes de forma consistente com o contexto do caso (Reclamante/Autor,
   Reclamada/Re, Tribunal). Mantenha a nomenclatura usada ao longo de toda a peca.

3. NARRATIVA: nos fatos, descreva a rotina concreta e os elementos do caso. Embuta calculos
   aritmeticos no corpo do paragrafo quando pertinente. Valores monetarios em formato
   brasileiro (R$ XX.XXX,XX).

4. TESE SUBSIDIARIA quando cabivel: apresentar pedido sucessivo para a hipotese de o Juizo
   entender de forma diversa.

5. ESTRUTURA DOS TOPICOS DE MERITO:
   a) Narrativa factual em 1-2 paragrafos
   b) Citacao do dispositivo legal EM BLOCO (transcrito literal)
   c) 1-2 ementas de jurisprudencia EM BLOCO com identificacao completa (processo, relator,
      turma, data)
   d) Fechamento com o pedido + valor monetario

6. FORMATACAO DE SAIDA (para o escritorio_format engine):
   - Titulos principais: I., II., III. (linha em maiusculo - usa travessao longo "–")
   - Subtitulos: I.I., I.II., III.I., a), b), c)
   - NAO usar marcadores markdown (# / ## / ###) - usar I., I.I., a) direto
   - Citacoes de jurisprudencia/sumulas/lei: linha comecando com aspa "
   - **negrito** inline / _italico_ inline
   - Pedidos finais: cada pedido em paragrafo com letra: a), b), c), ..., aa), bb)

7. NAO inventar fatos novos. Usar SOMENTE o que consta no contexto fornecido. Se um dado
   essencial faltar, usar placeholder explicito [FALTA: descricao do dado].

Voce SEMPRE responde com a peca completa, da primeira linha (enderecamento) ate a assinatura
final do escritorio: "{ESCRITORIO_ASSINATURA}"."""


# ============================================================
# GERADORES
# ============================================================

def _chamar_opus_com_retry(client, messages, max_tokens=24000, tentativas=3, save_partial=None):
    """Streaming com retry em caso de erro de rede. Opcional: salva parcial em disco."""
    for tent in range(tentativas):
        try:
            chunks = []
            with client.messages.stream(
                model=MODELO_PECA,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT_ESCRITORIO,
                messages=messages,
            ) as stream:
                for t in stream.text_stream:
                    chunks.append(t)
                    if save_partial and len(chunks) % 50 == 0:
                        Path(save_partial).write_text(''.join(chunks), encoding='utf-8')
                final = stream.get_final_message()
            return ''.join(chunks), final.usage.input_tokens, final.usage.output_tokens, final.stop_reason
        except Exception as e:
            print(f'  Tentativa {tent+1} falhou: {type(e).__name__}: {e}')
            if tent < tentativas - 1:
                time.sleep(5 * (tent + 1))
    raise RuntimeError('Todas as tentativas de Opus falharam')


def gerar_texto_peca(
    dados_caso: str,
    tipo_peca: str = 'PETICAO INICIAL',
    *,
    esqueleto: str = '',
    jurisprudencia: str = '',
    incluir_amostras: bool = True,
    save_partial_path: str = None,
):
    """
    Gera texto bruto de uma peca aplicando o DNA do escritorio com Opus (streaming + retry).

    Args:
      dados_caso: descricao completa do caso (qualificacao das partes, fatos, contexto)
      tipo_peca: 'PETICAO INICIAL', 'CONTESTACAO', 'REPLICA', 'RECURSO ORDINARIO', etc.
      esqueleto: opcional - texto de outra peca/modelo a ser ADAPTADO (mantem estrutura e jurisprudencia)
      jurisprudencia: opcional - bloco de jurisprudencia verificada a incluir
      incluir_amostras: se True, anexa as pecas-modelo do escritorio como contexto de estilo
      save_partial_path: opcional - caminho para salvar saida parcial durante streaming

    Returns: texto bruto da peca (string)
    """
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), timeout=600.0)

    blocos_contexto = []
    if incluir_amostras:
        for i, (nome, texto) in enumerate(carregar_amostras_escritorio(max_chars_cada=14000), 1):
            blocos_contexto.append(
                f'==================== AMOSTRA {i}: PECA-MODELO DO ESCRITORIO ({nome}) ====================\n'
                f'{texto}\n'
                f'==================== FIM AMOSTRA {i} ===================='
            )

    dna = carregar_dna_escritorio()
    if dna:
        blocos_contexto.append(
            f'==================== DNA DA ESCRITA DO ESCRITORIO (regras) ====================\n'
            f'{dna}\n'
            f'==================== FIM DNA ===================='
        )

    if esqueleto:
        blocos_contexto.append(
            f'==================== ESQUELETO JURIDICO (manter pedidos e jurisprudencia) ====================\n'
            f'{esqueleto}\n'
            f'==================== FIM ESQUELETO ===================='
        )

    if jurisprudencia:
        blocos_contexto.append(
            f'==================== JURISPRUDENCIA VERIFICADA (usar essas ementas) ====================\n'
            f'{jurisprudencia}\n'
            f'==================== FIM JURISPRUDENCIA ===================='
        )

    user_prompt = f"""Elabore a {tipo_peca} COMPLETA aplicando integralmente o DNA do escritorio.

==================== DADOS DO CASO ====================
{dados_caso}
==================== FIM DADOS ====================

{chr(10).join(blocos_contexto)}

INICIE PELA QUALIFICACAO DAS PARTES E ESCREVA A PECA INTEIRA APLICANDO O ESTILO DO ESCRITORIO. Termine com '{ESCRITORIO_ASSINATURA}'."""

    print(f'Gerando {tipo_peca} com {MODELO_PECA} + DNA do escritorio...')
    peca, in_tk, out_tk, stop_reason = _chamar_opus_com_retry(
        client,
        messages=[{'role': 'user', 'content': user_prompt}],
        max_tokens=24000,
        save_partial=save_partial_path,
    )
    print(f'  geracao: {len(peca)} chars | in={in_tk} out={out_tk} stop={stop_reason}')

    if stop_reason == 'max_tokens':
        print('  atingiu max_tokens; continuando...')
        peca2, _, out2, _ = _chamar_opus_com_retry(
            client,
            messages=[
                {'role': 'user', 'content': user_prompt},
                {'role': 'assistant', 'content': peca},
                {'role': 'user', 'content': 'Continue exatamente de onde parou, sem repetir conteudo. Termine a peticao ate a assinatura final.'},
            ],
            max_tokens=14000,
            save_partial=save_partial_path,
        )
        peca += peca2
        print(f'  continuacao: {len(peca2)} chars | out={out2}')

    return peca


def formatar_no_timbrado(texto_peca: str, output_path: str | Path) -> Path:
    """
    Aplica formatacao do escritorio (Montserrat 11, recuo 7cm, citacoes 10pt italico,
    margens 3/1.6/3/3) no timbrado e salva como .docx.

    Limpa marcadores markdown (# / ## / ###) e <<CITACAO>>...<</CITACAO>>.
    """
    import re
    proc = []
    for linha in texto_peca.split('\n'):
        s = linha.rstrip()
        if s.startswith('<<CITACAO>>'):
            s = s.replace('<<CITACAO>>', '').strip()
            if s and not s.startswith('"'):
                s = '"' + s
            elif not s:
                continue
        if s.endswith('<</CITACAO>>'):
            s = s.replace('<</CITACAO>>', '').rstrip()
            if not s.endswith('"'):
                s = s + '"'
        s = re.sub(r'^#{1,6}\s+', '', s)
        proc.append(s)
    texto_limpo = '\n'.join(proc)
    return PF.gerar_peca_escritorio(texto_limpo, output_path)


def produzir_peca(
    dados_caso: str,
    output_path: str | Path,
    tipo_peca: str = 'PETICAO INICIAL',
    **kwargs,
) -> Path:
    """Helper end-to-end: gera texto com Opus + DNA + formata no timbrado."""
    texto = gerar_texto_peca(dados_caso, tipo_peca, **kwargs)
    return formatar_no_timbrado(texto, output_path)
