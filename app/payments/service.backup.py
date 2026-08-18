from datetime import datetime

from app.database.database import get_connection


class PaymentService:

    def create_test_payment(self, order_id: int):

        connection = get_connection()
        cursor = connection.cursor()

        # ==========================
        # Buscar pedido
        # ==========================

        cursor.execute(
            """
            SELECT
                id,
                product_id,
                customer_email,
                amount,
                currency,
                status
            FROM orders
            WHERE id = ?
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
        # Verificar status
        # ==========================

        if order[5] == "paid":

            connection.close()

            return {
                "status": "already_paid",
                "order_id": order_id
            }

        # ==========================
        # Dados do pagamento teste
        # ==========================

        gateway = "test"
        external_id = f"TEST-{order_id}-{int(datetime.now().timestamp())}"

        amount = order[3]

        # Taxa simulada de 5%
        fee = round(amount * 0.05, 2)

        net_amount = round(
            amount - fee,
            2
        )

        payment_method = "test"

        paid_at = datetime.now().isoformat()

        # ==========================
        # Registrar pagamento
        # ==========================

        cursor.execute(
            """
            INSERT INTO payments (
                order_id,
                gateway,
                external_id,
                amount,
                fee,
                net_amount,
                currency,
                status,
                payment_method,
                paid_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                gateway,
                external_id,
                amount,
                fee,
                net_amount,
                order[4],
                "paid",
                payment_method,
                paid_at
            )
        )

        payment_id = cursor.lastrowid

        # ==========================
        # Atualizar pedido
        # ==========================

        cursor.execute(
            """
            UPDATE orders
            SET
                status = 'paid',
                gateway = ?,
                external_id = ?,
                paid_at = ?
            WHERE id = ?
            """,
            (
                gateway,
                external_id,
                paid_at,
                order_id
            )
        )

        connection.commit()
        connection.close()

        return {
            "status": "paid",
            "payment": {
                "id": payment_id,
                "order_id": order_id,
                "gateway": gateway,
                "external_id": external_id,
                "amount": amount,
                "fee": fee,
                "net_amount": net_amount,
                "currency": order[4],
                "status": "paid",
                "payment_method": payment_method,
                "paid_at": paid_at
            }
        }


payment_service = PaymentService()
