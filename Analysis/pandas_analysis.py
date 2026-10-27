
import pandas as pd
from Backend.db_connection import get_db_connection


def get_inventory_data():
    """Retrieve current inventory data from MySQL."""

    connection = get_db_connection()

    try:
        query = "SELECT * FROM current_stock_report"

        cursor = connection.cursor()
        cursor.execute(query)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        inventory = pd.DataFrame(data, columns=columns)

        return inventory

    finally:
        connection.close()


def get_low_stock_products():
    """Find products at or below their reorder level."""

    inventory = get_inventory_data()

    low_stock = inventory[
        inventory["current_stock"] <= inventory["reorder_level"]
    ]

    return low_stock


def get_sorted_inventory():
    """Sort products from lowest to highest current stock."""

    inventory = get_inventory_data()

    sorted_inventory = inventory.sort_values(
        by="current_stock",
        ascending=True
    )

    return sorted_inventory


def get_stock_by_category():
    """Summarize inventory quantities by category."""

    inventory = get_inventory_data()

    category_summary = inventory.groupby("category").agg(
        total_products=("product_id", "count"),
        total_stock=("current_stock", "sum")
    ).reset_index()

    return category_summary


def get_stock_movement_summary():
    """Summarize stock-in and stock-out transaction quantities."""

    connection = get_db_connection()

    try:
        query = """
            SELECT
                transaction_type,
                SUM(quantity) AS total_quantity,
                COUNT(*) AS total_transactions
            FROM stock_transactions
            GROUP BY transaction_type
        """

        cursor = connection.cursor()
        cursor.execute(query)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        movement_summary = pd.DataFrame(data, columns=columns)

        return movement_summary

    finally:
        connection.close()


def get_fast_moving_products(limit=5):
    """Find products with the highest stock-out quantities."""

    connection = get_db_connection()

    try:
        query = """
            SELECT
                p.product_id,
                p.sku,
                p.product_name,
                SUM(t.quantity) AS total_stock_out
            FROM products p
            JOIN stock_transactions t
                ON p.product_id = t.product_id
            WHERE t.transaction_type = %s
            GROUP BY p.product_id, p.sku, p.product_name
            ORDER BY total_stock_out DESC
            LIMIT %s
        """

        cursor = connection.cursor()
        cursor.execute(query, ("STOCK_OUT", limit))

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        fast_moving = pd.DataFrame(data, columns=columns)

        return fast_moving

    finally:
        connection.close()


if __name__ == "__main__":

    print("\n--- Current Inventory ---")
    print(get_inventory_data().to_string(index=False))

    print("\n--- Low Stock Products ---")
    low_stock = get_low_stock_products()

    if low_stock.empty:
        print("No low-stock products found.")
    else:
        print(low_stock.to_string(index=False))

    print("\n--- Inventory Sorted by Current Stock ---")
    print(get_sorted_inventory().to_string(index=False))

    print("\n--- Stock Summary by Category ---")
    print(get_stock_by_category().to_string(index=False))

    print("\n--- Stock Movement Summary ---")
    movement = get_stock_movement_summary()

    if movement.empty:
        print("No stock transactions found.")
    else:
        print(movement.to_string(index=False))

    print("\n--- Fast-Moving Products ---")
    fast_moving = get_fast_moving_products()

    if fast_moving.empty:
        print("No stock-out transactions found.")
    else:
        print(fast_moving.to_string(index=False))
