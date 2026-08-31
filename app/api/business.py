from fastapi import APIRouter
from pydantic import BaseModel

from app.business.engine import business_engine


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
