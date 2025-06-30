import sqlite3
import json
from datetime import date

DATABASE_NAME = 'canteen.db'

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    barcode TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0
                )
            """)
            # NEWLY ADDED SALES TABLE
            # This table holds each cart sale as a single record.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_date DATE NOT NULL,
                    cart_contents TEXT NOT NULL, -- We will store the cart as JSON
                    total_amount REAL NOT NULL
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(e)
        finally:
            conn.close()


def save_sale_db(cart, total_amount):
    """Adds the confirmed cart as a single record to the 'sales' table."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # Convert the Python dictionary (cart) to a JSON formatted string
            cart_json = json.dumps(cart, ensure_ascii=False)

            # Get today's date (in YYYY-MM-DD format)
            today_date = date.today().strftime('%Y-%m-%d')

            cursor.execute(
                "INSERT INTO sales (sale_date, cart_contents, total_amount) VALUES (?, ?, ?)",
                (today_date, cart_json, total_amount)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Sale recording error: {e}")
            return False
        finally:
            conn.close()
    return False

def add_product_db(barcode, product_name, price, stock=0):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (barcode, product_name, price, stock) VALUES (?, ?, ?, ?)", (barcode, product_name, price, stock))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Barcode already exists
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()
    return False

def get_product_info_db(barcode):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Adding 'stock' info to the query
            cursor.execute("SELECT barcode, product_name, price, stock FROM products WHERE barcode=?", (barcode,))
            return cursor.fetchone() # Now returns 4 values: (barcode, name, price, stock)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
    return None

def get_all_products_db():
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Adding 'stock' column to the query
            cursor.execute("SELECT barcode, product_name, price, stock FROM products")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
    return None

def update_product_db(barcode, product_name=None, price=None, stock=None):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            fields_to_update = []
            parameters = []
            if product_name is not None:
                fields_to_update.append("product_name=?")
                parameters.append(product_name)
            if price is not None:
                fields_to_update.append("price=?")
                parameters.append(price)
            if stock is not None:
                fields_to_update.append("stock=?")
                parameters.append(stock)

            if fields_to_update:
                query = f"UPDATE products SET {', '.join(fields_to_update)} WHERE barcode=?"
                parameters.append(barcode)
                cursor.execute(query, tuple(parameters))
                conn.commit()
                return True
            return False # If there are no fields to update
        except sqlite3.Error as e:
            print(f"Database update error: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_product_db(barcode):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE barcode=?", (barcode,))
            conn.commit()
            # Check the number of rows affected by the change
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database delete error: {e}")
            return False
        finally:
            conn.close()
    return False

def get_all_sales_db():
    """Fetches all main sale records from the 'sales' table."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Sort by ID in descending order to see the latest sale at the top
            cursor.execute("SELECT id, sale_date, total_amount FROM sales ORDER BY id DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error while fetching sales: {e}")
            return []
        finally:
            conn.close()
    return []

def get_sale_details_db(sale_id):
    """Returns the JSON formatted cart contents for the given ID."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cart_contents FROM sales WHERE id=?", (sale_id,))
            result = cursor.fetchone()
            # fetchone() returns a tuple, e.g., ('{"json..."}',), we just want the text inside.
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error fetching sale details: {e}")
            return None
        finally:
            conn.close()
    return None


def get_product_based_report_db(start_date, end_date):
    """
    Calculates the total quantity sold and total revenue for each product
    within the specified date range.
    """
    conn = create_connection()
    if conn is None:
        return []

    # This SQL query parses and analyzes the data inside the JSON.
    query = """
        SELECT
            product_details.value ->> '$.isim' AS product_name,
            SUM(CAST(product_details.value ->> '$.adet' AS INTEGER)) AS total_quantity,
            SUM( (CAST(product_details.value ->> '$.adet' AS REAL)) * (CAST(product_details.value ->> '$.fiyat' AS REAL)) ) AS total_revenue
        FROM
            sales,
            json_each(cart_contents) AS product_details
        WHERE
            sale_date BETWEEN ? AND ?
        GROUP BY
            product_name
        ORDER BY
            total_revenue DESC;
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query, (start_date, end_date))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Product-based report error: {e}")
        # The error is often caused by an older SQLite version.
        # It's good practice to show a warning to the user in this case.
        return f"ERROR: {e}"
    finally:
        conn.close()