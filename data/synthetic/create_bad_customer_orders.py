from pathlib import Path

import pandas as pd


SOURCE_PATH = Path("data/processed/customer_orders.csv")
OUTPUT_PATH = Path("data/synthetic/customer_orders_bad.csv")


def main():
    dataframe = pd.read_csv(SOURCE_PATH)

    # Simulate a production data-quality issue:
    # an order arrives with an impossible negative amount.
    dataframe.loc[0, "total_amount"] = -89.99

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUTPUT_PATH, index=False)

    print(f"Bad test dataset created: {OUTPUT_PATH}")
    print(f"Injected invalid total_amount: {dataframe.loc[0, 'total_amount']}")


if __name__ == "__main__":
    main()