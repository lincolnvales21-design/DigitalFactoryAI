from pydantic import BaseModel

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from app.business.sales_engine import sales_engine
from app.business.checkout_engine import checkout_engine

router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)



@router.get("/buy/{product_id}", response_class=HTMLResponse)
async def buyer_sales_page(
    product_id: int,
    channel: str = "unknown",
    source: str | None = None,
    campaign: str | None = None,
    medium: str | None = None,
):
    data = sales_engine.sales_page(product_id)

    if data.get("status") != "ready":
        return HTMLResponse(
            "<h1>Oferta indisponível</h1>",
            status_code=404
        )

    product = data["product"]
    offer = data["offer"]

    benefits = offer.get("benefits", [])
    benefits_html = "".join(
        f"<li>{str(item)}</li>" for item in benefits
    )

    price = offer.get("price", product.get("price"))
    currency = offer.get("currency", product.get("currency"))

    return HTMLResponse(f"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{offer.get("name") or product["name"]}</title>
<style>
body {{
    margin:0;
    font-family:Arial,sans-serif;
    background:#f5f7fb;
    color:#172033;
}}
.container {{
    max-width:760px;
    margin:40px auto;
    padding:24px;
}}
.card {{
    background:white;
    border-radius:18px;
    padding:32px;
    box-shadow:0 8px 30px rgba(0,0,0,.08);
}}
h1 {{ font-size:32px; margin-top:0; }}
.promise {{ font-size:20px; line-height:1.5; }}
.copy {{ line-height:1.7; }}
.price {{ font-size:34px; font-weight:bold; margin:24px 0; }}
input {{
    width:100%;
    box-sizing:border-box;
    padding:15px;
    border:1px solid #ccd2dc;
    border-radius:10px;
    font-size:16px;
    margin:10px 0 14px;
}}
button {{
    width:100%;
    padding:16px;
    border:0;
    border-radius:10px;
    background:#111827;
    color:white;
    font-size:18px;
    font-weight:bold;
    cursor:pointer;
}}
small {{ color:#667085; }}
</style>
</head>
<body>
<div class="container">
<div class="card">

<h1>{offer.get("name") or product["name"]}</h1>

<p class="promise">
<strong>{offer.get("promise") or offer.get("positioning") or ""}</strong>
</p>

<p class="copy">
{offer.get("sales_copy") or ""}
</p>

<h2>O que você recebe</h2>
<ul>
{benefits_html}
</ul>

<div class="price">
{currency} {price}
</div>

<form method="post"
      action="/sales/checkout/{product_id}">
<input type="email"
       name="customer_email"
       placeholder="Seu melhor e-mail"
       required>

<input type="hidden" name="channel" value="{channel}">
<input type="hidden" name="source" value="{source or ''}">
<input type="hidden" name="campaign" value="{campaign or ''}">
<input type="hidden" name="medium" value="{medium or ''}">

<button type="submit">
{offer.get("cta") or "Comprar agora"}
</button>
</form>

<p>
<small>Pagamento processado com segurança.</small>
</p>

</div>
</div>
</body>
</html>
""")

@router.get("/product/{product_id}")
async def get_sales_page(product_id: int):
    return sales_engine.sales_page(product_id)


@router.get("/checkout/{product_id}")
async def get_checkout_info(product_id: int):
    return sales_engine.checkout_info(product_id)


class CheckoutRequest(BaseModel):
    customer_email: str
    channel: str = "unknown"
    source: str | None = None
    campaign: str | None = None
    medium: str | None = None


@router.post("/checkout/{product_id}")
async def create_checkout(
    product_id: int,
    customer_email: str = Form(...),
    channel: str = Form("unknown"),
    source: str | None = Form(None),
    campaign: str | None = Form(None),
    medium: str | None = Form(None),
):
    """
    Cria o pedido e redireciona o comprador
    diretamente para o checkout do gateway.
    """
    result = checkout_engine.checkout(
        product_id=product_id,
        customer_email=customer_email,
        channel=channel,
        source=source,
        campaign=campaign,
        medium=medium,
    )

    payment = result.get("payment") or {}

    if payment.get("status") == "pending":
        payment_data = payment.get("payment") or {}
        checkout_url = payment_data.get("checkout_url")

        if checkout_url:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(
                url=checkout_url,
                status_code=303,
            )

    return result

