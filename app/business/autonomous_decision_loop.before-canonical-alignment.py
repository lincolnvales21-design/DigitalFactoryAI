import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.business.autonomous_cycle_gate import autonomous_cycle_gate
from app.business.optimization_engine import optimization_engine
from app.business.revenue_intelligence import revenue_intelligence


class AutonomousDecisionLoop:
    """
    Decisão central do DigitalFactoryAI.

    O Cycle Gate define a direção soberana do próximo ciclo.
    Revenue Intelligence e Optimization fornecem contexto
    econômico e operacional complementar.

    Esta camada:
      - não movimenta capital
      - não autoriza gastos
      - não executa agentes
      - não publica produtos

    Ela somente transforma sinais em uma decisão de ciclo.
    """

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                product_id INTEGER,
                reason TEXT,
                decision_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # DECISÃO CENTRAL
    # --------------------------------------------------------

    def decide(self):
        # ----------------------------------------------------
        # 1. GATE — FONTE PRINCIPAL DA DECISÃO
        # ----------------------------------------------------

        gate = autonomous_cycle_gate.analyze()

        # ----------------------------------------------------
        # 2. INTELIGÊNCIA COMPLEMENTAR
        # ----------------------------------------------------

        try:
            revenue = revenue_intelligence.analyze()
        except Exception:
            revenue = {}

        try:
            optimization = optimization_engine.next_move()
        except Exception:
            optimization = {}

        gate_decision = gate.get(
            "decision",
            "discover_opportunity",
        )

        product_id = gate.get("product_id")

        # ----------------------------------------------------
        # MAPA DO GATE → AÇÃO DO CICLO
        # ----------------------------------------------------

        cycle_action_map = {
            "wait": "wait",
            "expand_winner": "expand_product",
            "validate_product": "validate_product",
            "optimize_offer": "optimize_offer",
            "discover_opportunity": "discover_opportunity",
        }

        cycle_action = cycle_action_map.get(
            gate_decision,
            "wait",
        )

        # ----------------------------------------------------
        # CONTEXTO DO PRODUTO
        # ----------------------------------------------------

        product = None

        if product_id is not None:
            try:
                product = optimization.get("product")
            except Exception:
                product = None

        # ----------------------------------------------------
        # DECISÃO FINAL
        # ----------------------------------------------------

        decision = {
            "status": "decision_ready",
            "gate_decision": gate_decision,
            "cycle_action": cycle_action,
            "product_id": product_id,
            "product": product,
            "reason": gate.get(
                "reason",
                "Decisão definida pelo Cycle Gate.",
            ),
            "confidence": gate.get(
                "confidence",
                0.0,
            ),
            "should_run": bool(
                gate.get("should_run", False)
            ),
            "revenue_signal": revenue.get(
                "next_move"
            ),
            "optimization_signal": optimization.get(
                "action"
            ),
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "automatic_ads": False,
                "owner_controls_capital": True,
                "automatic_revenue_threshold_brl": 1000.0,
                "automatic_spend_limit_brl": 100.0,
            },
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._save(decision)

        return decision

    # --------------------------------------------------------
    # OBJETIVO DO PRÓXIMO CICLO
    # --------------------------------------------------------

    def build_cycle_objective(self):
        decision = self.decide()

        action = decision["cycle_action"]
        product_id = decision.get("product_id")
        product = decision.get("product")

        product_label = (
            f"#{product_id} ({product})"
            if product_id is not None
            else "sem produto específico"
        )

        if action == "wait":

            objective = (
                "Aguardar a confirmação dos pedidos "
                "pendentes. Não criar produtos, não "
                "expandir e não alterar capital."
            )

        elif action == "expand_product":

            objective = (
                f"Expandir o produto vencedor "
                f"{product_label}. "
                "Criar uma nova oportunidade comercial "
                "relacionada ao problema validado, "
                "preservando diferenciação."
            )

        elif action == "validate_product":

            objective = (
                f"Validar comercialmente o produto "
                f"{product_label} antes de qualquer expansão."
            )

        elif action == "optimize_offer":

            objective = (
                f"Otimizar a oferta do produto "
                f"{product_label}. "
                "Melhorar posicionamento, proposta de valor, "
                "benefícios, objeções, copy e chamada para ação "
                "antes de criar novos produtos."
            )

        else:

            objective = (
                "Descobrir uma nova oportunidade comercial "
                "com potencial de produto digital diferenciado. "
                "Só produzir após validar a tese comercial."
            )

        return {
            "decision": decision,
            "objective": objective,
        }

    # --------------------------------------------------------
    # PREPARAÇÃO DO CICLO
    # --------------------------------------------------------

    async def execute_next_cycle(self):
        plan = self.build_cycle_objective()

        decision = plan["decision"]

        return {
            "status": (
                "cycle_ready"
                if decision["should_run"]
                else "cycle_wait"
            ),
            "objective": plan["objective"],
            "decision": decision,
            "execution": {
                "automatic_execution_enabled": False,
                "reason": (
                    "A decisão foi preparada. "
                    "A execução financeira permanece "
                    "sob controle exclusivo do proprietário."
                ),
            },
        }

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    def _save(self, decision):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO autonomous_decisions
            (
                action,
                product_id,
                reason,
                decision_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            decision.get(
                "cycle_action",
                "unknown",
            ),
            decision.get("product_id"),
            decision.get("reason"),
            json.dumps(
                decision,
                ensure_ascii=False,
            ),
            datetime.now(
                timezone.utc
            ).isoformat(),
        ))

        conn.commit()
        conn.close()

    def history(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                action,
                product_id,
                reason,
                decision_json,
                created_at
            FROM autonomous_decisions
            ORDER BY id DESC
            LIMIT 50
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            try:
                decision = json.loads(row[4])
            except Exception:
                decision = row[4]

            result.append({
                "id": row[0],
                "action": row[1],
                "product_id": row[2],
                "reason": row[3],
                "decision": decision,
                "created_at": row[5],
            })

        return result


autonomous_decision_loop = AutonomousDecisionLoop()
