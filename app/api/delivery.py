from fastapi import APIRouter

from app.delivery.service import delivery_service


router = APIRouter(
    prefix="/delivery",
    tags=["Delivery"]
)


@router.post("/{order_id}")
def deliver_order(order_id: int):

    return delivery_service.deliver(
        order_id
    )
