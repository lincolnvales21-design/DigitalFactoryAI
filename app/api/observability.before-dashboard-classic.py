import sqlite3
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.business.autonomous_runtime import autonomous_runtime
from app.business.autonomous_cycle_orchestrator import (
    autonomous_cycle_orchestrator,
)
from app.business.autonomous_cycle_gate import (
    autonomous_cycle_gate,
)
from app.business.publication_tracker import publication_tracker
from app.database.database import get_connection


router = APIRouter(tags=["Observability"])
DB_PATH = Path("digitalfactory.db")


def _find_value(value, keys):
    if isinstance(value, dict):
        for key in keys:
            if value.get(key) not in (None, ""):
                return value[key]
        for child in value.values():
            found = _find_value(child, keys)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_value(child, keys)
            if found not in (None, ""):
                return found
    return None


def _text(value):
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def _product_name(product_id):
    if product_id is None:
        return None
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT name FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return row[0] if row else None
    finally:
        connection.close()


def _decision_label(decision):
    value = _find_value(
        decision,
        (
            "gate_decision",
            "cycle_action",
            "action",
            "outcome",
            "status",
        ),
    )
    if isinstance(value, dict):
        value = _find_value(value, ("gate_decision", "cycle_action", "status"))
    return _text(value)


def _confidence_label(value):
    if value in (None, ""):
        return None
    try:
        numeric = float(value)
        if 0 <= numeric <= 1:
            return f"{numeric * 100:.0f}%"
        if 0 <= numeric <= 100:
            return f"{numeric:.0f}%"
    except (TypeError, ValueError):
        pass
    return _text(value)


def _cycle_summary(cycle):
    return {
        "id": cycle.get("id"),
        "cycle_number": cycle.get("cycle_number"),
        "status": cycle.get("status"),
        "decision": _decision_label(cycle.get("decision")),
        "started_at": cycle.get("started_at"),
        "finished_at": cycle.get("finished_at"),
    }


