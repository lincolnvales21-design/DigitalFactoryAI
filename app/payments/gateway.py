from abc import ABC, abstractmethod


class PaymentGateway(ABC):

    @abstractmethod
    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str
    ):
        pass
