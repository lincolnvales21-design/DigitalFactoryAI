from app.payments.test_gateway import TestGateway
from app.payments.gateways.mercadopago import MercadoPagoGateway
from app.payments.gateways.stripe import StripeGateway


class GatewayFactory:

    @staticmethod
    def get_gateway(gateway_name: str):

        if gateway_name == "test":
            return TestGateway()

        if gateway_name == "mercadopago":
            return MercadoPagoGateway()

        if gateway_name == "stripe":
            return StripeGateway()

        raise ValueError(
            f"Gateway não suportado: {gateway_name}"
        )