def _business_metrics(finance):
    connection = sqlite3.connect(DB_PATH)
    try:
        total_orders = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        pending_orders = connection.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
        ).fetchone()[0]

        total_products = connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        # ------------------------------------------------
        # VENCEDOR COMERCIAL
        # ------------------------------------------------
        # Métrica comercial para observabilidade.
        # Não substitui nem altera a decisão soberana
        # do Cycle Gate.
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.name,
                p.price,
                p.currency,
                p.status,
                COUNT(o.id) AS total_orders,
                SUM(
                    CASE
                        WHEN o.status = 'paid' THEN 1
                        ELSE 0
                    END
                ) AS paid_orders,
                SUM(
                    CASE
                        WHEN o.status = 'pending' THEN 1
                        ELSE 0
                    END
                ) AS pending_orders,
                COALESCE(
                    SUM(
                        CASE
                            WHEN o.status = 'paid'
                            THEN o.amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS revenue
            FROM products p
            LEFT JOIN orders o
                ON o.product_id = p.id
            GROUP BY
                p.id,
                p.name,
                p.price,
                p.currency,
                p.status
            """
        ).fetchall()
    finally:
        connection.close()

    currencies = finance.get("financial_summary", {}).get("currencies", [])
    brl = next(
        (row for row in currencies if row.get("currency") == "BRL"),
        None,
    )

    paid_orders = finance.get("financial_summary", {}).get(
        "paid_orders",
        0,
    )

    winner = None

    candidates = []

    for row in rows:
        (
            product_id,
            product_name,
            price,
            currency,
            status,
            product_total_orders,
            product_paid_orders,
            product_pending_orders,
            product_revenue,
        ) = row

        product_total_orders = int(product_total_orders or 0)
        product_paid_orders = int(product_paid_orders or 0)
        product_pending_orders = int(product_pending_orders or 0)
        product_revenue = round(float(product_revenue or 0), 2)

        if product_paid_orders > 0:
            conversion = round(
                product_paid_orders
                / product_total_orders
                * 100,
                2,
            ) if product_total_orders else 0.0

            candidates.append(
                {
                    "product_id": product_id,
                    "product_name": product_name,
                    "price": price,
                    "currency": currency,
                    "status": status,
                    "paid_orders": product_paid_orders,
                    "total_orders": product_total_orders,
                    "pending_orders": product_pending_orders,
                    "revenue": product_revenue,
                    "conversion_rate_percent": conversion,
                }
            )

    candidates.sort(
        key=lambda item: (
            item["paid_orders"],
            item["revenue"],
        ),
        reverse=True,
    )

    if candidates:
        winner = candidates[0]

    total_conversion = round(
        paid_orders / total_orders * 100,
        2,
    ) if total_orders else 0.0

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "paid_orders": paid_orders,
        "total_products": total_products,
        "revenue_brl": float((brl or {}).get("gross_revenue", 0) or 0),
        "currencies": currencies,
        "conversion_rate_percent": total_conversion,
        "winner": winner,
    }


def _observability_data():
    source_errors = []

    try:
        runtime = autonomous_runtime.status()
    except Exception as exc:
        runtime = {}
        source_errors.append(f"Runtime: {exc}")

    try:
        history = autonomous_cycle_orchestrator.history()
    except Exception as exc:
        history = []
        source_errors.append(f"Histórico de ciclos: {exc}")

    try:
        gate_history = autonomous_cycle_gate.history()
    except Exception as exc:
        gate_history = []
        source_errors.append(f"Histórico do Cycle Gate: {exc}")

    try:
        finance = _read_finance()
        business = _business_metrics(finance)
    except Exception as exc:
        finance = {}
        business = {
            "total_orders": None,
            "pending_orders": None,
            "paid_orders": None,
            "total_products": None,
            "revenue_brl": None,
            "currencies": [],
        }
        source_errors.append(f"Financeiro: {exc}")

    try:
        activities = publication_tracker.list_activities(limit=8)
        publications = publication_tracker.list_publications()[:8]
    except Exception as exc:
        activities = []
        publications = []
        source_errors.append(f"Publicações: {exc}")

    latest = history[0] if history else {}
    canonical_gate = gate_history[0] if gate_history else {}
    latest_payload = {
        "decision": latest.get("decision"),
        "action": latest.get("action"),
        "learning": latest.get("learning"),
    }
    decision_reason = _find_value(
        latest_payload,
        ("reason", "rationale", "explanation", "message"),
    )
    product_id = canonical_gate.get("product_id")
    if product_id is None:
        product_id = _find_value(
        latest_payload,
        ("product_id", "productId"),
        )
    product_label = _find_value(
        latest_payload,
        ("product_name", "productName", "product_title", "productTitle"),
    )
    offer = _find_value(
        latest_payload,
        ("offer", "offer_name", "offerName", "offer_title", "offerTitle"),
    )
    if isinstance(offer, dict):
        offer = _find_value(
            offer,
            ("offer_name", "name", "title", "offer_title"),
        )
    confidence = canonical_gate.get("confidence")
    if confidence is None:
        confidence = _find_value(
        latest_payload,
        ("confidence", "confidence_score", "confidenceScore"),
        )
    agent = _find_value(
        latest_payload,
        ("agent", "agent_name", "agentName"),
    )

    if product_id is not None:
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            product_id = _text(product_id)

    last_error = runtime.get("last_error")
    if not last_error and latest.get("status") in {"failed", "error"}:
        last_error = _find_value(
            {
                "decision": latest.get("decision"),
                "action": latest.get("action"),
            },
            ("error", "reason", "message"),
        )

    policy = runtime.get("capital_policy") or {
        "automatic_revenue_threshold_brl": 1000.0,
        "automatic_spend_limit_brl": 100.0,
        "owner_controls_capital": True,
    }
    revenue_brl = business.get("revenue_brl") or 0
    cycle_history = [_cycle_summary(cycle) for cycle in history[:8]]

    return {
        "updated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "source_errors": source_errors,
        "runtime": {
            "status": (
                "online"
                if runtime.get("running")
                else "offline"
            ),
            "enabled": runtime.get("enabled"),
            "running": runtime.get("running", False),
            "interval_seconds": runtime.get("interval_seconds"),
            "cycles_completed": runtime.get("cycles_completed", 0),
            "cycles_failed": runtime.get("cycles_failed", 0),
            "last_cycle": runtime.get("last_cycle"),
            "last_error": _text(last_error),
        },
        "decision": {
            "available": bool(canonical_gate),
            "source": "autonomous_cycle_gate",
            "gate_id": canonical_gate.get("id"),
            "status": latest.get("status") if latest else None,
            "cycle_number": latest.get("cycle_number") if latest else None,
            "decided_at": canonical_gate.get("created_at"),
            "value": _text(
                canonical_gate.get("decision")
                or _decision_label(latest.get("decision"))
            ),
            "reason": _text(
                canonical_gate.get("reason")
                or decision_reason
            ),
            "product_id": product_id,
            "product_name": _product_name(product_id) or _text(product_label),
            "offer": _text(offer),
            "confidence": _confidence_label(
                canonical_gate.get("confidence")
                if canonical_gate
                else confidence
            ),
            "should_run": canonical_gate.get("should_run"),
            "agent": _text(agent),
        },
        "last_cycle": _cycle_summary(latest) if latest else {},
        "cycle_history": cycle_history,
        "business": business,
        "instagram": {
            "available": bool(activities or publications),
            "latest": (
                {
                    "id": publications[0].get("id"),
                    "product_id": publications[0].get("product_id"),
                    "channel": publications[0].get("channel"),
                    "status": publications[0].get("status"),
                    "title": publications[0].get("title"),
                    "created_at": publications[0].get("created_at"),
                    "published_at": publications[0].get("published_at"),
                }
                if publications
                else None
            ),
            "activities": activities,
            "publications": [
                {
                    "id": row.get("id"),
                    "product_id": row.get("product_id"),
                    "channel": row.get("channel"),
                    "status": row.get("status"),
                    "title": row.get("title"),
                    "created_at": row.get("created_at"),
                    "published_at": row.get("published_at"),
                }
                for row in publications
            ],
        },
        "capital_policy": {
            **policy,
            "revenue_brl": revenue_brl,
            "threshold_reached": revenue_brl
            >= float(
                policy.get(
                    "automatic_revenue_threshold_brl",
                    1000,
                )
            ),
        },
    }


def _read_finance():
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT
                p.currency,
                COUNT(*),
                COALESCE(SUM(p.amount), 0),
                COALESCE(SUM(p.fee), 0),
                COALESCE(SUM(p.net_amount), 0)
            FROM payments p
            WHERE p.status = 'paid'
              AND p.gateway != 'test'
              AND p.id = (
                  SELECT p2.id
                  FROM payments p2
                  WHERE p2.order_id = p.order_id
                    AND p2.status = 'paid'
                    AND p2.gateway != 'test'
                  ORDER BY p2.id DESC
                  LIMIT 1
              )
            GROUP BY p.currency
            ORDER BY p.currency
            """
        ).fetchall()
        paid_orders = connection.execute(
            """
            SELECT COUNT(DISTINCT order_id)
            FROM payments
            WHERE status = 'paid' AND gateway != 'test'
            """
        ).fetchone()[0]
    finally:
        connection.close()

    return {
        "financial_summary": {
            "paid_orders": paid_orders,
            "currencies": [
                {
                    "currency": row[0],
                    "orders": row[1],
                    "gross_revenue": row[2],
                    "fees": row[3],
                    "net_revenue": row[4],
                }
                for row in rows
            ],
        }
    }


@router.get("/observability/data")
def observability_data():
    return _observability_data()


OBSERVABILITY_HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0b1020">
  <title>DigitalFactoryAI · Observabilidade</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #090d18;
      --panel: rgba(18, 25, 43, .88);
      --panel-soft: #151d31;
      --line: rgba(155, 172, 206, .16);
      --text: #f4f7fb;
      --muted: #9aa7be;
      --green: #52e3a4;
      --yellow: #f4c96d;
      --red: #ff7d91;
      --blue: #86a8ff;
      --purple: #c19cff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-width: 320px;
      background:
        radial-gradient(circle at 84% -8%, rgba(93, 113, 255, .2), transparent 34rem),
        radial-gradient(circle at -10% 30%, rgba(82, 227, 164, .09), transparent 28rem),
        var(--bg);
      color: var(--text);
      font: 14px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .shell { max-width: 1440px; margin: 0 auto; padding: 34px 32px 52px; }
    .topbar { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 30px; }
    .eyebrow { color: var(--green); font-size: 11px; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
    h1 { margin: 6px 0 5px; font-size: clamp(28px, 4vw, 44px); letter-spacing: -.04em; line-height: 1; }
    .lede { margin: 0; color: var(--muted); max-width: 650px; font-size: 15px; }
    .toolbar { display: flex; align-items: center; gap: 12px; color: var(--muted); white-space: nowrap; }
    .live-pill, .tag { border: 1px solid var(--line); border-radius: 999px; padding: 8px 12px; background: rgba(255,255,255,.04); }
    .live-pill { display: inline-flex; align-items: center; gap: 8px; color: var(--green); font-weight: 700; }
    .dot { width: 8px; height: 8px; display: inline-block; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 16%, transparent); }
    button { border: 1px solid var(--line); color: var(--text); background: var(--panel-soft); border-radius: 10px; padding: 9px 12px; cursor: pointer; font: inherit; }
    button:hover { border-color: rgba(255,255,255,.35); }
    .grid { display: grid; grid-template-columns: 1.35fr .65fr; gap: 16px; }
    .grid > *, .runtime > *, .kpis, .metric-grid, .metric { min-width: 0; }
    .panel { background: linear-gradient(145deg, rgba(21, 29, 49, .96), rgba(13, 19, 34, .92)); border: 1px solid var(--line); border-radius: 18px; padding: 22px; box-shadow: 0 16px 50px rgba(0,0,0,.16); }
    .span-2 { grid-column: span 2; }
    .section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 18px; }
    h2 { margin: 0; font-size: 16px; letter-spacing: -.01em; }
    .section-note { color: var(--muted); font-size: 12px; }
    .runtime { display: grid; grid-template-columns: minmax(230px, .9fr) 1.1fr; gap: 24px; align-items: center; }
    .runtime-state { display: flex; align-items: center; gap: 14px; }
    .state-ring { width: 52px; height: 52px; border-radius: 16px; display: grid; place-items: center; color: var(--green); background: rgba(82,227,164,.1); border: 1px solid rgba(82,227,164,.3); }
    .state-ring.offline { color: var(--red); background: rgba(255,125,145,.1); border-color: rgba(255,125,145,.3); }
    .state-name { font-size: 25px; font-weight: 800; letter-spacing: -.03em; }
    .state-detail { color: var(--muted); margin-top: 2px; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .metric { padding: 13px; border: 1px solid var(--line); border-radius: 12px; background: rgba(255,255,255,.025); }
    .metric-label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { font-size: 22px; font-weight: 800; margin-top: 4px; letter-spacing: -.03em; }
    .kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }
    .kpi { min-height: 118px; }
    .kpi .metric-value { font-size: 30px; }
    .accent-green { color: var(--green); } .accent-blue { color: var(--blue); } .accent-purple { color: var(--purple); } .accent-yellow { color: var(--yellow); }
    .decision-box { min-height: 150px; padding: 18px; border-radius: 14px; background: rgba(134,168,255,.07); border: 1px solid rgba(134,168,255,.22); }
    .decision-label { color: var(--blue); font-size: 11px; letter-spacing: .13em; text-transform: uppercase; font-weight: 800; }
    .decision-value { margin: 10px 0 7px; font-size: 20px; font-weight: 750; }
    .reason { color: #cbd6ea; }
    .tags { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
    .tag { font-size: 12px; padding: 5px 9px; color: #ccd7eb; }
    .policy-row { display: flex; justify-content: space-between; gap: 14px; padding: 11px 0; border-bottom: 1px solid var(--line); }
    .policy-row:last-child { border: 0; }
    .policy-key { color: var(--muted); } .policy-value { font-weight: 750; text-align: right; }
    .progress { height: 8px; margin: 18px 0 8px; overflow: hidden; border-radius: 20px; background: #29334a; }
    .progress > span { display: block; height: 100%; max-width: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--blue), var(--green)); transition: width .35s ease; }
    .progress-note { display: flex; justify-content: space-between; color: var(--muted); font-size: 12px; }
    .policy-note { margin-top: 15px; color: #cbd6ea; font-size: 12px; }
    .history { display: grid; gap: 9px; }
    .history-item { display: grid; grid-template-columns: 82px 1fr auto; gap: 14px; align-items: center; padding: 13px 0; border-bottom: 1px solid var(--line); }
    .history-item:last-child { border: 0; }
    .history-id { color: var(--muted); font-variant-numeric: tabular-nums; }
    .history-title { font-weight: 700; }
    .history-time { color: var(--muted); font-size: 12px; }
    .status-badge { display: inline-flex; align-items: center; gap: 7px; border-radius: 999px; padding: 5px 9px; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .status-completed { color: var(--green); background: rgba(82,227,164,.1); }
    .status-failed, .status-error { color: var(--red); background: rgba(255,125,145,.1); }
    .status-waiting, .status-blocked { color: var(--yellow); background: rgba(244,201,109,.1); }
    .activity-list { display: grid; gap: 10px; }
    .activity { padding: 13px; border: 1px solid var(--line); border-radius: 12px; }
    .activity-title { font-weight: 700; }
    .activity-meta { color: var(--muted); font-size: 12px; margin-top: 4px; }
    .error-note { margin-top: 14px; padding: 11px 13px; color: var(--red); border: 1px solid rgba(255,125,145,.25); border-radius: 10px; background: rgba(255,125,145,.07); }
    .empty { padding: 24px 4px; color: var(--muted); }
    .source-errors { margin: 16px 0 0; color: var(--yellow); font-size: 12px; }
    @media (max-width: 960px) { .grid { grid-template-columns: 1fr; } .span-2 { grid-column: auto; } .runtime { grid-template-columns: 1fr; } }
    @media (max-width: 680px) {
      .shell { padding: 22px 15px 36px; } .topbar { display: block; } .toolbar { margin-top: 18px; justify-content: space-between; }
      .panel { padding: 17px; border-radius: 15px; } .metric-grid, .kpis { grid-template-columns: repeat(2, 1fr); }
      .history-item { grid-template-columns: 1fr auto; } .history-id { grid-column: 1 / -1; } .history-time { grid-column: 1 / -1; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div>
        <div class="eyebrow">DigitalFactoryAI / observability</div>
        <h1>Estado da fábrica</h1>
        <p class="lede">Uma leitura operacional do Runtime, decisões autônomas, negócio e distribuição.</p>
      </div>
      <div class="toolbar">
        <span class="live-pill" id="live-pill"><span class="dot"></span> atualização automática</span>
        <span id="updated-at">—</span>
        <button id="refresh" type="button">Atualizar</button>
      </div>
    </header>

    <div class="grid">
      <section class="panel span-2">
        <div class="section-head"><div><h2>Runtime autônomo</h2><div class="section-note">Leitura em tempo real, sem controles operacionais nesta tela</div></div><span id="runtime-enabled" class="tag">—</span></div>
        <div class="runtime">
          <div class="runtime-state">
            <div id="state-ring" class="state-ring"><span class="dot"></span></div>
            <div><div id="runtime-status" class="state-name">—</div><div id="runtime-detail" class="state-detail">Carregando dados reais…</div></div>
          </div>
          <div class="metric-grid">
            <div class="metric"><div class="metric-label">Intervalo</div><div id="runtime-interval" class="metric-value">—</div></div>
            <div class="metric"><div class="metric-label">Ciclos concluídos</div><div id="runtime-completed" class="metric-value accent-green">—</div></div>
            <div class="metric"><div class="metric-label">Ciclos com falha</div><div id="runtime-failed" class="metric-value accent-yellow">—</div></div>
            <div class="metric"><div class="metric-label">Último ciclo</div><div id="runtime-last" class="metric-value" style="font-size:14px">—</div></div>
          </div>
        </div>
        <div id="runtime-error"></div>
      </section>

      <div class="kpis span-2">
        <section class="panel kpi">
          <div class="metric-label">Pedidos</div>
          <div id="orders-total" class="metric-value accent-blue">—</div>
          <div class="section-note">total registrado</div>
        </section>

        <section class="panel kpi">
          <div class="metric-label">Vendas</div>
          <div id="orders-paid" class="metric-value accent-green">—</div>
          <div class="section-note">pedidos pagos reais</div>
        </section>

        <section class="panel kpi">
          <div class="metric-label">Receita BRL</div>
          <div id="revenue" class="metric-value accent-purple">—</div>
          <div class="section-note">pagamentos confirmados</div>
        </section>

        <section class="panel kpi">
          <div class="metric-label">Pendentes</div>
          <div id="orders-pending" class="metric-value accent-yellow">—</div>
          <div class="section-note">aguardando pagamento</div>
        </section>

        <section class="panel kpi">
          <div class="metric-label">Conversão geral</div>
          <div id="conversion-general" class="metric-value accent-blue">—</div>
          <div class="section-note">vendas ÷ pedidos</div>
        </section>

        <section class="panel kpi">
          <div class="metric-label">Produto vencedor</div>
          <div id="winner-product" class="metric-value accent-green" style="font-size:15px">—</div>
          <div id="winner-detail" class="section-note">sem dados</div>
        </section>
      </div>

      <section class="panel">
        <div class="section-head"><div><h2>Última decisão autônoma</h2><div class="section-note">Razão e contexto disponíveis</div></div></div>
        <div id="decision-content" class="decision-box"><div class="empty">Sem dados ainda.</div></div>
      </section>

      <section class="panel">
        <div class="section-head"><div><h2>Política de capital</h2><div class="section-note">Somente observação</div></div></div>
        <div class="policy-row"><span class="policy-key">Receita atual</span><strong id="policy-revenue" class="policy-value">—</strong></div>
        <div class="policy-row"><span class="policy-key">Limite para gasto automático</span><strong id="policy-threshold" class="policy-value">—</strong></div>
        <div class="policy-row"><span class="policy-key">Teto de gasto</span><strong id="policy-cap" class="policy-value">—</strong></div>
        <div class="progress"><span id="policy-progress" style="width:0%"></span></div>
        <div class="progress-note"><span id="policy-state">—</span><span>R$ 1.000</span></div>
        <div id="policy-explanation" class="policy-note">Gastos automáticos permanecem bloqueados até a receita superar R$ 1.000. Teto automático: R$ 100.</div>
      </section>

      <section class="panel">
        <div class="section-head"><div><h2>Histórico recente</h2><div class="section-note">Últimos ciclos persistidos</div></div></div>
        <div id="history" class="history"><div class="empty">Sem dados ainda.</div></div>
      </section>

      <section class="panel">
        <div class="section-head"><div><h2>Instagram e distribuição</h2><div class="section-note">Atividade local registrada</div></div></div>
        <div id="instagram" class="activity-list"><div class="empty">Sem dados ainda.</div></div>
      </section>
    </div>
    <div id="source-errors"></div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const text = (id, value) => { $(id).textContent = value ?? "—"; };
    const fmtDate = (value) => value ? new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—";
    const fmtMoney = (value) => value == null ? "—" : Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    const clean = (value) => {
      if (value == null || value === "") return "—";
      if (typeof value === "object") return JSON.stringify(value);
      return String(value);
    };
    const statusClass = (value) => "status-" + String(value || "unknown").toLowerCase().replace(/[^a-z0-9]+/g, "-");

    function render(data) {
      const runtime = data.runtime || {};
      const business = data.business || {};
      const policy = data.capital_policy || {};
      const online = runtime.status === "online";
      $("state-ring").classList.toggle("offline", !online);
      text("runtime-status", online ? "Online" : "Offline");
      text("runtime-detail", runtime.enabled === false ? "Desativado por configuração" : (runtime.last_error ? "Última execução com erro" : "Monitorando ciclos autônomos"));
      text("runtime-enabled", runtime.enabled === false ? "desabilitado" : "habilitado");
      text("runtime-interval", runtime.interval_seconds == null ? "—" : `${runtime.interval_seconds}s`);
      text("runtime-completed", runtime.cycles_completed ?? 0);
      text("runtime-failed", runtime.cycles_failed ?? 0);
      text("runtime-last", fmtDate(runtime.last_cycle));
      $("runtime-error").replaceChildren();
      if (runtime.last_error) {
        const error = document.createElement("div");
        error.className = "error-note";
        error.textContent = "Último erro: " + runtime.last_error;
        $("runtime-error").append(error);
      }

      text("orders-total", business.total_orders);
      text("orders-paid", business.paid_orders);
      text("orders-pending", business.pending_orders);
      text("revenue", fmtMoney(business.revenue_brl));

      const generalConversion = Number(business.conversion_rate_percent || 0);
      text(
        "conversion-general",
        Number.isFinite(generalConversion)
          ? generalConversion.toLocaleString("pt-BR", {
              minimumFractionDigits: 0,
              maximumFractionDigits: 2
            }) + "%"
          : "—"
      );

      const winner = business.winner || null;

      if (winner) {
        text("winner-product", `#${winner.product_id} · ${winner.product_name || "sem nome"}`);
        text(
          "winner-detail",
          `${winner.paid_orders || 0} venda(s) · ${Number(winner.conversion_rate_percent || 0).toLocaleString("pt-BR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
          })}% conversão · ${fmtMoney(winner.revenue || 0)}`
        );
      } else {
        text("winner-product", "Nenhum vencedor");
        text("winner-detail", "Ainda não há vendas confirmadas.");
      }

      const decision = data.decision || {};
      const box = $("decision-content");
      box.replaceChildren();
      if (!decision.available) {
        const empty = document.createElement("div"); empty.className = "empty"; empty.textContent = "Sem dados ainda."; box.append(empty);
      } else {
        const label = document.createElement("div"); label.className = "decision-label"; label.textContent = `Ciclo ${decision.cycle_number ?? "—"} · ${decision.status ?? "—"}`; box.append(label);
        const value = document.createElement("div"); value.className = "decision-value"; value.textContent = clean(decision.value || "sem dados ainda"); box.append(value);

        const next = document.createElement("div");
        next.className = "policy-note";
        next.style.marginTop = "12px";
        next.innerHTML = "<strong>Próxima ação:</strong> " + clean(decision.value || "aguardando decisão");
        box.append(next);

        const reason = document.createElement("div"); reason.className = "reason"; reason.textContent = decision.reason || "Sem dados ainda."; box.append(reason);
        const tags = document.createElement("div"); tags.className = "tags";
        [
          ["Produto", decision.product_name || "sem dados ainda"],
          ["Oferta", decision.offer || "sem dados ainda"],
          ["product_id", decision.product_id != null ? `#${decision.product_id}` : "sem dados ainda"],
          ["Confiança", decision.confidence || "sem dados ainda"],
          ["Agente", decision.agent || "sem dados ainda"],
          ["Registrado", fmtDate(decision.decided_at)]
        ].forEach(([label, value]) => { const tag = document.createElement("span"); tag.className = "tag"; tag.textContent = `${label}: ${value}`; tags.append(tag); });
        box.append(tags);
      }

      text("policy-revenue", fmtMoney(policy.revenue_brl));
      text("policy-threshold", fmtMoney(policy.automatic_revenue_threshold_brl));
      text("policy-cap", fmtMoney(policy.automatic_spend_limit_brl));
      const threshold = Number(policy.automatic_revenue_threshold_brl || 1000);
      const revenue = Number(policy.revenue_brl || 0);
      $("policy-progress").style.width = `${Math.min(100, Math.max(0, revenue / threshold * 100))}%`;
      text("policy-state", policy.threshold_reached ? "limite atingido" : "gasto automático bloqueado");
      text("policy-explanation", `Gastos automáticos permanecem bloqueados até a receita superar ${fmtMoney(threshold)}. Teto automático: ${fmtMoney(policy.automatic_spend_limit_brl ?? 100)}.`);

      const history = $("history"); history.replaceChildren();
      if (!(data.cycle_history || []).length) { const empty = document.createElement("div"); empty.className = "empty"; empty.textContent = "Sem dados ainda."; history.append(empty); }
      (data.cycle_history || []).forEach((item) => {
        const row = document.createElement("div"); row.className = "history-item";
        const id = document.createElement("div"); id.className = "history-id"; id.textContent = `Ciclo #${item.cycle_number ?? "—"}`; row.append(id);
        const middle = document.createElement("div"); const title = document.createElement("div"); title.className = "history-title"; title.textContent = item.status || "sem status"; middle.append(title);
        const time = document.createElement("div"); time.className = "history-time"; time.textContent = fmtDate(item.finished_at || item.started_at); middle.append(time); row.append(middle);
        const badge = document.createElement("span"); badge.className = `status-badge ${statusClass(item.status)}`; badge.textContent = item.status || "—"; row.append(badge); history.append(row);
      });

      const instagram = $("instagram"); instagram.replaceChildren();
      const latestPublication = data.instagram?.latest ? [{ ...data.instagram.latest, kind: "última publicação" }] : [];
      const latestId = data.instagram?.latest?.id;
      const items = [...latestPublication, ...(data.instagram?.activities || []).map((item) => ({ ...item, kind: "atividade" })), ...(data.instagram?.publications || []).filter((item) => item.id !== latestId).map((item) => ({ ...item, kind: item.channel || "publicação" }))].slice(0, 8);
      if (!items.length) { const empty = document.createElement("div"); empty.className = "empty"; empty.textContent = "Sem dados ainda."; instagram.append(empty); }
      items.forEach((item) => { const row = document.createElement("div"); row.className = "activity"; const title = document.createElement("div"); title.className = "activity-title"; title.textContent = item.title || `${item.kind} · produto ${item.product_id ? "#" + item.product_id : "—"}`; row.append(title); const meta = document.createElement("div"); meta.className = "activity-meta"; meta.textContent = `${item.channel ? item.channel + " · " : ""}${item.status || "registrada"} · ${fmtDate(item.created_at || item.published_at)}`; row.append(meta); instagram.append(row); });

      text("updated-at", "atualizado " + fmtDate(data.updated_at));
      const errors = $("source-errors"); errors.replaceChildren();
      if ((data.source_errors || []).length) { const note = document.createElement("div"); note.className = "source-errors"; note.textContent = "Fontes indisponíveis: " + data.source_errors.join(" · "); errors.append(note); }
    }

    async function refresh() {
      $("live-pill").style.color = "var(--yellow)";
      try {
        const response = await fetch("/observability/data", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        render(await response.json());
        $("live-pill").style.color = "var(--green)";
      } catch (error) {
        $("live-pill").style.color = "var(--red)";
        text("updated-at", "falha na atualização");
        console.error(error);
      }
    }
    $("refresh").addEventListener("click", refresh);
    refresh();
    setInterval(refresh, 12000);
  </script>
</body>
</html>"""


@router.get("/observability", response_class=HTMLResponse)
def observability():
    return HTMLResponse(OBSERVABILITY_HTML)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_alias():
    return HTMLResponse(OBSERVABILITY_HTML)