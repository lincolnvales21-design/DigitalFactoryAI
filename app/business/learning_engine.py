
import json
import sqlite3
from pathlib import Path
from datetime import datetime


from app.business.revenue_intelligence import revenue_intelligence


from app.business.optimization_engine import optimization_engine


class LearningEngine:
    """
    Analisa os resultados comerciais do DigitalFactoryAI
    e transforma dados históricos em decisões.

    Importante:
    - não movimenta dinheiro;
    - não executa investimentos;
    - apenas analisa e recomenda;
    - decisões podem alimentar os próximos ciclos.
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
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT NOT NULL,
                insight_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # DADOS DE PRODUTOS
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
                "price": row[3],
                "currency": row[4],
                "status": row[5],
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # DADOS DE PEDIDOS
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
                gateway,
                created_at,
                paid_at
            FROM orders
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "product_id": row[1],
                "amount": row[2],
                "currency": row[3],
                "status": row[4],
                "gateway": row[5],
                "created_at": row[6],
                "paid_at": row[7],
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # MÉTRICAS
    # --------------------------------------------------------

    def metrics(self):
        products = self._products()
        orders = self._orders()

        total_orders = len(orders)
        paid_orders = [
            order
            for order in orders
            if order["status"] == "paid"
        ]

        pending_orders = [
            order
            for order in orders
            if order["status"] == "pending"
        ]

        total_revenue = sum(
            float(order["amount"] or 0)
            for order in paid_orders
        )

        paid_count = len(paid_orders)

        conversion = (
            paid_count / total_orders
            if total_orders
            else 0
        )

        product_sales = {}

        for order in paid_orders:
            product_id = order["product_id"]

            product_sales[product_id] = (
                product_sales.get(product_id, 0) + 1
            )

        published = [
            product
            for product in products
            if product["status"] == "published"
        ]

        return {
            "total_products": len(products),
            "published_products": len(published),
            "total_orders": total_orders,
            "paid_orders": paid_count,
            "pending_orders": len(pending_orders),
            "conversion_rate": round(
                conversion,
                4
            ),
            "total_revenue": round(
                total_revenue,
                2
            ),
            "product_sales": product_sales,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # --------------------------------------------------------
    # DESEMPENHO POR PRODUTO
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

            revenue = sum(
                float(order["amount"] or 0)
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
                "revenue": round(revenue, 2),
            })

        return result

    # --------------------------------------------------------
    # DECISÃO
    # --------------------------------------------------------

    def decide(self):
        metrics = self.metrics()
        performance = self.product_performance()

        winners = [
            item
            for item in performance
            if item["sales"] > 0
        ]

        candidates = [
            item
            for item in performance
            if item["status"] == "published"
            and item["sales"] == 0
        ]

        if winners:
            best = sorted(
                winners,
                key=lambda item: (
                    item["sales"],
                    item["revenue"],
                ),
                reverse=True,
            )[0]
        else:
            best = None

        if best:
            next_action = "scale_winner"
            reason = (
                "Existe produto com venda confirmada. "
                "Priorizar variações, melhoria da oferta "
                "e exploração do mesmo problema."
            )
        elif candidates:
            next_action = "optimize_validation"
            reason = (
                "Existem produtos publicados sem venda "
                "confirmada. Melhorar oferta, posicionamento "
                "e validação antes de criar volume."
            )
        else:
            next_action = "discover_new_opportunity"
            reason = (
                "Não existe sinal comercial suficiente. "
                "Buscar nova oportunidade com tese comercial."
            )

        decision = {
            "next_action": next_action,
            "reason": reason,
            "best_product": best,
            "metrics": metrics,
            "signals": {
                "winning_products": len(winners),
                "products_without_sales": len(candidates),
            },
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "owner_controls_capital": True,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        self._save_insight(
            "decision",
            decision
        )

        return decision

    # --------------------------------------------------------
    # SALVAR APRENDIZADO
    # --------------------------------------------------------

    def _save_insight(self, insight_type, data):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO learning_insights
            (
                insight_type,
                insight_json,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            insight_type,
            json.dumps(
                data,
                ensure_ascii=False
            ),
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # RESUMO
    # --------------------------------------------------------

    def learn(self):
        decision = self.decide()
        revenue = revenue_intelligence.analyze()

        return {
            "status": "learned",
            "supervisor_decision": decision.get("next_action"),
            "decision": decision,
            "revenue_analysis": revenue,
            "optimization": optimization_engine.next_move(),
        }

    def status(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                insight_type,
                insight_json,
                created_at
            FROM learning_insights
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            try:
                data = json.loads(row[2])
            except Exception:
                data = row[2]

            result.append({
                "id": row[0],
                "type": row[1],
                "data": data,
                "created_at": row[3],
            })

        return result


learning_engine = LearningEngine()
