from app.business.acquisition_tracker import acquisition_tracker

import os
import sqlite3
from pathlib import Path
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json


class CheckoutEngine:
    """
    Fecha a conexão entre Sales, Orders e Payments.

    O motor:
    1. verifica se o produto está publicado;
    2. cria o pedido;
    3. chama a infraestrutura de pagamento existente;
    4. devolve ao comprador o resultado do checkout.

    Não movimenta dinheiro do proprietário.
    O pagamento só ocorre quando o comprador decide pagar.
    """

    def __init__(self):
        self.db_path = Path("digitalfactory.db")

    def _connect(self):
        return sqlite3.connect(self.db_path)

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

    def _create_order(
        self,
        product,
        customer_email,
        channel="unknown",
        source=None,
        campaign=None,
        medium=None,
    ):
        conn = self._connect()
        cursor = conn.cursor()

        gateway = (
            "mercadopago"
            if product["currency"] == "BRL"
            else "stripe"
        )

        cursor.execute("""
            INSERT INTO orders
            (
                product_id,
                amount,
                currency,
                status,
                gateway
            )
            VALUES (?, ?, ?, 'pending', ?)
        """, (
            product["id"],
            product["price"],
            product["currency"],
            gateway,
        ))

        order_id = cursor.lastrowid

        # Algumas versões do schema possuem customer_email.
        # Tentamos atualizar sem interromper o checkout caso
        # o schema legado não tenha essa coluna.
        try:
            cursor.execute("""
                UPDATE orders
                SET customer_email = ?
                WHERE id = ?
            """, (
                customer_email,
                order_id,
            ))
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

        # Registra a origem do pedido.
        try:
            acquisition_tracker.track_order(
                product_id=product["id"],
                order_id=order_id,
                channel=channel,
                source=source,
                campaign=campaign,
                medium=medium,
                customer_email=customer_email,
                amount=product["price"],
                currency=product["currency"],
            )
        except Exception:
            # O rastreamento nunca pode derrubar o checkout.
            pass

        return order_id

    def _create_payment(self, order_id):
        """
        Utiliza o endpoint de pagamentos já existente.
        Isso evita duplicar a lógica Mercado Pago/Stripe.
        """

        payload = json.dumps({}).encode("utf-8")

        request = Request(
            f"{os.getenv("DIGITALFACTORY_API_URL", "http://127.0.0.1:" + os.getenv("PORT", "8000"))}/payments/create/{order_id}",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")

                try:
                    return json.loads(body)
                except Exception:
                    return {
                        "status": "success",
                        "raw": body,
                    }

        except HTTPError as exc:
            body = exc.read().decode("utf-8")

            try:
                detail = json.loads(body)
            except Exception:
                detail = body

            return {
                "status": "failed",
                "http_status": exc.code,
                "detail": detail,
            }

        except Exception as exc:
            return {
                "status": "failed",
                "detail": str(exc),
            }

    def checkout(
        self,
        product_id,
        customer_email,
        channel="unknown",
        source=None,
        campaign=None,
        medium=None,
    ):
        product = self._get_product(product_id)

        if not product:
            return {
                "status": "failed",
                "reason": "product_not_found",
            }

        if product["status"] != "published":
            return {
                "status": "blocked",
                "reason": "product_not_published",
                "product_id": product_id,
            }

        if not customer_email:
            return {
                "status": "failed",
                "reason": "customer_email_required",
            }

        order_id = self._create_order(
            product,
            customer_email,
            channel=channel,
            source=source,
            campaign=campaign,
            medium=medium,
        )

        payment = self._create_payment(order_id)

        return {
            "status": "ready",
            "order_id": order_id,
            "product": product,
            "customer_email": customer_email,
            "payment": payment,
            "created_at": datetime.utcnow().isoformat(),
        }


checkout_engine = CheckoutEngine()
