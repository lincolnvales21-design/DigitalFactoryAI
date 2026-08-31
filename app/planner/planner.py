from app.planner.models import Plan, PlanStep
from app.ai.engine import engine


class Planner:


    async def create_plan(self, objective: str):

        analysis = await engine.process(objective)

        category = analysis["analysis"]["category"]


        steps = []


        if category == "ebook":

            steps = [

                PlanStep(
                    id="research",
                    agent="ResearchAgent",
                    task=f"Pesquisar mercado e tendências para: {objective}",
                    depends_on=[]
                ),

                PlanStep(
                    id="product",
                    agent="ProductAgent",
                    task=f"Criar ebook baseado na pesquisa sobre: {objective}",
                    depends_on=["research"]
                ),

                PlanStep(
                    id="marketing",
                    agent="MarketingAgent",
                    task=f"Criar estratégia de vendas para o ebook: {objective}",
                    depends_on=["product"]
                ),

                PlanStep(
                    id="automation",
                    agent="AutomationAgent",
                    task=f"Automatizar divulgação do ebook: {objective}",
                    depends_on=["marketing"]
                )

            ]


        elif category == "research":

            steps = [

                PlanStep(
                    id="research",
                    agent="ResearchAgent",
                    task=f"Realizar pesquisa e análise de mercado: {objective}",
                    depends_on=[]
                )

            ]


        else:

            steps = [

                PlanStep(
                    id="research",
                    agent="ResearchAgent",
                    task=f"Pesquisar sobre: {objective}",
                    depends_on=[]
                )

            ]


        return Plan(
            objective=objective,
            steps=steps
        )


planner = Planner()