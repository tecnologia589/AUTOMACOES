import anthropic
import json
import os
import sys

def analisar_transcricao(texto_pdf: str, texto_documentos: str = "") -> dict:
    """
    Envia o texto extraido da reuniao para o Claude analisar em duas etapas:
    1. Analise tecnica completa (resumo_fatos)
    2. Questionario + dados pessoais
    """

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERRO: A variavel ANTHROPIC_API_KEY nao foi encontrada no ambiente (.env).")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # =============================================
    # CHAMADA 1: Analise tecnica completa
    # =============================================
    system_analise = '''Voce e uma advogada senior com 20 anos de experiencia pratica em direito processual, atuando no Corbelino Advogados Associados, sob a responsabilidade do Dr. Paulo Alexandre Soares Corbelino, inscrito na OAB/MT 33.267. Formam um time vitorioso e buscam sempre a solucao para o exito do cliente com embasamentos solidos e juridicos. Sao especialistas e realistas.

Voce e redatora criteriosa: sem prolixidade, escreve em terceira pessoa com o impeto de quem e detentor do direito. Sua redacao e coesa, profissional, atinente as regras processuais e faticas. Se refere as partes nao pelo nome, mas sim pelo polo que ocupa na acao (O Reclamante, a Requerida, O Recorrente, O Autor, a Re...). Nao emite opinioes vagas nem trabalha com achismo. Domina a CLT, CPC, CC, CDC, Constituicao Federal, LOAS e normas dos tribunais.

TAREFA: Voce vai receber a transcricao de uma reuniao inicial com um cliente. Retorne ESTRITAMENTE um objeto JSON valido com estas chaves:

1. "resumo_fatos": ANALISE TECNICA COMPLETA DO CASO, estruturada exatamente assim:

.Analise Tecnica do Caso

Informacoes Iniciais
Cliente: [nome do cliente]
Tipo de demanda: [area/natureza identificada: trabalhista, civel ou empresarial]
Tempo de relacao/contrato: [periodo extraido da transcricao, quando aplicavel]

Sintese dos Fatos
[Resumo cronologico dos fatos narrados pelo cliente, em linguagem juridica formal, em terceira pessoa, referindo-se as partes pelo polo processual. Liste as principais condicoes relatadas em topicos.]

Fundamentos Juridicos
[Analise juridica com base na legislacao aplicavel a area identificada (CLT, CF, CC, CDC, CPC e legislacao especial pertinente). Identifique artigos violados e teses aplicaveis.]

Principais Pedidos Possiveis na Inicial
[Liste todos os pedidos cabiveis com base nos fatos narrados]

Gestao de Riscos
Riscos: [liste os riscos do caso]
Pontos Fortes: [liste os pontos fortes]
Pior Cenario: [descreva]

Documentos Necessarios para Propor a Acao
[Liste os documentos que o cliente deve providenciar]

Perguntas ao Cliente (para reforco probatorio)
[Liste perguntas complementares para reforcar as provas]

Conclusao Tecnica
[Conclusao sobre viabilidade da acao e recomendacao de proximos passos]

2. "nome": nome completo do cliente
3. "tipo_acao": tipo da acao identificada
4. "qual_empresa": nome da empresa/parte reclamada ou requerida

Possiveis direitos/teses a validar com os fatos (quando aplicaveis ao caso trabalhista):
Horas extras e intervalos (intrajornada e interjornada)
Adicionais legais (insalubridade, periculosidade, noturno)
Verbas rescisorias e registro integral do contrato de trabalho
Descontos indevidos
Comissoes e salario por fora
Equiparacao salarial e desvio de funcao
Reconhecimento de vinculo empregaticio
Danos morais e descumprimentos normativos

IMPORTANTE: Na analise, NAO use hifens ou travessoes para listar itens. Use topicos com asterisco (*) ou numeracao.

============================================================
PADROES DE FORMATACAO DO ESCRITORIO (OBRIGATORIOS)
============================================================
- Fonte: Montserrat, corpo 11pt
- Alinhamento do corpo: JUSTIFICADO (sempre)
- Espacamento entre linhas: 1,5
- Recuo da primeira linha: 7 (a esquerda)
- Titulos de secao com numeral alfanumerico em negrito (I., II., III., 1., 2., A), B)): NEGRITO + JUSTIFICADO, NUNCA centralizados.
- So centralizar em pecas juridicas: enderecamento ao juizo, nome da acao, fecho (Nestes termos/pede deferimento), data e assinatura.

REGRAS:
1. Nao invente fatos. Voce nao trabalha com achismo.
2. Se identificar obice ao deferimento de algum direito, indique estrategia para contornar.
3. A analise deve ser COMPLETA e EXTENSA com TODAS as secoes listadas acima.

RETORNE APENAS O JSON. Nao inclua texto, introducoes ou blocos ```json markdown.'''

    print("Enviando transcricao para analise pela IA (Claude)...")
    print("  Etapa 1/2: Analise tecnica do caso...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=system_analise,
            messages=[{
                "role": "user",
                "content": f"Ola, de acordo com a transcricao da reuniao de fechamento, inicial, que encontra-se anexa, resuma os fatos narrados pelo cliente. Apos isso, favor, identificar quais direitos foram violados, elencando-os, organizadamente abaixo do relatorio resumido dos fatos, apontando qual o trecho da conversa que valida esses direitos, bem como, quais provas foram requeridas ao cliente, e quais provas o cliente sera capaz de nos apresentar tudo isso, pensando em melhorar nossas chances de exito e a qualidade do nosso trabalho que sera ofertado ao cliente.\n\n<transcricao>\n{texto_pdf}\n</transcricao>"
            }]
        )

        texto_resp1 = response.content[0].text.strip()
        if texto_resp1.startswith("```json"):
            texto_resp1 = texto_resp1[7:]
        if texto_resp1.startswith("```"):
            texto_resp1 = texto_resp1[3:]
        if texto_resp1.endswith("```"):
            texto_resp1 = texto_resp1[:-3]

        dados = json.loads(texto_resp1)

    except json.JSONDecodeError:
        print("ERRO DE IA: A IA nao retornou um formato JSON valido na etapa 1.")
        print("Resposta recebida:")
        print(texto_resp1)
        sys.exit(1)
    except Exception as e:
        print(f"ERRO DE CONEXAO TECNICA (etapa 1): {str(e)}")
        sys.exit(1)

    # =============================================
    # CHAMADA 2: Questionario + Dados pessoais
    # =============================================
    system_dados = '''Voce e um assistente juridico. Sua tarefa e extrair informacoes de uma transcricao de reuniao entre advogado e cliente, e de documentos pessoais anexos (CNH, RG, etc).

Retorne ESTRITAMENTE um objeto JSON valido com as chaves abaixo. Responda de forma CURTA e DIRETA (1 a 3 frases por campo). Se a informacao nao foi mencionada, NAO inclua a chave no JSON.

Chaves do questionario (extrair da transcricao, quando aplicaveis ao caso):
registrado, contrato_ativo, empresa, estrutura_empresa, data_admissao, data_rescisao, funcao, salario, local_trabalho, rotina_trabalho, jornada, semana_trabalho, controle_jornada, assinatura_ponto, intervalo_almoco, intervalo_interjornada, horas_extras, banco_horas, ferias, decimo_terceiro, fgts, verbas_rescisorias, vale_refeicao, vale_transporte, sindicato, comissao, adicionais, descontos, danos_morais, testemunhas_documentos

Chaves de dados pessoais (extrair dos documentos anexos como CNH, RG, comprovante de endereco):
cpf, nacionalidade, rg, endereco, bairro, cidade_estado, cep, estado_civil, profissao, email, telefone

RETORNE APENAS O JSON. Nao inclua texto, introducoes ou blocos ```json markdown.'''

    print("  Etapa 2/2: Extraindo questionario e dados pessoais...")

    try:
        msg_usuario = f"Extraia as informacoes da transcricao e documentos abaixo.\n\n<transcricao>\n{texto_pdf}\n</transcricao>"
        if texto_documentos:
            msg_usuario += f"\n\n<documentos_pessoais>\n{texto_documentos}\n</documentos_pessoais>"

        response2 = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_dados,
            messages=[{"role": "user", "content": msg_usuario}]
        )

        texto_resp2 = response2.content[0].text.strip()
        if texto_resp2.startswith("```json"):
            texto_resp2 = texto_resp2[7:]
        if texto_resp2.startswith("```"):
            texto_resp2 = texto_resp2[3:]
        if texto_resp2.endswith("```"):
            texto_resp2 = texto_resp2[:-3]

        dados_extras = json.loads(texto_resp2)

        # Campos pessoais: dados do cadastro/documento TEM PRIORIDADE sobre a transcricao
        # (transcricao pode trazer nome incompleto, CPF errado, etc.)
        campos_pessoais = {
            'nome', 'cpf', 'rg', 'nacionalidade', 'estado_civil', 'profissao',
            'telefone', 'email', 'endereco', 'bairro', 'cidade_estado', 'cep'
        }

        for chave, valor in dados_extras.items():
            if not valor:
                continue
            if chave in campos_pessoais:
                # Cadastro/documento sempre sobrescreve a transcricao
                dados[chave] = valor
            elif chave not in dados:
                # Demais campos: so adiciona se nao existir
                dados[chave] = valor

    except Exception as e:
        print(f"  Aviso: Nao foi possivel extrair dados extras: {str(e)}")
        # Nao e fatal - a analise principal ja foi feita

    return dados
