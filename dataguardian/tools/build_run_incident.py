from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import json
import sys

from sqlalchemy import create_engine, text


DATABASE_URL = (
    "postgresql+psycopg2://"
    "dataguardian_user:dataguardian_password"
    "@localhost:5432/dataguardian"
)

INCIDENT_DIR = Path("incidents/historical")


def get_pipeline_run(engine, run_id):
    query = text(
        """
        SELECT
            run_id,
            pipeline_name,
            run_status,
            started_at,
            completed_at,
            source_name,
            target_name,
            rows_processed,
            duration_seconds,
            error_message
        FROM pipeline_runs
        WHERE run_id = :run_id
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {"run_id": run_id},
        ).mappings().first()

    return dict(row) if row else None


def get_pipeline_events(engine, run_id):
    query = text(
        """
        SELECT
            event_id,
            event_type,
            table_name,
            event_message,
            event_timestamp
        FROM pipeline_events
        WHERE run_id = :run_id
        ORDER BY event_id
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"run_id": run_id},
        ).mappings().all()

    return [dict(row) for row in rows]


def make_json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    return value


def convert_record(record):
    return {
        key: make_json_safe(value)
        for key, value in record.items()
    }


def build_incident(run_id, pipeline_run, events):
    safe_pipeline_run = convert_record(pipeline_run)

    safe_events = [
        convert_record(event)
        for event in events
    ]

    return {
        "incident_id": f"PIPELINE-RUN-{run_id}",
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "category": "PIPELINE_EXECUTION",
        "severity": (
            "HIGH"
            if pipeline_run["run_status"] == "FAILED"
            else "INFO"
        ),
        "status": (
            "OPEN"
            if pipeline_run["run_status"] == "FAILED"
            else "CLOSED"
        ),
        "pipeline_run": safe_pipeline_run,
        "events": safe_events,
    }


def save_incident(run_id, incident):
    INCIDENT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        INCIDENT_DIR
        / f"pipeline_run_{run_id}_incident.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            incident,
            file,
            indent=4,
        )

    return output_path


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "dataguardian\\tools\\build_run_incident.py "
            "<run_id>"
        )
        sys.exit(1)

    try:
        run_id = int(sys.argv[1])
    except ValueError:
        print("Run ID must be an integer.")
        sys.exit(1)

    engine = create_engine(DATABASE_URL)

    try:
        pipeline_run = get_pipeline_run(
            engine,
            run_id,
        )

        if not pipeline_run:
            print(
                f"Run ID {run_id} was not found."
            )
            sys.exit(1)

        events = get_pipeline_events(
            engine,
            run_id,
        )

        incident = build_incident(
            run_id,
            pipeline_run,
            events,
        )

        output_path = save_incident(
            run_id,
            incident,
        )

        print(
            f"Incident snapshot created: "
            f"{output_path}"
        )

        print(
            f"Run status: "
            f"{pipeline_run['run_status']}"
        )

        print(
            f"Events captured: {len(events)}"
        )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()