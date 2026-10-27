
import numpy as np
from Backend.db_connection import get_db_connection


def get_product_statistics():
    """Calculate statistics for each product."""

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                product_id,
                sku,
                product_name,
                category,
                current_stock,
                reorder_level,
                unit_cost
            FROM current_stock_report
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        product_statistics = []

        for row in rows:
            product_id, sku, name, category, stock, reorder, cost = row

            stock = float(stock)
            reorder = float(reorder)
            cost = float(cost)

            product_statistics.append({
                "product_id": product_id,
                "sku": sku,
                "product_name": name,
                "category": category,
                "current_stock": stock,
                "reorder_level": reorder,
                "stock_value": round(stock * cost, 2),
                "stock_status": (
                    "Low Stock" if stock <= reorder else "In Stock"
                )
            })

        return product_statistics

    finally:
        connection.close()


def get_overall_statistics():
    """Calculate statistics for the entire inventory."""

    products = get_product_statistics()

    if not products:
        return {
            "total_products": 0,
            "total_stock_units": 0,
            "average_stock": 0,
            "highest_stock": 0,
            "lowest_stock": 0,
            "low_stock_products": 0,
            "total_inventory_value": 0
        }

    stock = np.array(
        [product["current_stock"] for product in products],
        dtype=float
    )

    stock_values = np.array(
        [product["stock_value"] for product in products],
        dtype=float
    )

    return {
        "total_products": int(stock.size),
        "total_stock_units": float(np.sum(stock)),
        "average_stock": round(float(np.mean(stock)), 2),
        "highest_stock": float(np.max(stock)),
        "lowest_stock": float(np.min(stock)),
        "stock_standard_deviation": round(float(np.std(stock)), 2),
        "low_stock_products": sum(
            product["stock_status"] == "Low Stock"
            for product in products
        ),
        "total_inventory_value": round(float(np.sum(stock_values)), 2)
    }


if __name__ == "__main__":

    print("\n--- Product-wise Statistics ---")

    products = get_product_statistics()

    if not products:
        print("No inventory data available.")
    else:
        for product in products:
            print(
                f"\nProduct: {product['product_name']}"
                f"\nSKU: {product['sku']}"
                f"\nCurrent Stock: {product['current_stock']:g}"
                f"\nReorder Level: {product['reorder_level']:g}"
                f"\nStock Value: Rs. {product['stock_value']:,.2f}"
                f"\nStatus: {product['stock_status']}"
            )

    print("\n--- Overall Inventory Statistics ---")

    statistics = get_overall_statistics()

    for name, value in statistics.items():
        label = name.replace("_", " ").title()

        if name == "total_inventory_value":
            print(f"{label}: Rs. {value:,.2f}")
        else:
            print(f"{label}: {value}")
