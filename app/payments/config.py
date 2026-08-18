import os


class PaymentConfig:

    DEFAULT_GATEWAY = os.getenv(
        "PAYMENT_DEFAULT_GATEWAY",
        "test"
    )

    BRAZIL_GATEWAY = os.getenv(
        "PAYMENT_BRAZIL_GATEWAY",
        "mercadopago"
    )

    INTERNATIONAL_GATEWAY = os.getenv(
        "PAYMENT_INTERNATIONAL_GATEWAY",
        "stripe"
    )

    @classmethod
    def gateway_for_currency(cls, currency: str):

        currency = currency.upper()

        if currency == "BRL":
            return cls.BRAZIL_GATEWAY

        return cls.INTERNATIONAL_GATEWAY
