from app.database.database import get_connection


def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    # ==========================
    # Agent Tasks
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT,
            task TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TEXT,
            result TEXT
        )
        """
    )

    # ==========================
    # Products
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            product_type TEXT,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'BRL',
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==========================
    # Orders
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            customer_email TEXT,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'BRL',
            status TEXT DEFAULT 'pending',
            gateway TEXT,
            external_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """
    )

    # ==========================
    # Payments
    # ==========================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            gateway TEXT NOT NULL,
            external_id TEXT,
            amount REAL NOT NULL,
            fee REAL DEFAULT 0,
            net_amount REAL DEFAULT 0,
            currency TEXT DEFAULT 'BRL',
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
        """
    )

    connection.commit()
    connection.close()