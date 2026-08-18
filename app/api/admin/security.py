from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.security.security_manager import security
from app.security.emergency_stop import emergency_stop
from app.security.audit import audit


router = APIRouter(
    prefix="/admin/security",
    tags=["Security"]
)


class SecurityRequest(BaseModel):

    secret: str
    reason: str = "Manual shutdown"



@router.get("/status")
async def status():

    return {
        "system": "DigitalFactoryAI",
        "security": "online",
        "emergency_stop": emergency_stop.status()
    }



@router.get("/logs")
async def logs():

    return {
        "events": audit.latest()
    }



@router.post("/shutdown")
async def shutdown(request: SecurityRequest):

    result = security.emergency_shutdown(
        request.secret,
        request.reason
    )

    if result["status"] in ["denied", "locked"]:
        raise HTTPException(
            status_code=403,
            detail=result
        )

    return result



@router.post("/start")
async def start(request: SecurityRequest):

    result = security.unlock(
        request.secret
    )

    if result["status"] in ["denied", "locked"]:
        raise HTTPException(
            status_code=403,
            detail=result
        )

    return result