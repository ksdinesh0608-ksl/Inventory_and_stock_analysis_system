
import os
import sys
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = CURRENT_DIR

BASE_DIR = os.path.dirname(CURRENT_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Backend.db_connection import get_db_connection


def fetch_data(query):
    connection = get_db_connection()

    try:
        return pd.read_sql(query, connection)
    finally:
        connection.close()


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150, bbox_inches="tight")
    plt.close()


def low_stock_chart():
    query = """
        SELECT product_name, current_stock, reorder_level
        FROM current_stock_report
        WHERE current_stock < reorder_level
        ORDER BY current_stock ASC
    """

    df = fetch_data(query)

    plt.figure(figsize=(9, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No low-stock products",
                 ha="center", va="center")
        plt.axis("off")
    else:
        plt.bar(df["product_name"], df["current_stock"])
        plt.axhline(
            y=df["reorder_level"].mean(),
            linestyle="--",
            label="Average reorder level"
        )
        plt.xticks(rotation=35, ha="right")
        plt.ylabel("Available Stock")
        plt.title("Low Stock Products")
        plt.legend()

    save_chart("low_stock_products.png")


def fast_moving_chart():
    query = """
        SELECT
            p.product_name,
            SUM(st.quantity) AS total_sold
        FROM stock_transactions st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.transaction_type = 'STOCK_OUT'
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sold DESC
        LIMIT 10
    """

    df = fetch_data(query)

    plt.figure(figsize=(9, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No stock-out transactions",
                 ha="center", va="center")
        plt.axis("off")
    else:
        plt.bar(df["product_name"], df["total_sold"])
        plt.xticks(rotation=35, ha="right")
        plt.ylabel("Quantity Sold")
        plt.title("Top 10 Fast-Moving Products")

    save_chart("fast_moving_products.png")


def category_chart():
    query = """
        SELECT
            p.category,
            SUM(r.current_stock) AS total_stock
        FROM products p
        JOIN current_stock_report r
            ON p.product_id = r.product_id
        GROUP BY p.category
        ORDER BY total_stock DESC
    """

    df = fetch_data(query)

    plt.figure(figsize=(8, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No category data",
                 ha="center", va="center")
        plt.axis("off")
    else:
        plt.bar(df["category"].fillna("Uncategorized"),
                df["total_stock"])
        plt.xticks(rotation=35, ha="right")
        plt.ylabel("Total Stock")
        plt.title("Stock by Category")

    save_chart("stock_by_category.png")


def stock_movement_chart():
    query = """
        SELECT
            DATE(transaction_date) AS movement_date,
            SUM(
                CASE
                    WHEN transaction_type = 'STOCK_IN'
                    THEN quantity ELSE 0
                END
            ) AS stock_in,
            SUM(
                CASE
                    WHEN transaction_type = 'STOCK_OUT'
                    THEN quantity ELSE 0
                END
            ) AS stock_out
        FROM stock_transactions
        GROUP BY DATE(transaction_date)
        ORDER BY movement_date
    """

    df = fetch_data(query)

    plt.figure(figsize=(9, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No stock movement data",
                 ha="center", va="center")
        plt.axis("off")
    else:
        plt.plot(df["movement_date"], df["stock_in"],
                 marker="o", label="Stock In")
        plt.plot(df["movement_date"], df["stock_out"],
                 marker="o", label="Stock Out")
        plt.xlabel("Date")
        plt.ylabel("Quantity")
        plt.title("Stock Movement Over Time")
        plt.xticks(rotation=35, ha="right")
        plt.legend()

    save_chart("stock_movement_over_time.png")


def inventory_value_chart():
    query = """
        SELECT
            p.product_name,
            (r.current_stock * p.unit_cost) AS inventory_value
        FROM products p
        JOIN current_stock_report r
            ON p.product_id = r.product_id
        ORDER BY inventory_value DESC
        LIMIT 10
    """

    df = fetch_data(query)

    plt.figure(figsize=(9, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No inventory value data",
                 ha="center", va="center")
        plt.axis("off")
    else:
        plt.bar(df["product_name"], df["inventory_value"])
        plt.xticks(rotation=35, ha="right")
        plt.ylabel("Inventory Value")
        plt.title("Top 10 Products by Inventory Value")

    save_chart("inventory_value_by_product.png")


def generate_all_charts():
    low_stock_chart()
    fast_moving_chart()
    category_chart()
    stock_movement_chart()
    inventory_value_chart()


if __name__ == "__main__":
    generate_all_charts()
