from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.database.database import get_connection


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


class OrderRequest(BaseModel):

    product_id: int
    customer_email: EmailStr


@router.post("/")
def create_order(data: OrderRequest):

    connection = get_connection()
    cursor = connection.cursor()

    # ==========================
    # Verificar produto
    # ==========================

    cursor.execute(
        """
        SELECT
            id,
            name,
            price,
            currency,
            status
        FROM products
        WHERE id = ?
        """,
        (data.product_id,)
    )

    product = cursor.fetchone()

    if product is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    # ==========================
    # Produto precisa estar publicado
    # ==========================

    if product[4] != "published":

        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Produto não está publicado"
        )

    # ==========================
    # Criar pedido
    # ==========================

    cursor.execute(
        """
        INSERT INTO orders (
            product_id,
            customer_email,
            amount,
            currency,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            product[0],
            data.customer_email,
            product[2],
            product[3],
            "pending"
        )
    )

    order_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "status": "created",
        "order": {
            "id": order_id,
            "product_id": product[0],
            "product_name": product[1],
            "customer_email": data.customer_email,
            "amount": product[2],
            "currency": product[3],
            "status": "pending"
        }
    }


@router.get("/")
def list_orders():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            product_id,
            customer_email,
            amount,
            currency,
            status,
            gateway,
            external_id,
            created_at,
            paid_at
        FROM orders
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "product_id": row[1],
            "customer_email": row[2],
            "amount": row[3],
            "currency": row[4],
            "status": row[5],
            "gateway": row[6],
            "external_id": row[7],
            "created_at": row[8],
            "paid_at": row[9]
        }
        for row in rows
    ]
