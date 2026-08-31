from datetime import datetime
from app.database.database import get_connection
import json


class KnowledgeBase:


    def add(
        self,
        agent,
        knowledge
    ):

        connection = get_connection()

        cursor = connection.cursor()


        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        cursor.execute(
            """
            INSERT INTO knowledge
            (
                agent,
                knowledge,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                agent,
                json.dumps(
                    knowledge,
                    ensure_ascii=False
                ),
                created_at
            )
        )


        connection.commit()

        connection.close()


        return {
            "agent": agent,
            "knowledge": knowledge,
            "created_at": created_at
        }



    def search(
        self,
        query=None
    ):

        connection = get_connection()

        cursor = connection.cursor()


        if query:

            cursor.execute(
                """
                SELECT
                    agent,
                    knowledge,
                    created_at
                FROM knowledge
                WHERE knowledge LIKE ?
                ORDER BY id DESC
                """,
                (
                    f"%{query}%",
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    agent,
                    knowledge,
                    created_at
                FROM knowledge
                ORDER BY id DESC
                """
            )


        rows = cursor.fetchall()


        connection.close()


        results = []


        for row in rows:

            results.append(
                {
                    "agent": row[0],
                    "knowledge": json.loads(row[1]),
                    "created_at": row[2]
                }
            )


        return results



    def latest(self):

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                agent,
                knowledge,
                created_at
            FROM knowledge
            ORDER BY id DESC
            LIMIT 1
            """
        )


        row = cursor.fetchone()


        connection.close()


        if row:

            return {
                "agent": row[0],
                "knowledge": json.loads(row[1]),
                "created_at": row[2]
            }


        return None



knowledge = KnowledgeBase()