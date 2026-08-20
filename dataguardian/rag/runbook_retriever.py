from pathlib import Path
import re
import sys


RUNBOOK_DIR = Path("incidents/runbooks")


def load_runbooks():
    runbooks = []

    for path in RUNBOOK_DIR.glob("*.md"):
        content = path.read_text(
            encoding="utf-8"
        )

        runbooks.append(
            {
                "name": path.name,
                "path": str(path),
                "content": content,
            }
        )

    return runbooks


def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9_]+",
            text.lower(),
        )
    )


def score_runbook(query, runbook):
    query_tokens = tokenize(query)
    runbook_tokens = tokenize(
        runbook["content"]
    )

    matching_tokens = (
        query_tokens
        & runbook_tokens
    )

    score = len(matching_tokens)

    return score, sorted(
        matching_tokens
    )


def retrieve_runbook(query):
    runbooks = load_runbooks()

    if not runbooks:
        raise RuntimeError(
            "No runbooks were found."
        )

    results = []

    for runbook in runbooks:
        score, matches = score_runbook(
            query,
            runbook,
        )

        results.append(
            {
                "name": runbook["name"],
                "path": runbook["path"],
                "score": score,
                "matches": matches,
                "content": runbook["content"],
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[0]


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python "
            "dataguardian\\rag\\runbook_retriever.py "
            "<search text>"
        )
        sys.exit(1)

    query = " ".join(
        sys.argv[1:]
    )

    try:
        result = retrieve_runbook(
            query
        )

        print("\nDataGuardian Runbook Retrieval")
        print("=" * 45)

        print(
            f"Query: {query}"
        )

        print(
            f"Best runbook: "
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

    except Exception as error:
        print(
            f"Retrieval failed: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()