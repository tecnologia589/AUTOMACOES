"""
Conciliacao Extrato Bancario (PDF) x ADVBOX - Corbelino Advogados Associados
Cruza as SAIDAS de um extrato bancario em PDF com as DESPESAS lancadas no
ADVBOX no mesmo mes, por valor. Aponta:
  - saidas do banco sem lancamento no ADVBOX (precisam ser lancadas);
  - despesas no ADVBOX sem saida correspondente no banco;
  - despesas ADVBOX pendentes de baixa.

NAO contem nenhum dado hardcoded: o extrato vem de um PDF e as despesas vem
da API do ADVBOX do proprio escritorio.

Uso:
  py conciliar_c6_advbox.py 03/2026 --extrato "EXTRATO.pdf" --senha 123456
  py conciliar_c6_advbox.py 03/2026 --extrato "EXTRATO.pdf"   (PDF sem senha)
"""
import sys, io, os, re, argparse
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'INTEGRACOES'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

from advbox_integration import listar_transacoes


MESES_NOME = {
    '01': 'JANEIRO', '02': 'FEVEREIRO', '03': 'MARCO', '04': 'ABRIL',
    '05': 'MAIO', '06': 'JUNHO', '07': 'JULHO', '08': 'AGOSTO',
    '09': 'SETEMBRO', '10': 'OUTUBRO', '11': 'NOVEMBRO', '12': 'DEZEMBRO'
}


def extrair_saidas_pdf(pdf_path, senha=None):
    """
    Extrai as SAIDAS (valores negativos) de um extrato bancario em PDF.
    Suporta PDF protegido por senha. Retorna lista de (data, descricao, valor).
    """
    import pdfplumber

    temp_path = None
    caminho = pdf_path
    if senha:
        import pikepdf
        temp_path = pdf_path.replace('.pdf', '_aberto.pdf')
        pdf = pikepdf.open(pdf_path, password=senha)
        pdf.save(temp_path)
        pdf.close()
        caminho = temp_path

    saidas = []
    with pdfplumber.open(caminho) as plumber:
        for page in plumber.pages:
            text = page.extract_text() or ''
            for line in text.split('\n'):
                match = re.search(r'(\d{2}/\d{2})\s+\d{2}/\d{2}\s+(.+?)\s+(-?R\$\s*[\d.,]+)', line)
                if match:
                    data = match.group(1)
                    desc = match.group(2).strip()
                    valor_str = match.group(3).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                    valor = float(valor_str)
                    if valor < 0:
                        saidas.append((data, desc, abs(valor)))

    if temp_path:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return saidas


def baixar_despesas_advbox(competencia):
    """Baixa despesas do ADVBOX (por vencimento) na competencia MM/YYYY."""
    mes, ano = competencia.split('/')
    start_date = f'{ano}-{mes}-01'
    if int(mes) == 12:
        end_dt = datetime(int(ano) + 1, 1, 1) - timedelta(days=1)
    else:
        end_dt = datetime(int(ano), int(mes) + 1, 1) - timedelta(days=1)
    end_date = end_dt.strftime('%Y-%m-%d')

    trans = listar_transacoes({'date_due_start': start_date, 'date_due_end': end_date})
    despesas = []
    for t in trans:
        if t.get('entry_type') != 'expense':
            continue
        despesas.append((
            t.get('date_due', ''),
            t.get('category', '') or 'SEM CATEGORIA',
            t.get('description', '') or (t.get('name', '') or ''),
            float(t.get('amount', 0) or 0),
            'PAGO' if t.get('date_payment') else 'PENDENTE',
        ))
    return despesas


