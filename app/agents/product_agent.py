from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge
from app.products.generator import product_generator
from app.database.database import get_connection


class ProductAgent(BaseAgent):

    def __init__(self):

        super().__init__("ProductAgent")

        self.add_capability("product_creation")
        self.add_capability("ebook")
        self.add_capability("course")
        self.add_capability("digital_product")

    async def execute_task(self, task: str):

        # ==========================
        # Contexto de pesquisa
        # ==========================

        research_context = memory.get_latest_result(
            "ResearchAgent"
        )

        # ==========================
        # Conhecimento persistente
        # ==========================

        knowledge_context = knowledge.latest()

        # ==========================
        # Definição do produto
        # ==========================

        title = "Produto Digital - Oportunidade de Mercado"

        description = (
            "Produto digital criado automaticamente pelo "
            "DigitalFactoryAI a partir de pesquisa de mercado."
        )

        price = 19.90
        currency = "USD"

        # ==========================
        # Gerar produto
        # ==========================

        generated = product_generator.create_ebook(
            title=title,
            research=research_context
        )

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
            "research_memory_used": research_context,
            "knowledge_used": knowledge_context,
            "message": "Produto digital criado e registrado com sucesso."
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