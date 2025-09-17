
import pandas as pd
import camelot

def parse(pdf_path: str) -> pd.DataFrame:
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    if not tables:
        raise ValueError("Could not find any tables in the PDF.")
    df = pd.concat([tbl.df for tbl in tables], ignore_index=True)
    
    header_idx = -1
    for i, row in df.iterrows():
        if 'Date' in str(row[0]) and 'Description' in str(row[1]):
            header_idx = i
            break
            
    if header_idx != -1:
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
        
    if df.shape[1] == 5:
        df.columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
    else:
        df = df[df[0].str.match(r'\d{2}-\d{2}-\d{4}', na=False)]
        df = df.iloc[:, :5]
        df.columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
        
    df['Description'] = df['Description'].str.replace('\n', ' ', regex=False).str.strip()
    
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df.dropna(subset=['Date'], inplace=True)
    df = df[df['Date'].str.match(r'\d{2}-\d{2}-\d{4}', na=False)].reset_index(drop=True)
    return df
