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
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'paid'
        """
    )

    paid_orders = cursor.fetchone()[0]

    # ==========================
    # Totais por moeda
    # ==========================

    cursor.execute(
        """
        SELECT
            currency,
            COUNT(*),
            COALESCE(SUM(amount), 0),
            COALESCE(SUM(fee), 0),
            COALESCE(SUM(net_amount), 0)
        FROM payments
        WHERE status = 'paid'
        GROUP BY currency
        ORDER BY currency
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
