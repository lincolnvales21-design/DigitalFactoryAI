class AIEngine:

    def __init__(self):

        self.name = "DigitalFactoryAI Engine"
        self.version = "1.2"


    async def process(self, objective):

        objective_lower = objective.lower()


        analysis = {

            "objective": objective,

            "category": "general",

            "recommended_agents": [],

            "strategy": ""

        }


        # Ebook
        if "ebook" in objective_lower:

            analysis["category"] = "ebook"

            analysis["recommended_agents"] = [

                "ResearchAgent",
                "ProductAgent",
                "MarketingAgent",
                "AutomationAgent"

            ]

            analysis["strategy"] = (
                "Pesquisar mercado, criar ebook, "
                "vender e automatizar divulgação"
            )


        # Curso
        elif "curso" in objective_lower:

            analysis["category"] = "course"

            analysis["recommended_agents"] = [

                "ResearchAgent",
                "ProductAgent",
                "MarketingAgent",
                "AutomationAgent"

            ]

            analysis["strategy"] = (
                "Criar curso digital, estratégia de vendas "
                "e automação"
            )


        # Pesquisa somente
        elif (
            "pesquisar" in objective_lower
            or "pesquisa" in objective_lower
            or "analisar" in objective_lower
        ):

            analysis["category"] = "research"

            analysis["recommended_agents"] = [

                "ResearchAgent"

            ]

            analysis["strategy"] = (
                "Realizar pesquisa e análise de mercado"
            )


        # Marketing somente
        elif (
            "campanha" in objective_lower
            or "vendas" in objective_lower
            or "marketing" in objective_lower
        ):

            analysis["category"] = "marketing"

            analysis["recommended_agents"] = [

                "MarketingAgent"

            ]

            analysis["strategy"] = (
                "Criar estratégia de marketing e vendas"
            )


        # Produto genérico
        elif "produto" in objective_lower:

            analysis["category"] = "digital_product"

            analysis["recommended_agents"] = [

                "ProductAgent",
                "MarketingAgent"

            ]

            analysis["strategy"] = (
                "Criar produto digital e preparar lançamento"
            )


        else:

            analysis["recommended_agents"] = [

                "ResearchAgent"

            ]

            analysis["strategy"] = (
                "Analisar objetivo antes de executar"
            )


        return {

            "engine": self.name,

            "version": self.version,

            "status": "analyzed",

            "analysis": analysis

        }


engine = AIEngine()