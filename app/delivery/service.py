from pathlib import Path
from datetime import datetime

from app.database.database import get_connection


class DeliveryService:

    def deliver(self, order_id: int):

        connection = get_connection()
        cursor = connection.cursor()

        # ==========================
        # Buscar pedido
        # ==========================

        cursor.execute(
            """
            SELECT
                o.id,
                o.product_id,
                o.customer_email,
                o.status,
                o.delivered_at,
                p.name,
                p.product_type
            FROM orders o
            JOIN products p
                ON p.id = o.product_id
            WHERE o.id = ?
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if order is None:
            connection.close()

            return {
                "status": "error",
                "message": "Pedido não encontrado."
            }

        # ==========================
        # Verificar pagamento
        # ==========================

        if order[3] != "paid":
            connection.close()

            return {
                "status": "error",
                "message": "Pedido ainda não foi pago."
            }

        # ==========================
        # Verificar entrega anterior
        # ==========================

        if order[4] is not None:
            connection.close()

            return {
                "status": "already_delivered",
                "delivery": {
                    "order_id": order_id,
                    "delivered_at": order[4],
                    "message": "Este pedido já foi entregue."
                }
            }

        # ==========================
        # Localizar arquivo
        # ==========================

        if order[6] == "ebook":

            file_path = Path(
                "generated_products/ebook/ebook_final.md"
            )

        else:
            connection.close()

            return {
                "status": "error",
                "message": "Tipo de produto não suportado."
            }

        # ==========================
        # Verificar arquivo
        # ==========================

        if not file_path.exists():
            connection.close()

            return {
                "status": "error",
                "message": "Arquivo do produto não encontrado."
            }

        # ==========================
        # Registrar entrega
        # ==========================

        delivered_at = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE orders
            SET delivered_at = ?
            WHERE id = ?
            """,
            (
                delivered_at,
                order_id
            )
        )

        connection.commit()
        connection.close()

        # ==========================
        # Resultado
        # ==========================

        return {
            "status": "delivered",
            "delivery": {
                "order_id": order_id,
                "customer_email": order[2],
                "product_id": order[1],
                "product_name": order[5],
                "product_type": order[6],
                "file": str(file_path),
                "delivered_at": delivered_at,
                "message": "Produto liberado para entrega."
            }
        }


delivery_service = DeliveryService()
