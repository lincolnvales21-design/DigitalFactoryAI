from fastapi import APIRouter
from pydantic import BaseModel

from app.business.engine import business_engine
from app.business.autonomous_engine import autonomous_business_engine


router = APIRouter(
    prefix="/business",
    tags=["Business"]
)


class BusinessRequest(BaseModel):

    objective: str


@router.post("/run")
async def run_business(data: BusinessRequest):

    return await business_engine.run(
        data.objective
    )


@router.post("/autonomous/run")
async def run_autonomous_business():
    """
    Inicia um ciclo autônomo sem necessidade de objetivo fornecido pelo usuário.
    """
    return await autonomous_business_engine.run_once()


@router.get("/autonomous/status")
async def autonomous_business_status():
    """
    Mostra os últimos ciclos autônomos.
    """
    return autonomous_business_engine.status()
