from datetime import datetime
import os

import mercadopago

from fastapi import APIRouter, Request

from app.database.database import get_connection
from app.payments.service import payment_service


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# ==========================================================
# PAGAMENTO DE TESTE
# ==========================================================

@router.post("/test/{order_id}")
def test_payment(order_id: int):

    return payment_service.create_test_payment(
        order_id
    )


# ==========================================================
# CRIAR PAGAMENTO
# ==========================================================

@router.post("/create/{order_id}")
def create_payment(order_id: int):

    return payment_service.create_payment(
        order_id
    )


# ==========================================================
# CONFIRMAR PAGAMENTO - SIMULAÇÃO
# ==========================================================

@router.post("/confirm/{order_id}")
def confirm_payment(order_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # Buscar pagamento
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
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
            FROM payments
            WHERE order_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (order_id,)
        )

        payment = cursor.fetchone()

        if payment is None:

            return {
                "status": "error",
                "message": "Pagamento não encontrado.",
                "order_id": order_id
            }

        # --------------------------------------------------
        # Já pago
        # --------------------------------------------------

        if payment[8] == "paid":

            return {
                "status": "already_paid",
                "order_id": order_id,
                "payment_id": payment[0]
            }

        # --------------------------------------------------
        # Confirmar pagamento simulado
        # --------------------------------------------------

        paid_at = datetime.now().isoformat()

        fee = payment[5] or round(
            payment[4] * 0.05,
            2
        )

        net_amount = round(
            payment[4] - fee,
            2
        )

        payment_method = (
            payment[9]
            or "simulated"
        )

        external_id = (
            payment[3]
            or f"CONFIRMED-{order_id}"
        )

        # --------------------------------------------------
        # Atualizar payment
        # --------------------------------------------------

        cursor.execute(
            """
            UPDATE payments
            SET
                external_id = ?,
                fee = ?,
                net_amount = ?,
                status = 'paid',
                payment_method = ?,
                paid_at = ?
            WHERE id = ?
            """,
            (
                external_id,
                fee,
                net_amount,
                payment_method,
                paid_at,
                payment[0]
            )
        )

        # --------------------------------------------------
        # Atualizar order
        # --------------------------------------------------

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
                payment[2],
                external_id,
                paid_at,
                order_id
            )
        )

        connection.commit()

        return {
            "status": "paid",
            "order_id": order_id,
            "payment": {
                "id": payment[0],
                "gateway": payment[2],
                "external_id": external_id,
                "amount": payment[4],
                "fee": fee,
                "net_amount": net_amount,
                "currency": payment[7],
                "status": "paid",
                "payment_method": payment_method,
                "paid_at": paid_at
            }
        }

    finally:
        connection.close()


# ==========================================================
# WEBHOOK MERCADO PAGO
# ==========================================================

