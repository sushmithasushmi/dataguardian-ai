from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


DATABASE_URL = (
    "postgresql+psycopg2://"
    "dataguardian_user:dataguardian_password"
    "@localhost:5432/dataguardian"
)

TABLES = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
]

RAW_DATA_DIR = Path("data/raw")


def extract_table(engine, table_name):
    query = f"SELECT * FROM {table_name}"
    dataframe = pd.read_sql(query, engine)

    output_path = RAW_DATA_DIR / f"{table_name}.csv"
    dataframe.to_csv(output_path, index=False)

    print(f"Extracted {table_name}: {len(dataframe)} rows -> {output_path}")


def main():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    engine = create_engine(DATABASE_URL)

    for table in TABLES:
        extract_table(engine, table)

    engine.dispose()

    print("Raw data extraction completed successfully.")


if __name__ == "__main__":
    main()