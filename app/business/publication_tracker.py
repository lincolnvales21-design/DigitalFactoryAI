import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("digitalfactory.db")


class PublicationTracker:

    def _connect(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        with self._connect() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS publication_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    tracking_url TEXT,
                    source TEXT,
                    campaign TEXT,
                    medium TEXT,
                    external_id TEXT,
                    views INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    orders INTEGER DEFAULT 0,
                    sales INTEGER DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    currency TEXT DEFAULT 'BRL',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS machine_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type TEXT NOT NULL,
                    product_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'completed',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def __init__(self):
        self._ensure_tables()

    def log_activity(
        self,
        activity_type,
        title,
        description=None,
        product_id=None,
        status="completed",
        metadata=None,
    ):
        import json

        metadata_json = (
            json.dumps(metadata, ensure_ascii=False)
            if metadata is not None
            else None
        )

        with self._connect() as conn:

            cursor = conn.execute(
                """
                INSERT INTO machine_activity (
                    activity_type,
                    product_id,
                    title,
                    description,
                    status,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    activity_type,
                    product_id,
                    title,
                    description,
                    status,
                    metadata_json,
                ),
            )

            conn.commit()

            return {
                "status": "logged",
                "activity_id": cursor.lastrowid,
                "activity_type": activity_type,
                "product_id": product_id,
            }

    def create_publication(
        self,
        product_id,
        channel,
        title=None,
        content=None,
        tracking_url=None,
        source=None,
        campaign=None,
        medium=None,
        status="prepared",
        external_id=None,
    ):
        published_at = None

        if status == "published":
            published_at = datetime.now(
                timezone.utc
            ).isoformat()

        with self._connect() as conn:

            cursor = conn.execute(
                """
                INSERT INTO publication_records (
                    product_id,
                    channel,
                    status,
                    title,
                    content,
                    tracking_url,
                    source,
                    campaign,
                    medium,
                    external_id,
                    published_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    channel,
                    status,
                    title,
                    content,
                    tracking_url,
                    source,
                    campaign,
                    medium,
                    external_id,
                    published_at,
                ),
            )

            conn.commit()

            return {
                "status": "created",
                "publication_id": cursor.lastrowid,
                "product_id": product_id,
                "channel": channel,
                "publication_status": status,
                "published_at": published_at,
            }

    def update_metrics(
        self,
        publication_id,
        views=0,
        clicks=0,
        orders=0,
        sales=0,
        revenue=0,
        currency="BRL",
    ):
        with self._connect() as conn:

            conn.execute(
                """
                UPDATE publication_records
                SET
                    views = ?,
                    clicks = ?,
                    orders = ?,
                    sales = ?,
                    revenue = ?,
                    currency = ?
                WHERE id = ?
                """,
                (
                    int(views or 0),
                    int(clicks or 0),
                    int(orders or 0),
                    int(sales or 0),
                    float(revenue or 0),
                    currency or "BRL",
                    publication_id,
                ),
            )

            conn.commit()

        return {
            "status": "updated",
            "publication_id": publication_id,
        }

    def list_publications(self, product_id=None):
        with self._connect() as conn:

            if product_id is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM publication_records
                    ORDER BY created_at DESC, id DESC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM publication_records
                    WHERE product_id = ?
                    ORDER BY created_at DESC, id DESC
                    """,
                    (product_id,),
                ).fetchall()

        return [dict(row) for row in rows]

    def list_activities(self, product_id=None, limit=100):
        with self._connect() as conn:

            if product_id is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM machine_activity
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM machine_activity
                    WHERE product_id = ?
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                    """,
                    (product_id, limit),
                ).fetchall()

        return [dict(row) for row in rows]

    def publication_metrics(self, publication_id):
        """
        Calcula métricas reais de uma publicação
        usando os eventos de aquisição registrados.
        """

        with self._connect() as conn:

            publication = conn.execute(
                """
                SELECT
                    id,
                    product_id,
                    channel,
                    source,
                    campaign,
                    medium
                FROM publication_records
                WHERE id = ?
                """,
                (publication_id,),
            ).fetchone()

            if not publication:
                return {
                    "status": "not_found",
                    "publication_id": publication_id,
                }

            product_id = publication["product_id"]
            channel = publication["channel"]
            source = publication["source"]
            campaign = publication["campaign"]
            medium = publication["medium"]

            conditions = [
                "product_id = ?",
                "channel = ?",
            ]

            params = [
                product_id,
                channel,
            ]

            if source:
                conditions.append("source = ?")
                params.append(source)

            if campaign:
                conditions.append("campaign = ?")
                params.append(campaign)

            if medium:
                conditions.append("medium = ?")
                params.append(medium)

            where = " AND ".join(conditions)

            row = conn.execute(
                f"""
                SELECT
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
                WHERE {where}
                """,
                params,
            ).fetchone()

        return {
            "status": "analyzed",
            "publication_id": publication_id,
            "product_id": product_id,
            "channel": channel,
            "source": source,
            "campaign": campaign,
            "medium": medium,
            "visits": int(row["visits"] or 0),
            "orders": int(row["orders"] or 0),
            "sales": int(row["sales"] or 0),
            "revenue": float(row["revenue"] or 0),
        }

    def summary(self):
        with self._connect() as conn:

            publications = conn.execute(
                """
                SELECT COUNT(*)
                FROM publication_records
                """
            ).fetchone()[0]

            published = conn.execute(
                """
                SELECT COUNT(*)
                FROM publication_records
                WHERE status = 'published'
                """
            ).fetchone()[0]

            prepared = conn.execute(
                """
                SELECT COUNT(*)
                FROM publication_records
                WHERE status = 'prepared'
                """
            ).fetchone()[0]

            sales = conn.execute(
                """
                SELECT COALESCE(SUM(sales), 0)
                FROM publication_records
                """
            ).fetchone()[0]

            revenue = conn.execute(
                """
                SELECT COALESCE(SUM(revenue), 0)
                FROM publication_records
                """
            ).fetchone()[0]

        return {
            "status": "ready",
            "total_publications": publications,
            "published_publications": published,
            "prepared_publications": prepared,
            "sales": int(sales or 0),
            "revenue": float(revenue or 0),
        }


publication_tracker = PublicationTracker()
