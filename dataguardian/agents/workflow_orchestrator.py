from pathlib import Path
import subprocess
import sys


PYTHON = sys.executable


def run_command(command):
    print("\n" + "=" * 60)
    print("Running:")
    print(" ".join(command))
    print("=" * 60)

    result = subprocess.run(
        command,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}"
        )


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "dataguardian\\agents\\workflow_orchestrator.py "
            "<incident_json>"
        )
        sys.exit(1)

    incident_path = Path(
        sys.argv[1]
    )

    if not incident_path.exists():
        raise FileNotFoundError(
            f"Incident file not found: {incident_path}"
        )

    incident_stem = incident_path.stem

    if incident_stem.startswith(
        "pipeline_run_"
    ):
        run_number = (
            incident_stem
            .replace(
                "pipeline_run_",
                "",
            )
            .replace(
                "_incident",
                "",
            )
        )

        incident_id = (
            f"PIPELINE-RUN-{run_number}"
        )

    else:
        raise RuntimeError(
            "Unsupported incident filename format."
        )

    investigation_path = Path(
        "incidents/investigations"
    ) / f"{incident_id}_investigation.json"

    validation_path = Path(
        "incidents/validations"
    ) / f"{incident_id}_validation.json"

    validated_path = Path(
        "incidents/validated"
    ) / f"{incident_id}_validated.json"

    remediation_path = Path(
        "incidents/remediation_plans"
    ) / f"{incident_id}_remediation.json"

    policy_path = Path(
        "incidents/remediation_policy"
    ) / f"{incident_id}_policy.json"

    run_command(
        [
            PYTHON,
            "dataguardian/agents/incident_investigator.py",
            str(incident_path),
        ]
    )

    run_command(
        [
            PYTHON,
            "dataguardian/agents/evidence_validator.py",
            str(incident_path),
            str(investigation_path),
        ]
    )

    run_command(
        [
            PYTHON,
            "dataguardian/agents/validated_investigation_builder.py",
            str(investigation_path),
            str(validation_path),
        ]
    )

    run_command(
        [
            PYTHON,
            "dataguardian/agents/remediation_planner.py",
            str(validated_path),
        ]
    )

    run_command(
        [
            PYTHON,
            "dataguardian/agents/remediation_policy.py",
            str(remediation_path),
        ]
    )

    print("\n" + "=" * 60)
    print("DataGuardian Workflow Completed")
    print("=" * 60)

    print(
        f"Incident: {incident_path}"
    )

    print(
        f"Investigation: {investigation_path}"
    )

    print(
        f"Validation: {validation_path}"
    )

    print(
        f"Validated investigation: {validated_path}"
    )

    print(
        f"Remediation plan: {remediation_path}"
    )

    print(
        f"Policy result: {policy_path}"
    )


if __name__ == "__main__":
    main()