from app.database.database import get_connection
from app.payments.factory import GatewayFactory
from app.payments.config import PaymentConfig


class PaymentService:

    def __init__(self):

        # Gateway usado exclusivamente pelo fluxo de teste
        self.gateway = GatewayFactory.get_gateway("test")

    # ==========================================================
    # PAGAMENTO DE TESTE
    # ==========================================================

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
        # Gateway de teste
        # ==========================

        payment = self.gateway.create_payment(
            order_id=order[0],
            amount=order[3],
            currency=order[4]
        )

        # Pagamentos de teste não confirmam pagamentos reais.
        # Mantemos um status separado para impedir que o registro
        # seja usado pelo fluxo de confirmação ou entrega.
        test_payment = {
            **payment,
            "status": "test_paid"
        }

        # ==========================
        # Registrar pagamento de teste
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
            RETURNING id
            """,
            (
                order_id,
                test_payment["gateway"],
                test_payment["external_id"],
                test_payment["amount"],
                test_payment["fee"],
                test_payment["net_amount"],
                test_payment["currency"],
                test_payment["status"],
                test_payment["payment_method"],
                test_payment["paid_at"]
            )
        )

        row = cursor.fetchone()
        payment_id = row[0] if row else None

        if not payment_id:
            connection.rollback()
            connection.close()
            raise RuntimeError("Falha ao obter ID do pagamento no PostgreSQL")

        connection.commit()
        connection.close()

        # ==========================
        # Resultado
        # ==========================

        return {
            "status": "test_paid",
            "payment": {
                "id": payment_id,
                "order_id": order_id,
                "gateway": test_payment["gateway"],
                "external_id": test_payment["external_id"],
                "amount": test_payment["amount"],
                "fee": test_payment["fee"],
                "net_amount": test_payment["net_amount"],
                "currency": test_payment["currency"],
                "status": test_payment["status"],
                "payment_method": test_payment["payment_method"],
                "paid_at": test_payment["paid_at"]
            }
        }

    # ==========================================================
    # PAGAMENTO DE PRODUÇÃO
    # ==========================================================

    def create_payment(self, order_id: int):

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
        # Escolher gateway
        # ==========================

        gateway_name = PaymentConfig.gateway_for_currency(
            order[4]
        )

        gateway = GatewayFactory.get_gateway(
            gateway_name
        )

        # ==========================
        # Criar pagamento
        # ==========================

        payment = gateway.create_payment(
            order_id=order[0],
            amount=order[3],
            currency=order[4]
        )

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
            RETURNING id
            """,
            (
                order_id,
                payment["gateway"],
                payment["external_id"],
                payment["amount"],
                payment["fee"],
                payment["net_amount"],
                payment["currency"],
                payment["status"],
                payment["payment_method"],
                payment["paid_at"]
            )
        )

        row = cursor.fetchone()
        payment_id = row[0] if row else None

        if not payment_id:
            connection.rollback()
            connection.close()
            raise RuntimeError("Falha ao obter ID do pagamento no PostgreSQL")

        # ==========================
        # Atualizar pedido
        # ==========================

        if payment["status"] == "paid":

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
                    payment["gateway"],
                    payment["external_id"],
                    payment["paid_at"],
                    order_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE orders
                SET
                    gateway = ?,
                    external_id = ?
                WHERE id = ?
                """,
                (
                    payment["gateway"],
                    payment["external_id"],
                    order_id
                )
            )

        connection.commit()
        connection.close()

        # ==========================
        # Resultado
        # ==========================

        return {
            "status": payment["status"],
            "payment": {
                "id": payment_id,
                "order_id": order_id,
                "gateway": payment["gateway"],
                "external_id": payment["external_id"],
                "amount": payment["amount"],
                "fee": payment["fee"],
                "net_amount": payment["net_amount"],
                "currency": payment["currency"],
                "status": payment["status"],
                "payment_method": payment["payment_method"],
                "paid_at": payment["paid_at"],
                "checkout_url": payment.get("checkout_url")
            }
        }


# ==========================================================
# INSTÂNCIA GLOBAL
# ==========================================================

payment_service = PaymentService()