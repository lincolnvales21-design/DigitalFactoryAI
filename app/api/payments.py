from datetime import datetime
import hashlib
import hmac
import os

import mercadopago

from fastapi import APIRouter, HTTPException, Request

from app.database.database import get_connection
from app.payments.service import payment_service
from app.delivery.service import delivery_service


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
# VALIDAR CONFIRMAÇÃO DE PAGAMENTO
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
            raise HTTPException(
                status_code=404,
                detail="Pagamento não encontrado."
            )

        # Pagamentos de teste nunca confirmam pagamentos reais.
        if payment[2] == "test" or payment[8] == "test_paid":
            raise HTTPException(
                status_code=409,
                detail="Pagamento de teste não confirma pagamento real."
            )

        # O endpoint não cria confirmações; somente expõe uma confirmação
        # que já foi registrada pelo gateway.
        if payment[8] != "paid":
            raise HTTPException(
                status_code=409,
                detail="A confirmação deve ser recebida pelo webhook do gateway."
            )

        return {
            "status": "already_confirmed",
            "order_id": order_id,
            "payment": {
                "id": payment[0],
                "gateway": payment[2],
                "external_id": payment[3],
                "amount": payment[4],
                "fee": payment[5],
                "net_amount": payment[6],
                "currency": payment[7],
                "status": payment[8],
                "payment_method": payment[9],
                "paid_at": payment[10]
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
    # Validar assinatura do Mercado Pago
    # ------------------------------------------------------

    webhook_secret = os.getenv("MERCADOPAGO_WEBHOOK_SECRET")

    if not webhook_secret:
        return {
            "status": "error",
            "message": "MERCADOPAGO_WEBHOOK_SECRET não configurado."
        }

    x_signature = request.headers.get("x-signature")
    x_request_id = request.headers.get("x-request-id")

    if not x_signature or not x_request_id:
        raise HTTPException(
            status_code=401,
            detail="Assinatura do webhook não informada."
        )

    # Ler o corpo sem perder a requisição
    body = await request.json()

    payment_data = body.get("data", {})
    payment_id = payment_data.get("id")

    if not payment_id:
        raise HTTPException(
            status_code=401,
            detail="Payment ID não informado."
        )

    # Extrair ts e v1 do header:
    # ts=...;v1=...
    signature_parts = {}

    for item in x_signature.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            signature_parts[key.strip()] = value.strip()

    timestamp = signature_parts.get("ts")
    received_signature = signature_parts.get("v1")

    if not timestamp or not received_signature:
        raise HTTPException(
            status_code=401,
            detail="Assinatura do webhook inválida."
        )

    # Manifest oficial do Mercado Pago
    manifest = (
        f"id:{payment_id};"
        f"request-id:{x_request_id};"
        f"ts:{timestamp};"
    )

    calculated_signature = hmac.new(
        webhook_secret.encode(),
        manifest.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_signature,
        received_signature
    ):
        raise HTTPException(
            status_code=401,
            detail="Assinatura do webhook inválida."
        )

    # ------------------------------------------------------
    # Receber evento
    # ------------------------------------------------------

    data = body

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
                gateway,
                status
            FROM payments
            WHERE external_id = ?
            ORDER BY id DESC
            """,
            (
                str(payment_id),
            )
        )

        processed_payments = cursor.fetchall()

        if any(row[1] != order_id for row in processed_payments):
            return {
                "status": "error",
                "message": "Pagamento associado a outro pedido.",
                "payment_id": str(payment_id)
            }

        processed_payment = next(
            (
                row
                for row in processed_payments
                if row[2] == "mercadopago"
            ),
            None
        )

        if processed_payment is not None and processed_payment[3] == "paid":
            delivery = delivery_service.deliver(
                order_id
            )

            return {
                "status": "already_processed",
                "order_id": order_id,
                "payment_id": str(payment_id),
                "delivery": delivery
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
              AND gateway = 'mercadopago'
              AND status IN ('pending', 'in_process', 'authorized')
            ORDER BY id DESC
            """,
            (
                order_id,
            )
        )

        pending_payments = cursor.fetchall()

        if processed_payment is not None:
            local_payment = next(
                (
                    row
                    for row in pending_payments
                    if row[0] == processed_payment[0]
                ),
                None
            )
        elif len(pending_payments) == 1:
            local_payment = pending_payments[0]
        else:
            local_payment = None

        if len(pending_payments) > 1 and processed_payment is None:
            return {
                "status": "error",
                "message": "Mais de uma tentativa de pagamento pendente; associação ambígua.",
                "order_id": order_id,
                "payment_id": str(payment_id)
            }

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

            transaction_amount = payment.get(
                "transaction_amount"
            )
            provider_currency = payment.get(
                "currency_id"
            )

            if (
                transaction_amount is None
                or provider_currency is None
                or round(float(transaction_amount), 2)
                != round(float(local_payment[4]), 2)
                or str(provider_currency).upper()
                != str(local_payment[7]).upper()
            ):
                return {
                    "status": "error",
                    "message": "Valor ou moeda do pagamento não correspondem ao pedido.",
                    "order_id": order_id,
                    "payment_id": str(payment_id)
                }

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
                  AND status != 'paid'
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

            if cursor.rowcount != 1:
                connection.rollback()

                return {
                    "status": "already_processed",
                    "order_id": order_id,
                    "payment_id": str(payment_id)
                }

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

            # --------------------------------------------------
            # Entrega automática após pagamento aprovado
            # --------------------------------------------------

            delivery = delivery_service.deliver(
                order_id
            )

            return {
                "status": "paid",
                "order_id": order_id,
                "payment_id": str(payment_id),
                "amount": transaction_amount,
                "fee": fee,
                "net_amount": net_amount,
                "currency": provider_currency,
                "delivery": delivery
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
