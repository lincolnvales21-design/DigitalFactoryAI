from cryptography.fernet import Fernet
import os


class VaultEncryption:

    def __init__(self):

        self.key_file = "vault.key"

        self.key = self.load_or_create_key()

        self.cipher = Fernet(self.key)


    def load_or_create_key(self):

        if not os.path.exists(self.key_file):

            key = Fernet.generate_key()

            with open(self.key_file, "wb") as file:

                file.write(key)

            return key


        with open(self.key_file, "rb") as file:

            return file.read()



    def encrypt(self, value: str):

        return self.cipher.encrypt(
            value.encode()
        ).decode()



    def decrypt(self, value: str):

        return self.cipher.decrypt(
            value.encode()
        ).decode()



encryption = VaultEncryption()