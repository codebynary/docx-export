from main import processar_pdf
import pandas as pd

pdf_path = "1126 - Ficha de Registro.pdf"
try:
    df = processar_pdf(pdf_path)
    print("Columns found:", df.columns.tolist())
    print("\nFirst 3 rows:")
    print(df[['ID']].head(3) if 'ID' in df.columns else df.head(3))
    print("\nFull Dataframe Shape:", df.shape)
    # Print first record details to check fields
    if not df.empty:
        print("\nFirst Record Details:")
        print(df.iloc[0].to_dict())
except Exception as e:
    print(f"Error: {e}")
