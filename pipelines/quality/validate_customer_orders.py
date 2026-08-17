from pathlib import Path
from datetime import datetime, timezone
import json
import sys

import pandas as pd
import great_expectations as gx


DEFAULT_DATA_PATH = Path("data/processed/customer_orders.csv")
INCIDENT_DIR = Path("incidents/historical")


def create_incident(data_path, expectation_name, result):
    INCIDENT_DIR.mkdir(parents=True, exist_ok=True)

    incident_id = datetime.now(timezone.utc).strftime(
        "INC-%Y%m%d-%H%M%S"
    )

    result_dict = result.to_json_dict()

    evidence = {
        "success": result.success,
        "unexpected_count": result_dict.get("result", {}).get(
            "unexpected_count"
        ),
        "unexpected_percent": result_dict.get("result", {}).get(
            "unexpected_percent"
        ),
        "partial_unexpected_list": result_dict.get("result", {}).get(
            "partial_unexpected_list",
            []
        ),
    }

    incident = {
        "incident_id": incident_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(data_path),
        "status": "OPEN",
        "severity": "HIGH",
        "category": "DATA_QUALITY",
        "failed_rule": expectation_name,
        "evidence": evidence,
    }

    output_path = INCIDENT_DIR / f"{incident_id}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(incident, file, indent=4)

    print(f"Incident created: {output_path}")

def main():
    data_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else DEFAULT_DATA_PATH
    )

    print(f"Validating dataset: {data_path}")

    dataframe = pd.read_csv(data_path)

    context = gx.get_context()

    data_source = context.data_sources.add_pandas(
        name="customer_orders_source"
    )

    data_asset = data_source.add_dataframe_asset(
        name="customer_orders"
    )

    batch_definition = data_asset.add_batch_definition_whole_dataframe(
        name="customer_orders_batch"
    )

    batch = batch_definition.get_batch(
        batch_parameters={"dataframe": dataframe}
    )

    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="order_id"
        ),
        gx.expectations.ExpectColumnValuesToBeUnique(
            column="order_id"
        ),
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="customer_id"
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="total_amount",
            min_value=0
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="order_status",
            value_set=[
                "COMPLETED",
                "PENDING",
                "CANCELLED",
            ],
        ),
    ]

    print("\nDataGuardian Data Quality Results")
    print("-" * 40)

    all_passed = True

    for expectation in expectations:
        result = batch.validate(expectation)

        expectation_name = expectation.__class__.__name__

        status = "PASS" if result.success else "FAIL"

        print(f"{status}: {expectation_name}")

        if not result.success:
            all_passed = False
            create_incident(
                data_path,
                expectation_name,
                result
            )

    print("-" * 40)

    if all_passed:
        print("Overall Status: PASS")
    else:
        print("Overall Status: FAIL")


if __name__ == "__main__":
    main()