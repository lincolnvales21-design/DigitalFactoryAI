
import asyncio
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class AutonomousScheduler:
    """
    Operação recorrente controlada do DigitalFactoryAI.

    Segurança:
    - não movimenta dinheiro;
    - não cria anúncios pagos;
    - não faz investimentos;
    - possui limite de ciclos;
    - possui intervalo configurável;
    - pode ser pausado;
    - registra execução e falhas.
    """

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self.task = None
        self.running = False
        self.paused = False
        self.cycles_completed = 0
        self.max_cycles = 1
        self.interval_seconds = 3600
        self.last_result = None
        self._ensure_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_scheduler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                cycle_number INTEGER,
                max_cycles INTEGER,
                interval_seconds INTEGER,
                result_json TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _save(self, action, status, result=None):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO autonomous_scheduler
            (
                action,
                status,
                cycle_number,
                max_cycles,
                interval_seconds,
                result_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            action,
            status,
            self.cycles_completed,
            self.max_cycles,
            self.interval_seconds,
            json.dumps(
                result,
                ensure_ascii=False,
                default=str
            ) if result is not None else None,
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

    async def _loop(self):
        try:
            from app.business.supervisor import autonomous_supervisor

            while self.running:
                if self.paused:
                    await asyncio.sleep(1)
                    continue

                if self.cycles_completed >= self.max_cycles:
                    self.running = False
                    self._save(
                        "scheduler",
                        "completed"
                    )
                    break

                try:
                    result = await autonomous_supervisor.run_cycle()

                    self.cycles_completed += 1
                    self.last_result = result

                    self._save(
                        "cycle",
                        "completed",
                        result
                    )

                except Exception as exc:
                    error = {
                        "error": str(exc),
                        "type": type(exc).__name__,
                    }

                    self.last_result = error

                    self._save(
                        "cycle",
                        "failed",
                        error
                    )

                    # Falha não deve provocar loop agressivo.
                    await asyncio.sleep(
                        min(self.interval_seconds, 60)
                    )
                    continue

                if self.cycles_completed >= self.max_cycles:
                    self.running = False
                    self._save(
                        "scheduler",
                        "completed"
                    )
                    break

                await asyncio.sleep(
                    self.interval_seconds
                )

        finally:
            self.running = False

    async def start(
        self,
        max_cycles=1,
        interval_seconds=3600
    ):
        if self.running:
            return {
                "status": "already_running",
                "cycles_completed": self.cycles_completed,
                "max_cycles": self.max_cycles,
            }

        max_cycles = int(max_cycles)
        interval_seconds = int(interval_seconds)

        if max_cycles < 1:
            max_cycles = 1

        if max_cycles > 100:
            max_cycles = 100

        if interval_seconds < 10:
            interval_seconds = 10

        self.max_cycles = max_cycles
        self.interval_seconds = interval_seconds
        self.cycles_completed = 0
        self.paused = False
        self.running = True
        self.last_result = None

        self._save(
            "start",
            "running"
        )

        self.task = asyncio.create_task(
            self._loop()
        )

        return {
            "status": "started",
            "max_cycles": self.max_cycles,
            "interval_seconds": self.interval_seconds,
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "automatic_ads": False,
                "owner_controls_capital": True,
            },
            "started_at": datetime.utcnow().isoformat(),
        }

    def pause(self):
        if not self.running:
            return {
                "status": "not_running"
            }

        self.paused = True

        self._save(
            "pause",
            "paused"
        )

        return {
            "status": "paused",
            "cycles_completed": self.cycles_completed,
        }

    def resume(self):
        if not self.running:
            return {
                "status": "not_running"
            }

        self.paused = False

        self._save(
            "resume",
            "running"
        )

        return {
            "status": "resumed",
            "cycles_completed": self.cycles_completed,
        }

    def stop(self):
        was_running = self.running

        self.running = False
        self.paused = False

        if self.task and not self.task.done():
            self.task.cancel()

        self._save(
            "stop",
            "stopped"
        )

        return {
            "status": "stopped",
            "was_running": was_running,
            "cycles_completed": self.cycles_completed,
        }

    def status(self):
        return {
            "running": self.running,
            "paused": self.paused,
            "cycles_completed": self.cycles_completed,
            "max_cycles": self.max_cycles,
            "interval_seconds": self.interval_seconds,
            "last_result": self.last_result,
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "automatic_ads": False,
                "owner_controls_capital": True,
            },
        }

    def history(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                action,
                status,
                cycle_number,
                max_cycles,
                interval_seconds,
                result_json,
                created_at
            FROM autonomous_scheduler
            ORDER BY id DESC
            LIMIT 50
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            data = None

            if row[6]:
                try:
                    data = json.loads(row[6])
                except Exception:
                    data = row[6]

            result.append({
                "id": row[0],
                "action": row[1],
                "status": row[2],
                "cycle_number": row[3],
                "max_cycles": row[4],
                "interval_seconds": row[5],
                "result": data,
                "created_at": row[7],
            })

        return result


autonomous_scheduler = AutonomousScheduler()