@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request):

    # ------------------------------------------------------
    # Receber evento
    # ------------------------------------------------------

    try:
        data = await request.json()
    except Exception:
        return {
            "status": "error",
            "message": "JSON inválido."
        }

    # ------------------------------------------------------
    # Identificar evento
    # ------------------------------------------------------

    event_type = data.get("type")

    if event_type != "payment":
        return {
            "status": "ignored",
            "type": event_type
        }

    # ------------------------------------------------------
    # Obter ID real do pagamento
    # ------------------------------------------------------

    payment_data = data.get(
        "data",
        {}
    )

    payment_id = payment_data.get(
        "id"
    )

    if not payment_id:
        return {
            "status": "error",
            "message": "Payment ID não informado."
        }

    # ------------------------------------------------------
    # Token Mercado Pago
    # ------------------------------------------------------

    access_token = os.getenv(
        "MERCADOPAGO_ACCESS_TOKEN"
    )

    if not access_token:
        return {
            "status": "error",
            "message": "MERCADOPAGO_ACCESS_TOKEN não configurado."
        }

    # ------------------------------------------------------
    # Consultar pagamento real
    # ------------------------------------------------------

    sdk = mercadopago.SDK(
        access_token
    )

    response = sdk.payment().get(
        payment_id
    )

    if response.get("status") != 200:
        return {
            "status": "error",
            "message": "Não foi possível consultar o pagamento.",
            "payment_id": str(payment_id)
        }

    payment = response.get(
        "response",
        {}
    )

    # ------------------------------------------------------
    # Dados reais
    # ------------------------------------------------------

    payment_status = payment.get(
        "status"
    )

    external_reference = payment.get(
        "external_reference"
    )

    if not external_reference:
        return {
            "status": "error",
            "message": "external_reference não encontrado.",
            "payment_id": str(payment_id)
        }

    try:
        order_id = int(
            external_reference
        )
    except (TypeError, ValueError):

        return {
            "status": "error",
            "message": "external_reference inválido.",
            "external_reference": external_reference
        }

    # ------------------------------------------------------
    # Conectar banco
    # ------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # Idempotência
        #
        # Se este pagamento real já foi processado,
        # não processar novamente.
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                order_id,
                status
            FROM payments
            WHERE external_id = ?
            LIMIT 1
            """,
            (
                str(payment_id),
            )
        )

        processed_payment = cursor.fetchone()

        if (
            processed_payment is not None
            and processed_payment[2] == "paid"
        ):

            return {
                "status": "already_processed",
                "order_id": processed_payment[1],
                "payment_id": str(payment_id)
            }

        # --------------------------------------------------
        # Buscar pagamento local pelo pedido
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
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
            FROM payments
            WHERE order_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                order_id,
            )
        )

        local_payment = cursor.fetchone()

        if local_payment is None:

            return {
                "status": "error",
                "message": "Pagamento local não encontrado.",
                "order_id": order_id,
                "payment_id": str(payment_id)
            }

        # --------------------------------------------------
        # Pagamento aprovado
        # --------------------------------------------------

        if payment_status == "approved":

            paid_at = datetime.now().isoformat()

            transaction_amount = (
                payment.get(
                    "transaction_amount"
                )
                or local_payment[4]
            )

            # --------------------------------------------------
            # Taxa REAL retornada pelo Mercado Pago
            # --------------------------------------------------

            fee = 0.0

            fee_details = payment.get(
                "fee_details",
                []
            )

            for fee_detail in fee_details:

                fee_amount = fee_detail.get(
                    "amount"
                )

                if fee_amount:
                    fee += float(
                        fee_amount
                    )

            # --------------------------------------------------
            # Fallback caso a API não retorne fee_details
            # --------------------------------------------------

            if fee == 0.0:

                transaction_details = payment.get(
                    "transaction_details",
                    {}
                )

                total_paid = transaction_details.get(
                    "total_paid_amount"
                )

                net_received = transaction_details.get(
                    "net_received_amount"
                )

                if (
                    total_paid is not None
                    and net_received is not None
                ):

                    fee = round(
                        float(total_paid)
                        - float(net_received),
                        2
                    )

            # --------------------------------------------------
            # Valor líquido
            # --------------------------------------------------

            net_amount = round(
                float(transaction_amount)
                - fee,
                2
            )

            payment_method = (
                payment.get(
                    "payment_method_id"
                )
                or local_payment[9]
                or "mercadopago"
            )

            # --------------------------------------------------
            # Atualizar payment
            # --------------------------------------------------

            cursor.execute(
                """
                UPDATE payments
                SET
                    external_id = ?,
                    amount = ?,
                    fee = ?,
                    net_amount = ?,
                    status = 'paid',
                    payment_method = ?,
                    paid_at = ?
                WHERE id = ?
                """,
                (
                    str(payment_id),
                    transaction_amount,
                    fee,
                    net_amount,
                    payment_method,
                    paid_at,
                    local_payment[0]
                )
            )

            # --------------------------------------------------
            # Atualizar order
            # --------------------------------------------------

            cursor.execute(
                """
                UPDATE orders
                SET
                    status = 'paid',
                    gateway = 'mercadopago',
                    external_id = ?,
                    paid_at = ?
                WHERE id = ?
                """,
                (
                    str(payment_id),
                    paid_at,
                    order_id
                )
            )

            connection.commit()

            return {
                "status": "paid",
                "order_id": order_id,
                "payment_id": str(payment_id),
                "amount": transaction_amount,
                "fee": fee,
                "net_amount": net_amount,
                "currency": payment.get(
                    "currency_id"
                )
            }

        # --------------------------------------------------
        # Outros estados do Mercado Pago
        # --------------------------------------------------

        cursor.execute(
            """
            UPDATE payments
            SET
                external_id = ?,
                status = ?
            WHERE id = ?
            """,
            (
                str(payment_id),
                payment_status or "unknown",
                local_payment[0]
            )
        )

        connection.commit()

        return {
            "status": payment_status,
            "order_id": order_id,
            "payment_id": str(payment_id)
        }

    finally:

        connection.close()
