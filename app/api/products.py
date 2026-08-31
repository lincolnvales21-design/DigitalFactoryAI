from fastapi import APIRouter, HTTPException
from app.database.database import get_connection


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ==========================
# Catálogo interno
# ==========================

@router.get("/")
def list_products():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            description,
            product_type,
            price,
            currency,
            status,
            created_at
        FROM products
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "product_type": row[3],
            "price": row[4],
            "currency": row[5],
            "status": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]


# ==========================
# Catálogo público
# ==========================

@router.get("/public")
def list_public_products():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            description,
            product_type,
            price,
            currency,
            status,
            created_at
        FROM products
        WHERE status = 'published'
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "product_type": row[3],
            "price": row[4],
            "currency": row[5],
            "status": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]


# ==========================
# Consultar produto
# ==========================

@router.get("/{product_id}")
def get_product(product_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            description,
            product_type,
            price,
            currency,
            status,
            created_at
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "product_type": row[3],
        "price": row[4],
        "currency": row[5],
        "status": row[6],
        "created_at": row[7]
    }


# ==========================
# Publicar produto
# ==========================

@router.post("/{product_id}/publish")
def publish_product(product_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, status
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    )

    row = cursor.fetchone()

    if row is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    if row[1] == "published":

        connection.close()

        return {
            "status": "already_published",
            "product_id": product_id
        }

    cursor.execute(
        """
        UPDATE products
        SET status = 'published'
        WHERE id = ?
        """,
        (product_id,)
    )

    connection.commit()
    connection.close()

    return {
        "status": "published",
        "product_id": product_id
    }