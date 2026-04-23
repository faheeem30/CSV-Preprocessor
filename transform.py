import pandas as pd


# ── Keywords that signal a column must always be positive ─────────────────────
ALWAYS_POSITIVE_KEYWORDS = [
    'price', 'cost', 'amount', 'revenue', 'sales', 'salary', 'wage',
    'fee', 'tax', 'income', 'profit', 'budget', 'spend', 'payment',
    'quantity', 'qty', 'count', 'total', 'units', 'volume', 'stock',
    'age', 'height', 'weight', 'distance', 'size', 'area', 'duration',
    'pm2', 'pm10', 'humidity', 'concentration', 'pressure', 'speed',
    'radiation', 'population', 'score', 'rating', 'rank', 'humidity',
    'benzene', 'toluene', 'ozone', 'sulfur', 'nitrogen', 'oxygen',
]


def should_be_positive(col_name, series):
    """
    Decide if a numeric column should only contain positive values.
    Uses two signals:
      1. Column name contains a known always-positive keyword
      2. 95%+ of existing non-null values are already positive
    Leaves negatives alone for: temperature, coordinates, profit/loss, deltas.
    """
    name = col_name.lower()

    # Signal 1: name-based detection
    if any(kw in name for kw in ALWAYS_POSITIVE_KEYWORDS):
        return True

    # Signal 2: distribution-based detection
    valid = series.dropna()
    if len(valid) == 0:
        return False
    pct_positive = (valid > 0).sum() / len(valid)
    if pct_positive >= 0.95:
        return True

    return False


def fix_invalid_negatives(df, numeric_cols):
    """
    For columns that should be positive, replace values <= 0 with the column
    median of valid (positive) rows. Works on any CSV — no hardcoded names.
    Returns updated df and a dict of fixes made.
    """
    fixes = {}

    for col in numeric_cols:
        if not should_be_positive(col, df[col]):
            continue

        invalid_mask = df[col] <= 0
        invalid_count = int(invalid_mask.sum())
        if invalid_count == 0:
            continue

        # Median of valid rows only
        median_val = df.loc[~invalid_mask, col].median()
        if pd.isna(median_val):
            continue

        df.loc[invalid_mask, col] = median_val
        fixes[col] = {
            'count': invalid_count,
            'median_used': round(float(median_val), 4),
        }

    return df, fixes


def transform_data(df):
    """
    Generic data transformation for any CSV file.

    Steps:
      1. Drop fully empty columns (all-null) — not meaningful data
      2. Parse timestamp/date columns
      3. Remove duplicate rows
      4. For numeric columns: fill NaN with column median (robust to outliers)
      5. Clip extreme outliers using IQR method (optional, only flags — no row deletion)

    Returns: (df_clean, stats dict)
    """
    original_count = len(df)
    original_cols = list(df.columns)

    # ── 1. Drop all-null columns ───────────────────────────────────────────────
    all_null_cols = [c for c in df.columns if df[c].isnull().all()]
    df = df.drop(columns=all_null_cols)
    print(f"[transform] Dropped {len(all_null_cols)} all-null columns: {all_null_cols}")

    # ── 2. Parse timestamp column if present ──────────────────────────────────
    timestamp_col = None
    for col in df.columns:
        if col.lower() in ("timestamp", "date", "datetime", "time"):
            try:
                df[col] = pd.to_datetime(df[col])
                timestamp_col = col
                print(f"[transform] Parsed '{col}' as datetime")
            except Exception:
                pass
            break

    # ── 3. Remove duplicate rows ───────────────────────────────────────────────
    before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before_dedup - len(df)
    print(f"[transform] Removed {duplicates_removed} duplicate rows")

    # ── 4. Fill NaN in numeric columns with median ────────────────────────────
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    null_counts_before = df[numeric_cols].isnull().sum().sum()
    fill_values = {}

    for col in numeric_cols:
        median_val = df[col].median()
        null_n = df[col].isnull().sum()
        if null_n > 0:
            df[col] = df[col].fillna(median_val)
            fill_values[col] = round(median_val, 4)

    null_filled = int(null_counts_before)
    print(f"[transform] Filled {null_filled} NaN values with column medians")

    # ── 5. Fix impossible negatives/zeros (universal) ─────────────────────────
    df, negative_fixes = fix_invalid_negatives(df, numeric_cols)
    total_negatives_fixed = sum(v['count'] for v in negative_fixes.values())
    if total_negatives_fixed:
        for col, info in negative_fixes.items():
            print(f"[transform] Fixed {info['count']} invalid (<=0) in '{col}' -> median {info['median_used']}")
    else:
        print("[transform] No invalid negatives found")

    # ── 6. Flag outliers (IQR), do NOT delete rows ────────────────────────────
    outlier_flags = {}
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        n_outliers = int(((df[col] < lower) | (df[col] > upper)).sum())
        if n_outliers > 0:
            outlier_flags[col] = n_outliers

    # ── Save cleaned file ──────────────────────────────────────────────────────
    output_path = "data/cleaned_output.csv"
    df.to_csv(output_path, index=False)
    print(f"[transform] Saved cleaned data to '{output_path}'")

    cleaned_count = len(df)

    stats = {
        "original_rows": original_count,
        "cleaned_rows": cleaned_count,
        "original_cols": len(original_cols),
        "remaining_cols": len(df.columns),
        "all_null_cols_dropped": all_null_cols,
        "duplicates_removed": duplicates_removed,
        "null_filled": null_filled,
        "fill_values": fill_values,
        "negative_fixes": negative_fixes,
        "total_negatives_fixed": total_negatives_fixed,
        "outlier_flags": outlier_flags,
        "timestamp_col": timestamp_col,
        "numeric_cols": numeric_cols,
    }

    return df, stats
