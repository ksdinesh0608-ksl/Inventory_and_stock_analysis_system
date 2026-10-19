from flask import Flask, jsonify, request
import mysql.connector
from db_connection import get_db_connection

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
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.*,
                r.current_stock
            FROM products p
            LEFT JOIN current_stock_report r
                ON p.product_id = r.product_id
        """)

        products = cursor.fetchall()

        return jsonify(products)

    except Exception:
        app.logger.exception("Failed to retrieve products")
        return jsonify({"error": "Could not retrieve products"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/products", methods=["POST"])
def add_product():
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

        if opening_stock < 0 or reorder_level < 0 or unit_cost < 0:
            raise ValueError

        if not __import__("math").isfinite(unit_cost):
            raise ValueError

    except (ValueError, TypeError, OverflowError):
        return jsonify({
            "error": "Stock, reorder level and cost must be valid non-negative numbers"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO products
            (sku, product_name, category, opening_stock, reorder_level, unit_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            sku.strip(),
            product_name.strip(),
            category.strip() if category else None,
            opening_stock,
            reorder_level,
            unit_cost
        ))

        connection.commit()

        return jsonify({
            "message": "Product added successfully",
            "product_id": cursor.lastrowid
        }), 201

    except mysql.connector.IntegrityError:
        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({
            "error": "Could not add product. Check whether the SKU already exists."
        }), 409

    except Exception:
        app.logger.exception("Failed to add product")

        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({"error": "Could not add product"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
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

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            UPDATE products
            SET product_name = %s,
                category = %s,
                opening_stock = %s,
                reorder_level = %s,
                unit_cost = %s
            WHERE product_id = %s
        """

        cursor.execute(query, (
            product_name.strip(),
            category.strip() if category else None,
            opening_stock,
            reorder_level,
            unit_cost,
            product_id
        ))

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT product_id FROM products WHERE product_id = %s",
                (product_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({"error": "Product not found"}), 404

        connection.commit()

        return jsonify({"message": "Product updated successfully"})

    except Exception:
        app.logger.exception("Failed to update product")

        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({"error": "Could not update product"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM products WHERE product_id = %s",
            (product_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return jsonify({"error": "Product not found"}), 404

        connection.commit()

        return jsonify({
            "message": "Product deleted successfully"
        }), 200

    except mysql.connector.IntegrityError:
        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({
            "error": "Cannot delete this product because related records may exist"
        }), 409

    except Exception:
        app.logger.exception("Failed to delete product")

        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({"error": "Could not delete product"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


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

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT product_id FROM products WHERE sku = %s",
            (sku.strip(),)
        )
        product = cursor.fetchone()

        if product is None:
            return jsonify({"error": "Product SKU not found"}), 404

        cursor.execute(
            """
            INSERT INTO stock_transactions
            (product_id, transaction_type, quantity, supplier_id, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                product["product_id"],
                "STOCK_IN",
                quantity,
                supplier_id,
                notes
            )
        )

        transaction_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Stock received successfully",
            "transaction_id": transaction_id,
            "sku": sku.strip(),
            "quantity_received": quantity
        }), 201

    except mysql.connector.IntegrityError:
        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({
            "error": "Invalid supplier or database constraint violation"
        }), 400

    except Exception:
        app.logger.exception("Stock-in failed")

        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({"error": "Could not record incoming stock"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()



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

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT product_id FROM products WHERE sku = %s",
            (sku.strip(),)
        )
        product = cursor.fetchone()

        if product is None:
            return jsonify({"error": "Product SKU not found"}), 404

        cursor.execute(
            "SELECT current_stock FROM current_stock_report WHERE product_id = %s",
            (product["product_id"],)
        )
        stock = cursor.fetchone()

        if stock is None or stock["current_stock"] is None:
            return jsonify({"error": "Could not determine current stock"}), 500

        if quantity > stock["current_stock"]:
            return jsonify({"error": "Insufficient stock"}), 400

        cursor.execute(
            """
            INSERT INTO stock_transactions
            (product_id, transaction_type, quantity, supplier_id, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                product["product_id"],
                "STOCK_OUT",
                quantity,
                None,
                notes
            )
        )

        transaction_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "message": "Stock-out recorded successfully",
            "transaction_id": transaction_id,
            "sku": sku.strip(),
            "quantity_removed": quantity,
            "remaining_stock": stock["current_stock"] - quantity
        }), 201

    except mysql.connector.Error:
        app.logger.exception("Stock-out database operation failed")

        if connection is not None and connection.is_connected():
            connection.rollback()

        return jsonify({"error": "Could not record stock-out"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()



@app.route("/low-stock", methods=["GET"])
def get_low_stock():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM low_stock_report")
        products = cursor.fetchall()

        return jsonify({
            "count": len(products),
            "low_stock_products": products
        }), 200

    except mysql.connector.Error:
        app.logger.exception("Failed to retrieve low-stock products")
        return jsonify({"error": "Could not retrieve low-stock products"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()



@app.route("/transactions", methods=["GET"])
def get_transactions():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                st.transaction_id,
                p.sku,
                p.product_name,
                st.transaction_date,
                st.transaction_type,
                st.quantity,
                st.notes
            FROM stock_transactions st
            JOIN products p
                ON st.product_id = p.product_id
            ORDER BY st.transaction_date DESC
        """)

        transactions = cursor.fetchall()

        return jsonify({
            "count": len(transactions),
            "transactions": transactions
        }), 200

    except mysql.connector.Error:
        app.logger.exception("Failed to retrieve transactions")
        return jsonify({
            "error": "Could not retrieve transactions"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    app.run(debug=True)
