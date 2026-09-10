import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class AutonomousCycleGate:
    """
    Porta de decisão do ciclo autônomo.

    Decide o próximo movimento da fábrica:

      wait
      expand_winner
      validate_product
      optimize_offer
      discover_opportunity

    Também controla estagnação:
      - evita repetir indefinidamente a mesma decisão;
      - permite mudança de estratégia;
      - permite descoberta de nova oportunidade quando
        um produto não evolui após várias tentativas.

    Esta camada NÃO executa ações e NÃO autoriza gastos.

    Controle financeiro permanece no
    ActionExecutionEngine.
    """

    MAX_REPEATED_DECISIONS = 3

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_cycle_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                product_id INTEGER,
                confidence REAL NOT NULL,
                should_run INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # DADOS
    # --------------------------------------------------------

    def _products(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                product_type,
                price,
                currency,
                status
            FROM products
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows

    def _orders(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                product_id,
                amount,
                currency,
                status
            FROM orders
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows

    # --------------------------------------------------------
    # UTILITÁRIOS
    # --------------------------------------------------------

    @staticmethod
    def _is_status(value, expected):
        return str(value).strip().lower() == expected

    def _published_products(self, products):
        return [
            product
            for product in products
            if self._is_status(product[5], "published")
        ]

    def _paid_orders(self, orders):
        return [
            order
            for order in orders
            if self._is_status(order[4], "paid")
        ]

    def _pending_orders(self, orders):
        return [
            order
            for order in orders
            if self._is_status(order[4], "pending")
        ]

    def _sales_by_product(self, paid_orders):
        sales = {}

        for order in paid_orders:
            product_id = order[1]

            if product_id is None:
                continue

            sales[product_id] = sales.get(product_id, 0) + 1

        return sales

    def _find_winner(self, sales_by_product, published_products):
        published_ids = {
            product[0]
            for product in published_products
        }

        candidates = [
            (product_id, sales)
            for product_id, sales in sales_by_product.items()
            if product_id in published_ids
        ]

        if not candidates:
            return None, 0

        candidates.sort(
            key=lambda item: (-item[1], item[0])
        )

        return candidates[0]

    # --------------------------------------------------------
    # ANTI-REPETIÇÃO
    # --------------------------------------------------------

    def _recent_decisions(self, limit=3):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                decision,
                product_id
            FROM autonomous_cycle_gates
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return rows

    def _is_repeating(self, decision, product_id):
        recent = self._recent_decisions(
            self.MAX_REPEATED_DECISIONS
        )

        if len(recent) < self.MAX_REPEATED_DECISIONS:
            return False

        return all(
            row[0] == decision
            and row[1] == product_id
            for row in recent
        )

    # --------------------------------------------------------
    # ANÁLISE
    # --------------------------------------------------------

    def analyze(self):
        products = self._products()
        orders = self._orders()

        published = self._published_products(products)
        paid = self._paid_orders(orders)
        pending = self._pending_orders(orders)

        sales_by_product = self._sales_by_product(paid)

        winner_id, winner_sales = self._find_winner(
            sales_by_product,
            published,
        )

        # ----------------------------------------------------
        # REGRA 1 — PEDIDOS PENDENTES
        # ----------------------------------------------------

        if pending:

            result = {
                "decision": "wait",
                "reason": (
                    "Existem pedidos pendentes. "
                    "O sistema deve aguardar a confirmação "
                    "dos pagamentos antes de tomar novas "
                    "decisões de expansão ou criação."
                ),
                "product_id": None,
                "confidence": 0.90,
                "should_run": False,
            }

            self._save(result)
            return result

        # ----------------------------------------------------
        # REGRA 2 — VENCEDOR
        # ----------------------------------------------------

        if winner_id is not None and winner_sales >= 2:

            result = {
                "decision": "expand_winner",
                "reason": (
                    f"O produto #{winner_id} possui "
                    f"{winner_sales} vendas confirmadas. "
                    "Existe evidência comercial suficiente "
                    "para considerar expansão."
                ),
                "product_id": winner_id,
                "confidence": min(
                    1.0,
                    0.75 + winner_sales * 0.05,
                ),
                "should_run": True,
            }

            self._save(result)
            return result

        # ----------------------------------------------------
        # REGRA 3 — UMA VENDA
        # ----------------------------------------------------

        if winner_id is not None and winner_sales == 1:

            result = {
                "decision": "validate_product",
                "reason": (
                    f"O produto #{winner_id} possui uma venda "
                    "confirmada. Há sinal comercial, mas ainda "
                    "não existe evidência suficiente para "
                    "expansão."
                ),
                "product_id": winner_id,
                "confidence": 0.70,
                "should_run": True,
            }

            self._save(result)
            return result

        # ----------------------------------------------------
        # REGRA 4 — PRODUTO PUBLICADO SEM VENDAS
        # ----------------------------------------------------

        if published:

            target = sorted(
                published,
                key=lambda product: product[0],
                reverse=True,
            )[0]

            product_id = target[0]

            # ------------------------------------------------
            # DETECÇÃO DE ESTAGNAÇÃO
            # ------------------------------------------------

            if self._is_repeating(
                "optimize_offer",
                product_id,
            ):

                result = {
                    "decision": "discover_opportunity",
                    "reason": (
                        f"O produto #{product_id} permaneceu "
                        "sem vendas após repetidas tentativas "
                        "de otimização da oferta. "
                        "A fábrica deve mudar de estratégia e "
                        "descobrir uma nova oportunidade."
                    ),
                    "product_id": None,
                    "confidence": 0.85,
                    "should_run": True,
                    "evolution": {
                        "stagnation_detected": True,
                        "previous_action": "optimize_offer",
                        "repeated_decisions": (
                            self.MAX_REPEATED_DECISIONS
                        ),
                    },
                }

                self._save(result)
                return result

            # ------------------------------------------------
            # OTIMIZAÇÃO NORMAL
            # ------------------------------------------------

            result = {
                "decision": "optimize_offer",
                "reason": (
                    f"O produto #{product_id} está publicado "
                    "sem vendas confirmadas. "
                    "A oferta deve ser otimizada antes de "
                    "considerar expansão."
                ),
                "product_id": product_id,
                "confidence": 0.65,
                "should_run": True,
                "evolution": {
                    "stagnation_detected": False,
                },
            }

            self._save(result)
            return result

        # ----------------------------------------------------
        # REGRA 5 — NENHUM PRODUTO PUBLICADO
        # ----------------------------------------------------

        result = {
            "decision": "discover_opportunity",
            "reason": (
                "Não existem produtos publicados. "
                "O próximo ciclo deve descobrir uma nova "
                "oportunidade comercial."
            ),
            "product_id": None,
            "confidence": 0.95,
            "should_run": True,
            "evolution": {
                "stagnation_detected": False,
            },
        }

        self._save(result)
        return result

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    def _save(self, result):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO autonomous_cycle_gates
            (
                decision,
                reason,
                product_id,
                confidence,
                should_run,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            result["decision"],
            result["reason"],
            result.get("product_id"),
            result["confidence"],
            1 if result["should_run"] else 0,
            datetime.now(timezone.utc).isoformat(),
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
                decision,
                reason,
                product_id,
                confidence,
                should_run,
                created_at
            FROM autonomous_cycle_gates
            ORDER BY id DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "decision": row[1],
                "reason": row[2],
                "product_id": row[3],
                "confidence": row[4],
                "should_run": bool(row[5]),
                "created_at": row[6],
            }
            for row in rows
        ]


autonomous_cycle_gate = AutonomousCycleGate()
