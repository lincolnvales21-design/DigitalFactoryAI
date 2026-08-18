from app.security.emergency_stop import emergency_stop
from app.security.audit import audit
from app.security.owner import owner
from app.security.vault.secret_vault import vault


class SecurityManager:

    def __init__(self):

        # Agora as chaves vêm do Secret Vault
        self.master_secret = vault.get("master_secret")
        self.recovery_secret = vault.get("recovery_secret")


    def validate(self, secret: str):

        return secret == self.master_secret



    def emergency_shutdown(
        self,
        secret: str,
        reason: str
    ):

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