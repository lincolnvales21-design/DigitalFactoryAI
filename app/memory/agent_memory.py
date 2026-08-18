import json

from datetime import datetime
from zoneinfo import ZoneInfo

from app.database.database import get_connection


class AgentMemory:


    def save(
        self,
        agent,
        task,
        status,
        result=None
    ):

        connection = get_connection()

        cursor = connection.cursor()


        now = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        cursor.execute(
            """
            INSERT INTO agent_tasks
            (agent, task, status, result, executed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                agent,
                task,
                status,
                json.dumps(
                    result,
                    ensure_ascii=False
                ),
                now
            )
        )


        connection.commit()
        connection.close()



    def history(self):

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                id,
                agent,
                task,
                status,
                executed_at,
                result
            FROM agent_tasks
            ORDER BY id DESC
            """
        )


        rows = cursor.fetchall()

        connection.close()


        history = []


        for row in rows:

            result = None

            if row[5]:
                try:
                    result = json.loads(row[5])
                except:
                    result = row[5]


            history.append(
                {
                    "id": row[0],
                    "agent": row[1],
                    "task": row[2],
                    "status": row[3],
                    "executed_at": row[4],
                    "result": result
                }
            )


        return history



    def get_latest_result(
        self,
        agent
    ):

        connection = get_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT result
            FROM agent_tasks
            WHERE agent = ?
            AND result IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                agent,
            )
        )


        row = cursor.fetchone()

        connection.close()


        if row:

            try:
                return json.loads(row[0])

            except:
                return row[0]


        return None



memory = AgentMemory()