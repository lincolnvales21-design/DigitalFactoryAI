import os

import mercadopago

from app.database.database import get_connection
from app.payments.gateway import PaymentGateway


class MercadoPagoGateway(PaymentGateway):

    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str
    ):

        access_token = os.getenv(
            "MERCADOPAGO_ACCESS_TOKEN"
        )

        if not access_token:
            raise RuntimeError(
                "MERCADOPAGO_ACCESS_TOKEN não configurado."
            )

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    p.name,
                    p.description,
                    o.customer_email
                FROM orders o
                JOIN products p
                    ON p.id = o.product_id
                WHERE o.id = ?
                """,
                (order_id,)
            )

            product = cursor.fetchone()

        finally:
            connection.close()

        if product is None:
            raise ValueError(
                f"Produto do pedido {order_id} não encontrado."
            )

        product_name = product[0]
        product_description = product[1]
        customer_email = product[2]

        sdk = mercadopago.SDK(
            access_token
        )

        preference_data = {
            "items": [
                {
                    "title": product_name,
                    "description": product_description or "",
                    "quantity": 1,
                    "currency_id": currency.upper(),
                    "unit_price": float(amount)
                }
            ],
            "external_reference": str(order_id)
        }

        if customer_email:
            preference_data["payer"] = {
                "email": customer_email
            }

        response = sdk.preference().create(
            preference_data
        )

        if response.get("status") not in (200, 201):
            raise RuntimeError(
                "Erro ao criar preferência no Mercado Pago: "
                f"{response}"
            )

        preference = response["response"]

        return {
            "gateway": "mercadopago",
            "external_id": preference["id"],
            "amount": amount,
            "fee": 0.0,
            "net_amount": amount,
            "currency": currency,
            "status": "pending",
            "payment_method": None,
            "paid_at": None,
            "checkout_url": preference.get(
                "init_point"
            )
        }