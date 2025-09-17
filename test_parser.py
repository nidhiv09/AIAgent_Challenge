import pandas as pd
from pathlib import Path

# Note: This test requires that the agent has been run first to generate the parser.
from custom_parsers.icici_parser import parse

def test_icici_parser_output():
    """
    Verifies that the agent-generated parser for ICICI Bank produces a DataFrame
    that is identical to the provided sample CSV file.
    """
    # Define paths for the source PDF and the ground-truth CSV
    source_pdf_path = Path("data/icici/icici_sample.pdf")
    ground_truth_csv_path = Path("data/icici/icici_sample.csv")

    # 1. Generate the DataFrame by calling the agent-created parser
    parsed_df = parse(str(source_pdf_path))

    # 2. Load the ground-truth DataFrame from the sample CSV
    ground_truth_df = pd.read_csv(ground_truth_csv_path)
    # Ensure numeric columns are consistently typed for accurate comparison
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        ground_truth_df[col] = pd.to_numeric(ground_truth_df[col], errors='coerce')

    # Standardize indices on both DataFrames before comparison to prevent index-related failures
    parsed_df.reset_index(drop=True, inplace=True)
    ground_truth_df.reset_index(drop=True, inplace=True)

    # 3. Assert that the parsed DataFrame is exactly equal to the ground-truth DataFrame.
    assert parsed_df.equals(ground_truth_df), \
        "Validation failed: The parsed DataFrame does not exactly match the expected CSV data."