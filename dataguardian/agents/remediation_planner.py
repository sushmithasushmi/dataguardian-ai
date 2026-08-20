from pathlib import Path
import json
import sys

from ollama import chat
from pydantic import BaseModel
from typing import List, Literal


MODEL_NAME = "qwen3:8b"

REMEDIATION_DIR = Path(
    "incidents/remediation_plans"
)


class RemediationStep(BaseModel):
    step_number: int
    action: str
    purpose: str
    risk_level: Literal[
        "LOW",
        "MEDIUM",
        "HIGH"
    ]


class RemediationPlan(BaseModel):
    incident_id: str
    remediation_summary: str
    steps: List[RemediationStep]
    requires_human_approval: bool
    safe_to_auto_execute: bool
    rollback_plan: str
    validation_after_fix: List[str]


def load_validated_investigation(
    path,
):
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Validated investigation not found: "
            f"{file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_remediation_plan(
    investigation,
):
    system_prompt = """
You are DataGuardian AI's remediation planner.

You receive a validated incident investigation.

Your job is to produce a SAFE remediation plan.

Rules:
1. Never perform an action.
2. Only propose actions.
3. Do not create, delete, rename, or alter source database tables automatically.
4. Do not modify production schemas automatically.
5. Do not fabricate missing evidence.
6. If safe_for_remediation is false, human approval must be required.
7. Prefer configuration validation and read-only checks before changes.
8. Every plan must include rollback and post-fix validation.
9. safe_to_auto_execute must remain false for schema/configuration-changing incidents.
10. Return only data matching the supplied JSON schema.
"""

    user_prompt = (
        "Create a remediation plan for this validated incident:\n\n"
        + json.dumps(
            investigation,
            indent=2,
        )
    )

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        format=RemediationPlan.model_json_schema(),
        options={
            "temperature": 0
        },
    )

    return RemediationPlan.model_validate_json(
        response.message.content
    )


def save_plan(
    plan,
):
    REMEDIATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        REMEDIATION_DIR
        / f"{plan.incident_id}_remediation.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            plan.model_dump(),
            file,
            indent=4,
        )

    return output_path


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "dataguardian\\agents\\remediation_planner.py "
            "<validated_investigation_json>"
        )
        sys.exit(1)

    investigation_path = sys.argv[1]

    try:
        investigation = (
            load_validated_investigation(
                investigation_path
            )
        )

        plan = build_remediation_plan(
            investigation
        )

        output_path = save_plan(
            plan
        )

        print(
            "\nDataGuardian Remediation Plan"
        )
        print("=" * 45)

        print(
            plan.model_dump_json(
                indent=4
            )
        )

        print(
            f"\nRemediation plan saved to: "
            f"{output_path}"
        )

    except Exception as error:
        print(
            f"Remediation planning failed: "
            f"{error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()