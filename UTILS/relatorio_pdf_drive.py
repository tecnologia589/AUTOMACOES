# -*- coding: utf-8 -*-
"""
Pipeline reaproveitavel: HTML premium -> PDF -> Google Drive (link compartilhavel).

Usado por qualquer relatorio visual do escritorio
(roteiros de audiencia, analises de probabilidade, colas, pareceres).

Corbelino Advogados Associados.

Uso CLI:
    python UTILS/relatorio_pdf_drive.py "caminho/arquivo.html" --title "TITULO NO DRIVE"
    python UTILS/relatorio_pdf_drive.py "arquivo.html" --no-upload      # so gera o PDF
    python UTILS/relatorio_pdf_drive.py --selftest                       # roda todos os caminhos

Uso como modulo:
    from relatorio_pdf_drive import html_to_pdf, upload_pdf, update_pdf
"""
import os
import sys
import time
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'INTEGRACOES'))

TEMP = os.path.join(os.environ.get('TEMP', '/tmp'), 'mpd_relatorios')

CHROME_PATHS = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
]


def _find_browser():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    raise RuntimeError("Chrome/Edge nao encontrado para gerar PDF.")


def _file_url(path):
    """Converte caminho local em file:/// URL (com escape de espacos/acentos)."""
    from urllib.parse import quote
    abspath = os.path.abspath(path).replace('\\', '/')
    return 'file:///' + quote(abspath)


def html_to_pdf(html_path, pdf_path=None):
    """Renderiza um HTML em PDF via Chrome/Edge headless (preserva cores/fundos)."""
    import subprocess
    if not os.path.exists(html_path):
        raise FileNotFoundError(html_path)
    if pdf_path is None:
        pdf_path = os.path.splitext(html_path)[0] + '.pdf'
    os.makedirs(TEMP, exist_ok=True)
    profile = os.path.join(TEMP, f'profile_{int(time.time()*1000) % 100000}')
    browser = _find_browser()
    cmd = [
        browser, '--headless', '--disable-gpu',
        f'--user-data-dir={profile}',
        '--no-pdf-header-footer',
        f'--print-to-pdf={os.path.abspath(pdf_path)}',
        _file_url(html_path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    # Chrome as vezes demora a soltar o arquivo
    for _ in range(20):
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            break
        time.sleep(0.3)
    if not (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0):
        raise RuntimeError(f"Falha ao gerar PDF: {pdf_path}")
    return pdf_path


def _drive():
    from google_integration import autenticar_google
    drive_service, _docs = autenticar_google()
    return drive_service


def upload_pdf(pdf_path, title=None, parent_id=None, share=True):
    """Sobe um PDF no Drive e (opcional) compartilha por link. Retorna (file_id, link)."""
    from googleapiclient.http import MediaFileUpload
    drive = _drive()
    meta = {'name': title or os.path.basename(pdf_path)}
    if parent_id:
        meta['parents'] = [parent_id]
    media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=False)
    f = drive.files().create(body=meta, media_body=media,
                             fields='id, webViewLink').execute()
    if share:
        drive.permissions().create(
            fileId=f['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
    return f['id'], f.get('webViewLink')


def update_pdf(file_id, pdf_path):
    """Substitui o conteudo de um PDF existente no Drive (mantem o mesmo link)."""
    from googleapiclient.http import MediaFileUpload
    drive = _drive()
    media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=False)
    drive.files().update(fileId=file_id, media_body=media, fields='id').execute()
    return file_id


def gerar_e_subir(html_path, title=None, parent_id=None, share=True):
    """Atalho: HTML -> PDF -> Drive. Retorna dict com pdf, file_id, link."""
    pdf = html_to_pdf(html_path)
    fid, link = upload_pdf(pdf, title=title, parent_id=parent_id, share=share)
    return {'pdf': pdf, 'file_id': fid, 'link': link}


def _selftest():
    """Roda todos os caminhos: gera PDF de teste e valida auth do Drive (sem subir lixo)."""
    print('[selftest] 1/3 localizar navegador...')
    print('   navegador:', _find_browser())

    print('[selftest] 2/3 HTML -> PDF...')
    os.makedirs(TEMP, exist_ok=True)
    html = os.path.join(TEMP, '_selftest.html')
    with open(html, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><meta charset=utf-8>'
                 '<h1 style="font-family:sans-serif;color:#b8923f">CORBELINO_ADVOGADOS selftest</h1>'
                 '<p>Pipeline relatorio_pdf_drive OK.</p>')
    pdf = html_to_pdf(html)
    print('   PDF gerado:', pdf, f'({os.path.getsize(pdf)} bytes)')

    print('[selftest] 3/3 autenticacao Google Drive...')
    try:
        drive = _drive()
        about = drive.about().get(fields='user').execute()
        print('   Drive OK como:', about.get('user', {}).get('emailAddress', '???'))
    except Exception as e:
        print('   AVISO: Drive indisponivel:', e)
        return False
    finally:
        for p in (html, pdf):
            try:
                os.remove(p)
            except OSError:
                pass
    print('[selftest] TODOS OS CAMINHOS OK.')
    return True


def main():
    ap = argparse.ArgumentParser(description='HTML -> PDF -> Google Drive (CORBELINO_ADVOGADOS)')
    ap.add_argument('html', nargs='?', help='caminho do arquivo .html')
    ap.add_argument('--title', help='titulo no Drive')
    ap.add_argument('--parent', help='ID da pasta no Drive')
    ap.add_argument('--no-upload', action='store_true', help='gera so o PDF')
    ap.add_argument('--no-share', action='store_true', help='nao compartilhar por link')
    ap.add_argument('--update', help='ID de arquivo Drive para substituir (mantem link)')
    ap.add_argument('--selftest', action='store_true', help='roda todos os caminhos')
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if _selftest() else 1)

    if not args.html:
        ap.error('informe o arquivo .html ou use --selftest')

    pdf = html_to_pdf(args.html)
    print('PDF:', pdf)

    if args.no_upload:
        return
    if args.update:
        update_pdf(args.update, pdf)
        print('Atualizado no Drive (mesmo link):', args.update)
    else:
        fid, link = upload_pdf(pdf, title=args.title, parent_id=args.parent,
                               share=not args.no_share)
        print('LINK:', link)


if __name__ == '__main__':
    main()
