from datetime import datetime

from app.database.database import get_connection


class SecurityAudit:

    def log(
        self,
        action: str,
        reason: str = None,
        status: str = "success"
    ):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO security_logs
            (
                action,
                reason,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                action,
                reason,
                status,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        connection.commit()
        connection.close()


    def latest(self):

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM security_logs
            ORDER BY id DESC
            LIMIT 10
            """
        )

        logs = cursor.fetchall()

        connection.close()

        return logs


audit = SecurityAudit()