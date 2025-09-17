import os
import sys
import difflib
import importlib.util
from pathlib import Path

import pandas as pd
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ============================
# GROQ CLIENT CONFIGURATION
# ============================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"

# ============================
# UTILITY FUNCTIONS
# ============================

def read_csv_as_df(csv_path: str) -> pd.DataFrame:
    """
    Reads a CSV file into a pandas DataFrame, ensuring correct data types.
    Empty strings in numeric columns are treated as NaN.
    """
    df = pd.read_csv(csv_path)
    # Coerce numeric columns to handle potential non-numeric entries
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def run_generated_code(code: str, pdf_path: str, target: str) -> pd.DataFrame:
    """
    Dynamically executes the generated parser code and returns a DataFrame.
    The generated code must contain a `parse(pdf_path)` function.
    """
    # Use the 'target' variable to create a unique, dynamic module name
    parser_module_name = f"parser_for_{target}_{os.urandom(4).hex()}"
    
    temp_dir = Path("custom_parsers")
    temp_dir.mkdir(exist_ok=True)
    parser_file = temp_dir / f"{parser_module_name}.py"
    
    (temp_dir / "__init__.py").touch()

    parser_file.write_text(code, encoding="utf-8")

    try:
        spec = importlib.util.spec_from_file_location(f"custom_parsers.{parser_module_name}", parser_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"custom_parsers.{parser_module_name}"] = module
        spec.loader.exec_module(module)
        return module.parse(pdf_path)
    finally:
        # Clean up the temporary parser file after execution
        if parser_file.exists():
            parser_file.unlink()

def ask_groq_for_parser(target: str, pdf_path: str, csv_path: str) -> str:
    """
    Requests parser code from the Groq API using a detailed prompt.
    """
    expected_df = read_csv_as_df(csv_path)
    expected_head_str = expected_df.head(5).to_string()

    prompt = f"""
As a senior Python developer, your task is to create a script for extracting data from a PDF bank statement.
The script should output a clean pandas DataFrame.

Target Institution: {target}

The final script MUST be a Python module with a single function: parse(pdf_path: str) -> pd.DataFrame

Please adhere to these specifications:
1.  Use the `camelot-py` library with `flavor='stream'` for table extraction from the stream-based PDF.
2.  The PDF might span multiple pages. Ensure you process all pages and merge the tables into one DataFrame.
3.  The raw extracted tables may include headers or irrelevant data. Filter out any rows that aren't transactions. A reliable indicator of a transaction row is a valid date in the first column.
4.  The final DataFrame must have these exact columns in this sequence: ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
5.  Data Transformation Rules:
    - The 'Date' column should be formatted as a 'DD-MM-YYYY' string.
    - The 'Description' column might contain newlines (`\\n`); replace these with a single space.
    - 'Debit Amt', 'Credit Amt', and 'Balance' columns must be numeric (float). Use `pd.to_numeric` with `errors='coerce'` to handle non-numeric data, which will be converted to `NaN`. Do not fill `NaN` values.

For your reference, here are the first 5 rows of the target output DataFrame:
{expected_head_str}

Return nothing but the complete, raw Python code for the parser. Omit any explanations, markdown formatting, or introductory text.
    """

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert in Python code generation for data processing."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content

def run_test(target: str, pdf_path: str, csv_path: str, code: str) -> tuple[bool, str]:
    """Compares the generated DataFrame against the expected CSV to validate correctness."""
    if not code or not code.strip():
        return False, "The LLM returned an empty code block."
    
    try:
        # Pass 'target' to the function for dynamic module naming
        generated_df = run_generated_code(code, pdf_path, target)
    except Exception as e:
        return False, f"Code Execution Failed (Import/Runtime):\n{e}"

    expected_df = read_csv_as_df(csv_path)
    generated_df.reset_index(drop=True, inplace=True)
    expected_df.reset_index(drop=True, inplace=True)
    
    if list(generated_df.columns) != list(expected_df.columns):
        return False, f"Column mismatch.\nExpected: {expected_df.columns.to_list()}\nReceived: {generated_df.columns.to_list()}"

    # Use DataFrame.equals for a precise match as per the challenge requirements
    if generated_df.equals(expected_df):
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{target}_output.csv"
        generated_df.to_csv(output_path, index=False)
        
        success_msg = (
            f"✅ Success! Parser output matches the expected data.\n"
            f"   -> Verification file saved at: {output_path}"
        )
        return True, success_msg
    else:
        # Generate a diff to help debug mismatches
        diff = difflib.unified_diff(
            expected_df.to_string().splitlines(),
            generated_df.to_string().splitlines(),
            lineterm=""
        )
        error_details = "Data mismatch found. Debugging diff:\n" + "\n".join(list(diff)[:40])
        return False, error_details

