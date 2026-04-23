import pandas as pd

def extract_data(filepath="data/sales_raw.csv"):
    """
    Extract CSV data with robust NA handling.
    Treats 'NA', 'N/A', 'na', 'n/a', 'NaN', '--', '' as missing values.
    """
    NA_VALUES = ['NA', 'N/A', 'na', 'n/a', 'NaN', 'nan', '--', '-', 'null', 'NULL', 'None', '']

    df = pd.read_csv(filepath, na_values=NA_VALUES, keep_default_na=True)
    print(f"[extract] Loaded {len(df)} rows x {len(df.columns)} columns from '{filepath}'")
    return df
