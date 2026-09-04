import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path("digitalfactory.db")

# Memória que representa evolução, decisões e aprendizado autônomo.
# Dados comerciais/financeiros NÃO entram nesta lista.
EVOLUTION_MEMORY_TABLES = [
    "learning_insights",
    "revenue_insights",
    "optimization_actions",
    "supervisor_decisions",
    "autonomous_decisions",
    "autonomous_action_runs",
    "autonomous_cycle_runs",
    "autonomous_cycle_gates",
    "autonomous_cycles",
]

# Estado persistente do Kill Switch.
CONTROL_TABLE = "emergency_shutdown_state"


class EmergencyShutdown:
    def __init__(self):
        self.db_path = DB_PATH

    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def _ensure_state_table(self, conn):
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CONTROL_TABLE} (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                emergency_off INTEGER NOT NULL DEFAULT 0,
                shutdown_at TEXT,
                memory_reset_at TEXT
            )
            """
        )

        conn.execute(
            f"""
            INSERT OR IGNORE INTO {CONTROL_TABLE}
            (id, emergency_off)
            VALUES (1, 0)
            """
        )

    def is_emergency_off(self):
        with self._connect() as conn:
            self._ensure_state_table(conn)
            row = conn.execute(
                f"""
                SELECT emergency_off
                FROM {CONTROL_TABLE}
                WHERE id = 1
                """
            ).fetchone()

            return bool(row and row[0])

    def shutdown_and_reset(self):
        """
        DESLIGAMENTO DE SEGURANÇA MÁXIMA.

        1. Ativa o bloqueio persistente.
        2. Zera a memória de evolução.
        3. NÃO apaga produtos, pedidos, pagamentos ou dados financeiros.
        """
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            self._ensure_state_table(conn)

            # Primeiro bloqueia a evolução.
            conn.execute(
                f"""
                UPDATE {CONTROL_TABLE}
                SET emergency_off = 1,
                    shutdown_at = ?,
                    memory_reset_at = ?
                WHERE id = 1
                """,
                (now, now),
            )

            # Depois zera exclusivamente a memória evolutiva.
            existing = {
                row[0]
                for row in conn.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """
                ).fetchall()
            }

            cleared = []

            for table in EVOLUTION_MEMORY_TABLES:
                if table in existing:
                    conn.execute(f'DELETE FROM "{table}"')
                    cleared.append(table)

            conn.commit()

        return {
            "status": "emergency_off",
            "autonomous_intelligence": "OFF",
            "evolution_memory": "RESET",
            "shutdown_at": now,
            "memory_tables_cleared": cleared,
            "financial_data_preserved": True,
            "products_preserved": True,
            "orders_preserved": True,
            "payments_preserved": True,
            "code_preserved": True,
            "automatic_restart": False,
        }

    def release(self):
        """
        Liberação manual do bloqueio pelo proprietário.
        NÃO recria memória apagada.
        """
        with self._connect() as conn:
            self._ensure_state_table(conn)

            conn.execute(
                f"""
                UPDATE {CONTROL_TABLE}
                SET emergency_off = 0
                WHERE id = 1
                """
            )

            conn.commit()

        return {
            "status": "released",
            "autonomous_intelligence": "READY",
            "evolution_memory": "EMPTY",
            "message": "A fábrica pode ser iniciada novamente pelo proprietário."
        }

    def status(self):
        with self._connect() as conn:
            self._ensure_state_table(conn)

            row = conn.execute(
                f"""
                SELECT emergency_off, shutdown_at, memory_reset_at
                FROM {CONTROL_TABLE}
                WHERE id = 1
                """
            ).fetchone()

        return {
            "emergency_off": bool(row[0]),
            "shutdown_at": row[1],
            "memory_reset_at": row[2],
            "automatic_restart": False,
            "evolution_memory": "RESET" if bool(row[0]) else "ACTIVE",
        }


emergency_shutdown = EmergencyShutdown()
