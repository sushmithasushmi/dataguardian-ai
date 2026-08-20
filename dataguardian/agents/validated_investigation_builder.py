from pathlib import Path
import json
import sys


OUTPUT_DIR = Path(
    "incidents/validated"
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


def build_validated_investigation(
    investigation,
    validation,
):
    evidence_status = {}

    for item in validation[
        "evidence_validation"
    ]:
        evidence_status[
            item["evidence"]
        ] = item["status"]

    validated_evidence = []

    rejected_evidence = []

    for evidence in investigation.get(
        "evidence",
        [],
    ):
        status = evidence_status.get(
            evidence,
            "WARNING",
        )

        if status == "PASS":
            validated_evidence.append(
                evidence
            )
        else:
            rejected_evidence.append(
                evidence
            )

    validation_status = validation[
        "validation_status"
    ]

    safe_for_remediation = (
        validation_status == "PASS"
    )

    return {
        "incident_id": investigation[
            "incident_id"
        ],
        "validation_status": validation_status,
        "safe_for_remediation": safe_for_remediation,
        "root_cause": investigation[
            "root_cause"
        ],
        "failure_stage": investigation[
            "failure_stage"
        ],
        "failed_component": investigation[
            "failed_component"
        ],
        "impact_summary": investigation[
            "impact_summary"
        ],
        "validated_evidence": validated_evidence,
        "rejected_evidence": rejected_evidence,
        "runbook_used": investigation.get(
            "runbook_used"
        ),
        "historical_incident_used": investigation.get(
            "historical_incident_used"
        ),
        "historical_similarity_score": investigation.get(
            "historical_similarity_score"
        ),
        "recommended_action": investigation[
            "recommended_action"
        ],
        "confidence": investigation[
            "confidence"
        ],
    }


def save_result(result):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / f"{result['incident_id']}_validated.json"
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
            "dataguardian\\agents\\validated_investigation_builder.py "
            "<investigation_json> <validation_json>"
        )
        sys.exit(1)

    investigation_path = sys.argv[1]
    validation_path = sys.argv[2]

    try:
        investigation = load_json(
            investigation_path
        )

        validation = load_json(
            validation_path
        )

        result = build_validated_investigation(
            investigation,
            validation,
        )

        output_path = save_result(
            result
        )

        print(
            "\nDataGuardian Validated Investigation"
        )
        print("=" * 45)

        print(
            json.dumps(
                result,
                indent=4,
            )
        )

        print(
            f"\nValidated investigation saved to: "
            f"{output_path}"
        )

    except Exception as error:
        print(
            f"Validated investigation build failed: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()