from datetime import datetime

from fastapi import APIRouter

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