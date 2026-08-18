import os

from dotenv import load_dotenv

from app.security.emergency_stop import emergency_stop
from app.security.audit import audit
from app.security.owner import owner
from app.security.permissions import permissions


load_dotenv()


class SecurityManager:

    def __init__(self):

        self.master_secret = os.getenv("MASTER_SECRET")
        self.recovery_secret = os.getenv("RECOVERY_SECRET")


    def validate(self, secret: str):

        return secret == self.master_secret



    def emergency_shutdown(
        self,
        secret: str,
        reason: str
    ):

        if not self.validate(secret):

            audit.log(
                "INVALID_SHUTDOWN_ATTEMPT",
                "Secret inválido",
                "denied"
            )

            return {
                "status": "denied",
                "message": "Invalid secret."
            }



        if not owner.has_role(owner.role):

            audit.log(
                "UNAUTHORIZED_OWNER_ACCESS",
                "Owner inválido",
                "denied"
            )

            return {
                "status": "denied",
                "message": "Owner authorization failed."
            }



        if not permissions.can(
            owner.role,
            "shutdown"
        ):

            audit.log(
                "PERMISSION_DENIED",
                "Sem permissão shutdown",
                "denied"
            )

            return {
                "status": "denied",
                "message": "Permission denied."
            }



        emergency_stop.activate(reason)


        audit.log(
            "EMERGENCY_SHUTDOWN",
            reason,
            "success"
        )


        return {
            "status": "stopped",
            "reason": reason
        }



    def unlock(self, secret: str):

        if (
            secret != self.master_secret
            and secret != self.recovery_secret
        ):

            audit.log(
                "INVALID_UNLOCK_ATTEMPT",
                "Secret inválido",
                "denied"
            )

            return {
                "status": "denied",
                "message": "Invalid secret."
            }


        emergency_stop.deactivate()


        audit.log(
            "SYSTEM_UNLOCK",
            "Sistema iniciado",
            "success"
        )


        return {
            "status": "running"
        }



security = SecurityManager()