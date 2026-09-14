from pathlib import Path
from datetime import datetime

from app.database.database import get_connection
from app.products.generator import product_generator


class DeliveryService:

    def deliver(self, order_id: int):

        connection = get_connection()
        cursor = connection.cursor()

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

        if order[3] != "paid":
            connection.close()

            return {
                "status": "error",
                "message": "Pedido ainda não foi pago."
            }

        cursor.execute(
            """
            SELECT id
            FROM payments
            WHERE order_id = ?
              AND status = 'paid'
              AND gateway != 'test'
            ORDER BY id DESC
            LIMIT 1
            """,
            (order_id,)
        )

        confirmed_payment = cursor.fetchone()

        if confirmed_payment is None:
            connection.close()

            return {
                "status": "error",
                "message": "Pagamento do gateway ainda não foi confirmado."
            }

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

        if order[6] not in ("ebook", "course"):
            connection.close()

            return {
                "status": "error",
                "message": "Tipo de produto não suportado."
            }

        product_path = Path("generated_products") / order[6]

        md_file = product_path / f"product_{order[1]}.md"
        pdf_file = product_path / f"product_{order[1]}.pdf"

        if not md_file.exists():
            connection.close()

            return {
                "status": "error",
                "message": "Arquivo Markdown do produto não encontrado."
            }

        if not pdf_file.exists():

            try:
                product_generator._generate_pdf(
                    md_file.read_text(
                        encoding="utf-8"
                    ),
                    pdf_file
                )

            except Exception as error:
                connection.close()

                return {
                    "status": "error",
                    "message": "Não foi possível gerar o PDF.",
                    "error": str(error)
                }

        if not pdf_file.exists():
            connection.close()

            return {
                "status": "error",
                "message": "PDF do produto não foi gerado."
            }

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

        return {
            "status": "delivered",
            "delivery": {
                "order_id": order_id,
                "customer_email": order[2],
                "product_id": order[1],
                "product_name": order[5],
                "product_type": order[6],
                "file": str(pdf_file),
                "format": "pdf",
                "delivered_at": delivered_at,
                "message": "Produto PDF liberado para entrega automaticamente."
            }
        }


delivery_service = DeliveryService()
