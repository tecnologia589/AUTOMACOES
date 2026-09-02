import pdfplumber
import os
import sys

def extrair_texto_pdf(caminho_arquivo: str) -> str:
    """
    Extrai texto de um PDF. Primeiro tenta extracao de texto puro.
    Se o resultado for muito curto (ex: CNH, RG escaneados), usa OCR.
    """
    if not os.path.exists(caminho_arquivo):
        print(f"ERRO: Arquivo PDF nao encontrado no caminho fornecido: {caminho_arquivo}")
        sys.exit(1)

    texto_completo = []

    try:
        with pdfplumber.open(caminho_arquivo) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo.append(texto_pagina)

        conteudo_final = "\n\n".join(texto_completo)

        # Se o texto extraido for curto ou nao conter dados pessoais (CPF, RG),
        # provavelmente e um documento escaneado com imagem (CNH, RG, etc.)
        tem_dados_pessoais = any(termo in conteudo_final.upper() for termo in ['CPF', 'IDENTIDADE', 'HABILITACAO', 'NASCIMENTO'])
        if len(conteudo_final.strip()) < 500 or (not tem_dados_pessoais and len(conteudo_final.strip()) < 1000):
            conteudo_ocr = extrair_texto_ocr(caminho_arquivo)
            if conteudo_ocr and len(conteudo_ocr.strip()) > len(conteudo_final.strip()):
                return conteudo_ocr

        if not conteudo_final.strip():
            print("AVISO: Nenhum texto detectado no PDF. Tentando OCR...")
            return extrair_texto_ocr(caminho_arquivo)

        return conteudo_final

    except Exception as e:
        print(f"ERRO ao processar PDF: {str(e)}")
        sys.exit(1)


def extrair_texto_ocr(caminho_arquivo: str) -> str:
    """
    Usa OCR (Tesseract) para extrair texto de PDFs com imagens/escaneados.
    """
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
        import io

        # Caminho do executavel do Tesseract (ajuste conforme a maquina do cliente).
        tesseract_cmd = os.getenv("TESSERACT_CMD", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        doc = fitz.open(caminho_arquivo)
        texto_completo = []

        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes('png')))
            texto = pytesseract.image_to_string(img)
            if texto.strip():
                texto_completo.append(texto)

        doc.close()
        return "\n\n".join(texto_completo)

    except ImportError:
        print("AVISO: PyMuPDF ou pytesseract nao instalados. OCR indisponivel.")
        return ""
    except Exception as e:
        print(f"AVISO: Erro no OCR: {str(e)}")
        return ""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        texto = extrair_texto_pdf(sys.argv[1])
        print(texto[:500] + "\n\n... (truncado)")
    else:
        print("Ex: python pdf_extractor.py meupdf.pdf")
