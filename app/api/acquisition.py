from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Query

from app.business.acquisition_tracker import acquisition_tracker


router = APIRouter(
    prefix="/acquisition",
    tags=["Acquisition"],
)


@router.get("/link/{product_id}")
async def generate_acquisition_link(
    product_id: int,
    channel: str = "unknown",
    source: str | None = None,
    campaign: str | None = None,
    medium: str | None = None,
):
    return acquisition_tracker.generate_link(
        product_id=product_id,
        channel=channel,
        source=source,
        campaign=campaign,
        medium=medium,
    )


@router.get("/track")
def track_acquisition(
    product_id: int = Query(...),
    channel: str = Query(...),
    source: str | None = Query(default=None),
    campaign: str | None = Query(default=None),
    medium: str | None = Query(default=None),
):
    return acquisition_tracker.track(
        product_id=product_id,
        channel=channel,
        source=source,
        campaign=campaign,
        medium=medium,
        event_type="visit",
    )


@router.get("/report")
def acquisition_report(
    product_id: int | None = Query(default=None),
):
    return {
        "status": "success",
        "product_id": product_id,
        "summary": acquisition_tracker.summary(product_id),
        "channels": acquisition_tracker.report(product_id),
    }


@router.post("/order")
def track_order(
    product_id: int,
    order_id: int,
    channel: str = "unknown",
    source: str | None = None,
    campaign: str | None = None,
    medium: str | None = None,
    amount: float = 0,
    currency: str | None = None,
):
    return acquisition_tracker.track_order(
        product_id=product_id,
        order_id=order_id,
        channel=channel,
        source=source,
        campaign=campaign,
        medium=medium,
        amount=amount,
        currency=currency,
    )


@router.post("/sale")
def track_sale(
    product_id: int,
    order_id: int,
    channel: str = "unknown",
    source: str | None = None,
    campaign: str | None = None,
    medium: str | None = None,
    amount: float = 0,
    currency: str | None = None,
):
    return acquisition_tracker.track_sale(
        product_id=product_id,
        order_id=order_id,
        channel=channel,
        source=source,
        campaign=campaign,
        medium=medium,
        amount=amount,
        currency=currency,
    )


@router.get("/visit/{product_id}")
async def acquisition_visit(
    product_id: int,
    channel: str = "unknown",
    source: str | None = None,
    campaign: str | None = None,
    medium: str | None = None,
):
    acquisition_tracker.track(
        product_id=product_id,
        channel=channel,
        source=source,
        campaign=campaign,
        medium=medium,
        event_type="visit",
    )

    from os import getenv

    base_url = (
        getenv("DIGITALFACTORY_PUBLIC_URL")
        or getenv("REPLIT_DEV_DOMAIN")
        or "http://127.0.0.1:5000"
    )

    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    return RedirectResponse(
        url=f"{base_url}/sales/product/{product_id}",
        status_code=302,
    )


@router.get("/intelligence")
async def acquisition_intelligence(
    product_id: int | None = None,
):
    return acquisition_tracker.intelligence(
        product_id=product_id
    )
