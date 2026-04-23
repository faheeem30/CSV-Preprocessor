import os
import pandas as pd
from scripts.transform import should_be_positive


def check_data_quality(df):
    """
    Run a full data quality check on any DataFrame.
    Returns a detailed report string and a dict of issues.
    """
    total_rows = len(df)
    total_cols = len(df.columns)

    # ── Nulls ─────────────────────────────────────────────────────────────────
    null_counts = df.isnull().sum()
    total_nulls = int(null_counts.sum())
    cols_with_nulls = {col: int(count) for col, count in null_counts.items() if count > 0}
    all_null_cols = [col for col, count in null_counts.items() if count == total_rows]

    # ── Duplicates ────────────────────────────────────────────────────────────
    duplicates = int(df.duplicated().sum())

    # ── Numeric columns ───────────────────────────────────────────────────────
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # ── Invalid negatives (universal detection) ───────────────────────────────
    invalid_negative_counts = {}
    for col in numeric_cols:
        if should_be_positive(col, df[col]):
            n = int((df[col] <= 0).sum())
            if n > 0:
                invalid_negative_counts[col] = n

    # ── Build report ──────────────────────────────────────────────────────────
    report_lines = [
        "=" * 54,
        "          DATA QUALITY REPORT",
        "=" * 54,
        f"Total Rows              : {total_rows}",
        f"Total Columns           : {total_cols}",
        f"Total Nulls             : {total_nulls}",
        f"Duplicate Rows          : {duplicates}",
        f"All-Null Columns        : {len(all_null_cols)}",
        f"Cols with Invalid <=0   : {len(invalid_negative_counts)}",
        "",
        "── Null Counts by Column ──",
    ]

    if cols_with_nulls:
        for col, cnt in cols_with_nulls.items():
            pct = round(cnt / total_rows * 100, 1)
            tag = " [ALL NULL -> will be DROPPED]" if col in all_null_cols else f" ({pct}% -> fill with median)"
            report_lines.append(f"  {col}: {cnt}{tag}")
    else:
        report_lines.append("  None -- all columns complete!")

    report_lines += ["", "── Invalid Values (<= 0 in always-positive columns) ──"]
    if invalid_negative_counts:
        for col, cnt in invalid_negative_counts.items():
            report_lines.append(f"  {col}: {cnt} value(s) -> will replace with median")
    else:
        report_lines.append("  None found")

    report_lines += ["", "── Actions Planned ──"]
    if all_null_cols:
        report_lines.append(f"  DROP all-null columns : {', '.join(all_null_cols)}")
    partial = [c for c in cols_with_nulls if c not in all_null_cols]
    if partial:
        report_lines.append(f"  FILL NaN with median  : {', '.join(partial)}")
    if invalid_negative_counts:
        report_lines.append(f"  FIX invalid (<=0)     : {', '.join(invalid_negative_counts.keys())}")
    if duplicates > 0:
        report_lines.append(f"  REMOVE {duplicates} duplicate row(s)")
    report_lines.append("  FLAG outliers via IQR (rows kept)")
    report_lines.append("=" * 54)

    report = "\n".join(report_lines)

    os.makedirs("logs", exist_ok=True)
    with open("logs/data_quality_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    issues = {
        "total_nulls": total_nulls,
        "cols_with_nulls": cols_with_nulls,
        "all_null_cols": all_null_cols,
        "duplicates": duplicates,
        "invalid_negative_counts": invalid_negative_counts,
        "numeric_cols": numeric_cols,
    }

    return report, issues
