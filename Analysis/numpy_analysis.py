
import os
import sys
import numpy as np
import pandas as pd

ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))

if ANALYSIS_DIR not in sys.path:
    sys.path.insert(0, ANALYSIS_DIR)

from Backend.db_connection import get_db_connection


def fetch_inventory():
    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
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

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def run_numpy_analysis():
    rows = fetch_inventory()

    if not rows:
        print("No inventory records found.")
        return

    df = pd.DataFrame(rows)

    stock = np.asarray(df["current_stock"], dtype=float)
    reorder = np.asarray(df["reorder_level"], dtype=float)
    cost = np.asarray(df["unit_cost"], dtype=float)

    stock = np.nan_to_num(stock, nan=0.0)
    reorder = np.nan_to_num(reorder, nan=0.0)
    cost = np.nan_to_num(cost, nan=0.0)

    inventory_value = stock * cost

    print("\n--- NumPy Inventory Analysis ---")

    print("\nTotal Products:")
    print(len(stock))

    print("\nTotal Stock Units:")
    print(np.sum(stock))

    print("\nAverage Stock:")
    print(round(np.mean(stock), 2))

    print("\nHighest Stock:")
    print(np.max(stock))

    print("\nLowest Stock:")
    print(np.min(stock))

    print("\nTotal Inventory Value:")
    print(round(np.sum(inventory_value), 2))

    print("\nAverage Inventory Value per Product:")
    print(round(np.mean(inventory_value), 2))

    low_stock_mask = stock <= reorder

    print("\nLow Stock Product Count:")
    print(np.count_nonzero(low_stock_mask))

    print("\nLow Stock Products:")
    for index in np.where(low_stock_mask)[0]:
        print(
            df.iloc[index]["product_name"],
            "- Current:",
            stock[index],
            "- Reorder Level:",
            reorder[index]
        )

    print("\nProducts Above Reorder Level:")
    print(np.count_nonzero(stock > reorder))

    print("\nStock Distribution:")
    print("25th Percentile:", np.percentile(stock, 25))
    print("50th Percentile:", np.percentile(stock, 50))
    print("75th Percentile:", np.percentile(stock, 75))

    print("\nInventory Value Array:")
    print(inventory_value)


if __name__ == "__main__":
    run_numpy_analysis()
