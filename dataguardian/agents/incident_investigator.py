from pathlib import Path
import json
import re
import sys

from ollama import chat

from investigation_schema import InvestigationResult


MODEL_NAME = "qwen3:8b"

INVESTIGATION_DIR = Path(
    "incidents/investigations"
)

RUNBOOK_DIR = Path(
    "incidents/runbooks"
)

HISTORICAL_INCIDENT_DIR = Path(
    "incidents/historical"
)


def load_incident(incident_path):
    path = Path(incident_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Incident file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def prepare_incident_context(incident):
    pipeline_run = incident["pipeline_run"]
    events = incident["events"]

    event_history = []

    for event in events:
        event_history.append(
            {
                "event_type": event["event_type"],
                "table_name": event["table_name"],
                "event_message": event["event_message"],
            }
        )

    return {
        "incident_id": incident["incident_id"],
        "severity": incident["severity"],
        "pipeline_name": pipeline_run["pipeline_name"],
        "run_id": pipeline_run["run_id"],
        "run_status": pipeline_run["run_status"],
        "source": pipeline_run["source_name"],
        "target": pipeline_run["target_name"],
        "rows_processed": pipeline_run["rows_processed"],
        "duration_seconds": pipeline_run["duration_seconds"],
        "error_message": pipeline_run["error_message"],
        "event_history": event_history,
    }


def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9_]+",
            text.lower(),
        )
    )


def build_query_from_context(context):
    parts = [
        context["pipeline_name"],
        context["error_message"] or "",
    ]

    for event in context["event_history"]:
        parts.append(
            event["event_type"]
        )

        if event["table_name"]:
            parts.append(
                event["table_name"]
            )

        parts.append(
            event["event_message"]
        )

    return " ".join(parts)


def retrieve_runbook(context):
    query = build_query_from_context(
        context
    )

    query_tokens = tokenize(
        query
    )

    best_runbook = None
    best_score = -1

    for runbook_path in RUNBOOK_DIR.glob("*.md"):
        content = runbook_path.read_text(
            encoding="utf-8"
        )

        runbook_tokens = tokenize(
            content
        )

        score = len(
            query_tokens & runbook_tokens
        )

        if score > best_score:
            best_score = score

            best_runbook = {
                "name": runbook_path.name,
                "score": score,
                "content": content,
            }

    if best_runbook is None:
        raise RuntimeError(
            "No runbooks were found."
        )

    return best_runbook


def retrieve_historical_incident(
    context,
    current_incident_path,
):
    query = build_query_from_context(
        context
    )

    query_tokens = tokenize(
        query
    )

    current_name = Path(
        current_incident_path
    ).name

    best_incident = None
    best_score = -1

    for incident_path in HISTORICAL_INCIDENT_DIR.glob("*.json"):
        if incident_path.name == current_name:
            continue

        try:
            with open(
                incident_path,
                "r",
                encoding="utf-8",
            ) as file:
                incident_data = json.load(
                    file
                )

        except json.JSONDecodeError:
            continue

        incident_text = json.dumps(
            incident_data,
            default=str,
        )

        incident_tokens = tokenize(
            incident_text
        )

        score = len(
            query_tokens & incident_tokens
        )

        if score > best_score:
            best_score = score

            best_incident = {
                "name": incident_path.name,
                "score": score,
                "data": incident_data,
            }

    return best_incident


def investigate_incident(
    context,
    runbook,
    historical_incident,
):
    system_prompt = """
You are DataGuardian AI, a senior data platform incident investigator.

You are given:
1. Current incident evidence.
2. A retrieved operational runbook.
3. A similar historical incident.

The current incident evidence is the source of truth.

The runbook and historical incident are supporting context only.

Return a structured investigation containing:
- root cause
- failure stage
- failed component
- operational impact
- strongest supporting evidence
- runbook used
- relevant guidance from the runbook
- historical incident used
- historical similarity score
- safest recommended action
- confidence level

Use one of these failure stages:
- SOURCE_EXTRACTION
- TRANSFORMATION
- DATA_QUALITY
- LOAD
- ORCHESTRATION
- UNKNOWN

Rules:
1. Do not invent facts.
2. Do not copy the historical incident's root cause unless current evidence supports it.
3. Treat historical resolution as precedent, not proof.
4. Clearly separate confirmed facts from possible causes.
5. rows_processed means rows successfully processed before failure.
6. TABLE_START without TABLE_EXTRACTED means failure occurred while handling that table.
7. PostgreSQL SELECT failures during ingestion normally map to SOURCE_EXTRACTION.
8. Recommended actions must be safe and specific.
9. Use HIGH confidence only when current incident evidence directly supports the conclusion.
10. Return only data matching the supplied JSON schema.
"""

    historical_text = (
        json.dumps(
            historical_incident["data"],
            indent=2,
        )
        if historical_incident
        else "No similar historical incident found."
    )

    user_prompt = (
        "CURRENT INCIDENT:\n\n"
        + json.dumps(
            context,
            indent=2,
        )
        + "\n\nRETRIEVED RUNBOOK:\n\n"
        + runbook["content"]
        + "\n\nRUNBOOK FILE:\n"
        + runbook["name"]
        + "\n\nSIMILAR HISTORICAL INCIDENT:\n\n"
        + historical_text
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
        format=InvestigationResult.model_json_schema(),
        options={
            "temperature": 0
        },
    )

    investigation = InvestigationResult.model_validate_json(
        response.message.content
    )

    investigation.runbook_used = runbook["name"]

    if historical_incident:
        investigation.historical_incident_used = (
            historical_incident["name"]
        )

        investigation.historical_similarity_score = (
            historical_incident["score"]
        )
    else:
        investigation.historical_incident_used = None
        investigation.historical_similarity_score = None

    return investigation


def save_investigation(
    investigation,
):
    INVESTIGATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        INVESTIGATION_DIR
        / f"{investigation.incident_id}_investigation.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            investigation.model_dump(),
            file,
            indent=4,
        )

    return output_path


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "dataguardian\\agents\\incident_investigator.py "
            "<incident_json>"
        )
        sys.exit(1)

    incident_path = sys.argv[1]

    try:
        incident = load_incident(
            incident_path
        )

        context = prepare_incident_context(
            incident
        )

        runbook = retrieve_runbook(
            context
        )

        historical_incident = retrieve_historical_incident(
            context,
            incident_path,
        )

        print(
            f"\nRetrieved runbook: "
            f"{runbook['name']}"
        )

        print(
            f"Runbook score: "
            f"{runbook['score']}"
        )

        if historical_incident:
            print(
                f"Similar historical incident: "
                f"{historical_incident['name']}"
            )

            print(
                f"Historical similarity score: "
                f"{historical_incident['score']}"
            )

        investigation = investigate_incident(
            context,
            runbook,
            historical_incident,
        )

        output_path = save_investigation(
            investigation
        )

        print(
            "\nDataGuardian AI Investigation"
        )
        print("=" * 45)

        print(
            investigation.model_dump_json(
                indent=4
            )
        )

        print(
            f"\nInvestigation saved to: "
            f"{output_path}"
        )

    except Exception as error:
        print(
            f"Investigation failed: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()