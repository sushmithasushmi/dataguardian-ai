from pathlib import Path
import json
import subprocess
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="DataGuardian AI API",
    version="1.1.0",
    description=(
        "API for AI-powered data pipeline incident "
        "investigation and remediation planning."
    ),
)


PYTHON = sys.executable

INCIDENT_DIR = Path(
    "incidents/historical"
)

INVESTIGATION_DIR = Path(
    "incidents/investigations"
)

VALIDATION_DIR = Path(
    "incidents/validations"
)

VALIDATED_DIR = Path(
    "incidents/validated"
)

REMEDIATION_DIR = Path(
    "incidents/remediation_plans"
)

POLICY_DIR = Path(
    "incidents/remediation_policy"
)


class InvestigationRequest(BaseModel):
    run_id: int


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Expected artifact was not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


@app.get("/")
def root():
    return {
        "service": "DataGuardian AI",
        "version": "1.1.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/investigate")
def investigate(request: InvestigationRequest):
    run_id = request.run_id

    incident_id = (
        f"PIPELINE-RUN-{run_id}"
    )

    incident_path = (
        INCIDENT_DIR
        / f"pipeline_run_{run_id}_incident.json"
    )

    if not incident_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Incident for run_id "
                f"{run_id} was not found."
            ),
        )

    command = [
        PYTHON,
        "dataguardian/agents/workflow_orchestrator.py",
        str(incident_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "DataGuardian workflow failed."
                ),
                "stderr": result.stderr,
                "stdout": result.stdout,
            },
        )

    investigation_path = (
        INVESTIGATION_DIR
        / f"{incident_id}_investigation.json"
    )

    validation_path = (
        VALIDATION_DIR
        / f"{incident_id}_validation.json"
    )

    validated_path = (
        VALIDATED_DIR
        / f"{incident_id}_validated.json"
    )

    remediation_path = (
        REMEDIATION_DIR
        / f"{incident_id}_remediation.json"
    )

    policy_path = (
        POLICY_DIR
        / f"{incident_id}_policy.json"
    )

    try:
        investigation = load_json(
            investigation_path
        )

        validation = load_json(
            validation_path
        )

        validated = load_json(
            validated_path
        )

        remediation = load_json(
            remediation_path
        )

        policy = load_json(
            policy_path
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Workflow completed but artifacts "
                f"could not be loaded: {error}"
            ),
        )

    return {
        "status": "completed",
        "incident_id": incident_id,
        "investigation": {
            "root_cause": investigation.get(
                "root_cause"
            ),
            "failure_stage": investigation.get(
                "failure_stage"
            ),
            "failed_component": investigation.get(
                "failed_component"
            ),
            "impact_summary": investigation.get(
                "impact_summary"
            ),
            "confidence": investigation.get(
                "confidence"
            ),
            "runbook_used": investigation.get(
                "runbook_used"
            ),
            "historical_incident_used": (
                investigation.get(
                    "historical_incident_used"
                )
            ),
            "historical_similarity_score": (
                investigation.get(
                    "historical_similarity_score"
                )
            ),
        },
        "validation": {
            "status": validation.get(
                "validation_status"
            ),
            "safe_for_remediation": validated.get(
                "safe_for_remediation"
            ),
            "validated_evidence": validated.get(
                "validated_evidence",
                [],
            ),
            "rejected_evidence": validated.get(
                "rejected_evidence",
                [],
            ),
        },
        "remediation": {
            "summary": remediation.get(
                "remediation_summary"
            ),
            "steps": remediation.get(
                "steps",
                [],
            ),
            "requires_human_approval": (
                remediation.get(
                    "requires_human_approval"
                )
            ),
            "safe_to_auto_execute": (
                remediation.get(
                    "safe_to_auto_execute"
                )
            ),
            "rollback_plan": remediation.get(
                "rollback_plan"
            ),
            "validation_after_fix": (
                remediation.get(
                    "validation_after_fix",
                    [],
                )
            ),
        },
        "policy": {
            "status": policy.get(
                "policy_status"
            ),
            "automatic_execution_allowed": (
                policy.get(
                    "automatic_execution_allowed"
                )
            ),
            "blocked_step_count": policy.get(
                "blocked_step_count"
            ),
            "step_evaluations": policy.get(
                "step_evaluations",
                [],
            ),
        },
    }