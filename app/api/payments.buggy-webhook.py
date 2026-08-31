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

    # ==========================
    # Buscar pagamento pendente
    # ==========================

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

        connection.close()

        return {
            "status": "error",
            "message": "Pagamento não encontrado."
            "order_id": order_id
        }
    

        cursor.execute(
            """
            SELECT
                id,
                status
            FROM payments
            WHERE external_id = ?
            AND status = 'paid'
            LIMIT 1
            """,
            (str(payment_id),)
          )

        processed_payment = cursor.fetchone()

        if processed_payment is not None:

            connection.close()

            return {
                "status": "already_processed",
                "order_id": order_id,
                "payment_id": str(payment_id)
            }
    # ==========================
    # Já pago
    # ==========================

    if payment[8] == "paid":

        connection.close()

        return {
            "status": "already_paid",
            "order_id": order_id,
            "payment_id": payment[0]
        }

    # ==========================
    # Confirmar pagamento
    # ==========================

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

    # ==========================
    # Atualizar payment
    # ==========================

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

    # ==========================
    # Atualizar order
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
            payment[2],
            external_id,
            paid_at,
            order_id
        )
    )

    connection.commit()
    connection.close()

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
# ==========================================================
# WEBHOOK MERCADO PAGO
# ==========================================================

@router.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request):

    data = await request.json()

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

    payment_data = data.get("data", {})
    payment_id = payment_data.get("id")

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
    # Consultar pagamento real no Mercado Pago
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
            "payment_id": payment_id
        }

    payment = response.get(
        "response",
        {}
    )

    # ------------------------------------------------------
    # Dados do pagamento
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
            "payment_id": payment_id
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
    # Atualizar banco
    # ------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

        local_payment = cursor.fetchone()

        if local_payment is None:

            connection.close()

            return {
                "status": "error",
                "message": "Pagamento local não encontrado.",
                "order_id": order_id
            }

        # --------------------------------------------------
        # Pagamento aprovado
        # --------------------------------------------------

        if payment_status == "approved":

            paid_at = datetime.now().isoformat()

            transaction_amount = payment.get(
                "transaction_amount"
            ) or local_payment[4]

            fee = local_payment[5] or 0.0

            net_amount = round(
                transaction_amount - fee,
                2
            )

            payment_method = (
                payment.get(
                    "payment_method_id"
                )
                or local_payment[9]
                or "mercadopago"
            )

            cursor.execute(
                """
                UPDATE payments
                SET
                    external_id = ?,
                    amount = ?,
                    status = 'paid',
                    payment_method = ?,
                    paid_at = ?,
                    net_amount = ?
                WHERE id = ?
                """,
                (
                    str(payment_id),
                    transaction_amount,
                    payment_method,
                    paid_at,
                    net_amount,
                    local_payment[0]
                )
            )

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
                "payment_id": str(payment_id)
            }

        # --------------------------------------------------
        # Outros estados
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