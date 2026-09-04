from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import sqlite3
from pathlib import Path
from app.business.autonomous_factory_loop import autonomous_factory_loop

router = APIRouter(tags=["Business Dashboard"])

DB_PATH = Path("digitalfactory.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/business/dashboard", response_class=HTMLResponse)
def business_dashboard():
    conn = get_db()

    # Produtos
    products = conn.execute("""
        SELECT
            p.id,
            p.name,
            p.product_type,
            p.price,
            p.currency,
            p.status,
            p.created_at,
            COUNT(CASE WHEN o.status = 'paid' THEN 1 END) AS paid_sales,
            COUNT(CASE WHEN o.status = 'pending' THEN 1 END) AS pending_sales,
            COALESCE(
                SUM(CASE
                    WHEN o.status = 'paid' AND o.currency = p.currency
                    THEN o.amount
                    ELSE 0
                END),
                0
            ) AS revenue,
            COUNT(DISTINCT CASE
                WHEN o.status = 'paid' THEN o.customer_email
            END) AS buyers
        FROM products p
        LEFT JOIN orders o ON o.product_id = p.id
        GROUP BY
            p.id,
            p.name,
            p.product_type,
            p.price,
            p.currency,
            p.status,
            p.created_at
        ORDER BY
            paid_sales DESC,
            p.id DESC
        LIMIT 50
    """).fetchall()

    # Pedidos
    orders = conn.execute("""
        SELECT
            id,
            product_id,
            customer_email,
            amount,
            currency,
            status,
            gateway,
            created_at,
            paid_at
        FROM orders
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    # Receita BRL paga
    revenue_row = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM orders
        WHERE status = 'paid'
        AND currency = 'BRL'
    """).fetchone()

    revenue = float(revenue_row[0] or 0)

    # Quantidades
    total_products = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    published_products = conn.execute(
        "SELECT COUNT(*) FROM products WHERE status = 'published'"
    ).fetchone()[0]

    total_orders = conn.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    paid_orders = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'paid'"
    ).fetchone()[0]

    pending_orders = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
    ).fetchone()[0]

    buyers = conn.execute("""
        SELECT COUNT(DISTINCT customer_email)
        FROM orders
        WHERE status = 'paid'
    """).fetchone()[0]

    # Política financeira atual
    automatic_spend = 100 if revenue > 1000 else 0

    # Estado atual da fábrica
    factory_state = autonomous_factory_loop.status()

    conn.close()

    product_rows = ""
    product_cards = ""

    for p in products:
        sales = int(p["paid_sales"] or 0)
        pending = int(p["pending_sales"] or 0)
        revenue_product = float(p["revenue"] or 0)
        buyers_product = int(p["buyers"] or 0)

        if sales >= 2:
            diagnosis = "🟢 VENCEDOR"
            diagnosis_text = "Produto com vendas reais. Vale estudar expansão."
            next_action = "Analisar possibilidade de variação."
        elif sales == 1:
            diagnosis = "🟡 PROMISSOR"
            diagnosis_text = "Já existe validação comercial real."
            next_action = "Observar novas vendas antes de expandir."
        elif pending > 0:
            diagnosis = "🟠 INTERESSE PENDENTE"
            diagnosis_text = "Existem pedidos ainda não pagos."
            next_action = "Acompanhar conversão dos pedidos."
        elif p["status"] == "published":
            diagnosis = "🔵 PUBLICADO"
            diagnosis_text = "Está disponível, mas ainda sem venda paga."
            next_action = "Gerar tráfego e medir interesse."
        else:
            diagnosis = "⚪ EM PREPARAÇÃO"
            diagnosis_text = "Produto ainda não está publicado."
            next_action = "Aguardar decisão de publicação."

        product_rows += f"""
        <tr>
            <td>#{p['id']}</td>
            <td><strong>{p['name'] or '-'}</strong></td>
            <td>{p['product_type'] or '-'}</td>
            <td>{p['currency']} {float(p['price'] or 0):.2f}</td>
            <td>{p['status']}</td>
            <td>{sales}</td>
            <td>{p['currency']} {revenue_product:.2f}</td>
            <td>{diagnosis}</td>
        </tr>
        """

        product_cards += f"""
        <div class="product-card">
            <div class="product-header">
                <div>
                    <div class="product-id">PRODUTO #{p['id']}</div>
                    <h3>{p['name'] or 'Produto sem nome'}</h3>
                </div>
                <div class="badge">{diagnosis}</div>
            </div>

            <div class="product-meta">
                <span>📦 {p['product_type'] or '-'}</span>
                <span>💰 {p['currency']} {float(p['price'] or 0):.2f}</span>
                <span>🛒 {sales} venda(s)</span>
                <span>👥 {buyers_product} comprador(es)</span>
                <span>💵 Receita: {p['currency']} {revenue_product:.2f}</span>
            </div>

            <div class="product-analysis">
                <strong>🧠 Diagnóstico</strong>
                <p>{diagnosis_text}</p>

                <strong>🎯 Próxima ação</strong>
                <p>{next_action}</p>
            </div>
        </div>
        """

    order_rows = ""

    for o in orders:
        customer = o["customer_email"] or "-"
        masked = customer

        if "@" in customer:
            name, domain = customer.split("@", 1)
            if len(name) > 2:
                masked = name[:2] + "***@" + domain

        order_rows += f"""
        <tr>
            <td>#{o['id']}</td>
            <td>Produto #{o['product_id']}</td>
            <td>{masked}</td>
            <td>{o['currency']} {o['amount']}</td>
            <td>{o['status']}</td>
            <td>{o['gateway'] or '-'}</td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="30">
<title>DigitalFactoryAI — Central de Negócios</title>

<style>
body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
}}

.container {{
    max-width: 1400px;
    margin: auto;
    padding: 30px;
}}

h1 {{
    margin-bottom: 5px;
}}

.subtitle {{
    color: #94a3b8;
    margin-bottom: 30px;
}}

.status {{
    background: #064e3b;
    border: 1px solid #10b981;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 25px;
}}

.cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}}

.card {{
    background: #1e293b;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #334155;
}}

.card .label {{
    color: #94a3b8;
    font-size: 14px;
}}

.card .value {{
    font-size: 28px;
    font-weight: bold;
    margin-top: 8px;
}}

.product-card {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
}}

.product-header {{
    display: flex;
    justify-content: space-between;
    gap: 20px;
    align-items: flex-start;
}}

.product-header h3 {{
    margin: 5px 0 15px 0;
}}

.product-id {{
    font-size: 12px;
    color: #94a3b8;
}}

.badge {{
    background: #334155;
    padding: 8px 12px;
    border-radius: 20px;
    white-space: nowrap;
}}

.product-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}}

.product-meta span {{
    background: #1e293b;
    border: 1px solid #334155;
    padding: 8px 10px;
    border-radius: 7px;
}}

.product-analysis {{
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #334155;
}}

.product-analysis p {{
    color: #cbd5e1;
}}

.section {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th, td {{
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid #334155;
}}

th {{
    color: #94a3b8;
}}

.pipeline {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
}}

.step {{
    background: #334155;
    padding: 15px;
    border-radius: 8px;
}}

.arrow {{
    color: #64748b;
}}

.real {{
    border-left: 4px solid #10b981;
}}

.waiting {{
    border-left: 4px solid #f59e0b;
}}

.factory-control {{
    background: #020617;
    border: 1px solid #475569;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 25px;
}}

.factory-status {{
    font-size: 24px;
    font-weight: bold;
    margin: 10px 0 18px;
}}

.factory-buttons {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}}

.factory-buttons button {{
    border: 0;
    border-radius: 10px;
    padding: 14px 10px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    color: white;
    background: #334155;
}}

.factory-buttons button:hover {{
    opacity: 0.85;
}}

.factory-start {{
    background: #15803d !important;
}}

.factory-pause {{
    background: #b45309 !important;
}}

.factory-resume {{
    background: #0369a1 !important;
}}

.factory-stop {{
    background: #991b1b !important;
}}

.factory-info {{
    color: #94a3b8;
    font-size: 13px;
    margin-top: 14px;
}}

@media (max-width: 800px) {{
    .factory-buttons {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}
</style>
</head>

<body>

<div class="container">

<h1>🏭 DigitalFactoryAI</h1>
<div class="subtitle">Central de Comando do Negócio</div>

<div class="status">
    🟢 SISTEMA OPERACIONAL —
    dados atualizados automaticamente a cada 30 segundos
</div>

<div class="factory-control">

    <h2>🏭 Controle da Fábrica</h2>

    <div id="factory-status" class="factory-status">
        Consultando...
    </div>

    <div class="factory-buttons">

        <button class="factory-start"
                onclick="factoryAction('/factory/start')">
            🟢 INICIAR
        </button>

        <button class="factory-pause"
                onclick="factoryAction('/factory/pause')">
            ⏸ PAUSAR
        </button>

        <button class="factory-resume"
                onclick="factoryAction('/factory/resume')">
            ▶ RETOMAR
        </button>

        <button class="factory-stop"
                onclick="factoryAction('/factory/stop')">
            ⏹ PARAR
        </button>

    </div>

    <div id="factory-message" class="factory-info">
        Controles protegidos do proprietário.
    </div>

</div>

<div class="cards">

    <div class="card real">
        <div class="label">💰 Receita BRL</div>
        <div class="value">R$ {revenue:.2f}</div>
    </div>

    <div class="card real">
        <div class="label">🛒 Vendas pagas</div>
        <div class="value">{paid_orders}</div>
    </div>

    <div class="card real">
        <div class="label">👥 Compradores</div>
        <div class="value">{buyers}</div>
    </div>

    <div class="card">
        <div class="label">📦 Produtos</div>
        <div class="value">{total_products}</div>
    </div>

    <div class="card">
        <div class="label">📢 Publicados</div>
        <div class="value">{published_products}</div>
    </div>

    <div class="card waiting">
        <div class="label">⏳ Pedidos pendentes</div>
        <div class="value">{pending_orders}</div>
    </div>

</div>

<div class="section">

<h2>🔄 Funil do negócio</h2>

<div class="pipeline">
    <div class="step">💡 Oportunidade</div>
    <div class="arrow">→</div>
    <div class="step">📦 Produto</div>
    <div class="arrow">→</div>
    <div class="step">📢 Oferta</div>
    <div class="arrow">→</div>
    <div class="step">👀 Visitante</div>
    <div class="arrow">→</div>
    <div class="step">🛒 Checkout</div>
    <div class="arrow">→</div>
    <div class="step">💳 Compra</div>
    <div class="arrow">→</div>
    <div class="step">💰 Receita</div>
</div>

</div>

<div class="section waiting">

<h2>📢 Aquisição</h2>

<p>
<strong>Status:</strong> 🟡 Ainda não rastreada
</p>

<p>
O sistema ainda não possui dados confiáveis suficientes para afirmar
se uma venda veio de Instagram, Google, TikTok, anúncio pago,
indicação ou outro canal.
</p>

<p>
<strong>Próxima construção:</strong>
rastreamento de origem → visitante → clique → checkout → compra.
</p>

</div>

<div class="section">

<h2>👥 Quem está comprando</h2>

<p>
O painel mostra compradores somente quando existe um pedido com
status <strong>paid</strong>.
</p>

<table>
<thead>
<tr>
<th>Pedido</th>
<th>Produto</th>
<th>Cliente</th>
<th>Valor</th>
<th>Status</th>
<th>Gateway</th>
</tr>
</thead>
<tbody>
{order_rows}
</tbody>
</table>

</div>

<div class="section">

<h2>🧠 O que está funcionando?</h2>

<p>
A classificação abaixo usa somente vendas e pedidos existentes no banco.
Nenhum dado de visitante ou conversão é inventado.
</p>

{product_cards}

</div>

<div class="section">

<h2>📦 Produtos — visão comparativa</h2>

<table>
<thead>
<tr>
<th>ID</th>
<th>Produto</th>
<th>Formato</th>
<th>Preço</th>
<th>Status</th>
</tr>
</thead>
<tbody>
{product_rows}
</tbody>
</table>

</div>

<div class="section">

<h2>💸 Política de capital</h2>

<p>
Receita BRL atual:
<strong>R$ {revenue:.2f}</strong>
</p>

<p>
Gasto automático permitido agora:
<strong>R$ {automatic_spend:.2f}</strong>
</p>

<p>
Regra:
<strong>
receita acima de R$1.000 → máximo R$100 de gasto automático.
</strong>
</p>

</div>

<div class="section">

<h2>🎯 Próximo objetivo</h2>

<p>
<strong>Gerar vendas reais de mercado e descobrir quais canais
e produtos realmente convertem.</strong>
</p>

</div>

</div>

<script>

async function updateFactoryStatus() {{

    try {{

        const response =
            await fetch('/factory/status');

        const data =
            await response.json();

        const element =
            document.getElementById('factory-status');

        if (data.emergency_off) {{

            element.textContent =
                '🔴 DESLIGADA — SEGURANÇA MÁXIMA';

            return;
        }}

        if (data.running) {{

            element.textContent =
                '🟢 OPERANDO';

        }} else if (data.paused) {{

            element.textContent =
                '⏸ PAUSADA';

        }} else {{

            element.textContent =
                '⚪ PARADA';
        }}

    }} catch (error) {{

        document.getElementById('factory-status').textContent =
            '⚠️ STATUS INDISPONÍVEL';

    }}
}}


async function factoryAction(endpoint) {{

    const code = prompt(
        '🔐 Digite seu código de segurança operacional:'
    );

    if (code === null || code === '') {{
        return;
    }}

    const message =
        document.getElementById('factory-message');

    message.textContent =
        '⏳ Executando comando...';

    try {{

        const options = {{
            method: 'POST',
            headers: {{
                'X-Operational-Code': code
            }}
        }};

        const response =
            await fetch(endpoint, options);

        const data =
            await response.json();

        if (!response.ok) {{

            message.textContent =
                '⚠️ Comando não autorizado ou indisponível.';

            await updateFactoryStatus();

            return;
        }}

        message.textContent =
            '✅ Comando executado com sucesso.';

        await updateFactoryStatus();

    }} catch (error) {{

        message.textContent =
            '⚠️ Não foi possível executar o comando.';

    }}
}}


updateFactoryStatus();

setInterval(
    updateFactoryStatus,
    5000
);

</script>

</body>
</html>
"""

    return HTMLResponse(content=html)
