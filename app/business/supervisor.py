
import json
import sqlite3
from pathlib import Path
from datetime import datetime


from app.business.optimization_engine import optimization_engine


class AutonomousSupervisor:
    """
    Supervisor central do DigitalFactoryAI.

    Responsabilidades:
    - observar o aprendizado;
    - decidir se um novo ciclo deve ser iniciado;
    - iniciar um ciclo autônomo;
    - registrar a decisão;
    - impedir execução concorrente;
    - nunca movimentar capital automaticamente.

    Política:
    - capital = sempre controlado pelo proprietário;
    - investimento automático = proibido;
    - gasto automático = proibido;
    - execução contínua = controlada;
    """

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()
        self.running = False

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supervisor_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision TEXT NOT NULL,
                reason TEXT,
                action TEXT,
                decision_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # APRENDIZADO
    # --------------------------------------------------------

    def _latest_learning(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                insight_json
            FROM learning_insights
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        try:
            return json.loads(row[0])
        except Exception:
            return None

    # --------------------------------------------------------
    # CICLOS
    # --------------------------------------------------------

    def _latest_cycle(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                status,
                objective,
                started_at,
                completed_at
            FROM autonomous_cycles
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "status": row[1],
            "objective": row[2],
            "started_at": row[3],
            "completed_at": row[4],
        }

    # --------------------------------------------------------
    # DECISÃO
    # --------------------------------------------------------

    def decide(self):
        learning = self._latest_learning()
        latest_cycle = self._latest_cycle()

        if not learning:
            decision = {
                "decision": "start_cycle",
                "reason": (
                    "Ainda não existe aprendizado suficiente. "
                    "Iniciar ciclo para gerar dados comerciais."
                ),
                "action": "run_cycle",
            }

        else:
            next_action = learning.get(
                "next_action",
                "discover_new_opportunity"
            )

            if next_action == "scale_winner":
                action = "run_cycle"

                reason = (
                    "Existe sinal comercial positivo. "
                    "O próximo ciclo deve explorar o problema "
                    "e a oportunidade vencedora."
                )

            elif next_action == "optimize_validation":
                action = "run_cycle"

                reason = (
                    "Existem produtos publicados sem vendas. "
                    "O próximo ciclo deve melhorar validação, "
                    "posicionamento e oferta."
                )

            else:
                action = "run_cycle"

                reason = (
                    "É necessário descobrir uma nova oportunidade "
                    "com tese comercial."
                )

            decision = {
                "decision": "continue_business",
                "reason": reason,
                "action": action,
                "learning_action": next_action,
                "best_product": learning.get(
                    "best_product"
                ),
            }

        # Proteção contra ciclo concorrente.
        if latest_cycle:
            if latest_cycle["status"] == "running":
                decision["decision"] = "wait"
                decision["action"] = "none"
                decision["reason"] = (
                    "Já existe um ciclo autônomo em execução."
                )

        # Política financeira permanente.
        decision["capital_policy"] = {
            "automatic_investment": False,
            "automatic_spending": False,
            "automatic_ads": False,
            "owner_controls_capital": True,
        }

        self._save_decision(decision)

        return decision

    # --------------------------------------------------------
    # EXECUÇÃO
    # --------------------------------------------------------

    async def run_cycle(self):
        if self.running:
            return {
                "status": "blocked",
                "reason": "supervisor_already_running",
            }

        decision = self.decide()

        if decision["action"] != "run_cycle":
            return {
                "status": "waiting",
                "decision": decision,
            }

        self.running = True

        try:
            from app.business.autonomous_engine import (
                autonomous_business_engine
            )

            result = await autonomous_business_engine.run_once()

            return {
                "status": "cycle_started",
                "decision": decision,
                "cycle": result,
                "capital_policy": decision[
                    "capital_policy"
                ],
                "executed_at": datetime.utcnow().isoformat(),
            }

        finally:
            self.running = False

    # --------------------------------------------------------
    # DECISÃO AUTOMÁTICA SEM EXECUTAR
    # --------------------------------------------------------

    def plan(self):
        decision = self.decide()

        return {
            "status": "planned",
            "decision": decision,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    def _save_decision(self, decision):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO supervisor_decisions
            (
                decision,
                reason,
                action,
                decision_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            decision.get("decision"),
            decision.get("reason"),
            decision.get("action"),
            json.dumps(
                decision,
                ensure_ascii=False
            ),
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

    def status(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                decision,
                reason,
                action,
                decision_json,
                created_at
            FROM supervisor_decisions
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            try:
                data = json.loads(row[4])
            except Exception:
                data = row[4]

            result.append({
                "id": row[0],
                "decision": row[1],
                "reason": row[2],
                "action": row[3],
                "data": data,
                "created_at": row[5],
            })

        return result


autonomous_supervisor = AutonomousSupervisor()

# Alias de compatibilidade para os orquestradores.
supervisor = autonomous_supervisor
