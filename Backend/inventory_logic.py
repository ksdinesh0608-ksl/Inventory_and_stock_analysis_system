
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_db_connection


def get_all_products():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.*, r.current_stock
            FROM products p
            LEFT JOIN current_stock_report r
                ON p.product_id = r.product_id
        """)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def add_product(sku, product_name, category, opening_stock, reorder_level, unit_cost):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO products
            (sku, product_name, category, opening_stock, reorder_level, unit_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            sku, product_name, category,
            opening_stock, reorder_level, unit_cost
        ))

        connection.commit()
        return cursor.lastrowid

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def update_product(product_id, product_name, category, opening_stock, reorder_level, unit_cost):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE products
            SET product_name = %s,
                category = %s,
                opening_stock = %s,
                reorder_level = %s,
                unit_cost = %s
            WHERE product_id = %s
        """, (
            product_name, category, opening_stock,
            reorder_level, unit_cost, product_id
        ))

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT product_id FROM products WHERE product_id = %s",
                (product_id,)
            )
            if cursor.fetchone() is None:
                return False

        connection.commit()
        return True

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


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
            return False

        connection.commit()
        return True

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def record_stock_in(sku, quantity, supplier_id, notes):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT product_id FROM products WHERE sku = %s",
            (sku,)
        )
        product = cursor.fetchone()

        if product is None:
            return {"error": "Product SKU not found"}

        cursor.execute("""
            INSERT INTO stock_transactions
            (product_id, transaction_type, quantity, supplier_id, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            product["product_id"],
            "STOCK_IN",
            quantity,
            supplier_id,
            notes
        ))

        transaction_id = cursor.lastrowid
        connection.commit()

        return {
            "transaction_id": transaction_id,
            "product_id": product["product_id"]
        }

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def record_stock_out(sku, quantity, notes):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT product_id FROM products WHERE sku = %s FOR UPDATE",
            (sku,)
        )
        product = cursor.fetchone()

        if product is None:
            return {"error": "Product SKU not found"}

        product_id = product["product_id"]

        cursor.execute("""
            SELECT current_stock
            FROM current_stock_report
            WHERE product_id = %s
        """, (product_id,))

        stock = cursor.fetchone()

        if stock is None or stock["current_stock"] is None:
            return {"error": "Could not determine current stock"}

        current_stock = stock["current_stock"]

        if quantity > current_stock:
            return {
                "error": "Insufficient stock",
                "current_stock": current_stock
            }

        cursor.execute("""
            INSERT INTO stock_transactions
            (product_id, transaction_type, quantity, supplier_id, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            product_id, "STOCK_OUT", quantity, None, notes
        ))

        transaction_id = cursor.lastrowid
        connection.commit()

        return {
            "transaction_id": transaction_id,
            "current_stock": current_stock,
            "remaining_stock": current_stock - quantity
        }

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def get_low_stock_products():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM low_stock_report")
        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def get_all_transactions():
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
                st.notes,
                s.supplier_name
            FROM stock_transactions st
            JOIN products p
                ON st.product_id = p.product_id
            LEFT JOIN suppliers s
                ON st.supplier_id = s.supplier_id
            ORDER BY st.transaction_date DESC
        """)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def create_staff_user(full_name, username, email, password):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (full_name, username, email, password_hash,
             user_role, is_active, approval_status)
            VALUES (%s, %s, %s, %s, 'STAFF', 1, 'PENDING')
        """, (
            full_name, username, email, password_hash
        ))

        connection.commit()
        return cursor.lastrowid

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def create_admin_user(full_name, username, email, password):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (full_name, username, email, password_hash,
             user_role, is_active, approval_status)
            VALUES (%s, %s, %s, %s, 'ADMIN', 1, 'APPROVED')
        """, (
            full_name, username, email, password_hash
        ))

        connection.commit()
        return cursor.lastrowid

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def authenticate_user(identifier, password):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, full_name, username, email,
                   password_hash, user_role, is_active,
                   approval_status
            FROM users
            WHERE username = %s OR email = %s
            LIMIT 1
        """, (identifier, identifier))

        user = cursor.fetchone()

        if user is None:
            return {"status": "INVALID_CREDENTIALS"}

        if not check_password_hash(user["password_hash"], password):
            return {"status": "INVALID_CREDENTIALS"}

        if user["approval_status"] == "PENDING":
            return {"status": "PENDING"}

        if user["approval_status"] == "REJECTED":
            return {"status": "REJECTED"}

        if not user["is_active"]:
            return {"status": "INACTIVE"}

        user.pop("password_hash", None)

        return {
            "status": "SUCCESS",
            "user": user
        }

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def get_user_by_id(user_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, full_name, username, email,
                   user_role, is_active, approval_status
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def get_pending_users():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, full_name, username, email, created_at
            FROM users
            WHERE user_role = 'STAFF'
              AND approval_status = 'PENDING'
            ORDER BY created_at ASC
        """)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def update_user_approval(user_id, approval_status):
    if approval_status not in ("APPROVED", "REJECTED"):
        raise ValueError("Invalid approval status")

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET approval_status = %s,
                is_active = %s
            WHERE user_id = %s
              AND user_role = 'STAFF'
              AND approval_status = 'PENDING'
        """, (
            approval_status,
            1 if approval_status == "APPROVED" else 0,
            user_id
        ))

        updated = cursor.rowcount > 0
        connection.commit()

        return updated

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
