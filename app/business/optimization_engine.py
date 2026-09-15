
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class OptimizationEngine:
    """
    Decide como melhorar produtos e ofertas com base em desempenho.

    O sistema pode recomendar ações automaticamente, mas:
    - não investe dinheiro;
    - não compra anúncios;
    - não movimenta capital;
    - não altera pagamentos;
    - não promete resultados.
    """

    def __init__(self):
        self.db_path = Path("digitalfactory.db")
        self._ensure_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_database(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                action TEXT NOT NULL,
                reason TEXT,
                recommendation_json TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # --------------------------------------------------------
    # PRODUTOS
    # --------------------------------------------------------

    def _products(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                product_type,
                price,
                currency,
                status,
                COALESCE(is_test, 0)
            FROM products
            WHERE COALESCE(is_test, 0) = 0
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "name": row[1],
                "product_type": row[2],
                "price": float(row[3] or 0),
                "currency": row[4],
                "status": row[5],
                "is_test": bool(row[6]),
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # PEDIDOS
    # --------------------------------------------------------

    def _orders(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                product_id,
                amount,
                currency,
                status
            FROM orders
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "product_id": row[1],
                "amount": float(row[2] or 0),
                "currency": row[3],
                "status": row[4],
            }
            for row in rows
        ]

    # --------------------------------------------------------
    # OFERTAS
    # --------------------------------------------------------

    def _offers(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    product_id,
                    offer_json,
                    status
                FROM product_offers
            """)

            rows = cursor.fetchall()
            conn.close()

        except Exception:
            return {}

        result = {}

        for row in rows:
            try:
                offer = json.loads(row[2])
            except Exception:
                offer = {}

            result[row[1]] = {
                "id": row[0],
                "offer": offer,
                "status": row[3],
            }

        return result

    # --------------------------------------------------------
    # ANÁLISE INDIVIDUAL
    # --------------------------------------------------------

    def analyze_product(self, product_id):
        products = self._products()
        orders = self._orders()
        offers = self._offers()

        product = next(
            (
                p for p in products
                if p["id"] == product_id
            ),
            None
        )

        if not product:
            return {
                "status": "not_found",
                "product_id": product_id,
            }

        related = [
            order for order in orders
            if order["product_id"] == product_id
        ]

        paid = [
            order for order in related
            if order["status"] == "paid"
        ]

        pending = [
            order for order in related
            if order["status"] == "pending"
        ]

        revenue = sum(
            order["amount"]
            for order in paid
        )

        sales = len(paid)
        total_orders = len(related)

        offer = offers.get(product_id)

        # ----------------------------------------------------
        # REGRAS DE OTIMIZAÇÃO
        # ----------------------------------------------------

        if sales >= 2:
            action = "expand_winner"

            reason = (
                "Produto possui vendas confirmadas. "
                "A prioridade é expandir a linha, criar "
                "variações e aproveitar o posicionamento."
            )

            priority = "very_high"

        elif sales == 1:
            action = "create_variation"

            reason = (
                "Produto já demonstrou sinal comercial. "
                "Criar uma variação mantendo o problema "
                "central e testando um novo ângulo."
            )

            priority = "high"

        elif isinstance(pending, list) and len(pending) > 0:
            action = "optimize_conversion"

            reason = (
                "Existem pedidos pendentes sem venda confirmada. "
                "Priorizar melhoria de conversão e recuperação."
            )

            priority = "high"

        elif product["status"] == "published":
            action = "optimize_offer"

            reason = (
                "Produto publicado ainda não possui venda "
                "confirmada. Melhorar oferta, posicionamento "
                "e proposta de valor antes de criar outra versão."
            )

            priority = "medium"

        else:
            action = "validate_before_expansion"

            reason = (
                "Produto ainda não possui validação comercial "
                "suficiente. Evitar expansão prematura."
            )

            priority = "low"

        # ----------------------------------------------------
        # RECOMENDAÇÕES
        # ----------------------------------------------------

        recommendations = []

        if action == "expand_winner":
            recommendations = [
                "Criar variação do produto vencedor",
                "Criar versão premium",
                "Criar produto complementar",
                "Explorar novos ângulos de aquisição",
                "Manter o problema central validado",
            ]

        elif action == "create_variation":
            recommendations = [
                "Criar uma segunda versão",
                "Testar novo título",
                "Testar novo posicionamento",
                "Testar formato complementar",
            ]

        elif action == "optimize_conversion":
            recommendations = [
                "Revisar promessa",
                "Revisar CTA",
                "Revisar objeções",
                "Melhorar clareza da oferta",
                "Investigar pedidos pendentes",
            ]

        elif action == "optimize_offer":
            recommendations = [
                "Melhorar título",
                "Melhorar posicionamento",
                "Reforçar benefício principal",
                "Melhorar copy",
                "Testar novo ângulo comercial",
            ]

        else:
            recommendations = [
                "Manter em observação",
                "Coletar sinais de mercado",
                "Não aumentar produção ainda",
            ]

        return {
            "status": "analyzed",
            "product": product,
            "sales": sales,
            "orders": total_orders,
            "pending_orders": len(pending),
            "revenue": round(revenue, 2),
            "offer_exists": bool(offer),
            "action": action,
            "priority": priority,
            "reason": reason,
            "recommendations": recommendations,
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "automatic_ads": False,
                "owner_controls_capital": True,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    # --------------------------------------------------------
    # ANALISAR TODOS
    # --------------------------------------------------------

    def analyze_all(self):
        products = self._products()

        analyses = []

        for product in products:
            analysis = self.analyze_product(
                product["id"]
            )

            if analysis.get("status") == "analyzed":
                analyses.append(analysis)

        priority_order = {
            "very_high": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }

        analyses.sort(
            key=lambda item: priority_order.get(
                item.get("priority"),
                0
            ),
            reverse=True
        )

        return analyses

    # --------------------------------------------------------
    # PRÓXIMO MOVIMENTO
    # --------------------------------------------------------

    def next_move(self, product_id=None, canonical_action=None):
        # O Cycle Gate é a fonte soberana da decisão do ciclo.
        # Quando ele fornece um produto, este método atua somente
        # sobre esse produto e nunca seleciona outro.
        if product_id is not None:
            analysis = self.analyze_product(product_id)

            if analysis.get("status") != "analyzed":
                return {
                    "status": "not_found",
                    "product_id": product_id,
                    "action": canonical_action or "wait",
                    "reason": (
                        "O produto definido pelo Cycle Gate "
                        "não foi encontrado."
                    ),
                }

            product = analysis["product"]

            return {
                "status": "decision",
                "action": canonical_action or analysis["action"],
                "product_id": product["id"],
                "product": product["name"],
                "reason": analysis["reason"],
                "canonical": True,
                "source": "cycle_gate",
                "optimization_action": analysis["action"],
                "priority": analysis["priority"],
            }

        # Compatibilidade: chamadas antigas sem produto continuam
        # usando a análise global da Optimization Engine.
        analyses = self.analyze_all()

        if not analyses:
            return {
                "status": "no_products",
                "action": "discover_new_opportunity",
                "reason": (
                    "Não existem produtos suficientes "
                    "para otimização."
                ),
            }

        winner = next(
            (
                item for item in analyses
                if item["action"] == "expand_winner"
            ),
            None
        )

        if winner:
            return {
                "status": "decision",
                "action": "expand_winner",
                "product_id": winner["product"]["id"],
                "product": winner["product"]["name"],
                "reason": winner["reason"],
            }

        conversion = next(
            (
                item for item in analyses
                if item["action"] == "optimize_conversion"
            ),
            None
        )

        if conversion:
            return {
                "status": "decision",
                "action": "optimize_conversion",
                "product_id": conversion["product"]["id"],
                "product": conversion["product"]["name"],
                "reason": conversion["reason"],
            }

        variation = next(
            (
                item for item in analyses
                if item["action"] == "create_variation"
            ),
            None
        )

        if variation:
            return {
                "status": "decision",
                "action": "create_variation",
                "product_id": variation["product"]["id"],
                "product": variation["product"]["name"],
                "reason": variation["reason"],
            }

        offer = next(
            (
                item for item in analyses
                if item["action"] == "optimize_offer"
            ),
            None
        )

        if offer:
            return {
                "status": "decision",
                "action": "optimize_offer",
                "product_id": offer["product"]["id"],
                "product": offer["product"]["name"],
                "reason": offer["reason"],
            }

        return {
            "status": "decision",
            "action": "discover_new_opportunity",
            "reason": (
                "Nenhum produto apresenta sinal comercial "
                "forte. Buscar nova oportunidade."
            ),
        }

    # --------------------------------------------------------
    # REGISTRAR AÇÃO
    # --------------------------------------------------------

    def record_action(
        self,
        product_id,
        action,
        reason,
        recommendation,
        status="recommended",
    ):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO optimization_actions
            (
                product_id,
                action,
                reason,
                recommendation_json,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            product_id,
            action,
            reason,
            json.dumps(
                recommendation,
                ensure_ascii=False
            ),
            status,
            datetime.utcnow().isoformat(),
        ))

        conn.commit()
        conn.close()

        return {
            "status": "recorded",
            "product_id": product_id,
            "action": action,
        }

    # --------------------------------------------------------
    # EXECUTAR DECISÃO
    # --------------------------------------------------------

    def optimize(self):
        decision = self.next_move()

        if decision.get("product_id"):
            analysis = self.analyze_product(
                decision["product_id"]
            )

            self.record_action(
                decision["product_id"],
                decision["action"],
                decision["reason"],
                analysis.get("recommendations", []),
            )

            return {
                "status": "optimized",
                "decision": decision,
                "analysis": analysis,
                "capital_policy": {
                    "automatic_investment": False,
                    "automatic_spending": False,
                    "automatic_ads": False,
                    "owner_controls_capital": True,
                },
            }

        return {
            "status": "optimized",
            "decision": decision,
            "capital_policy": {
                "automatic_investment": False,
                "automatic_spending": False,
                "automatic_ads": False,
                "owner_controls_capital": True,
            },
        }

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    def history(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                product_id,
                action,
                reason,
                recommendation_json,
                status,
                created_at
            FROM optimization_actions
            ORDER BY id DESC
            LIMIT 50
        """)

        rows = cursor.fetchall()
        conn.close()

        result = []

        for row in rows:
            try:
                recommendation = json.loads(row[4])
            except Exception:
                recommendation = row[4]

            result.append({
                "id": row[0],
                "product_id": row[1],
                "action": row[2],
                "reason": row[3],
                "recommendation": recommendation,
                "status": row[5],
                "created_at": row[6],
            })

        return result


optimization_engine = OptimizationEngine()
