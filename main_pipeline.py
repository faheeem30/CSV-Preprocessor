import sys
from scripts.extract import extract_data
from scripts.data_quality import check_data_quality
from scripts.transform import transform_data
from scripts.load import load_data
from scripts.logger import get_logger

logger = get_logger()


def run_pipeline(
    filepath="data/sales_raw.csv",
    db_url="postgresql+psycopg2://postgres:password@localhost:5432/pipelinedb",
    table="cleaned_data",
    skip_db=False,
):
    """
    Run the full ETL data quality pipeline on any CSV file.

    Args:
        filepath : path to input CSV file
        db_url   : SQLAlchemy PostgreSQL connection URL
        table    : target table name in the database
        skip_db  : if True, skip database load step (useful for testing)

    Usage:
        python main_pipeline.py data/myfile.csv --skip-db
    """
    try:
        logger.info("=" * 54)
        logger.info("Pipeline started")

        # ── Extract ───────────────────────────────────────────────────────────
        df = extract_data(filepath)
        logger.info(f"Data extracted: {len(df)} rows, {len(df.columns)} columns")

        # ── Quality Check ─────────────────────────────────────────────────────
        report, issues = check_data_quality(df)
        logger.info("Data quality check completed")
        logger.info(f"  Nulls found        : {issues['total_nulls']}")
        logger.info(f"  Duplicates         : {issues['duplicates']}")
        logger.info(f"  All-null cols      : {issues['all_null_cols']}")
        logger.info(f"  Invalid negatives  : {sum(issues['invalid_negative_counts'].values())}")

        # ── Transform ─────────────────────────────────────────────────────────
        df_clean, stats = transform_data(df)
        logger.info("Data transformed successfully")
        logger.info(f"  Rows : {stats['original_rows']} -> {stats['cleaned_rows']}")
        logger.info(f"  Cols : {stats['original_cols']} -> {stats['remaining_cols']}")
        logger.info(f"  NaN filled         : {stats['null_filled']}")
        logger.info(f"  Duplicates removed : {stats['duplicates_removed']}")
        logger.info(f"  Negatives fixed    : {stats['total_negatives_fixed']}")

        # ── Load (optional) ───────────────────────────────────────────────────
        if not skip_db:
            load_data(df_clean, db_url=db_url, table=table)
            logger.info(f"Data loaded to PostgreSQL table '{table}'")
        else:
            logger.info("DB load skipped (skip_db=True)")

        logger.info("Pipeline completed successfully")
        logger.info("=" * 54)

        return df_clean, stats

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Usage: python main_pipeline.py [csv_path] [--skip-db]
    filepath = sys.argv[1] if len(sys.argv) > 1 else "data/sales_raw.csv"
    skip_db = "--skip-db" in sys.argv
    run_pipeline(filepath=filepath, skip_db=skip_db)
