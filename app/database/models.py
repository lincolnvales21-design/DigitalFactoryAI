import os

from app.database.database import get_connection


DATABASE_URL = os.getenv("DATABASE_URL")


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    if DATABASE_URL:
        # ==========================
        # PostgreSQL
        # ==========================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id BIGSERIAL PRIMARY KEY,
                agent TEXT,
                task TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TEXT,
                result TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                product_type TEXT,
                price DOUBLE PRECISION NOT NULL,
                currency TEXT DEFAULT 'BRL',
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id BIGSERIAL PRIMARY KEY,
                product_id BIGINT NOT NULL,
                customer_email TEXT,
                amount DOUBLE PRECISION NOT NULL,
                currency TEXT DEFAULT 'BRL',
                status TEXT DEFAULT 'pending',
                gateway TEXT,
                external_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TEXT,
                delivered_at TEXT,
                download_token TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """
        )

        cursor.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS delivered_at TEXT
            """
        )

        cursor.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS download_token TEXT
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id BIGSERIAL PRIMARY KEY,
                order_id BIGINT NOT NULL,
                gateway TEXT NOT NULL,
                external_id TEXT,
                amount DOUBLE PRECISION NOT NULL,
                fee DOUBLE PRECISION DEFAULT 0,
                net_amount DOUBLE PRECISION DEFAULT 0,
                currency TEXT DEFAULT 'BRL',
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS security_logs (
                id BIGSERIAL PRIMARY KEY,
                action TEXT NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id BIGSERIAL PRIMARY KEY,
                agent TEXT NOT NULL,
                knowledge TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    else:
        # ==========================
        # SQLite
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
                delivered_at TEXT,
                download_token TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """
        )

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

        if "download_token" not in order_columns:
            cursor.execute(
                """
                ALTER TABLE orders
                ADD COLUMN download_token TEXT
                """
            )

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