def conciliar(competencia, extrato_pdf, senha=None):
    mes, ano = competencia.split('/')
    nome_mes = MESES_NOME.get(mes, mes)

    print('=' * 90)
    print(f'  CONCILIACAO EXTRATO BANCARIO vs ADVBOX - {nome_mes}/{ano}')
    print('=' * 90)

    print('\n  Lendo saidas do extrato (PDF)...')
    banco_saidas = extrair_saidas_pdf(extrato_pdf, senha)
    print(f'  Saidas no extrato: {len(banco_saidas)}')

    print('  Baixando despesas do ADVBOX...')
    advbox_despesas = baixar_despesas_advbox(competencia)
    print(f'  Despesas no ADVBOX: {len(advbox_despesas)}')

    # MATCHING por valor
    used_advbox = set()
    conciliados = []
    nao_conciliados_banco = []

    for b_data, b_desc, b_valor in banco_saidas:
        found = False
        for i, (a_data, a_cat, a_desc, a_val, a_status) in enumerate(advbox_despesas):
            if i in used_advbox:
                continue
            if abs(b_valor - a_val) < 0.02:
                conciliados.append((b_data, b_desc, b_valor, a_desc, a_cat, a_status))
                used_advbox.add(i)
                found = True
                break
        if not found:
            nao_conciliados_banco.append((b_data, b_desc, b_valor))

    # RESULTADO
    print(f'\n  Conciliados: {len(conciliados)}/{len(banco_saidas)} saidas do extrato')
    print()
    print('-' * 90)
    print(f'  {"DATA":>6} | {"VALOR":>12} | {"BANCO":38} | {"ADVBOX":30} | ST')
    print('-' * 90)
    for b_data, b_desc, b_valor, a_desc, a_cat, a_status in conciliados:
        st = 'OK' if a_status == 'PAGO' else '!!'
        print(f'  {b_data:>6} | R$ {b_valor:>10,.2f} | {b_desc[:38]:38} | {a_desc[:30]:30} | {st}')

    # FALTAM NO ADVBOX
    print()
    print('=' * 90)
    print('  SAIDAS DO BANCO SEM LANCAMENTO NO ADVBOX')
    print('  (Precisam ser lancadas como despesa)')
    print('=' * 90)
    if nao_conciliados_banco:
        for b_data, b_desc, b_valor in nao_conciliados_banco:
            print(f'  {b_data} | R$ {b_valor:>10,.2f} | {b_desc}')
        total_faltante = sum(v for _, _, v in nao_conciliados_banco)
        print(f'\n  TOTAL FALTANTE NO ADVBOX: R$ {total_faltante:,.2f}')
    else:
        print('  Nenhuma - tudo lancado!')

    # DESPESAS ADVBOX SEM CORRESPONDENCIA NO BANCO
    nao_usados_advbox = [(i, advbox_despesas[i]) for i in range(len(advbox_despesas)) if i not in used_advbox]
    print()
    print('=' * 90)
    print('  DESPESAS NO ADVBOX SEM SAIDA NO BANCO')
    print('  (Lancadas no ADVBOX mas nao aparecem no extrato)')
    print('=' * 90)
    if nao_usados_advbox:
        for i, (a_data, a_cat, a_desc, a_val, a_status) in nao_usados_advbox:
            print(f'  {a_data} | R$ {a_val:>10,.2f} | {a_cat[:30]:30} | {a_desc[:40]:40} | {a_status}')
    else:
        print('  Nenhuma - tudo bateu!')

    # PENDENTES DE BAIXA
    pendentes = [(a_data, a_cat, a_desc, a_val)
                 for a_data, a_cat, a_desc, a_val, a_status in advbox_despesas
                 if a_status == 'PENDENTE']
    print()
    print('=' * 90)
    print('  DESPESAS ADVBOX PENDENTES DE BAIXA')
    print('  (Precisam marcar data de pagamento no ADVBOX)')
    print('=' * 90)
    if pendentes:
        for a_data, a_cat, a_desc, a_val in pendentes:
            print(f'  {a_data} | R$ {a_val:>10,.2f} | {a_cat[:30]:30} | {a_desc}')
        print(f'\n  TOTAL PENDENTE: R$ {sum(v for _, _, _, v in pendentes):,.2f}')

    # RESUMO
    print()
    print('=' * 90)
    print('  RESUMO FINAL')
    print('=' * 90)
    total_banco = sum(v for _, _, v in banco_saidas)
    total_advbox = sum(v for _, _, _, v, _ in advbox_despesas)
    print(f'  Total saidas banco:    R$ {total_banco:>12,.2f}')
    print(f'  Total despesas ADVBOX: R$ {total_advbox:>12,.2f}')
    print(f'  Diferenca:             R$ {total_banco - total_advbox:>12,.2f}')
    print()


def main():
    parser = argparse.ArgumentParser(description='Conciliacao Extrato Bancario (PDF) x ADVBOX')
    parser.add_argument('competencia', help='Competencia MM/YYYY (ex: 03/2026)')
    parser.add_argument('--extrato', required=True, help='Caminho do PDF do extrato bancario')
    parser.add_argument('--senha', default=None, help='Senha do PDF (se protegido)')
    args = parser.parse_args()
    conciliar(args.competencia, args.extrato, senha=args.senha)


if __name__ == '__main__':
    main()
