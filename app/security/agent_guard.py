from app.security.emergency_stop import emergency_stop
from app.security.permissions import permissions, Role
from app.security.audit import audit


class AgentGuard:

    def __init__(self):
        self.system_name = "DigitalFactoryAI"

    def check_system(self):

        if emergency_stop.is_active():
            audit.log(
                "AGENT_BLOCKED_SYSTEM_STOPPED",
                "Execução bloqueada pelo Emergency Stop",
                "denied"
            )

            return {
                "allowed": False,
                "status": "blocked",
                "reason": "Emergency Stop ativo."
            }

        return {
            "allowed": True,
            "status": "online"
        }

    def check_permission(self, role: Role, action: str):

        if not permissions.can(role, action):

            audit.log(
                "AGENT_PERMISSION_DENIED",
                f"Permissão negada: {role.value} -> {action}",
                "denied"
            )

            return {
                "allowed": False,
                "status": "denied",
                "reason": f"Role '{role.value}' não possui permissão para '{action}'."
            }

        return {
            "allowed": True,
            "status": "authorized"
        }

    def authorize(
        self,
        role: Role,
        action: str,
        agent_name: str
    ):

        system_check = self.check_system()

        if not system_check["allowed"]:
            return system_check

        permission_check = self.check_permission(
            role,
            action
        )

        if not permission_check["allowed"]:
            return permission_check

        audit.log(
            "AGENT_AUTHORIZED",
            f"{agent_name} autorizado para {action}",
            "success"
        )

        return {
            "allowed": True,
            "status": "authorized",
            "agent": agent_name,
            "action": action,
            "role": role.value
        }


agent_guard = AgentGuard()