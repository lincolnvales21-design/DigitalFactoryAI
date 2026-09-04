
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class ActionExecutionEngine:
    """
    Transforma decisões autônomas em ações operacionais.

    Política financeira:
    - receita <= R$1.000 -> nenhum gasto automático;
    - receita > R$1.000 -> máximo R$100 de gasto automático;
    - nunca ultrapassa o teto autorizado;
    - pagamentos e recebimentos existentes não são alterados.
    """

    AUTOMATIC_REVENUE_THRESHOLD = 1000.0
    AUTOMATIC_SPEND_LIMIT = 100.0

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                product_id INTEGER,
                status TEXT NOT NULL,
                estimated_cost REAL DEFAULT 0,
                approved_cost REAL DEFAULT 0,
                reason TEXT,
                result_json TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # RECEITA
    # --------------------------------------------------------

    def _revenue_brl(self):
        """
        Calcula receita confirmada em BRL.

        Moedas estrangeiras não são convertidas automaticamente
        nesta camada. Elas ficam fora do cálculo de autorização
        financeira para evitar conversões incorretas.
        """

        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM orders
                WHERE status = 'paid'
                AND currency = 'BRL'
            """)

            value = cursor.fetchone()[0] or 0

            conn.close()

            return float(value)

        except Exception:
            return 0.0

    # --------------------------------------------------------
    # POLÍTICA DE CAPITAL
    # --------------------------------------------------------

    def capital_policy(self):
        revenue = self._revenue_brl()

        if revenue > self.AUTOMATIC_REVENUE_THRESHOLD:
            automatic_spend_allowed = True
            maximum = self.AUTOMATIC_SPEND_LIMIT
        else:
            automatic_spend_allowed = False
            maximum = 0.0

        return {
            "revenue_brl": round(revenue, 2),
            "revenue_threshold_brl": (
                self.AUTOMATIC_REVENUE_THRESHOLD
            ),
            "automatic_spend_allowed": (
                automatic_spend_allowed
            ),
            "automatic_spend_limit_brl": maximum,
            "owner_controls_capital": True,
        }

    # --------------------------------------------------------
    # AÇÕES SEM CUSTO
    # --------------------------------------------------------

    def _execute_free_action(
        self,
        action,
        product_id=None,
    ):
        actions = {
            "expand_product": (
                "Preparar expansão do produto vencedor."
            ),
            "create_product_variation": (
                "Preparar variação do produto."
            ),
            "optimize_conversion": (
                "Preparar otimização de conversão."
            ),
            "optimize_offer": (
                "Preparar otimização da oferta."
            ),
            "validate_product": (
                "Preparar nova validação comercial."
            ),
            "discover_opportunity": (
                "Preparar descoberta de nova oportunidade."
            ),
        }

        return {
            "status": "prepared",
            "action": action,
            "product_id": product_id,
            "description": actions.get(
                action,
                "Ação operacional preparada."
            ),
            "cost": 0.0,
        }

    # --------------------------------------------------------
    # AUTORIZAÇÃO DE GASTO
    # --------------------------------------------------------

    def authorize_spend(self, requested_amount):
        policy = self.capital_policy()

        requested = max(
            0.0,
            float(requested_amount or 0)
        )

        if not policy["automatic_spend_allowed"]:
            return {
                "authorized": False,
                "requested_brl": requested,
                "approved_brl": 0.0,
                "reason": (
                    "Receita confirmada ainda não ultrapassou "
                    "R$1.000."
                ),
            }

        approved = min(
            requested,
            self.AUTOMATIC_SPEND_LIMIT
        )

        return {
            "authorized": approved > 0,
            "requested_brl": round(requested, 2),
            "approved_brl": round(approved, 2),
            "reason": (
                "Gasto autorizado dentro do limite automático "
                "de R$100 após receita superior a R$1.000."
            ),
        }

    # --------------------------------------------------------
    # EXECUÇÃO DE DECISÃO
    # --------------------------------------------------------

    async def execute(
        self,
        action,
        product_id=None,
        estimated_cost=0.0,
    ):
        policy = self.capital_policy()

        estimated_cost = max(
            0.0,
            float(estimated_cost or 0)
        )

        # Ações gratuitas nunca precisam de autorização financeira.
        if estimated_cost == 0:
            result = self._execute_free_action(
                action,
                product_id
            )

            self._log(
                action=action,
                product_id=product_id,
                status="prepared",
                estimated_cost=0,
                approved_cost=0,
                reason=(
                    "Ação sem custo financeiro automático."
                ),
                result=result,
            )

            return {
                "status": "executed",
                "result": result,
                "capital_policy": policy,
            }

        # Ações com custo passam pela política.
        authorization = self.authorize_spend(
            estimated_cost
        )

        if not authorization["authorized"]:
            result = {
                "status": "blocked",
                "action": action,
                "product_id": product_id,
                "requested_cost": estimated_cost,
                "approved_cost": 0.0,
                "reason": authorization["reason"],
            }

            self._log(
                action=action,
                product_id=product_id,
                status="blocked",
                estimated_cost=estimated_cost,
                approved_cost=0,
                reason=authorization["reason"],
                result=result,
            )

            return {
                "status": "blocked",
                "result": result,
                "capital_policy": policy,
            }

        approved = authorization["approved_brl"]

        result = {
            "status": "authorized",
            "action": action,
            "product_id": product_id,
            "requested_cost": estimated_cost,
            "approved_cost": approved,
            "execution_requires_provider": True,
            "reason": (
                "Ação financeira autorizada pelo limite "
                "automático do sistema."
            ),
        }

        self._log(
            action=action,
            product_id=product_id,
            status="authorized",
            estimated_cost=estimated_cost,
            approved_cost=approved,
            reason=result["reason"],
            result=result,
        )

        return {
            "status": "authorized",
            "result": result,
            "capital_policy": policy,
        }

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    def _log(
        self,
        action,
        product_id,
        status,
        estimated_cost,
        approved_cost,
        reason,
        result,
    ):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO action_execution_log
            (
                action,
                product_id,
                status,
                estimated_cost,
                approved_cost,
                reason,
                result_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action,
            product_id,
            status,
            estimated_cost,
            approved_cost,
            reason,
            json.dumps(
                result,
                ensure_ascii=False
            ),
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    def history(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                action,
                product_id,
                status,
                estimated_cost,
                approved_cost,
                reason,
                result_json,
                created_at
            FROM action_execution_log
            ORDER BY id DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            try:
                data = json.loads(row[7])
            except Exception:
                data = row[7]

            result.append({
                "id": row[0],
                "action": row[1],
                "product_id": row[2],
                "status": row[3],
                "estimated_cost": row[4],
                "approved_cost": row[5],
                "reason": row[6],
                "result": data,
                "created_at": row[8],
            })

        return result


action_execution_engine = ActionExecutionEngine()
