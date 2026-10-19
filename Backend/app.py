from flask import Flask, jsonify, request
import mysql.connector
from db_connection import get_db_connection
from inventory_logic import (
    get_all_products,
    add_product,
    update_product,
    delete_product,
    record_stock_in,
    record_stock_out,
    get_low_stock_products,
    get_all_transactions
)
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "message": "Inventory and Stock Analysis API is running"
    })

@app.route("/test-db")
def test_db():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        return jsonify({
            "message": "Database connected successfully",
            "tables": [table[0] for table in tables]
        })

    except Exception:
        app.logger.exception("Database test failed")
        return jsonify({
            "error": "Could not retrieve database tables"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

@app.route("/products", methods=["GET"])
def get_products():
    try:
        products = get_all_products()
        return jsonify(products), 200

    except mysql.connector.Error:
        app.logger.exception("Failed to retrieve products")
        return jsonify({
            "error": "Could not retrieve products"
        }), 500


@app.route("/products", methods=["POST"])
def add_product_route():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    sku = data.get("sku")
    product_name = data.get("product_name")
    category = data.get("category")
    opening_stock = data.get("opening_stock", 0)
    reorder_level = data.get("reorder_level", 10)
    unit_cost = data.get("unit_cost", 0)

    if not isinstance(sku, str) or not sku.strip():
        return jsonify({"error": "SKU is required"}), 400

    if not isinstance(product_name, str) or not product_name.strip():
        return jsonify({"error": "Product name is required"}), 400

    if category is not None and not isinstance(category, str):
        return jsonify({"error": "Category must be text"}), 400

    try:
        if isinstance(opening_stock, bool) or isinstance(reorder_level, bool):
            raise ValueError

        opening_stock = int(opening_stock)
        reorder_level = int(reorder_level)
        unit_cost = float(unit_cost)

        import math

        if opening_stock < 0 or reorder_level < 0 or unit_cost < 0:
            raise ValueError

        if not math.isfinite(unit_cost):
            raise ValueError

    except (ValueError, TypeError, OverflowError):
        return jsonify({
            "error": "Stock, reorder level and cost must be valid non-negative numbers"
        }), 400

    try:
        product_id = add_product(
            sku.strip(),
            product_name.strip(),
            category.strip() if category else None,
            opening_stock,
            reorder_level,
            unit_cost
        )

        return jsonify({
            "message": "Product added successfully",
            "product_id": product_id
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "Could not add product. Check whether the SKU already exists."
        }), 409

    except Exception:
        app.logger.exception("Failed to add product")
        return jsonify({"error": "Could not add product"}), 500


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product_route(product_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    product_name = data.get("product_name")
    category = data.get("category")
    opening_stock = data.get("opening_stock")
    reorder_level = data.get("reorder_level")
    unit_cost = data.get("unit_cost")

    if not isinstance(product_name, str) or not product_name.strip():
        return jsonify({"error": "Product name is required"}), 400

    if category is not None and not isinstance(category, str):
        return jsonify({"error": "Category must be text"}), 400

    try:
        if isinstance(opening_stock, bool) or isinstance(reorder_level, bool):
            raise ValueError

        opening_stock = int(opening_stock)
        reorder_level = int(reorder_level)
        unit_cost = float(unit_cost)

        if opening_stock < 0 or reorder_level < 0 or unit_cost < 0:
            raise ValueError

        import math
        if not math.isfinite(unit_cost):
            raise ValueError

    except (ValueError, TypeError, OverflowError):
        return jsonify({"error": "Enter valid non-negative numbers"}), 400

    try:
        updated = update_product(
            product_id,
            product_name.strip(),
            category.strip() if category else None,
            opening_stock,
            reorder_level,
            unit_cost
        )

        if not updated:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product updated successfully"}), 200

    except Exception:
        app.logger.exception("Failed to update product")
        return jsonify({"error": "Could not update product"}), 500



@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product_route(product_id):
    try:
        deleted = delete_product(product_id)

        if not deleted:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({
            "message": "Product deleted successfully"
        }), 200

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "Cannot delete this product because related records may exist"
        }), 409

    except Exception:
        app.logger.exception("Failed to delete product")
        return jsonify({"error": "Could not delete product"}), 500


@app.route("/stock-in", methods=["POST"])
def stock_in():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    sku = data.get("sku")
    quantity = data.get("quantity")
    supplier_id = data.get("supplier_id")
    notes = data.get("notes")

    if not isinstance(sku, str) or not sku.strip():
        return jsonify({"error": "SKU is required"}), 400

    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    if supplier_id is not None:
        if isinstance(supplier_id, bool) or not isinstance(supplier_id, int) or supplier_id <= 0:
            return jsonify({"error": "Supplier ID must be a positive integer"}), 400

    if notes is not None and not isinstance(notes, str):
        return jsonify({"error": "Notes must be text"}), 400

    try:
        result = record_stock_in(
            sku.strip(), quantity, supplier_id, notes
        )

        if "error" in result:
            return jsonify({"error": result["error"]}), 404

        return jsonify({
            "message": "Stock received successfully",
            "transaction_id": result["transaction_id"],
            "sku": sku.strip(),
            "quantity_received": quantity
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "Invalid supplier or database constraint violation"
        }), 400

    except Exception:
        app.logger.exception("Stock-in failed")
        return jsonify({"error": "Could not record incoming stock"}), 500


@app.route("/stock-out", methods=["POST"])
def stock_out():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    sku = data.get("sku")
    quantity = data.get("quantity")
    notes = data.get("notes")

    if not isinstance(sku, str) or not sku.strip():
        return jsonify({"error": "SKU is required"}), 400

    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    if notes is not None and not isinstance(notes, str):
        return jsonify({"error": "Notes must be text"}), 400

    try:
        result = record_stock_out(sku.strip(), quantity, notes)

        if result.get("error") == "Product SKU not found":
            return jsonify({"error": result["error"]}), 404

        if result.get("error") == "Insufficient stock":
            return jsonify({"error": result["error"]}), 400

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        return jsonify({
            "message": "Stock-out recorded successfully",
            "transaction_id": result["transaction_id"],
            "sku": sku.strip(),
            "quantity_removed": quantity,
            "remaining_stock": result["remaining_stock"]
        }), 201

    except Exception:
        app.logger.exception("Stock-out failed")
        return jsonify({"error": "Could not record stock-out"}), 500


@app.route("/low-stock", methods=["GET"])
def get_low_stock():
    try:
        products = get_low_stock_products()

        return jsonify({
            "count": len(products),
            "low_stock_products": products
        }), 200

    except Exception:
        app.logger.exception("Failed to retrieve low-stock products")
        return jsonify({
            "error": "Could not retrieve low-stock products"
        }), 500


@app.route("/transactions", methods=["GET"])
def get_transactions():
    try:
        transactions = get_all_transactions()

        return jsonify({
            "count": len(transactions),
            "transactions": transactions
        }), 200

    except Exception:
        app.logger.exception("Failed to retrieve transactions")
        return jsonify({
            "error": "Could not retrieve transactions"
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
