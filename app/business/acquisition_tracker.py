import sqlite3
from pathlib import Path


DB_PATH = Path("digitalfactory.db")


class AcquisitionTracker:

    def _connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        conn = self._connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS acquisition_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                channel TEXT NOT NULL,
                source TEXT,
                campaign TEXT,
                medium TEXT,
                event_type TEXT NOT NULL,
                order_id INTEGER,
                customer_email TEXT,
                amount REAL DEFAULT 0,
                currency TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def __init__(self):
        self._ensure_table()

    def track(
        self,
        product_id,
        channel,
        event_type,
        source=None,
        campaign=None,
        medium=None,
        order_id=None,
        customer_email=None,
        amount=0,
        currency=None,
    ):
        conn = self._connect()

        cursor = conn.execute(
            """
            INSERT INTO acquisition_events (
                product_id,
                channel,
                source,
                campaign,
                medium,
                event_type,
                order_id,
                customer_email,
                amount,
                currency
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                channel,
                source,
                campaign,
                medium,
                event_type,
                order_id,
                customer_email,
                amount,
                currency,
            ),
        )

        conn.commit()
        event_id = cursor.lastrowid
        conn.close()

        return {
            "status": "tracked",
            "event_id": event_id,
            "product_id": product_id,
            "channel": channel,
            "event_type": event_type,
        }

    def report(self, product_id=None):
        conn = self._connect()

        query = """
            SELECT
                channel,
                source,
                campaign,
                medium,
                event_type,
                COUNT(*) AS events,
                COUNT(DISTINCT order_id) AS orders,
                COALESCE(SUM(amount), 0) AS revenue
            FROM acquisition_events
        """

        params = []

        if product_id is not None:
            query += " WHERE product_id = ?"
            params.append(product_id)

        query += """
            GROUP BY
                channel,
                source,
                campaign,
                medium,
                event_type
            ORDER BY revenue DESC, events DESC
        """

        rows = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def summary(self, product_id=None):
        conn = self._connect()

        where = ""
        params = []

        if product_id is not None:
            where = " WHERE product_id = ?"
            params.append(product_id)

        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT order_id) AS orders,
                COALESCE(SUM(
                    CASE
                        WHEN event_type = 'sale'
                        THEN amount
                        ELSE 0
                    END
                ), 0) AS revenue
            FROM acquisition_events
            {where}
            """,
            params,
        ).fetchone()

        conn.close()

        return dict(row)

    def track_order(
        self,
        product_id,
        order_id,
        channel="unknown",
        source=None,
        campaign=None,
        medium=None,
        customer_email=None,
        amount=0,
        currency=None,
    ):
        return self.track(
            product_id=product_id,
            channel=channel,
            source=source,
            campaign=campaign,
            medium=medium,
            event_type="order",
            order_id=order_id,
            customer_email=customer_email,
            amount=amount,
            currency=currency,
        )

    def track_sale(
        self,
        product_id,
        order_id,
        channel="unknown",
        source=None,
        campaign=None,
        medium=None,
        customer_email=None,
        amount=0,
        currency=None,
    ):
        return self.track(
            product_id=product_id,
            channel=channel,
            source=source,
            campaign=campaign,
            medium=medium,
            event_type="sale",
            order_id=order_id,
            customer_email=customer_email,
            amount=amount,
            currency=currency,
        )

    def track_sale_from_order(
        self,
        order_id,
        product_id,
        amount=0,
        currency=None,
    ):
        conn = self._connect()

        existing = conn.execute(
            """
            SELECT id
            FROM acquisition_events
            WHERE order_id = ?
              AND event_type = 'sale'
            LIMIT 1
            """,
            (order_id,),
        ).fetchone()

        if existing:
            conn.close()
            return {
                "status": "already_tracked",
                "order_id": order_id,
                "event_id": existing["id"],
            }

        origin = conn.execute(
            """
            SELECT
                channel,
                source,
                campaign,
                medium,
                customer_email
            FROM acquisition_events
            WHERE order_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (order_id,),
        ).fetchone()

        conn.close()

        if not origin:
            return self.track_sale(
                product_id=product_id,
                order_id=order_id,
                channel="unknown",
                amount=amount,
                currency=currency,
            )

        return self.track_sale(
            product_id=product_id,
            order_id=order_id,
            channel=origin["channel"],
            source=origin["source"],
            campaign=origin["campaign"],
            medium=origin["medium"],
            customer_email=origin["customer_email"],
            amount=amount,
            currency=currency,
        )


    def generate_link(
        self,
        product_id,
        channel="unknown",
        source=None,
        campaign=None,
        medium=None,
        base_url=None,
    ):
        from urllib.parse import urlencode
        import os

        base_url = (
            base_url
            or os.getenv("DIGITALFACTORY_PUBLIC_URL")
            or os.getenv("REPLIT_DEV_DOMAIN")
            or "http://127.0.0.1:5000"
        )

        if not base_url.startswith("http"):
            base_url = "https://" + base_url

        params = {
            "channel": channel or "unknown",
            "source": source or "",
            "campaign": campaign or "",
            "medium": medium or "",
        }

        params = {
            key: value
            for key, value in params.items()
            if value
        }

        query = urlencode(params)

        return {
            "status": "ready",
            "product_id": product_id,
            "channel": channel or "unknown",
            "source": source,
            "campaign": campaign,
            "medium": medium,
            "tracking_url": (
                f"{base_url}/acquisition/visit/"
                f"{product_id}?{query}"
            ),
        }


    def intelligence(self, product_id=None):
        """
        Analisa desempenho comercial por origem/campanha.

        Importante:
        - visits indicam interesse;
        - orders indicam intenção de compra;
        - sales indicam venda confirmada;
        - somente receita/vendas confirmadas podem classificar
          uma origem como vencedora.
        """

        conn = self._connect()

        conditions = []
        params = []

        if product_id is not None:
            conditions.append("product_id = ?")
            params.append(product_id)

        where = (
            f"WHERE {' AND '.join(conditions)}"
            if conditions
            else ""
        )

        rows = conn.execute(
            f"""
            SELECT
                channel,
                source,
                campaign,
                medium,
                COUNT(
                    CASE
                        WHEN event_type = 'visit'
                        THEN 1
                    END
                ) AS visits,
                COUNT(
                    CASE
                        WHEN event_type = 'order'
                        THEN 1
                    END
                ) AS orders,
                COUNT(
                    CASE
                        WHEN event_type = 'sale'
                        THEN 1
                    END
                ) AS sales,
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
            {where}
            GROUP BY
                channel,
                source,
                campaign,
                medium
            ORDER BY
                revenue DESC,
                sales DESC,
                orders DESC,
                visits DESC
            """,
            params,
        ).fetchall()

        conn.close()

        intelligence = []

        for row in rows:
            visits = int(row["visits"] or 0)
            orders = int(row["orders"] or 0)
            sales = int(row["sales"] or 0)
            revenue = float(row["revenue"] or 0)

            conversion = (
                round(
                    (sales / visits) * 100,
                    2,
                )
                if visits
                else 0.0
            )

            if sales > 0 and revenue > 0:
                classification = "winner"
                priority = 100

            elif orders > 0:
                classification = "promising"
                priority = 70

            elif visits >= 5:
                classification = "weak"
                priority = 20

            else:
                classification = "insufficient_data"
                priority = 0

            intelligence.append({
                "channel": row["channel"] or "unknown",
                "source": row["source"],
                "campaign": row["campaign"],
                "medium": row["medium"],
                "visits": visits,
                "orders": orders,
                "sales": sales,
                "revenue": revenue,
                "conversion_rate": conversion,
                "classification": classification,
                "priority": priority,
            })

        winners = [
            item
            for item in intelligence
            if item["classification"] == "winner"
        ]

        promising = [
            item
            for item in intelligence
            if item["classification"] == "promising"
        ]

        weak = [
            item
            for item in intelligence
            if item["classification"] == "weak"
        ]

        recommended_focus = sorted(
            winners + promising,
            key=lambda item: (
                item["priority"],
                item["revenue"],
                item["sales"],
                item["orders"],
                item["visits"],
            ),
            reverse=True,
        )

        if not recommended_focus:
            recommended_focus = intelligence[:3]

        return {
            "status": "analyzed",
            "product_id": product_id,
            "channels": intelligence,
            "winners": winners,
            "promising": promising,
            "weak": weak,
            "recommended_focus": recommended_focus,
        }


acquisition_tracker = AcquisitionTracker()
