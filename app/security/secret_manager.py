import secrets
import string

from app.security.audit import audit


class SecretManager:


    def generate(self, length=32):

        chars = (
            string.ascii_letters
            + string.digits
            + "!@#$%^&*"
        )

        return "".join(
            secrets.choice(chars)
            for _ in range(length)
        )


    def rotate(self):

        new_secret = self.generate()

        audit.log(
            "SECRET_ROTATION",
            "Nova chave gerada",
            "success"
        )

        return {
            "status": "generated",
            "secret": new_secret
        }


secret_manager = SecretManager()