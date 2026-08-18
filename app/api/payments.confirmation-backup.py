from fastapi import APIRouter

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
# PAGAMENTO DE PRODUÇÃO
# ==========================================================

@router.post("/create/{order_id}")
def create_payment(order_id: int):

    return payment_service.create_payment(
        order_id
    )