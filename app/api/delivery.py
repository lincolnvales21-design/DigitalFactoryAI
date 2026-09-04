from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app.database.database import get_connection
from app.delivery.service import delivery_service


router = APIRouter(
    prefix="/delivery",
    tags=["Delivery"]
)


@router.post("/{order_id}")
def deliver_order(order_id: int):

    result = delivery_service.deliver(
        order_id
    )

    if result.get("status") != "delivered":
        if result.get("status") == "already_delivered":
            raise HTTPException(
                status_code=409,
                detail=result
            )

        raise HTTPException(
            status_code=400,
            detail=result
        )

    file_path = result["delivery"]["file"]

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"produto_{order_id}.pdf"
    )


@router.get("/download/{order_id}")
def download_product(
    order_id: int,
    token: str
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            product_id,
            status,
            delivered_at,
            download_token
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )

    order = cursor.fetchone()
    connection.close()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado."
        )

    if order[2] != "paid":
        raise HTTPException(
            status_code=403,
            detail="Pedido ainda não foi pago."
        )

    if order[4] is None:
        raise HTTPException(
            status_code=403,
            detail="Token de download não disponível."
        )

    if token != order[4]:
        raise HTTPException(
            status_code=403,
            detail="Token de download inválido."
        )

    result = delivery_service.deliver(
        order_id
    )

    if result.get("status") == "already_delivered":

        file_path = (
            f"generated_products/ebook/"
            f"product_{order[1]}.pdf"
        )

    elif result.get("status") == "delivered":

        file_path = result["delivery"]["file"]

    else:

        raise HTTPException(
            status_code=400,
            detail=result
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"produto_{order_id}.pdf"
    )


@router.get("/payment-failure/{order_id}")
def payment_failure(order_id: int):

    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <meta charset="utf-8">
                <title>Pagamento não concluído</title>
            </head>
            <body>
                <h1>Pagamento não concluído</h1>
                <p>
                    O pagamento do pedido #{order_id}
                    não foi concluído.
                </p>
            </body>
        </html>
        """
    )


@router.get("/payment-pending/{order_id}")
def payment_pending(order_id: int):

    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <meta charset="utf-8">
                <title>Pagamento pendente</title>
            </head>
            <body>
                <h1>Pagamento pendente</h1>
                <p>
                    O pagamento do pedido #{order_id}
                    ainda está sendo processado.
                </p>
            </body>
        </html>
        """
    )
