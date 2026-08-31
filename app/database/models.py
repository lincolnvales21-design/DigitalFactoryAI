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
    # Migração aditiva de Orders
    # ==========================
    cursor.execute("PRAGMA table_info(orders)")
    order_columns = {
        column[1]
        for column in cursor.fetchall()
    }

    if "delivered_at" not in order_columns:
        cursor.execute(
            """
            ALTER TABLE orders
            ADD COLUMN delivered_at TEXT
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

    # ==========================
    # Security Logs
    # ==========================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'success',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==========================
    # Knowledge Base
    # ==========================
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            knowledge TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()