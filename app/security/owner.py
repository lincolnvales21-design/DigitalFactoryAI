from app.security.permissions import Role


class Owner:

    def __init__(self):

        self.name = "System Owner"
        self.role = Role.OWNER


    def profile(self):

        return {
            "name": self.name,
            "role": self.role.value,
            "access": "full"
        }


    def has_role(self, role):

        return self.role == role



owner = Owner()