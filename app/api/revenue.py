
from fastapi import APIRouter

from app.business.revenue_intelligence import (
    revenue_intelligence
)


router = APIRouter(
    prefix="/revenue",
    tags=["Revenue Intelligence"]
)


@router.get("/analysis")
async def revenue_analysis():
    return revenue_intelligence.analyze()


@router.get("/currencies")
async def revenue_currencies():
    return revenue_intelligence.revenue_by_currency()


@router.get("/tickets")
async def revenue_tickets():
    return revenue_intelligence.average_ticket()


@router.get("/products")
async def revenue_products():
    return revenue_intelligence.product_performance()


@router.get("/formats")
async def revenue_formats():
    return revenue_intelligence.format_performance()


@router.get("/priorities")
async def revenue_priorities():
    return revenue_intelligence.commercial_priorities()


@router.get("/history")
async def revenue_history():
    return revenue_intelligence.history()
