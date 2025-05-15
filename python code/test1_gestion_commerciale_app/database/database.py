import sqlite3
import os

DATABASE_NAME = "gestion_commerciale.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", DATABASE_NAME)


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT UNIQUE,
        email TEXT UNIQUE
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        category TEXT,
        purchase_price REAL NOT NULL CHECK(purchase_price >= 0),
        selling_price REAL NOT NULL CHECK(selling_price >= 0),
        quantity_in_stock INTEGER NOT NULL DEFAULT 0 CHECK(quantity_in_stock >= 0)
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        purchase_date TEXT NOT NULL,
        cost_per_unit REAL NOT NULL CHECK(cost_per_unit >= 0),
        supplier TEXT,
        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS Sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        sale_date TEXT NOT NULL,
        total_amount REAL NOT NULL CHECK(total_amount >= 0),
        FOREIGN KEY (customer_id) REFERENCES Customers(id) ON DELETE SET NULL
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS SaleItems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        price_at_sale REAL NOT NULL CHECK(price_at_sale >= 0),
        FOREIGN KEY (sale_id) REFERENCES Sales(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE RESTRICT
    );
    """
    )

    cursor.execute(
        """
    CREATE TRIGGER IF NOT EXISTS increase_stock_on_purchase
    AFTER INSERT ON Purchases
    BEGIN
        UPDATE Products
        SET quantity_in_stock = quantity_in_stock + NEW.quantity
        WHERE id = NEW.product_id;
    END;
    """
    )

    cursor.execute(
        """
    CREATE TRIGGER IF NOT EXISTS decrease_stock_on_sale
    AFTER INSERT ON SaleItems
    BEGIN
        UPDATE Products
        SET quantity_in_stock = quantity_in_stock - NEW.quantity
        WHERE id = NEW.product_id;
    END;
    """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_name ON Products(name);")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_product_category ON Products(category);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_saleitems_sale_id ON SaleItems(sale_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_saleitems_product_id ON SaleItems(product_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_purchases_product_id ON Purchases(product_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON Sales(customer_id);"
    )

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


def add_customer(name, address=None, phone=None, email=None):
    """Adds a new customer to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Customers (name, address, phone, email) VALUES (?, ?, ?, ?)",
            (name, address, phone, email),
        )
        conn.commit()
        print(f"Customer '{name}' added successfully.")
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"Error adding customer: {e}")
        return None
    finally:
        conn.close()


def get_all_customers():
    """Retrieves all customers from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, address, phone, email FROM Customers ORDER BY name"
    )
    customers = cursor.fetchall()
    conn.close()
    return customers


def update_customer(customer_id, name, address=None, phone=None, email=None):
    """Updates an existing customer's details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE Customers
               SET name = ?, address = ?, phone = ?, email = ?
               WHERE id = ?""",
            (name, address, phone, email, customer_id),
        )
        conn.commit()
        print(f"Customer ID {customer_id} updated successfully.")
        return True
    except sqlite3.IntegrityError as e:
        print(f"Error updating customer {customer_id}: {e}")
        return False
    finally:
        conn.close()


def delete_customer(customer_id):
    """Deletes a customer from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Customers WHERE id = ?", (customer_id,))
        conn.commit()
        print(f"Customer ID {customer_id} deleted successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error deleting customer {customer_id}: {e}")
        return False
    finally:
        conn.close()


def add_product(
    name,
    description=None,
    category=None,
    purchase_price=0.0,
    selling_price=0.0,
    initial_stock=0,
):
    """Adds a new product to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO Products (name, description, category, purchase_price, selling_price, quantity_in_stock)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, category, purchase_price, selling_price, initial_stock),
        )
        conn.commit()
        print(f"Product '{name}' added successfully.")
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"Error adding product: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding product: {e}")
        return None
    finally:
        conn.close()


def get_all_products():
    """Retrieves all products from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, category, purchase_price, selling_price, quantity_in_stock FROM Products ORDER BY name"
    )
    products = cursor.fetchall()
    conn.close()
    return products


def get_product_by_id(product_id):
    """Retrieves a single product by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product


def update_product(
    product_id,
    name,
    description=None,
    category=None,
    purchase_price=0.0,
    selling_price=0.0,
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE Products
               SET name = ?, description = ?, category = ?, purchase_price = ?, selling_price = ?
               WHERE id = ?""",
            (name, description, category, purchase_price, selling_price, product_id),
        )
        conn.commit()
        print(f"Product ID {product_id} updated successfully.")
        return True
    except sqlite3.IntegrityError as e:
        print(f"Error updating product {product_id}: {e}")
        return False
    except sqlite3.Error as e:
        print(f"Database error updating product {product_id}: {e}")
        return False
    finally:
        conn.close()


def delete_product(product_id):
    """Deletes a product from the database."""

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Products WHERE id = ?", (product_id,))
        conn.commit()
        print(f"Product ID {product_id} deleted successfully.")
        return True
    except sqlite3.IntegrityError as e:

        print(
            f"Error deleting product {product_id}: Cannot delete product with existing sales records. {e}"
        )
        return False
    except sqlite3.Error as e:
        print(f"Database error deleting product {product_id}: {e}")
        return False
    finally:
        conn.close()


def search_products(query="", category_filter=None):
    """Searches products by name, description, or category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT id, name, description, category, purchase_price, selling_price, quantity_in_stock FROM Products WHERE 1=1"
    params = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    if category_filter:
        sql += " AND category = ?"
        params.append(category_filter)

    sql += " ORDER BY name"
    cursor.execute(sql, params)
    products = cursor.fetchall()
    conn.close()
    return products


def get_all_categories():
    """Retrieves a list of unique product categories."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT category FROM Products WHERE category IS NOT NULL AND category != '' ORDER BY category"
    )
    categories = [row["category"] for row in cursor.fetchall()]
    conn.close()
    return categories


