from pathlib import Path
import json
import re
import sys


INCIDENT_DIR = Path("incidents/historical")


def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9_]+",
            text.lower(),
        )
    )


def load_incidents():
    incidents = []

    for path in INCIDENT_DIR.glob("*.json"):
        try:
            with open(
                path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            incidents.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "data": data,
                }
            )

        except json.JSONDecodeError:
            continue

    return incidents


def incident_to_text(incident):
    return json.dumps(
        incident,
        default=str,
    )


def score_incident(
    query,
    incident,
):
    query_tokens = tokenize(query)

    incident_tokens = tokenize(
        incident_to_text(
            incident["data"]
        )
    )

    matching_tokens = (
        query_tokens
        & incident_tokens
    )

    return (
        len(matching_tokens),
        sorted(matching_tokens),
    )


def retrieve_similar_incident(
    query,
    exclude_file=None,
):
    incidents = load_incidents()

    results = []

    for incident in incidents:
        if (
            exclude_file
            and incident["name"] == exclude_file
        ):
            continue

        score, matches = score_incident(
            query,
            incident,
        )

        results.append(
            {
                "name": incident["name"],
                "path": incident["path"],
                "score": score,
                "matches": matches,
                "data": incident["data"],
            }
        )

    if not results:
        return None

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[0]


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python "
            "dataguardian\\rag\\historical_incident_retriever.py "
            "<search text>"
        )
        sys.exit(1)

    query = " ".join(
        sys.argv[1:]
    )

    result = retrieve_similar_incident(
        query
    )

    if result is None:
        print(
            "No historical incidents found."
        )
        sys.exit(0)

    print(
        "\nDataGuardian Historical Incident Retrieval"
    )
    print("=" * 45)

    print(
        f"Query: {query}"
    )

    print(
        f"Best historical incident: "
        f"{result['name']}"
    )

    print(
        f"Score: {result['score']}"
    )

    print(
        "Matching terms: "
        + ", ".join(
            result["matches"]
        )
    )


if __name__ == "__main__":
    main()