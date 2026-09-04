import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.business.autonomous_action_orchestrator import (
    autonomous_action_orchestrator
)

from app.business.autonomous_engine import (
    autonomous_business_engine
)

from app.business.learning_engine import (
    learning_engine
)

from app.business.supervisor import (
    supervisor
)

from app.business.emergency_shutdown import (
    emergency_shutdown
)


class AutonomousCycleOrchestrator:
    """
    Orquestrador central da fábrica autônoma.

    Fluxo:

        SUPERVISOR
             ↓
        DECISÃO
             ↓
        ┌─────────────────────────────┐
        │ NOVA OPORTUNIDADE?          │
        │                             │
        │ SIM → AutonomousBusinessEngine
        │       Produto → Oferta → Venda
        │                             │
        │ NÃO → ActionOrchestrator   │
        │       Otimização/Validação  │
        └─────────────────────────────┘
             ↓
        APRENDIZADO
             ↓
        PRÓXIMO CICLO

    O ciclo não possui autorização financeira própria.
    Qualquer gasto continua passando pelo
    ActionExecutionEngine.

    O Kill Switch possui prioridade máxima.
    """

    def __init__(self):

        self.db_path = Path(
            "digitalfactory.db"
        )

        self.running = False

        self._lock = asyncio.Lock()

        self._ensure_database()

    # ========================================================
    # DATABASE
    # ========================================================

    def _connect(self):

        return sqlite3.connect(
            self.db_path
        )

    def _ensure_database(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_cycle_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                decision_json TEXT,
                action_json TEXT,
                learning_json TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ========================================================
    # NUMERAÇÃO
    # ========================================================

    def _next_cycle_number(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(
                MAX(cycle_number),
                0
            ) + 1
            FROM autonomous_cycle_runs
        """)

        number = cursor.fetchone()[0]

        conn.close()

        return number

    # ========================================================
    # EXECUÇÃO DO CICLO
    # ========================================================

    async def run_cycle(self):

        # ====================================================
        # KILL SWITCH — BARREIRA 1
        # ====================================================

        if emergency_shutdown.is_emergency_off():

            return {
                "status": "emergency_off",
                "executed": False,
                "message": (
                    "Ciclo bloqueado pelo "
                    "desligamento de segurança máxima."
                ),
            }

        # ====================================================
        # LOCK
        # ====================================================

        if self._lock.locked():

            return {
                "status": "busy",
                "executed": False,
                "message": (
                    "Um ciclo autônomo já está "
                    "em execução."
                ),
            }

        async with self._lock:

            # =================================================
            # KILL SWITCH — BARREIRA 2
            # =================================================

            if emergency_shutdown.is_emergency_off():

                return {
                    "status": "emergency_off",
                    "executed": False,
                    "message": (
                        "Ciclo bloqueado pelo "
                        "desligamento de segurança máxima."
                    ),
                }

            self.running = True

            cycle_number = (
                self._next_cycle_number()
            )

            started_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            try:

                # =============================================
                # 1. SUPERVISOR
                # =============================================

                supervisor_plan = (
                    supervisor.plan()
                )

                # =============================================
                # 2. DECISÃO AUTÔNOMA
                # =============================================

                decision = (
                    autonomous_action_orchestrator
                    .get_decision()
                )

                # =============================================
                # KILL SWITCH — BARREIRA 3
                # =============================================

                if emergency_shutdown.is_emergency_off():

                    result = {
                        "status": "emergency_off",
                        "executed": False,
                        "cycle_number": cycle_number,
                        "message": (
                            "Execução interrompida pelo "
                            "Kill Switch antes da produção."
                        ),
                    }

                    finished_at = (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    )

                    self._save_cycle(
                        cycle_number,
                        "emergency_off",
                        decision,
                        result,
                        {},
                        started_at,
                        finished_at,
                    )

                    return result

                # =============================================
                # 3. IDENTIFICAR A AÇÃO
                # =============================================

                action_name = None

                if isinstance(decision, dict):

                    action_name = (
                        decision.get("action")
                        or decision.get("decision")
                        or decision.get("next_action")
                    )

                # =============================================
                # 4. NOVA OPORTUNIDADE
                # =============================================

                discovery_actions = {
                    "discover_opportunity",
                    "discover_new_opportunity",
                }

                if action_name in discovery_actions:

                    # -----------------------------------------
                    # PRODUÇÃO COMPLETA
                    # -----------------------------------------

                    action = await (
                        autonomous_business_engine
                        .run_once()
                    )

                    execution_mode = (
                        "autonomous_business_engine"
                    )

                else:

                    # =========================================
                    # 5. AÇÃO OPERACIONAL
                    # =========================================

                    action = await (
                        autonomous_action_orchestrator
                        .execute_decision()
                    )

                    execution_mode = (
                        "autonomous_action_orchestrator"
                    )

                # =============================================
                # KILL SWITCH — BARREIRA 4
                # =============================================

                if emergency_shutdown.is_emergency_off():

                    result = {
                        "status": "emergency_off",
                        "executed": False,
                        "cycle_number": cycle_number,
                        "execution_mode": execution_mode,
                        "decision": decision,
                        "message": (
                            "Ciclo interrompido pelo "
                            "Kill Switch após a execução."
                        ),
                    }

                    finished_at = (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    )

                    self._save_cycle(
                        cycle_number,
                        "emergency_off",
                        decision,
                        action,
                        {},
                        started_at,
                        finished_at,
                    )

                    return result

                # =============================================
                # 6. APRENDIZADO
                # =============================================

                learning = (
                    learning_engine.learn()
                )

                # =============================================
                # 7. STATUS FINAL
                # =============================================

                action_status = (
                    action.get("status")
                    if isinstance(
                        action,
                        dict
                    )
                    else None
                )

                if action_status in {
                    "failed",
                    "error",
                }:

                    cycle_status = "failed"

                elif action_status == "blocked":

                    cycle_status = "blocked"

                elif action_status == "emergency_off":

                    cycle_status = "emergency_off"

                elif action_status == "busy":

                    cycle_status = "busy"

                else:

                    cycle_status = "completed"

                result = {
                    "status": cycle_status,
                    "executed": (
                        cycle_status
                        == "completed"
                    ),
                    "cycle_number": cycle_number,
                    "execution_mode": execution_mode,
                    "supervisor": supervisor_plan,
                    "decision": decision,
                    "action": action,
                    "learning": learning,
                }

                finished_at = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                self._save_cycle(
                    cycle_number,
                    cycle_status,
                    decision,
                    action,
                    learning,
                    started_at,
                    finished_at,
                )

                return result

            except Exception as exc:

                finished_at = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                result = {
                    "status": "failed",
                    "executed": False,
                    "cycle_number": cycle_number,
                    "error": str(exc),
                }

                self._save_cycle(
                    cycle_number,
                    "failed",
                    {},
                    result,
                    {},
                    started_at,
                    finished_at,
                )

                return result

            finally:

                self.running = False

    # ========================================================
    # SALVAR CICLO
    # ========================================================

    def _save_cycle(
        self,
        cycle_number,
        status,
        decision,
        action,
        learning,
        started_at,
        finished_at,
    ):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO autonomous_cycle_runs
            (
                cycle_number,
                status,
                decision_json,
                action_json,
                learning_json,
                started_at,
                finished_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cycle_number,
                status,
                json.dumps(
                    decision,
                    ensure_ascii=False,
                    default=str,
                ),
                json.dumps(
                    action,
                    ensure_ascii=False,
                    default=str,
                ),
                json.dumps(
                    learning,
                    ensure_ascii=False,
                    default=str,
                ),
                started_at,
                finished_at,
            ),
        )

        conn.commit()
        conn.close()

    # ========================================================
    # STATUS
    # ========================================================

    def status(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                cycle_number,
                status,
                started_at,
                finished_at
            FROM autonomous_cycle_runs
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()

        conn.close()

        return {
            "running": self.running,

            "locked": self._lock.locked(),

            "emergency_off": (
                emergency_shutdown
                .is_emergency_off()
            ),

            "total_cycles": len(rows),

            "cycles": [
                {
                    "id": row[0],
                    "cycle_number": row[1],
                    "status": row[2],
                    "started_at": row[3],
                    "finished_at": row[4],
                }
                for row in rows
            ],
        }

    # ========================================================
    # HISTÓRICO
    # ========================================================

    def history(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                cycle_number,
                status,
                decision_json,
                action_json,
                learning_json,
                started_at,
                finished_at
            FROM autonomous_cycle_runs
            ORDER BY id DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()

        conn.close()

        result = []

        for row in rows:

            def parse(value):

                try:
                    return json.loads(value)
                except Exception:
                    return value

            result.append(
                {
                    "id": row[0],
                    "cycle_number": row[1],
                    "status": row[2],
                    "decision": parse(row[3]),
                    "action": parse(row[4]),
                    "learning": parse(row[5]),
                    "started_at": row[6],
                    "finished_at": row[7],
                }
            )

        return result


autonomous_cycle_orchestrator = (
    AutonomousCycleOrchestrator()
)