def add_purchase(
    product_id, quantity, cost_per_unit, supplier=None, purchase_date=None
):
    """Records a new purchase and updates stock via trigger."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if purchase_date is None:
        import datetime

        purchase_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute(
            """INSERT INTO Purchases (product_id, quantity, purchase_date, cost_per_unit, supplier)
               VALUES (?, ?, ?, ?, ?)""",
            (product_id, quantity, purchase_date, cost_per_unit, supplier),
        )
        conn.commit()
        print(f"Purchase recorded for product ID {product_id}, quantity {quantity}.")
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error recording purchase: {e}")
        return None
    finally:
        conn.close()


def get_purchase_history(limit=100):
    """Retrieves recent purchase history, joining with product names."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT p.id, p.purchase_date, pr.name AS product_name, p.quantity, p.cost_per_unit, p.supplier
        FROM Purchases p
        JOIN Products pr ON p.product_id = pr.id
        ORDER BY p.purchase_date DESC
        LIMIT ?
    """,
        (limit,),
    )
    purchases = cursor.fetchall()
    conn.close()
    return purchases


def add_sale(sale_items, customer_id=None, sale_date=None):
    if not sale_items:
        print("Error: Cannot add a sale with no items.")
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    if sale_date is None:
        import datetime

        sale_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_amount = sum(item["quantity"] * item["price_at_sale"] for item in sale_items)

    try:
        conn.execute("BEGIN TRANSACTION;")

        cursor.execute(
            "INSERT INTO Sales (customer_id, sale_date, total_amount) VALUES (?, ?, ?)",
            (customer_id, sale_date, total_amount),
        )
        sale_id = cursor.lastrowid
        if not sale_id:
            raise sqlite3.Error("Failed to get sale_id after insert.")

        for item in sale_items:
            cursor.execute(
                """INSERT INTO SaleItems (sale_id, product_id, quantity, price_at_sale)
                   VALUES (?, ?, ?, ?)""",
                (sale_id, item["product_id"], item["quantity"], item["price_at_sale"]),
            )

        conn.commit()
        print(
            f"Sale ID {sale_id} recorded successfully with {len(sale_items)} item(s)."
        )
        return sale_id

    except (sqlite3.Error, ValueError) as e:
        print(f"Database error recording sale: {e}. Rolling back transaction.")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_sales_history(limit=100):
    """Retrieves recent sales history, joining with customer names."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT s.id, s.sale_date, c.name AS customer_name, s.total_amount
        FROM Sales s
        LEFT JOIN Customers c ON s.customer_id = c.id
        ORDER BY s.sale_date DESC
        LIMIT ?
    """,
        (limit,),
    )
    sales = cursor.fetchall()
    conn.close()
    return sales


def get_sale_items(sale_id):
    """Retrieves all items associated with a specific sale ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT si.id, si.product_id, p.name AS product_name, si.quantity, si.price_at_sale
        FROM SaleItems si
        JOIN Products p ON si.product_id = p.id
        WHERE si.sale_id = ?
        ORDER BY p.name
    """,
        (sale_id,),
    )
    items = cursor.fetchall()
    conn.close()
    return items


def get_sales_by_customer(customer_id):
    """Retrieves sales history for a specific customer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, sale_date, total_amount
        FROM Sales
        WHERE customer_id = ?
        ORDER BY sale_date DESC
    """,
        (customer_id,),
    )
    sales = cursor.fetchall()
    conn.close()
    return sales


def get_monthly_sales_trend(limit=12):
    """
    Retrieves total sales amount grouped by month for the last 'limit' months.
    Returns a list of tuples: (month_year_str, total_sales)
    Example: [('2024-03', 1500.50), ('2024-04', 2100.00)]
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            strftime('%Y-%m', sale_date) AS sale_month,
            SUM(total_amount) AS monthly_total
        FROM Sales
        WHERE date(sale_date) >= date('now', '-' || ? || ' months') -- Filter for the relevant period
        GROUP BY sale_month
        ORDER BY sale_month ASC;
        -- LIMIT ?; -- Removed limit here, filter by date instead
    """
    try:

        cursor.execute(query, (limit,))
        trend_data = cursor.fetchall()

        return [(row["sale_month"], row["monthly_total"]) for row in trend_data]
    except sqlite3.Error as e:
        print(f"Error fetching monthly sales trend: {e}")
        return []
    finally:
        conn.close()


def get_top_selling_products(limit=5):
    """
    Retrieves the top selling products based on total quantity sold.
    Returns a list of tuples: (product_name, total_quantity_sold)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            p.name AS product_name,
            SUM(si.quantity) AS total_quantity_sold
        FROM SaleItems si
        JOIN Products p ON si.product_id = p.id
        GROUP BY si.product_id, p.name -- Group by both ID and name
        ORDER BY total_quantity_sold DESC
        LIMIT ?;
    """
    try:
        cursor.execute(query, (limit,))
        top_products = cursor.fetchall()
        return [
            (row["product_name"], row["total_quantity_sold"]) for row in top_products
        ]
    except sqlite3.Error as e:
        print(f"Error fetching top selling products: {e}")
        return []
    finally:
        conn.close()


if __name__ == "__main__":

    print(f"Initializing database at: {DATABASE_PATH}")
    initialize_database()
