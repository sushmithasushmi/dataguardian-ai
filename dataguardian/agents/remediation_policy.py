from pathlib import Path
import json
import sys


POLICY_DIR = Path(
    "incidents/remediation_policy"
)


HIGH_RISK_TERMS = [
    "drop table",
    "delete table",
    "truncate",
    "alter table",
    "create table",
    "rename table",
    "update ingestion configuration",
    "modify schema",
    "change schema",
]


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


def evaluate_step(step):
    action = step.get(
        "action",
        ""
    )

    action_lower = action.lower()

    detected_terms = [
        term
        for term in HIGH_RISK_TERMS
        if term in action_lower
    ]

    model_risk = step.get(
        "risk_level",
        "UNKNOWN"
    )

    if detected_terms:
        return {
            "step_number": step.get(
                "step_number"
            ),
            "action": action,
            "policy_status": "BLOCKED",
            "reason": (
                "Action contains a potentially "
                "state-changing operation."
            ),
            "detected_terms": detected_terms,
        }

    if model_risk == "HIGH":
        return {
            "step_number": step.get(
                "step_number"
            ),
            "action": action,
            "policy_status": "BLOCKED",
            "reason": (
                "LLM classified this action "
                "as HIGH risk."
            ),
            "detected_terms": [],
        }

    return {
        "step_number": step.get(
            "step_number"
        ),
        "action": action,
        "policy_status": "ALLOWED_FOR_REVIEW",
        "reason": (
            "No prohibited state-changing "
            "operation detected."
        ),
        "detected_terms": [],
    }


def evaluate_plan(plan):
    step_results = []

    for step in plan.get(
        "steps",
        []
    ):
        step_results.append(
            evaluate_step(step)
        )

    blocked_steps = [
        item
        for item in step_results
        if item["policy_status"]
        == "BLOCKED"
    ]

    if blocked_steps:
        overall_status = (
            "HUMAN_APPROVAL_REQUIRED"
        )
    else:
        overall_status = (
            "REVIEW_ALLOWED"
        )

    return {
        "incident_id": plan.get(
            "incident_id"
        ),
        "policy_status": overall_status,
        "automatic_execution_allowed": False,
        "blocked_step_count": len(
            blocked_steps
        ),
        "step_evaluations": step_results,
    }


def save_policy_result(result):
    POLICY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        POLICY_DIR
        / f"{result['incident_id']}_policy.json"
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
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "dataguardian\\agents\\remediation_policy.py "
            "<remediation_plan_json>"
        )
        sys.exit(1)

    try:
        plan = load_json(
            sys.argv[1]
        )

        result = evaluate_plan(
            plan
        )

        output_path = save_policy_result(
            result
        )

        print(
            "\nDataGuardian Remediation Policy"
        )
        print("=" * 45)

        print(
            json.dumps(
                result,
                indent=4,
            )
        )

        print(
            f"\nPolicy result saved to: "
            f"{output_path}"
        )

    except Exception as error:
        print(
            f"Policy evaluation failed: "
            f"{error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()