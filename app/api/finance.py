from fastapi import APIRouter

from app.database.database import get_connection


router = APIRouter(
    prefix="/finance",
    tags=["Finance"]
)


@router.get("/summary")
def finance_summary():

    connection = get_connection()
    cursor = connection.cursor()

    # ==========================
    # Pedidos pagos
    # ==========================

    cursor.execute(
        """
        SELECT COUNT(DISTINCT order_id)
        FROM payments
        WHERE status = 'paid'
          AND gateway != 'test'
        """
    )

    paid_orders = cursor.fetchone()[0]

    # ==========================
    # Totais por moeda
    # ==========================

    cursor.execute(
        """
        SELECT
            p.currency,
            COUNT(*),
            COALESCE(SUM(p.amount), 0),
            COALESCE(SUM(p.fee), 0),
            COALESCE(SUM(p.net_amount), 0)
        FROM payments p
        WHERE p.status = 'paid'
          AND p.gateway != 'test'
          AND p.id = (
              SELECT p2.id
              FROM payments p2
              WHERE p2.order_id = p.order_id
                AND p2.status = 'paid'
                AND p2.gateway != 'test'
              ORDER BY p2.id DESC
              LIMIT 1
          )
        GROUP BY p.currency
        ORDER BY p.currency
        """
    )

    rows = cursor.fetchall()

    connection.close()

    currencies = []

    for row in rows:

        currencies.append(
            {
                "currency": row[0],
                "orders": row[1],
                "gross_revenue": row[2],
                "fees": row[3],
                "net_revenue": row[4]
            }
        )

    return {
        "status": "success",
        "financial_summary": {
            "paid_orders": paid_orders,
            "currencies": currencies
        }
    }
