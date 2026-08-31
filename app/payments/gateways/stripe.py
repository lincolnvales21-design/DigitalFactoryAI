from app.payments.gateway import PaymentGateway


class StripeGateway(PaymentGateway):

    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str
    ):

        return {
            "gateway": "stripe",
            "external_id": None,
            "amount": amount,
            "fee": 0.0,
            "net_amount": amount,
            "currency": currency,
            "status": "pending",
            "payment_method": None,
            "paid_at": None
        }
