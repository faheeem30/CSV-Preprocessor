from sqlalchemy import create_engine


def load_data(df, db_url="postgresql+psycopg2://postgres:password@localhost:5432/pipelinedb", table="cleaned_data"):
    """
    Load cleaned DataFrame into a PostgreSQL table.

    Args:
        df: pandas DataFrame to load
        db_url: SQLAlchemy database connection URL
        table: target table name (default: 'cleaned_data')
    """
    engine = create_engine(db_url)
    df.to_sql(table, engine, if_exists="replace", index=False)
    print(f"[load] Loaded {len(df)} rows into table '{table}' successfully")
