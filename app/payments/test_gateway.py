from datetime import datetime

from app.payments.gateway import PaymentGateway


class TestGateway(PaymentGateway):

    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str
    ):

        external_id = (
            f"TEST-{order_id}-"
            f"{int(datetime.now().timestamp())}"
        )

        fee = round(amount * 0.05, 2)

        net_amount = round(
            amount - fee,
            2
        )

        return {
            "gateway": "test",
            "external_id": external_id,
            "amount": amount,
            "fee": fee,
            "net_amount": net_amount,
            "currency": currency,
            "status": "paid",
            "payment_method": "test",
            "paid_at": datetime.now().isoformat()
        }
