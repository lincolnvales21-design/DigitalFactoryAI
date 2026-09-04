
import json
import sqlite3
from datetime import datetime
from pathlib import Path


from app.business.checkout_engine import checkout_engine


class SalesEngine:
    """
    Camada comercial do DigitalFactoryAI.

    Responsabilidades:
    - publicar produtos aprovados;
    - armazenar a oferta comercial;
    - gerar uma página comercial estruturada;
    - preparar o produto para checkout;
    - nunca movimentar dinheiro automaticamente.
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
            CREATE TABLE IF NOT EXISTS product_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                offer_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _get_product(self, product_id):
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
            WHERE id = ?
        """, (product_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "product_type": row[2],
            "price": row[3],
            "currency": row[4],
            "status": row[5],
        }

    def save_offer(self, product_id, offer):
        now = datetime.utcnow().isoformat()

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE product_offers
            SET
                offer_json = ?,
                status = 'active',
                updated_at = ?
            WHERE product_id = ?
        """, (
            json.dumps(offer, ensure_ascii=False),
            now,
            product_id,
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO product_offers
                (
                    product_id,
                    offer_json,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, 'active', ?, ?)
            """, (
                product_id,
                json.dumps(offer, ensure_ascii=False),
                now,
                now,
            ))

        conn.commit()
        conn.close()

    def get_offer(self, product_id):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT offer_json
            FROM product_offers
            WHERE product_id = ?
              AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
        """, (product_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        try:
            return json.loads(row[0])
        except Exception:
            return None

    def publish(self, product_id, offer):
        product = self._get_product(product_id)

        if not product:
            return {
                "status": "failed",
                "reason": "product_not_found",
                "product_id": product_id,
            }

        if not offer:
            return {
                "status": "failed",
                "reason": "offer_missing",
                "product_id": product_id,
            }

        # Quality gate comercial.
        required_fields = [
            "offer_name",
            "positioning",
            "promise",
            "benefits",
            "sales_copy",
            "cta",
        ]

        missing = [
            field
            for field in required_fields
            if not offer.get(field)
        ]

        if missing:
            return {
                "status": "blocked",
                "reason": "offer_quality_gate",
                "missing": missing,
                "product_id": product_id,
            }

        self.save_offer(product_id, offer)

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE products
            SET status = 'published'
            WHERE id = ?
        """, (product_id,))

        conn.commit()
        conn.close()

        return {
            "status": "published",
            "product_id": product_id,
            "product": product,
            "offer": offer,
            "published_at": datetime.utcnow().isoformat(),
        }

    def sales_page(self, product_id):
        product = self._get_product(product_id)
        offer = self.get_offer(product_id)

        if not product:
            return {
                "status": "not_found",
                "product_id": product_id,
            }

        if not offer:
            return {
                "status": "not_published",
                "product_id": product_id,
            }

        return {
            "status": "ready",
            "product": product,
            "offer": {
                "name": offer.get("offer_name"),
                "positioning": offer.get("positioning"),
                "promise": offer.get("promise"),
                "core_benefit": offer.get("core_benefit"),
                "benefits": offer.get("benefits", []),
                "differentiator": offer.get("differentiator"),
                "offer_stack": offer.get("offer_stack", []),
                "price": offer.get(
                    "price",
                    product.get("price")
                ),
                "currency": offer.get(
                    "currency",
                    product.get("currency")
                ),
                "sales_copy": offer.get("sales_copy"),
                "cta": offer.get(
                    "cta",
                    "Comprar agora"
                ),
            },

            # O checkout será conectado à infraestrutura
            # de Orders/Payments já existente.
            "checkout": {
                "available": True,
                "product_id": product_id,
                "endpoint": (
                    f"/sales/checkout/{product_id}"
                ),
            },
        }

    def checkout_info(self, product_id):
        product = self._get_product(product_id)
        offer = self.get_offer(product_id)

        if not product:
            return {
                "status": "not_found",
                "product_id": product_id,
            }

        if not offer:
            return {
                "status": "not_published",
                "product_id": product_id,
            }

        return {
            "status": "ready",
            "product_id": product_id,
            "product_name": product["name"],
            "price": offer.get(
                "price",
                product["price"]
            ),
            "currency": offer.get(
                "currency",
                product["currency"]
            ),
            "gateway": (
                "mercadopago"
                if product["currency"] == "BRL"
                else "stripe"
            ),
            "next_step": "create_order",
        }


sales_engine = SalesEngine()
