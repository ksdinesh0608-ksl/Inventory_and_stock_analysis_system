
import os
import sys
import pandas as pd

ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))

if ANALYSIS_DIR not in sys.path:
    sys.path.insert(0, ANALYSIS_DIR)

from Backend.db_connection import get_db_connection


def fetch_data(query, params=None):
    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_inventory_dataframe():
    rows = fetch_data("""
        SELECT
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            COALESCE(r.current_stock, p.opening_stock, 0) AS current_stock,
            p.reorder_level,
            p.unit_cost
        FROM products p
        LEFT JOIN current_stock_report r
            ON p.product_id = r.product_id
        ORDER BY p.product_name
    """)

    return pd.DataFrame(rows)


def get_transaction_dataframe():
    rows = fetch_data("""
        SELECT
            st.transaction_id,
            p.product_id,
            p.sku,
            p.product_name,
            st.transaction_date,
            st.transaction_type,
            st.quantity,
            st.notes,
            s.supplier_name
        FROM stock_transactions st
        JOIN products p
            ON st.product_id = p.product_id
        LEFT JOIN suppliers s
            ON st.supplier_id = s.supplier_id
        ORDER BY st.transaction_date DESC
    """)

    return pd.DataFrame(rows)


def run_analysis():
    inventory = get_inventory_dataframe()
    transactions = get_transaction_dataframe()

    if inventory.empty:
        print("No inventory records found.")
        return

    inventory["current_stock"] = pd.to_numeric(
        inventory["current_stock"], errors="coerce"
    ).fillna(0)

    inventory["reorder_level"] = pd.to_numeric(
        inventory["reorder_level"], errors="coerce"
    ).fillna(0)

    inventory["unit_cost"] = pd.to_numeric(
        inventory["unit_cost"], errors="coerce"
    ).fillna(0)

    inventory["stock_value"] = (
        inventory["current_stock"] * inventory["unit_cost"]
    )

    inventory["category"] = inventory["category"].fillna("Uncategorized")

    print("\n--- Current Inventory ---")
    print(inventory.to_string(index=False))

    low_stock = inventory[
        inventory["current_stock"] <= inventory["reorder_level"]
    ]

    print("\n--- Low Stock Products ---")
    if low_stock.empty:
        print("No low-stock products.")
    else:
        print(low_stock.to_string(index=False))

    sorted_inventory = inventory.sort_values(
        by="current_stock",
        ascending=True
    )

    print("\n--- Inventory Sorted by Current Stock ---")
    print(
        sorted_inventory[
            ["sku", "product_name", "current_stock", "reorder_level"]
        ].to_string(index=False)
    )

    category_summary = inventory.groupby("category").agg(
        total_products=("product_id", "count"),
        total_stock=("current_stock", "sum"),
        total_value=("stock_value", "sum")
    ).reset_index()

    print("\n--- Stock Summary by Category ---")
    print(category_summary.to_string(index=False))

    if transactions.empty:
        print("\n--- Stock Movement Summary ---")
        print("No stock transactions available.")

        print("\n--- Fast-Moving Products ---")
        print("No stock-out transactions available.")
        return

    transactions["quantity"] = pd.to_numeric(
        transactions["quantity"], errors="coerce"
    ).fillna(0)

    movement_summary = transactions.groupby("transaction_type").agg(
        total_quantity=("quantity", "sum"),
        total_transactions=("transaction_id", "count")
    ).reset_index()

    print("\n--- Stock Movement Summary ---")
    print(movement_summary.to_string(index=False))

    stock_out = transactions[
        transactions["transaction_type"] == "STOCK_OUT"
    ]

    fast_moving = stock_out.groupby(
        ["product_id", "sku", "product_name"]
    ).agg(
        total_stock_out=("quantity", "sum")
    ).reset_index()

    fast_moving = fast_moving.sort_values(
        by="total_stock_out",
        ascending=False
    )

    print("\n--- Fast-Moving Products ---")
    if fast_moving.empty:
        print("No stock-out transactions available.")
    else:
        print(fast_moving.to_string(index=False))


if __name__ == "__main__":
    run_analysis()
