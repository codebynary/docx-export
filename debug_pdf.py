import pdfplumber

pdf_path = "1126 - Ficha de Registro.pdf"
try:
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) > 0:
            print("First page text snippet:")
            print(pdf.pages[0].extract_text()[:500])
        else:
            print("PDF has no pages.")
except Exception as e:
    print(f"Error reading PDF: {e}")
