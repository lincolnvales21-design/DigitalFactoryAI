from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge
from app.products.generator import product_generator
from app.database.database import get_connection
from app.pricing.pricing_engine import PricingEngine


pricing_engine = PricingEngine()

class ProductAgent(BaseAgent):

    def __init__(self):

        super().__init__("ProductAgent")

        self.add_capability("product_creation")
        self.add_capability("ebook")
        self.add_capability("course")
        self.add_capability("digital_product")


    async def execute_task(self, task: str):

        # ==========================
        # Contexto da pesquisa
        # ==========================

        research_context = memory.get_latest_result(
            "ResearchAgent"
        )

        if not research_context:

            return {
                "status": "error",
                "agent": self.name,
                "task": task,
                "message": "Nenhuma pesquisa do ResearchAgent encontrada."
            }


        # ==========================
        # Extrair pesquisa real
        # ==========================

        if isinstance(research_context, dict):

            research = research_context.get(
                "research",
                research_context
            )

        else:

            research = {}


        # ==========================
        # Conhecimento persistente
        # ==========================

        knowledge_context = knowledge.latest()


        # ==========================
        # Definição específica do produto
        # ==========================

        problem = research.get(
            "problem",
            "Problema não definido"
        )

        target_audience = research.get(
            "target_audience",
            "Público-alvo não definido"
        )

        niche = research.get(
            "niche",
            "Nicho não definido"
        )

        recommended_product = research.get(
            "recommended_product",
            "Ebook prático"
        )


        # ==========================
        # Criar título específico
        # ==========================

        title = (
            f"Guia Prático: {recommended_product}"
        )


        description = (
            "Produto digital criado automaticamente pelo "
            "DigitalFactoryAI a partir de uma pesquisa de mercado "
            "e direcionado para um problema específico."
        )


        # ==========================
        # Preço e moeda
        # ==========================

        pricing = pricing_engine.calculate(
             research=research,
             task=task
        )

        price = pricing["price"]
        currency = pricing["currency"]


        # ==========================
        # Registrar produto
        # ==========================

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO products (
                name,
                description,
                product_type,
                price,
                currency,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                "ebook",
                price,
                currency,
                "draft"
            )
        )

        product_id = cursor.lastrowid

        connection.commit()
        connection.close()


        # ==========================
        # Gerar ebook específico
        # ==========================

        generated = product_generator.create_ebook(
            title=title,
            research=research,
            product_id=product_id
        )


        # ==========================
        # Resultado
        # ==========================

        result = {

            "status": "success",

            "agent": self.name,

            "task": task,

            "product": {

                "id": product_id,

                "name": title,

                "type": "ebook",

                "price": price,

                "currency": currency,

                "status": "draft",

                "file": generated["path"]

            },

            "product_definition": {

                "problem": problem,

                "target_audience": target_audience,

                "niche": niche,

                "recommended_product": recommended_product

            },

            "research_memory_used": research_context,

            "knowledge_used": knowledge_context,

            "message": (
                "Produto digital específico criado "
                "e registrado com sucesso."
            )

        }


        # ==========================
        # Memória
        # ==========================

        memory.save(

            agent=self.name,

            task=task,

            status="completed",

            result=result

        )


        return result
