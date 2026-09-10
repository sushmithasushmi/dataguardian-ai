from pathlib import Path
import json

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"

INVESTIGATION_DIR = Path(
    "incidents/investigations"
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


st.set_page_config(
    page_title="DataGuardian AI",
    page_icon="🛡️",
    layout="wide",
)


def load_json(path):
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_demo_result(run_id):
    incident_id = f"PIPELINE-RUN-{run_id}"

    investigation_path = (
        INVESTIGATION_DIR
        / f"{incident_id}_investigation.json"
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

    for path in [
        investigation_path,
        validated_path,
        remediation_path,
        policy_path,
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Demo artifact not found: {path}"
            )

    investigation = load_json(
        investigation_path
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
            "status": validated.get(
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
        "remediation": remediation,
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


def run_live_result(run_id):
    response = requests.post(
        f"{API_URL}/investigate",
        json={
            "run_id": int(run_id)
        },
        timeout=600,
    )

    if response.status_code == 404:
        raise ValueError(
            f"No incident found for Run ID {run_id}."
        )

    if response.status_code != 200:
        raise RuntimeError(
            response.text
        )

    return response.json()


def render_result(result):
    investigation = result[
        "investigation"
    ]

    validation = result[
        "validation"
    ]

    remediation = result[
        "remediation"
    ]

    policy = result[
        "policy"
    ]

    st.success(
        f"Investigation loaded for "
        f"{result['incident_id']}"
    )

    st.divider()

    st.subheader(
        "Incident Investigation"
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:
        st.metric(
            "Failure Stage",
            investigation[
                "failure_stage"
            ],
        )

    with col2:
        st.metric(
            "Confidence",
            investigation[
                "confidence"
            ],
        )

    with col3:
        st.metric(
            "Validation",
            validation[
                "status"
            ],
        )

    st.markdown(
        "### Root Cause"
    )

    st.write(
        investigation[
            "root_cause"
        ]
    )

    st.markdown(
        "### Failed Component"
    )

    st.code(
        investigation[
            "failed_component"
        ]
    )

    st.markdown(
        "### Impact"
    )

    st.write(
        investigation[
            "impact_summary"
        ]
    )

    st.divider()

    st.subheader(
        "Grounding & Evidence"
    )

    st.markdown(
        "### Validated Evidence"
    )

    validated_evidence = (
        validation.get(
            "validated_evidence",
            [],
        )
    )

    if validated_evidence:
        for evidence in validated_evidence:
            st.write(
                f"✅ {evidence}"
            )
    else:
        st.info(
            "No validated evidence available."
        )

    rejected_evidence = (
        validation.get(
            "rejected_evidence",
            [],
        )
    )

    if rejected_evidence:
        st.markdown(
            "### Rejected Evidence"
        )

        for evidence in rejected_evidence:
            st.write(
                f"⚠️ {evidence}"
            )

    st.markdown(
        "### RAG Sources"
    )

    st.write(
        "**Runbook:** "
        f"{investigation['runbook_used']}"
    )

    st.write(
        "**Historical Incident:** "
        f"{investigation['historical_incident_used']}"
    )

    st.write(
        "**Similarity Score:** "
        f"{investigation['historical_similarity_score']}"
    )

    st.divider()

    st.subheader(
        "Remediation Plan"
    )

    st.write(
        remediation.get(
            "remediation_summary",
            remediation.get(
                "summary",
                "",
            ),
        )
    )

    for step in remediation.get(
        "steps",
        [],
    ):
        with st.expander(
            f"Step {step['step_number']} "
            f"— {step['risk_level']} Risk"
        ):
            st.write(
                f"**Action:** "
                f"{step['action']}"
            )

            st.write(
                f"**Purpose:** "
                f"{step['purpose']}"
            )

    st.markdown(
        "### Rollback Plan"
    )

    st.write(
        remediation.get(
            "rollback_plan",
            "",
        )
    )

    st.markdown(
        "### Post-fix Validation"
    )

    for item in remediation.get(
        "validation_after_fix",
        [],
    ):
        st.write(
            f"• {item}"
        )

    st.divider()

    st.subheader(
        "Safety Policy"
    )

    if policy[
        "automatic_execution_allowed"
    ]:
        st.success(
            "Automatic execution allowed."
        )
    else:
        st.warning(
            "Automatic execution is blocked."
        )

    st.write(
        "**Policy Status:** "
        f"{policy['status']}"
    )

    st.write(
        "**Blocked Steps:** "
        f"{policy['blocked_step_count']}"
    )

    requires_approval = remediation.get(
        "requires_human_approval",
        False,
    )

    if (
        requires_approval
        or policy["status"]
        == "HUMAN_APPROVAL_REQUIRED"
    ):
        st.error(
            "Human approval is required "
            "before remediation."
        )

    st.divider()

    st.caption(
        "DataGuardian AI combines pipeline telemetry, "
        "runbook retrieval, historical incident retrieval, "
        "LLM analysis, deterministic evidence validation, "
        "and remediation policy controls."
    )


st.title(
    "🛡️ DataGuardian AI"
)

st.caption(
    "AI-powered data pipeline incident investigation, "
    "evidence validation, and safe remediation planning."
)


mode = st.radio(
    "Choose Mode",
    [
        "Demo Mode",
        "Local Live Mode",
    ],
    horizontal=True,
)


if mode == "Demo Mode":
    st.info(
        "Demo Mode uses a pre-generated incident "
        "and committed investigation artifacts. "
        "No local Ollama or FastAPI server is required."
    )

    run_id = st.number_input(
        "Demo Pipeline Run ID",
        min_value=11,
        max_value=11,
        value=11,
        step=1,
    )

    button_label = (
        "Load Demo Investigation"
    )

else:
    st.info(
        "Local Live Mode runs the full AI workflow "
        "through the local FastAPI service and Ollama."
    )

    run_id = st.number_input(
        "Pipeline Run ID",
        min_value=1,
        value=11,
        step=1,
    )

    button_label = (
        "Investigate Incident"
    )


if st.button(
    button_label,
    type="primary",
):
    try:
        if mode == "Demo Mode":
            with st.spinner(
                "Loading demo investigation..."
            ):
                result = load_demo_result(
                    int(run_id)
                )

        else:
            with st.spinner(
                "Running live DataGuardian investigation..."
            ):
                result = run_live_result(
                    int(run_id)
                )

        render_result(
            result
        )

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to the DataGuardian API. "
            "Start FastAPI locally before using Local Live Mode."
        )

    except requests.exceptions.Timeout:
        st.error(
            "The live investigation timed out."
        )

    except Exception as error:
        st.error(
            f"Unable to load investigation: {error}"
        )