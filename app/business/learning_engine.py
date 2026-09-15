
import json
import sqlite3
from pathlib import Path

from app.business.acquisition_tracker import acquisition_tracker
from app.business.publication_tracker import publication_tracker
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
                status,
                is_test
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
                "is_test": bool(row[6]),
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
        products = [
            product
            for product in self._products()
            if not product.get("is_test")
        ]

        valid_product_ids = {
            product["id"]
            for product in products
        }

        orders = [
            order
            for order in self._orders()
            if order["product_id"] in valid_product_ids
        ]

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
        products = [
            product
            for product in self._products()
            if not product.get("is_test")
        ]

        valid_product_ids = {
            product["id"]
            for product in products
        }

        orders = [
            order
            for order in self._orders()
            if order["product_id"] in valid_product_ids
        ]

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
                "is_test": product.get("is_test", False),
                "orders": len(related),
                "sales": len(paid),
                "revenue": round(revenue, 2),
            })

        return result

    # --------------------------------------------------------
    # INTELIGÊNCIA DE AQUISIÇÃO
    # --------------------------------------------------------

    def acquisition_intelligence(self):
        """
        Analisa aquisição comercial excluindo permanentemente
        produtos marcados como teste.

        A inteligência global do AcquisitionTracker não deve
        permitir que dados históricos de produtos de teste
        contaminem decisões autônomas.
        """

        try:
            products = self._products()

            test_product_ids = {
                int(product["id"])
                for product in products
                if bool(product.get("is_test"))
            }

            # Consulta diretamente os eventos para preservar
            # product_id e permitir filtragem correta.
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    product_id,
                    channel,
                    source,
                    campaign,
                    medium,
                    event_type,
                    COUNT(*) AS events,
                    COUNT(
                        CASE
                            WHEN event_type IN ('order', 'sale')
                            THEN 1
                        END
                    ) AS orders,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN event_type = 'sale'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS revenue
                FROM acquisition_events
                GROUP BY
                    product_id,
                    channel,
                    source,
                    campaign,
                    medium,
                    event_type
                ORDER BY revenue DESC, events DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            channels = []

            for row in rows:
                (
                    product_id,
                    channel,
                    source,
                    campaign,
                    medium,
                    event_type,
                    events,
                    orders,
                    revenue,
                ) = row

                if product_id is not None and int(product_id) in test_product_ids:
                    continue

                events = int(events or 0)
                orders = int(orders or 0)
                revenue = float(revenue or 0)

                conversion = (
                    (orders / events) * 100
                    if events > 0
                    else 0
                )

                if revenue > 0:
                    classification = "winner"
                    priority = 100
                elif orders > 0:
                    classification = "promising"
                    priority = 70
                elif events >= 5:
                    classification = "weak"
                    priority = 30
                else:
                    classification = "insufficient_data"
                    priority = 10

                channels.append({
                    "product_id": product_id,
                    "channel": channel,
                    "source": source,
                    "campaign": campaign,
                    "medium": medium,
                    "event_type": event_type,
                    "events": events,
                    "orders": orders,
                    "revenue": revenue,
                    "conversion_rate": conversion,
                    "classification": classification,
                    "priority": priority,
                })

            winners = [
                item
                for item in channels
                if item["classification"] == "winner"
            ]

            promising = [
                item
                for item in channels
                if item["classification"] == "promising"
            ]

            weak = [
                item
                for item in channels
                if item["classification"] == "weak"
            ]

            recommended_focus = sorted(
                winners + promising,
                key=lambda item: (
                    item["priority"],
                    item["revenue"],
                    item["orders"],
                    item["events"],
                ),
                reverse=True,
            )

            return {
                "status": "analyzed",
                "product_id": None,
                "channels": channels,
                "winners": winners,
                "promising": promising,
                "weak": weak,
                "recommended_focus": recommended_focus,
                "excluded_test_products": sorted(
                    test_product_ids
                ),
            }

        except Exception as exc:
            return {
                "status": "error",
                "product_id": None,
                "channels": [],
                "winners": [],
                "promising": [],
                "weak": [],
                "recommended_focus": [],
                "excluded_test_products": [],
                "error": str(exc),
            }

    def publication_intelligence(self):
        """
        Analisa publicações comerciais excluindo produtos de teste.
        """

        try:
            products = self._products()

            test_product_ids = {
                int(product["id"])
                for product in products
                if bool(product.get("is_test"))
            }

            publications = publication_tracker.list_publications()

            analyzed = []

            for publication in publications:
                product_id = publication.get("product_id")

                if (
                    product_id is not None
                    and int(product_id) in test_product_ids
                ):
                    continue

                publication_id = publication.get("id")

                metrics = publication_tracker.publication_metrics(
                    publication_id
                )

                analyzed.append({
                    "publication_id": publication_id,
                    "product_id": product_id,
                    "channel": publication.get("channel"),
                    "status": publication.get("status"),
                    "title": publication.get("title"),
                    "tracking_url": publication.get("tracking_url"),
                    "views": publication.get("views", 0),
                    "reach": publication.get("reach", 0),
                    "likes": publication.get("likes", 0),
                    "comments": publication.get("comments", 0),
                    "saved": publication.get("saved", 0),
                    "shares": publication.get("shares", 0),
                    "clicks": publication.get("clicks", 0),
                    "visits": metrics.get("visits", 0),
                    "orders": metrics.get("orders", 0),
                    "sales": metrics.get("sales", 0),
                    "revenue": metrics.get("revenue", 0.0),
                })

            winners = [
                item
                for item in analyzed
                if (
                    float(item.get("revenue", 0) or 0) > 0
                    or int(item.get("sales", 0) or 0) > 0
                )
            ]

            promising = [
                item
                for item in analyzed
                if (
                    int(item.get("visits", 0) or 0) > 0
                    and int(item.get("sales", 0) or 0) == 0
                )
            ]

            return {
                "status": "analyzed",
                "publications": analyzed,
                "winners": winners,
                "promising": promising,
                "total_publications": len(analyzed),
                "excluded_test_products": sorted(
                    test_product_ids
                ),
            }

        except Exception as exc:
            return {
                "status": "error",
                "publications": [],
                "winners": [],
                "promising": [],
                "total_publications": 0,
                "excluded_test_products": [],
                "error": str(exc),
            }


    def decide(self):
        metrics = self.metrics()
        performance = self.product_performance()

        acquisition = self.acquisition_intelligence()
        publication = self.publication_intelligence()

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
                "acquisition_winners": len(
                    acquisition.get("winners", [])
                ),
                "acquisition_promising": len(
                    acquisition.get("promising", [])
                ),
                "publication_winners": len(
                    publication.get("winners", [])
                ),
                "publication_promising": len(
                    publication.get("promising", [])
                ),
                "total_publications": publication.get(
                    "total_publications",
                    0,
                ),
            },

            "acquisition_intelligence": acquisition,
            "publication_intelligence": publication,
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
