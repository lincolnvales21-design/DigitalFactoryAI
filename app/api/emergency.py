import os

from fastapi import APIRouter, Header, HTTPException

from app.business.emergency_shutdown import emergency_shutdown


router = APIRouter(prefix="/emergency", tags=["Emergency Security"])


def _verify_owner_code(code):
    configured = os.getenv("FACTORY_STOP_CODE")

    if not configured:
        raise HTTPException(
            status_code=503,
            detail="Código de segurança não configurado.",
        )

    if not code or code != configured:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado.",
        )


@router.get("/status")
def emergency_status():
    return emergency_shutdown.status()


@router.post("/shutdown")
def emergency_shutdown_now(
    x_factory_stop_code: str | None = Header(default=None),
):
    """
    KILL SWITCH:
    prioridade máxima do proprietário.
    """
    _verify_owner_code(x_factory_stop_code)

    return emergency_shutdown.shutdown_and_reset()


@router.post("/release")
def emergency_release(
    x_factory_stop_code: str | None = Header(default=None),
):
    """
    Liberação manual após o desligamento de emergência.
    """
    _verify_owner_code(x_factory_stop_code)

    return emergency_shutdown.release()
