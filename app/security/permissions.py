from enum import Enum


class Role(Enum):

    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"



class Permission:

    def __init__(self):

        self.rules = {

            Role.OWNER: [
                "shutdown",
                "start",
                "manage_secrets",
                "manage_config",
                "view_logs",
                "execute_agents"
            ],

            Role.ADMIN: [
                "view_logs",
                "monitor",
                "execute_agents"
            ],

            Role.AGENT: [
                "execute_tasks"
            ],

            Role.USER: [
                "request_tasks"
            ]
        }



    def can(self, role, action):

        permissions = self.rules.get(role, [])

        return action in permissions



    def list_permissions(self, role):

        return {
            "role": role.value,
            "permissions": self.rules.get(role, [])
        }



permissions = Permission()