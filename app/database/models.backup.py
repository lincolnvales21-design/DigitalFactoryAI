from app.database.database import get_connection


def create_tables():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT,
            task TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # adiciona executed_at se ainda não existir
    cursor.execute(
        """
        PRAGMA table_info(agent_tasks)
        """
    )

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]


    if "executed_at" not in columns:

        cursor.execute(
            """
            ALTER TABLE agent_tasks
            ADD COLUMN executed_at TEXT
            """
        )
    if "result" not in columns:

        cursor.execute(
            """
            ALTER TABLE agent_tasks
            ADD COLUMN result TEXT
            """
        )


    connection.commit()
    connection.close()