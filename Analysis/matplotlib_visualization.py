
import os
import sys
import traceback

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Backend.db_connection import get_db_connection

OUTPUT_DIR = CURRENT_DIR

CHART_FILES = [
    "low_stock_products.png",
    "fast_moving_products.png",
    "stock_by_category.png",
    "stock_movement_over_time.png",
    "inventory_value_by_product.png"
]


def fetch_data(query):
    connection = None

    try:
        connection = get_db_connection()
        return pd.read_sql_query(query, connection)
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


def save_chart(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)

    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)

    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise RuntimeError(
            f"Chart file was not created correctly: {filename}"
        )


def show_empty(ax, message):
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        transform=ax.transAxes
    )
    ax.set_axis_off()


def low_stock_chart():
    query = """
        SELECT
            product_name,
            current_stock,
            reorder_level
        FROM current_stock_report
        WHERE current_stock < reorder_level
        ORDER BY current_stock ASC
    """

    df = fetch_data(query)
    fig, ax = plt.subplots(figsize=(9, 5))

    if df.empty:
        show_empty(ax, "No low-stock products")
    else:
        ax.bar(
            df["product_name"],
            df["current_stock"],
            label="Current Stock"
        )

        ax.plot(
            df["product_name"],
            df["reorder_level"],
            marker="o",
            linestyle="--",
            label="Reorder Level"
        )

        ax.set_title("Low Stock Products")
        ax.set_ylabel("Quantity")
        ax.tick_params(axis="x", labelrotation=35)
        ax.legend()

    save_chart(fig, "low_stock_products.png")


def fast_moving_chart():
    query = """
        SELECT
            p.product_name,
            SUM(st.quantity) AS total_sold
        FROM stock_transactions st
        JOIN products p
            ON st.product_id = p.product_id
        WHERE st.transaction_type = 'STOCK_OUT'
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sold DESC
        LIMIT 10
    """

    df = fetch_data(query)
    fig, ax = plt.subplots(figsize=(9, 5))

    if df.empty:
        show_empty(ax, "No stock-out transactions")
    else:
        ax.bar(
            df["product_name"],
            df["total_sold"]
        )

        ax.set_title("Top 10 Fast-Moving Products")
        ax.set_ylabel("Quantity Sold")
        ax.tick_params(axis="x", labelrotation=35)

    save_chart(fig, "fast_moving_products.png")


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
    fig, ax = plt.subplots(figsize=(8, 5))

    if df.empty:
        show_empty(ax, "No category data")
    else:
        df["category"] = df["category"].fillna("Uncategorized")

        ax.bar(
            df["category"],
            df["total_stock"]
        )

        ax.set_title("Stock by Category")
        ax.set_ylabel("Total Stock")
        ax.tick_params(axis="x", labelrotation=35)

    save_chart(fig, "stock_by_category.png")


def stock_movement_chart():
    query = """
        SELECT
            DATE(transaction_date) AS movement_date,
            SUM(
                CASE
                    WHEN transaction_type = 'STOCK_IN'
                    THEN quantity
                    ELSE 0
                END
            ) AS stock_in,
            SUM(
                CASE
                    WHEN transaction_type = 'STOCK_OUT'
                    THEN quantity
                    ELSE 0
                END
            ) AS stock_out
        FROM stock_transactions
        GROUP BY DATE(transaction_date)
        ORDER BY movement_date
    """

    df = fetch_data(query)
    fig, ax = plt.subplots(figsize=(9, 5))

    if df.empty:
        show_empty(ax, "No stock movement data")
    else:
        ax.plot(
            df["movement_date"],
            df["stock_in"],
            marker="o",
            label="Stock In"
        )

        ax.plot(
            df["movement_date"],
            df["stock_out"],
            marker="o",
            label="Stock Out"
        )

        ax.set_title("Stock Movement Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Quantity")
        ax.tick_params(axis="x", labelrotation=35)
        ax.legend()

    save_chart(fig, "stock_movement_over_time.png")


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
    fig, ax = plt.subplots(figsize=(9, 5))

    if df.empty:
        show_empty(ax, "No inventory value data")
    else:
        ax.bar(
            df["product_name"],
            df["inventory_value"]
        )

        ax.set_title("Top 10 Products by Inventory Value")
        ax.set_ylabel("Value (₹)")
        ax.tick_params(axis="x", labelrotation=35)

    save_chart(fig, "inventory_value_by_product.png")


def generate_all_charts():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename in CHART_FILES:
        old_file = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(old_file):
            os.remove(old_file)

    chart_functions = [
        low_stock_chart,
        fast_moving_chart,
        category_chart,
        stock_movement_chart,
        inventory_value_chart
    ]

    for chart_function in chart_functions:
        print(f"Generating {chart_function.__name__}...")
        chart_function()

    missing_files = [
        filename
        for filename in CHART_FILES
        if not os.path.isfile(os.path.join(OUTPUT_DIR, filename))
        or os.path.getsize(os.path.join(OUTPUT_DIR, filename)) == 0
    ]

    if missing_files:
        raise RuntimeError(
            "Missing chart files: " + ", ".join(missing_files)
        )

    print("All five charts generated successfully.")


if __name__ == "__main__":
    try:
        generate_all_charts()
    except Exception as error:
        print(
            f"CHART GENERATION ERROR: {error}",
            file=sys.stderr
        )
        traceback.print_exc()
        sys.exit(1)
