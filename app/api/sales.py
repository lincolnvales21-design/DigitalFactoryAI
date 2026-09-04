from pydantic import BaseModel

from fastapi import APIRouter
from app.business.sales_engine import sales_engine
from app.business.checkout_engine import checkout_engine

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


@router.get("/product/{product_id}")
async def get_sales_page(product_id: int):
    return sales_engine.sales_page(product_id)


@router.get("/checkout/{product_id}")
async def get_checkout_info(product_id: int):
    return sales_engine.checkout_info(product_id)


class CheckoutRequest(BaseModel):
    customer_email: str


@router.post("/checkout/{product_id}")
async def create_checkout(
    product_id: int,
    data: CheckoutRequest
):
    """
    Cria o pedido e inicia o pagamento usando
    a infraestrutura existente.
    """
    return checkout_engine.checkout(
        product_id=product_id,
        customer_email=data.customer_email,
    )
