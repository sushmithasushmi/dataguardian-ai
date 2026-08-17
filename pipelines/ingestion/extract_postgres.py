from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text


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
PIPELINE_NAME = "postgres_raw_ingestion"


def create_pipeline_run(engine, started_at):
    query = text(
        """
        INSERT INTO pipeline_runs (
            pipeline_name,
            run_status,
            started_at,
            source_name,
            target_name,
            rows_processed
        )
        VALUES (
            :pipeline_name,
            :run_status,
            :started_at,
            :source_name,
            :target_name,
            :rows_processed
        )
        RETURNING run_id
        """
    )

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "pipeline_name": PIPELINE_NAME,
                "run_status": "RUNNING",
                "started_at": started_at,
                "source_name": "PostgreSQL",
                "target_name": "data/raw",
                "rows_processed": 0,
            },
        )

        return result.scalar_one()


def update_pipeline_run(
    engine,
    run_id,
    status,
    completed_at,
    rows_processed,
    duration_seconds,
    error_message=None,
):
    query = text(
        """
        UPDATE pipeline_runs
        SET
            run_status = :run_status,
            completed_at = :completed_at,
            rows_processed = :rows_processed,
            duration_seconds = :duration_seconds,
            error_message = :error_message
        WHERE run_id = :run_id
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "run_id": run_id,
                "run_status": status,
                "completed_at": completed_at,
                "rows_processed": rows_processed,
                "duration_seconds": duration_seconds,
                "error_message": error_message,
            },
        )


def log_pipeline_event(
    engine,
    run_id,
    event_type,
    event_message,
    table_name=None,
):
    query = text(
        """
        INSERT INTO pipeline_events (
            run_id,
            pipeline_name,
            event_type,
            event_message,
            table_name
        )
        VALUES (
            :run_id,
            :pipeline_name,
            :event_type,
            :event_message,
            :table_name
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "run_id": run_id,
                "pipeline_name": PIPELINE_NAME,
                "event_type": event_type,
                "event_message": event_message,
                "table_name": table_name,
            },
        )


def extract_table(engine, run_id, table_name):
    log_pipeline_event(
        engine,
        run_id=run_id,
        event_type="TABLE_START",
        event_message=f"Started extracting table {table_name}",
        table_name=table_name,
    )

    query = f"SELECT * FROM {table_name}"
    dataframe = pd.read_sql(query, engine)

    output_path = RAW_DATA_DIR / f"{table_name}.csv"
    dataframe.to_csv(output_path, index=False)

    log_pipeline_event(
        engine,
        run_id=run_id,
        event_type="TABLE_EXTRACTED",
        event_message=(
            f"Extracted {len(dataframe)} rows from {table_name}"
        ),
        table_name=table_name,
    )

    print(
        f"Extracted {table_name}: "
        f"{len(dataframe)} rows -> {output_path}"
    )

    return len(dataframe)


def main():
    started_at = datetime.now()
    total_rows = 0

    engine = create_engine(DATABASE_URL)

    run_id = create_pipeline_run(
        engine=engine,
        started_at=started_at,
    )

    try:
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

        log_pipeline_event(
            engine,
            run_id=run_id,
            event_type="PIPELINE_START",
            event_message="PostgreSQL raw ingestion started",
        )

        for table in TABLES:
            total_rows += extract_table(
                engine=engine,
                run_id=run_id,
                table_name=table,
            )

        completed_at = datetime.now()

        duration_seconds = (
            completed_at - started_at
        ).total_seconds()

        update_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="SUCCESS",
            completed_at=completed_at,
            rows_processed=total_rows,
            duration_seconds=duration_seconds,
        )

        log_pipeline_event(
            engine,
            run_id=run_id,
            event_type="PIPELINE_SUCCESS",
            event_message=(
                f"Pipeline completed successfully. "
                f"Rows processed: {total_rows}"
            ),
        )

        print(
            f"Raw data extraction completed successfully. "
            f"Run ID: {run_id}. "
            f"Total rows processed: {total_rows}. "
            f"Duration: {duration_seconds:.3f} seconds."
        )

    except Exception as error:
        completed_at = datetime.now()

        duration_seconds = (
            completed_at - started_at
        ).total_seconds()

        update_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="FAILED",
            completed_at=completed_at,
            rows_processed=total_rows,
            duration_seconds=duration_seconds,
            error_message=str(error),
        )

        log_pipeline_event(
            engine,
            run_id=run_id,
            event_type="PIPELINE_ERROR",
            event_message=str(error),
        )

        print(
            f"Pipeline failed. "
            f"Run ID: {run_id}. "
            f"Duration: {duration_seconds:.3f} seconds. "
            f"Error: {error}"
        )

        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()