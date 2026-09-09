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
        report = self.report(product_id=product_id)

        intelligence = []

        for row in report:

            events = int(row.get("events", 0) or 0)
            orders = int(row.get("orders", 0) or 0)
            revenue = float(row.get("revenue", 0) or 0)

            if events > 0:
                conversion = round(
                    (orders / events) * 100,
                    2
                )
            else:
                conversion = 0.0

            if revenue > 0:
                classification = "winner"
                priority = 100

            elif orders > 0:
                classification = "promising"
                priority = 70

            elif events >= 5:
                classification = "weak"
                priority = 20

            else:
                classification = "insufficient_data"
                priority = 0

            intelligence.append({
                "channel": row.get("channel") or "unknown",
                "source": row.get("source"),
                "campaign": row.get("campaign"),
                "medium": row.get("medium"),
                "event_type": row.get("event_type"),
                "events": events,
                "orders": orders,
                "revenue": revenue,
                "conversion_rate": conversion,
                "classification": classification,
                "priority": priority,
            })

        intelligence.sort(
            key=lambda item: (
                item["priority"],
                item["revenue"],
                item["orders"],
                item["events"],
            ),
            reverse=True,
        )

        winners = [
            item for item in intelligence
            if item["classification"] == "winner"
        ]

        promising = [
            item for item in intelligence
            if item["classification"] == "promising"
        ]

        weak = [
            item for item in intelligence
            if item["classification"] == "weak"
        ]

        return {
            "status": "analyzed",
            "product_id": product_id,
            "channels": intelligence,
            "winners": winners,
            "promising": promising,
            "weak": weak,
            "recommended_focus": (
                winners
                or promising
                or intelligence[:3]
            ),
        }


acquisition_tracker = AcquisitionTracker()
