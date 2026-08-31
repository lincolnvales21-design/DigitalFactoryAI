import json
import os
from datetime import datetime

from app.security.audit import audit
from app.security.vault.encryption import encryption


class SecretVault:

    def __init__(self):

        self.path = "digitalfactory_vault.json"

        self.data = self.load()



    def load(self):

        if not os.path.exists(self.path):

            return {}

        with open(self.path, "r") as file:

            return json.load(file)



    def save(self):

        with open(self.path, "w") as file:

            json.dump(
                self.data,
                file,
                indent=4
            )



    def store(
        self,
        name: str,
        value: str
    ):

        encrypted_value = encryption.encrypt(value)


        self.data[name] = {
            "value": encrypted_value,
            "created_at": str(datetime.now())
        }


        self.save()


        audit.log(
            "SECRET_STORED",
            f"Secret {name} armazenado criptografado",
            "success"
        )


        return {
            "status": "stored",
            "name": name
        }



    def get(
        self,
        name: str
    ):

        secret = self.data.get(name)


        if not secret:

            return None


        return encryption.decrypt(
            secret["value"]
        )



    def delete(
        self,
        name: str
    ):

        if name in self.data:

            del self.data[name]

            self.save()


            audit.log(
                "SECRET_DELETED",
                f"Secret {name} removido",
                "success"
            )


            return True


        return False



vault = SecretVault()