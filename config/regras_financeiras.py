"""
Regras financeiras configuraveis - Corbelino Advogados Associados.

Este modulo concentra TODAS as regras de negocio financeiras que variam de
escritorio para escritorio. O codigo das automacoes (fechamento, conciliacao,
classificacao de extrato) le APENAS deste arquivo - nada de regra hardcoded.

>>> TODO (onboarding): o escritorio deve cadastrar aqui as proprias regras de
>>> comissao e exececoes. Os valores abaixo vem VAZIOS de proposito. Enquanto
>>> nao forem preenchidos, nenhuma comissao e calculada e nenhuma excecao se
>>> aplica - o pipeline roda de forma neutra/segura.

------------------------------------------------------------------------------
COMISSOES (estrutura, vazia por padrao)
------------------------------------------------------------------------------
Cada comissionado e identificado por uma CHAVE (codigo curto, ex.: 'COMISS_1')
que tambem e usada como SUFIXO opcional na descricao da cobranca no Asaas
(ex.: "Cobranca recebida ... CLIENTE _COMISS_1"). Estrutura de cada entrada:

    "COMISS_1": {
        "rotulo": "Nome do comissionado",      # como aparece nos relatorios
        "sufixos": ["_C1"],                      # sufixos na descricao Asaas -> esta comissao
        "percentual": 0.10,                       # fracao do faturamento (ex.: 0.10 = 10%)
        "advbox_customers_id": None,              # ID no ADVBOX p/ lancar a comissao
        "exclusoes": [],                          # clientes que NAO geram comissao p/ este
        "lista_fechada": [],                      # se preenchida, SO estes clientes geram comissao
    }

Exemplo (NAO ativo - apenas ilustrativo, deixe vazio ate o onboarding):

    COMISSOES = {
        "COMISS_1": {"rotulo": "Comissionado A", "sufixos": ["_A"],
                     "percentual": 0.10, "advbox_customers_id": None,
                     "exclusoes": [], "lista_fechada": []},
    }
"""

# Tabela de comissoes do escritorio. VAZIA por padrao (cadastrar no onboarding).
COMISSOES = {}

# Banco/centro de custo/categoria usados ao lancar comissoes no ADVBOX.
# Preencher no onboarding com os IDs do escritorio (None = nao lancar).
ADVBOX_FINANCEIRO = {
    "banco_principal": None,     # debit_account
    "centro_custo": None,        # cost_centers_id
    "categoria_comissao": None,  # categories_id
}

# Clientes que NAO contam como receita do escritorio (excluir do faturamento).
# VAZIA por padrao - o escritorio adiciona aqui os casos dele, se houver.
# TODO (onboarding): cadastrar nomes (MAIUSCULO) a excluir do faturamento.
EXCLUIR_FATURAMENTO = []

# Percentual de provisao/destino sobre o lucro liquido (ex.: reserva, doacao).
# 0 = desativado. O escritorio define se/quanto usar.
# TODO (onboarding): definir, se aplicavel.
PERCENTUAL_PROVISAO_LUCRO = 0.0
ROTULO_PROVISAO_LUCRO = "Provisao s/ lucro"

# Categorias do ADVBOX consideradas "distribuicao de lucros" (nao sao despesa
# operacional). Mantido configuravel - palavras-chave em MAIUSCULO.
# TODO (onboarding): ajustar conforme o plano de contas do escritorio.
CATEGORIAS_DISTRIBUICAO = ["DISTRIBUI"]

# Palavras-chave para agrupar despesas no relatorio de resultado (configuravel).
PALAVRAS_COMISSOES = ["PARCEIRO", "ASSOCIADO"]
PALAVRAS_TAXAS = ["TAXAS", "INSS", "SIMPLES", "IMPOSTOS"]
PALAVRAS_SAZONAIS = ["MARKETING", "BRANDING", "CURSOS", "PASSAGEN",
                     "HOSPEDAGEM", "SEGURO DE RESP", "EQUIPAMENTO", "DESPESAS COM"]


def classificar_comissao(descricao):
    """
    Classifica a cobranca em uma chave de comissao com base nos sufixos
    cadastrados em COMISSOES. Retorna a CHAVE da comissao ou None (escritorio).

    Como COMISSOES vem vazia por padrao, esta funcao retorna None ate o
    onboarding cadastrar as regras.
    """
    desc = str(descricao)
    parte = desc.split('fatura nr.')[-1] if 'fatura nr.' in desc else desc
    for chave, regra in COMISSOES.items():
        for suf in regra.get("sufixos", []):
            if suf and suf in parte:
                return chave
    return None


def comissionado_recebe(chave, nome_cliente):
    """
    Indica se o comissionado 'chave' deve receber comissao deste cliente,
    respeitando 'exclusoes' e 'lista_fechada' cadastradas no onboarding.
    """
    regra = COMISSOES.get(chave)
    if not regra:
        return False
    nome = (nome_cliente or "").upper()
    if any(ex.upper() in nome for ex in regra.get("exclusoes", [])):
        return False
    fechada = regra.get("lista_fechada") or []
    if fechada:
        return any(item.upper() in nome or nome in item.upper() for item in fechada)
    return True


def eh_distribuicao(categoria):
    """True se a categoria ADVBOX representa distribuicao de lucros."""
    cat = (categoria or "").upper()
    return any(p in cat for p in CATEGORIAS_DISTRIBUICAO)


def excluir_do_faturamento(nome):
    """True se o cliente nao deve contar como receita do escritorio."""
    n = (nome or "").upper()
    return any(ex.upper() in n for ex in EXCLUIR_FATURAMENTO)
