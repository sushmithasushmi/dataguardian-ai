import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="DataGuardian AI",
    page_icon="🛡️",
    layout="wide",
)


st.title("🛡️ DataGuardian AI")

st.caption(
    "AI-powered data pipeline incident investigation, "
    "evidence validation, and safe remediation planning."
)


run_id = st.number_input(
    "Pipeline Run ID",
    min_value=1,
    value=11,
    step=1,
)


if st.button(
    "Investigate Incident",
    type="primary",
):
    with st.spinner(
        "Running DataGuardian investigation..."
    ):
        try:
            response = requests.post(
                f"{API_URL}/investigate",
                json={
                    "run_id": int(run_id)
                },
                timeout=600,
            )

            if response.status_code == 404:
                st.error(
                    f"No incident found for Run ID {run_id}."
                )

            elif response.status_code != 200:
                st.error(
                    "DataGuardian workflow failed."
                )

                st.code(
                    response.text
                )

            else:
                result = response.json()

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
                    f"Investigation completed for "
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
                    remediation[
                        "summary"
                    ]
                )

                for step in remediation[
                    "steps"
                ]:
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
                    remediation[
                        "rollback_plan"
                    ]
                )

                st.markdown(
                    "### Post-fix Validation"
                )

                for item in remediation[
                    "validation_after_fix"
                ]:
                    st.write(
                        f"• {item}"
                    )

                st.divider()

                st.subheader(
                    "Safety Policy"
                )

                if (
                    policy[
                        "automatic_execution_allowed"
                    ]
                ):
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

                if remediation[
                    "requires_human_approval"
                ]:
                    st.error(
                        "Human approval is required "
                        "before remediation."
                    )

                st.divider()

                st.caption(
                    "DataGuardian AI uses pipeline telemetry, "
                    "runbook retrieval, historical incident retrieval, "
                    "LLM analysis, deterministic evidence validation, "
                    "and remediation policy controls."
                )

        except requests.exceptions.ConnectionError:
            st.error(
                "Could not connect to the DataGuardian API. "
                "Make sure FastAPI is running on port 8000."
            )

        except requests.exceptions.Timeout:
            st.error(
                "The investigation timed out."
            )

        except Exception as error:
            st.error(
                f"Unexpected error: {error}"
            )