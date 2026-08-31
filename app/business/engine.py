from app.agents.manager import manager
from app.security.permissions import Role


class BusinessEngine:

    async def run(self, objective: str):

        results = []

        # ==========================================
        # 1. PESQUISA
        # ==========================================

        research = await manager.execute(
            Role.OWNER,
            "execute_agents",
            "ResearchAgent",
            objective
        )

        if research.get("status") != "success":
            return {
                "status": "failed",
                "stage": "research",
                "result": research
            }

        results.append({
            "stage": "research",
            "result": research
        })

        # ==========================================
        # 2. CRIAÇÃO DO PRODUTO
        # ==========================================

        product = await manager.execute(
            Role.OWNER,
            "execute_agents",
            "ProductAgent",
            "Criar o primeiro produto digital comercial usando a pesquisa realizada."
        )

        if product.get("status") != "success":
            return {
                "status": "failed",
                "stage": "product",
                "results": results,
                "result": product
            }

        results.append({
            "stage": "product",
            "result": product
        })

        # ==========================================
        # 3. MARKETING
        # ==========================================

        marketing = await manager.execute(
            Role.OWNER,
            "execute_agents",
            "MarketingAgent",
            "Criar a estratégia comercial, posicionamento, oferta e copy de venda para o produto criado."
        )

        if marketing.get("status") != "success":
            return {
                "status": "failed",
                "stage": "marketing",
                "results": results,
                "result": marketing
            }

        results.append({
            "stage": "marketing",
            "result": marketing
        })

        return {
            "status": "success",
            "message": "Ciclo comercial executado.",
            "objective": objective,
            "results": results
        }


business_engine = BusinessEngine()
