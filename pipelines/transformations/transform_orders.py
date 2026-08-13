from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


def main():
    spark = (
        SparkSession.builder
        .appName("DataGuardian-Orders-Transformation")
        .master("local[*]")
        .getOrCreate()
    )

    customers = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(str(RAW_DATA_DIR / "customers.csv"))
    )

    orders = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(str(RAW_DATA_DIR / "orders.csv"))
    )

    customers_clean = (
        customers
        .withColumn("customer_id", col("customer_id").cast("int"))
        .withColumn("created_at", to_timestamp("created_at"))
    )

    orders_clean = (
        orders
        .withColumn("order_id", col("order_id").cast("int"))
        .withColumn("customer_id", col("customer_id").cast("int"))
        .withColumn("total_amount", col("total_amount").cast("double"))
        .withColumn("order_date", to_timestamp("order_date"))
    )

    customer_orders = (
        orders_clean.alias("o")
        .join(
            customers_clean.alias("c"),
            col("o.customer_id") == col("c.customer_id"),
            "left"
        )
        .select(
            col("o.order_id"),
            col("o.customer_id"),
            col("c.first_name"),
            col("c.last_name"),
            col("c.state"),
            col("o.order_date"),
            col("o.order_status"),
            col("o.total_amount")
        )
    )

    customer_orders.show(truncate=False)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DATA_DIR / "customer_orders.csv"

    customer_orders.toPandas().to_csv(
        output_path,
        index=False
    )

    print(f"Processed dataset written to: {output_path}")

    spark.stop()


if __name__ == "__main__":
    main()