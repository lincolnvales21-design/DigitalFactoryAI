
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class RevenueIntelligence:
    """
    Analisa o desempenho econômico do DigitalFactoryAI.

    Importante:
    - somente analisa dados;
    - não movimenta dinheiro;
    - não investe;
    - não cria anúncios pagos;
    - produz recomendações para o sistema.
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
            CREATE TABLE IF NOT EXISTS revenue_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # PRODUTOS
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

        return [
            {
                "id": row[0],
                "name": row[1],
                "product_type": row[2],
                "price": float(row[3] or 0),
                "currency": row[4],
                "status": row[5],
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # PEDIDOS
    # --------------------------------------------------------

    def _orders(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                product_id,
                amount,
                currency,
                status,
                gateway
            FROM orders
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "product_id": row[1],
                "amount": float(row[2] or 0),
                "currency": row[3],
                "status": row[4],
                "gateway": row[5],
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # RECEITA POR MOEDA
    # --------------------------------------------------------

    def revenue_by_currency(self):
        orders = self._orders()

        result = {}

        for order in orders:
            if order["status"] != "paid":
                continue

            currency = order["currency"] or "UNKNOWN"

            result.setdefault(
                currency,
                {
                    "orders": 0,
                    "revenue": 0.0,
                }
            )

            result[currency]["orders"] += 1
            result[currency]["revenue"] += order["amount"]

        for currency in result:
            result[currency]["revenue"] = round(
                result[currency]["revenue"],
                2
            )

        return result

    # --------------------------------------------------------
    # TICKET MÉDIO
    # --------------------------------------------------------

    def average_ticket(self):
        orders = [
            order
            for order in self._orders()
            if order["status"] == "paid"
        ]

        by_currency = {}

        for order in orders:
            currency = order["currency"] or "UNKNOWN"

            by_currency.setdefault(
                currency,
                []
            )

            by_currency[currency].append(
                order["amount"]
            )

        result = {}

        for currency, values in by_currency.items():
            result[currency] = round(
                sum(values) / len(values),
                2
            )

        return result

    # --------------------------------------------------------
    # DESEMPENHO DOS PRODUTOS
    # --------------------------------------------------------

    def product_performance(self):
        products = self._products()
        orders = self._orders()

        result = []

        for product in products:
            related = [
                order
                for order in orders
                if order["product_id"] == product["id"]
            ]

            paid = [
                order
                for order in related
                if order["status"] == "paid"
            ]

            pending = [
                order
                for order in related
                if order["status"] == "pending"
            ]

            revenue = sum(
                order["amount"]
                for order in paid
            )

            result.append({
                "product_id": product["id"],
                "name": product["name"],
                "product_type": product["product_type"],
                "price": product["price"],
                "currency": product["currency"],
                "status": product["status"],
                "orders": len(related),
                "sales": len(paid),
                "pending": len(pending),
                "revenue": round(revenue, 2),
            })

        return result

    # --------------------------------------------------------
    # DESEMPENHO POR FORMATO
    # --------------------------------------------------------

    def format_performance(self):
        products = self._products()
        orders = self._orders()

        result = {}

        for product in products:
            product_type = product["product_type"] or "unknown"

            if product_type not in result:
                result[product_type] = {
                    "products": 0,
                    "orders": 0,
                    "sales": 0,
                    "revenue": 0.0,
                }

            result[product_type]["products"] += 1

            related = [
                order
                for order in orders
                if order["product_id"] == product["id"]
            ]

            for order in related:
                result[product_type]["orders"] += 1

                if order["status"] == "paid":
                    result[product_type]["sales"] += 1
                    result[product_type]["revenue"] += (
                        order["amount"]
                    )

        for product_type in result:
            result[product_type]["revenue"] = round(
                result[product_type]["revenue"],
                2
            )

        return result

    # --------------------------------------------------------
    # PRIORIDADE COMERCIAL
    # --------------------------------------------------------

    def commercial_priorities(self):
        performance = self.product_performance()

        priorities = []

        for item in performance:
            if item["sales"] > 0:
                score = (
                    100
                    + item["sales"] * 20
                    + item["revenue"]
                )

                action = "expand"

            elif item["orders"] > 0:
                score = 60 + item["orders"] * 10
                action = "optimize_conversion"

            elif item["status"] == "published":
                score = 30
                action = "improve_validation"

            else:
                score = 10
                action = "not_prioritized"

            priorities.append({
                "product_id": item["product_id"],
                "name": item["name"],
                "score": round(score, 2),
                "recommended_action": action,
            })

        return sorted(
            priorities,
            key=lambda x: x["score"],
            reverse=True
        )

    # --------------------------------------------------------
    # DECISÃO ECONÔMICA
    # --------------------------------------------------------

    def analyze(self):
        performance = self.product_performance()
        priorities = self.commercial_priorities()

        winners = [
            item
            for item in performance
            if item["sales"] > 0
        ]

        pending_signal = [
            item
            for item in performance
            if item["pending"] > 0
        ]

        if winners:
            best = sorted(
                winners,
                key=lambda x: (
                    x["sales"],
                    x["revenue"],
                ),
                reverse=True,
            )[0]

            next_move = "expand_winner"

            reason = (
                "Existe produto com receita confirmada. "
                "Priorizar expansão, variações e melhoria "
                "da oferta vencedora."
            )

        elif pending_signal:
            best = None

            next_move = "recover_pending_demand"

            reason = (
                "Existem pedidos pendentes. "
                "Priorizar recuperação e conversão antes "
                "de aumentar a produção."
            )

        else:
            best = None

            next_move = "find_new_opportunity"

            reason = (
                "Não existe receita confirmada suficiente. "
                "Priorizar novas oportunidades e validação."
            )

        analysis = {
            "status": "analyzed",
            "next_move": next_move,
            "reason": reason,
            "best_product": best,
            "revenue_by_currency": (
                self.revenue_by_currency()
            ),
            "average_ticket": self.average_ticket(),
            "product_performance": performance,
            "format_performance": (
                self.format_performance()
            ),
            "commercial_priorities": priorities,
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "automatic_ads": False,
                "owner_controls_capital": True,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        self._save(analysis)

        return analysis

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    def _save(self, analysis):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO revenue_insights
            (
                insight_json,
                created_at
            )
            VALUES (?, ?)
        """, (
            json.dumps(
                analysis,
                ensure_ascii=False
            ),
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

    def history(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                insight_json,
                created_at
            FROM revenue_insights
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            try:
                data = json.loads(row[1])
            except Exception:
                data = row[1]

            result.append({
                "id": row[0],
                "data": data,
                "created_at": row[2],
            })

        return result


revenue_intelligence = RevenueIntelligence()
