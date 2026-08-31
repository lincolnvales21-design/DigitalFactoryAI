from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge


class MarketingAgent(BaseAgent):

    def __init__(self):

        super().__init__("MarketingAgent")

        self.add_capability("marketing_strategy")
        self.add_capability("copywriting")
        self.add_capability("sales_page")
        self.add_capability("campaign_creation")


    async def execute_task(self, task: str):

        # ==========================================
        # Contexto do produto
        # ==========================================

        product_context = memory.get_latest_result(
            "ProductAgent"
        )

        knowledge_context = knowledge.latest()


        # ==========================================
        # Extrair produto
        # ==========================================

        product = {}

        if isinstance(product_context, dict):

            product = product_context.get(
                "product",
                {}
            )

            if not product:

                execution = product_context.get(
                    "execution",
                    {}
                )

                product = execution.get(
                    "product",
                    {}
                )


        product_id = product.get("id")
        product_name = product.get(
            "name",
            "Produto Digital"
        )

        product_type = product.get(
            "type",
            "ebook"
        )

        price = product.get(
            "price",
            19.90
        )

        currency = product.get(
            "currency",
            "USD"
        )


        # ==========================================
        # Oferta comercial
        # ==========================================

        offer = {

            "product_id": product_id,

            "product_name": product_name,

            "product_type": product_type,

            "target_audience":
                "Pessoas que querem resolver um problema específico "
                "de forma prática através de um produto digital simples.",

            "headline":
                f"Aprenda uma forma simples e prática de resolver "
                f"seu problema com {product_name}.",

            "promise":
                "Um guia objetivo, prático e fácil de aplicar, "
                "sem excesso de teoria.",

            "problem":
                "O cliente precisa de uma solução clara e prática "
                "sem precisar gastar muito tempo procurando informações.",

            "solution":
                "Um material digital estruturado com orientação passo "
                "a passo, checklist e plano de ação.",

            "benefits": [

                "Conteúdo direto ao ponto",

                "Aplicação prática",

                "Checklist para execução",

                "Plano de ação",

                "Acesso imediato ao produto digital"

            ],

            "price": price,

            "currency": currency,

            "international_price":
                "US$ 19,90",

            "brazil_price":
                "R$ 49,90",

            "sales_copy":
                f"Conheça {product_name}, um material digital criado "
                f"para ajudar você a transformar conhecimento em "
                f"ação de maneira simples e prática.",

            "call_to_action":
                "Começar agora",

            "validation_strategy":
                "Divulgar inicialmente através de tráfego orgânico, "
                "redes sociais e contatos diretos. Medir cliques, "
                "interesse e vendas antes de investir em anúncios."

        }


        # ==========================================
        # Resultado
        # ==========================================

        result = {

            "status": "success",

            "agent": self.name,

            "task": task,

            "product": product,

            "offer": offer,

            "product_memory_used": product_context,

            "knowledge_used": knowledge_context,

            "message":
                "Oferta comercial criada com sucesso."

        }


        # ==========================================
        # Memória
        # ==========================================

        memory.save(

            agent=self.name,

            task=task,

            status="completed",

            result=result

        )


        # ==========================================
        # Conhecimento
        # ==========================================

        knowledge.add(

            agent=self.name,

            knowledge={

                "type": "commercial_offer",

                "product_id": product_id,

                "product_name": product_name,

                "offer": offer

            }

        )


        return result
