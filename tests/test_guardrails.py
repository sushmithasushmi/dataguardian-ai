from dataguardian.agents.evidence_validator import (
    validate_investigation,
)
from dataguardian.agents.remediation_policy import (
    evaluate_plan,
)


def test_evidence_validator_passes_supported_claims():
    incident = {
        "pipeline_run": {
            "pipeline_name": "postgres_raw_ingestion",
            "rows_processed": 15,
            "error_message": (
                "psycopg2.errors.UndefinedTable: "
                'relation "missing_table" does not exist'
            ),
        },
        "events": [
            {
                "event_type": "TABLE_START",
                "table_name": "missing_table",
                "event_message": (
                    "Started extracting table missing_table"
                ),
            },
            {
                "event_type": "PIPELINE_ERROR",
                "table_name": None,
                "event_message": (
                    'relation "missing_table" does not exist'
                ),
            },
        ],
    }

    investigation = {
        "incident_id": "PIPELINE-RUN-TEST",
        "failed_component": "missing_table",
        "failure_stage": "SOURCE_EXTRACTION",
        "impact_summary": (
            "Pipeline failed after processing 15 rows."
        ),
        "evidence": [
            (
                "PostgreSQL returned UndefinedTable "
                "for missing_table"
            )
        ],
    }

    result = validate_investigation(
        incident,
        investigation,
    )

    assert result["checks"][0]["status"] == "PASS"
    assert result["checks"][1]["status"] == "PASS"
    assert result["checks"][2]["status"] == "PASS"


def test_evidence_validator_warns_on_unsupported_evidence():
    incident = {
        "pipeline_run": {
            "pipeline_name": "postgres_raw_ingestion",
            "rows_processed": 15,
            "error_message": (
                'relation "missing_table" does not exist'
            ),
        },
        "events": [],
    }

    investigation = {
        "incident_id": "PIPELINE-RUN-TEST",
        "failed_component": "missing_table",
        "failure_stage": "SOURCE_EXTRACTION",
        "impact_summary": (
            "Pipeline failed after processing 15 rows."
        ),
        "evidence": [
            "The source database server ran out of memory."
        ],
    }

    result = validate_investigation(
        incident,
        investigation,
    )

    assert (
        result["evidence_validation"][0]["status"]
        == "WARNING"
    )

    assert result["validation_status"] == "WARNING"


def test_remediation_policy_blocks_configuration_change():
    plan = {
        "incident_id": "PIPELINE-RUN-TEST",
        "steps": [
            {
                "step_number": 1,
                "action": (
                    "Update ingestion configuration "
                    "to reference the correct table"
                ),
                "risk_level": "HIGH",
            }
        ],
    }

    result = evaluate_plan(
        plan
    )

    assert (
        result["policy_status"]
        == "HUMAN_APPROVAL_REQUIRED"
    )

    assert (
        result["automatic_execution_allowed"]
        is False
    )

    assert (
        result["blocked_step_count"]
        == 1
    )


def test_remediation_policy_allows_read_only_check():
    plan = {
        "incident_id": "PIPELINE-RUN-TEST",
        "steps": [
            {
                "step_number": 1,
                "action": (
                    "Verify table existence "
                    "using pg_catalog.pg_tables"
                ),
                "risk_level": "LOW",
            }
        ],
    }

    result = evaluate_plan(
        plan
    )

    assert (
        result["policy_status"]
        == "REVIEW_ALLOWED"
    )

    assert (
        result["blocked_step_count"]
        == 0
    )

    assert (
        result["automatic_execution_allowed"]
        is False
    )