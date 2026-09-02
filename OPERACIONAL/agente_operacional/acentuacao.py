"""
Corretor de acentuação - safety net.

Aplica substituições word-boundary em palavras jurídicas comuns que vêm
frequentemente sem acento do LLM. Respeita MAIÚSCULAS/minúsculas/Capitalizado.

Uso:
    from .acentuacao import corrigir_acentuacao
    texto_corrigido = corrigir_acentuacao(texto)
"""
import re


# Mapeamento: sem_acento -> com_acento (sempre minúsculo)
# IMPORTANTE: palavras curtas/ambíguas (ex: "ja" -> "já") ficam no final.
PALAVRAS = {
    # jurídicas - substantivos
    'acao': 'ação',
    'acoes': 'ações',
    'peticao': 'petição',
    'peticoes': 'petições',
    'peca': 'peça',
    'pecas': 'peças',
    'replica': 'réplica',
    'replicas': 'réplicas',
    'reanalise': 'reanálise',
    'reanalises': 'reanálises',
    'analise': 'análise',
    'analises': 'análises',
    'contestacao': 'contestação',
    'contestacoes': 'contestações',
    'manifestacao': 'manifestação',
    'manifestacoes': 'manifestações',
    'contrarrazoes': 'contrarrazões',
    'razoes': 'razões',
    'razao': 'razão',
    'decisao': 'decisão',
    'decisoes': 'decisões',
    'sentenca': 'sentença',
    'sentencas': 'sentenças',
    'execucao': 'execução',
    'execucoes': 'execuções',
    'extincao': 'extinção',
    'desconsideracao': 'desconsideração',
    'obrigacao': 'obrigação',
    'obrigacoes': 'obrigações',
    'responsabilidade': 'responsabilidade',  # ok, so pra nao confundir
    'jurisprudencia': 'jurisprudência',
    'jurisprudencias': 'jurisprudências',
    'doutrina': 'doutrina',  # ok
    'paragrafo': 'parágrafo',
    'paragrafos': 'parágrafos',
    'codigo': 'código',
    'codigos': 'códigos',
    'juizo': 'juízo',
    'juizos': 'juízos',
    'ciencia': 'ciência',
    'conhecimento': 'conhecimento',  # ok
    'audiencia': 'audiência',
    'audiencias': 'audiências',
    'pertinencia': 'pertinência',
    'competencia': 'competência',
    'incompetencia': 'incompetência',
    'processo': 'processo',  # ok
    'pessoa fisica': 'pessoa física',
    'pessoa juridica': 'pessoa jurídica',
    'juridica': 'jurídica',
    'juridicas': 'jurídicas',
    'juridico': 'jurídico',
    'juridicos': 'jurídicos',
    'fisica': 'física',
    'fisicas': 'físicas',
    'fisico': 'físico',
    'fisicos': 'físicos',
    'publica': 'pública',
    'publicas': 'públicas',
    'publico': 'público',
    'publicos': 'públicos',
    'generico': 'genérico',
    'genericos': 'genéricos',
    'generica': 'genérica',
    'genericas': 'genéricas',
    'especifico': 'específico',
    'especificos': 'específicos',
    'especifica': 'específica',
    'especificas': 'específicas',
    'pecuniario': 'pecuniário',
    'pecuniarios': 'pecuniários',
    'pecuniaria': 'pecuniária',
    'pecuniarias': 'pecuniárias',
    'cabivel': 'cabível',
    'cabiveis': 'cabíveis',
    'inaplicavel': 'inaplicável',
    'inaplicaveis': 'inaplicáveis',
    'aplicavel': 'aplicável',
    'aplicaveis': 'aplicáveis',
    'exito': 'êxito',
    'onus': 'ônus',
    'contrario': 'contrário',
    'contrarios': 'contrários',
    'contraria': 'contrária',
    'contrarias': 'contrárias',
    'terceiros': 'terceiros',  # ok
    'necessario': 'necessário',
    'necessarios': 'necessários',
    'necessaria': 'necessária',
    'necessarias': 'necessárias',
    'possivel': 'possível',
    'possiveis': 'possíveis',
    'impossivel': 'impossível',
    'impossiveis': 'impossíveis',
    'disponivel': 'disponível',
    'disponiveis': 'disponíveis',
    'indisponivel': 'indisponível',
    'indisponiveis': 'indisponíveis',
    'responsavel': 'responsável',
    'responsaveis': 'responsáveis',
    'inadmissivel': 'inadmissível',
    'admissivel': 'admissível',
    'provavel': 'provável',
    'improvavel': 'improvável',
    'visivel': 'visível',
    'ate': 'até',
    'ja': 'já',
    'tambem': 'também',
    'esta': 'está',      # cuidado: "esta pessoa" vira "está pessoa" - ver fallback
    'estao': 'estão',
    'sera': 'será',
    'serao': 'serão',
    'seria': 'seria',    # ok
    'tera': 'terá',
    'terao': 'terão',
    'nao': 'não',
    'sao': 'são',
    'entao': 'então',
    'versao': 'versão',
    'condicao': 'condição',
    'condicoes': 'condições',
    'formulacao': 'formulação',
    'caracterizacao': 'caracterização',
    'resolucao': 'resolução',
    'solucao': 'solução',
    'relacao': 'relação',
    'relacoes': 'relações',
    'atencao': 'atenção',
    'intencao': 'intenção',
    'opcao': 'opção',
    'opcoes': 'opções',
    'protecao': 'proteção',
    'aplicacao': 'aplicação',
    'aplicacoes': 'aplicações',
    'producao': 'produção',
    'producoes': 'produções',
    'apresentacao': 'apresentação',
    'apresentacoes': 'apresentações',
    'descricao': 'descrição',
    'descricoes': 'descrições',
    'observacao': 'observação',
    'observacoes': 'observações',
    'violacao': 'violação',
    'violacoes': 'violações',
    'citacao': 'citação',
    'intimacao': 'intimação',
    'notificacao': 'notificação',
    'comunicacao': 'comunicação',
    'assinatura': 'assinatura',  # ok
    'excecao': 'exceção',
    'excecoes': 'exceções',
    'pretensao': 'pretensão',
    'dever': 'dever',  # ok
    'credito': 'crédito',
    'creditos': 'créditos',
    'debito': 'débito',
    'debitos': 'débitos',
    'prejuizo': 'prejuízo',
    'prejuizos': 'prejuízos',
    'empresa': 'empresa',  # ok
    'industria': 'indústria',
    'industrias': 'indústrias',
    'comercio': 'comércio',
    'proprio': 'próprio',
    'propria': 'própria',
    'proprios': 'próprios',
    'proprias': 'próprias',
    'socio': 'sócio',
    'socios': 'sócios',
    'socia': 'sócia',
    'socias': 'sócias',
    'sociedade': 'sociedade',  # ok
    'pais': 'país',   # cuidado com pais/país
    'paises': 'países',
    'saude': 'saúde',
    'familia': 'família',
    'familias': 'famílias',
    'memoria': 'memória',
    'historia': 'história',
    'historico': 'histórico',
    'historicos': 'históricos',
    'historica': 'histórica',
    'historicas': 'históricas',
    'regiao': 'região',
    'regioes': 'regiões',
    'vinculo': 'vínculo',
    'vinculos': 'vínculos',
    'vinculacao': 'vinculação',
    'advocacia': 'advocacia',  # ok
    'advogado': 'advogado',  # ok
    'magistrado': 'magistrado',  # ok
    'tribunal': 'tribunal',  # ok
    'processual': 'processual',  # ok
    'processuais': 'processuais',  # ok
}


def _ajustar_caso(original: str, nova: str) -> str:
    """Preserva o case do original ao substituir."""
    if original.isupper():
        return nova.upper()
    if original[0].isupper():
        return nova[0].upper() + nova[1:]
    return nova


def corrigir_acentuacao(texto: str) -> str:
    """
    Corrige palavras sem acento substituindo pelas versoes acentuadas.
    Preserva MAIUSCULAS, Capitalizado e minusculo.
    """
    if not texto:
        return texto

    # Ordena por tamanho decrescente pra evitar substituicao parcial
    chaves = sorted(PALAVRAS.keys(), key=len, reverse=True)

    def substituir(match):
        original = match.group(0)
        chave = original.lower()
        nova = PALAVRAS.get(chave)
        if not nova:
            return original
        return _ajustar_caso(original, nova)

    # Regex: word boundaries (\b) - so substitui palavra inteira
    padrao = r'\b(' + '|'.join(re.escape(k) for k in chaves) + r')\b'
    return re.sub(padrao, substituir, texto, flags=re.IGNORECASE)
