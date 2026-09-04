from fastapi import APIRouter, Depends, Header, HTTPException

from app.business.factory_security import verify_operational_code
from app.business.autonomous_factory_loop import autonomous_factory_loop


router = APIRouter(prefix="/factory", tags=["Factory Control"])


@router.post("/start")
def start_factory(
    interval: int = 3600,
    authorized: bool = Depends(verify_operational_code),
):
    """
    INICIAR — controle operacional protegido.
    """
    if autonomous_factory_loop.status().get("running"):
        return {
            "status": "already_running",
            "message": "A fábrica já está em execução.",
        }

    return autonomous_factory_loop.start(interval=interval)


@router.post("/pause")
def pause_factory(
    authorized: bool = Depends(verify_operational_code),
):
    """
    PAUSAR — controle operacional protegido.
    """
    return autonomous_factory_loop.pause()


@router.post("/resume")
def resume_factory(
    authorized: bool = Depends(verify_operational_code),
):
    """
    RETOMAR — controle operacional protegido.
    """
    return autonomous_factory_loop.resume()


@router.post("/stop")
def stop_factory(
    authorized: bool = Depends(verify_operational_code),
):
    """
    PARAR NORMAL — NÃO apaga memória.
    """
    return autonomous_factory_loop.stop()


@router.get("/status")
def factory_status():
    """
    Status pode ser consultado sem código.
    """
    return autonomous_factory_loop.status()
