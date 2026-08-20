from pathlib import Path
import json
import sys


VALIDATION_DIR = Path(
    "incidents/validations"
)


def load_json(path):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def flatten_incident_text(incident):
    pipeline_run = incident.get(
        "pipeline_run",
        {}
    )

    events = incident.get(
        "events",
        []
    )

    parts = [
        str(
            pipeline_run.get(
                "error_message",
                "",
            )
        ),
        str(
            pipeline_run.get(
                "rows_processed",
                "",
            )
        ),
        str(
            pipeline_run.get(
                "pipeline_name",
                "",
            )
        ),
    ]

    for event in events:
        parts.append(
            str(
                event.get(
                    "event_type",
                    "",
                )
            )
        )

        parts.append(
            str(
                event.get(
                    "table_name",
                    "",
                )
            )
        )

        parts.append(
            str(
                event.get(
                    "event_message",
                    "",
                )
            )
        )

    return " ".join(
        parts
    ).lower()


def validate_failed_component(
    investigation,
    incident_text,
):
    failed_component = investigation.get(
        "failed_component",
        ""
    )

    if not failed_component:
        return {
            "check": "failed_component",
            "status": "FAIL",
            "message": (
                "Investigation does not identify "
                "a failed component."
            ),
        }

    normalized_component = (
        failed_component
        .lower()
        .replace(
            "postgresql table extraction for",
            "",
        )
        .replace(
            "postgresql source table",
            "",
        )
        .replace(
            "'",
            "",
        )
        .strip()
    )

    if normalized_component in incident_text:
        return {
            "check": "failed_component",
            "status": "PASS",
            "message": (
                f"Failed component "
                f"'{normalized_component}' "
                f"is supported by incident evidence."
            ),
        }

    return {
        "check": "failed_component",
        "status": "WARNING",
        "message": (
            f"Failed component "
            f"'{failed_component}' "
            f"was not directly found in incident evidence."
        ),
    }


def validate_failure_stage(
    investigation,
    incident_text,
):
    failure_stage = investigation.get(
        "failure_stage",
        ""
    )

    if (
        failure_stage == "SOURCE_EXTRACTION"
        and (
            "select * from" in incident_text
            or "table_start" in incident_text
            or "undefinedtable" in incident_text
        )
    ):
        return {
            "check": "failure_stage",
            "status": "PASS",
            "message": (
                "SOURCE_EXTRACTION is supported "
                "by SQL extraction evidence."
            ),
        }

    return {
        "check": "failure_stage",
        "status": "WARNING",
        "message": (
            f"Failure stage '{failure_stage}' "
            f"could not be strongly verified."
        ),
    }


def validate_rows_processed(
    investigation,
    incident,
):
    pipeline_run = incident.get(
        "pipeline_run",
        {}
    )

    rows_processed = pipeline_run.get(
        "rows_processed"
    )

    impact_summary = investigation.get(
        "impact_summary",
        ""
    ).lower()

    if rows_processed is None:
        return {
            "check": "rows_processed",
            "status": "WARNING",
            "message": (
                "Incident does not contain a "
                "rows_processed value."
            ),
        }

    rows_text = str(
        rows_processed
    )

    if rows_text in impact_summary:
        return {
            "check": "rows_processed",
            "status": "PASS",
            "message": (
                f"Impact summary correctly references "
                f"{rows_processed} processed rows."
            ),
        }

    return {
        "check": "rows_processed",
        "status": "WARNING",
        "message": (
            f"Incident reports {rows_processed} "
            f"processed rows, but the impact summary "
            f"does not explicitly reference that value."
        ),
    }


def validate_evidence_items(
    investigation,
    incident_text,
):
    evidence_items = investigation.get(
        "evidence",
        []
    )

    results = []

    for evidence in evidence_items:
        words = [
            word.lower()
            for word in evidence.split()
            if len(word) >= 5
        ]

        meaningful_matches = [
            word
            for word in words
            if word in incident_text
        ]

        status = (
            "PASS"
            if meaningful_matches
            else "WARNING"
        )

        results.append(
            {
                "evidence": evidence,
                "status": status,
                "matching_terms": (
                    meaningful_matches[:5]
                ),
            }
        )

    return results


def calculate_overall_status(
    checks,
    evidence_checks,
):
    statuses = [
        item["status"]
        for item in checks
    ]

    statuses.extend(
        item["status"]
        for item in evidence_checks
    )

    if "FAIL" in statuses:
        return "FAIL"

    if "WARNING" in statuses:
        return "WARNING"

    return "PASS"


def validate_investigation(
    incident,
    investigation,
):
    incident_text = flatten_incident_text(
        incident
    )

    checks = [
        validate_failed_component(
            investigation,
            incident_text,
        ),
        validate_failure_stage(
            investigation,
            incident_text,
        ),
        validate_rows_processed(
            investigation,
            incident,
        ),
    ]

    evidence_checks = validate_evidence_items(
        investigation,
        incident_text,
    )

    overall_status = calculate_overall_status(
        checks,
        evidence_checks,
    )

    return {
        "incident_id": investigation.get(
            "incident_id"
        ),
        "validation_status": overall_status,
        "checks": checks,
        "evidence_validation": evidence_checks,
    }


def save_validation(result):
    VALIDATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        VALIDATION_DIR
        / f"{result['incident_id']}_validation.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=4,
        )

    return output_path


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python "
            "dataguardian\\agents\\evidence_validator.py "
            "<incident_json> <investigation_json>"
        )
        sys.exit(1)

    incident_path = sys.argv[1]
    investigation_path = sys.argv[2]

    try:
        incident = load_json(
            incident_path
        )

        investigation = load_json(
            investigation_path
        )

        result = validate_investigation(
            incident,
            investigation,
        )

        output_path = save_validation(
            result
        )

        print(
            "\nDataGuardian Evidence Validation"
        )
        print("=" * 45)

        print(
            json.dumps(
                result,
                indent=4,
            )
        )

        print(
            f"\nValidation saved to: "
            f"{output_path}"
        )

    except Exception as error:
        print(
            f"Evidence validation failed: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()