def make_fallback_parser_code() -> str:
    """Provides a robust, deterministic fallback parser using Camelot."""
    return """
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
        df = df[df[0].str.match(r'\\d{2}-\\d{2}-\\d{4}', na=False)]
        df = df.iloc[:, :5]
        df.columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
        
    df['Description'] = df['Description'].str.replace('\\n', ' ', regex=False).str.strip()
    
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df.dropna(subset=['Date'], inplace=True)
    df = df[df['Date'].str.match(r'\\d{2}-\\d{2}-\\d{4}', na=False)].reset_index(drop=True)
    return df
"""

def save_parser_code(target: str, code: str):
    """Saves the generated code to a file in the custom_parsers directory."""
    if not code or not code.strip():
        print("❌ ERROR: Code is empty. Aborting save operation.")
        return

    output_dir = Path("custom_parsers")
    output_dir.mkdir(exist_ok=True)
    (output_dir / "__init__.py").touch()

    parser_path = output_dir / f"{target}_parser.py"

    # --- DEBUGGING PREVIEW ---
    print(f"\nSaving generated code to {parser_path}:")
    print("--- CODE PREVIEW (first 5 lines) ---")
    print('\n'.join(code.split('\n')[:5]))
    print("...")
    print("--- END PREVIEW ---\n")

    parser_path.write_text(code, encoding="utf-8")
    print(f"✅ Parser file saved successfully: {parser_path}")

# ============================
# MAIN EXECUTION BLOCK
# ============================

def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--target":
        print("Usage: python agent.py --target <bank_name>")
        sys.exit(1)

    target_bank = sys.argv[2]
    print(f"\nInitializing agent for target: {target_bank}\n")

    pdf_path = Path(f"data/{target_bank}/{target_bank}_sample.pdf")
    csv_path = Path(f"data/{target_bank}/{target_bank}_sample.csv")
    
    if not pdf_path.exists() or not csv_path.exists():
        print(f"Error: Required files not found. Check for '{pdf_path}' and '{csv_path}'.")
        sys.exit(1)

    max_retries = 3
    is_successful = False

    for attempt_num in range(1, max_retries + 1):
        print(f"--- ATTEMPT {attempt_num}/{max_retries} ---")
        try:
            generated_code = ask_groq_for_parser(target_bank, str(pdf_path), str(csv_path))
            if generated_code.strip().startswith("```python"):
                generated_code = generated_code.strip()[9:].strip("`").strip()

            is_ok, result_message = run_test(target_bank, str(pdf_path), str(csv_path), generated_code)
            
            if is_ok:
                print(result_message)
                save_parser_code(target_bank, generated_code)
                is_successful = True
                break
            else:
                print(f"Attempt {attempt_num} failed: {result_message}")
        except Exception as e:
            print(f"An unexpected error occurred during attempt {attempt_num}: {e}")

    if not is_successful:
        print("\nLLM attempts failed. Deploying deterministic fallback parser.")
        fallback_code = make_fallback_parser_code()
        is_ok, result_message = run_test(target_bank, str(pdf_path), str(csv_path), fallback_code)
        if is_ok:
            print(result_message)
            save_parser_code(target_bank, fallback_code)
        else:
            print(f"❌ Fallback parser failed to match the expected CSV. Details:\n{result_message}")

if __name__ == "__main__":
    main()