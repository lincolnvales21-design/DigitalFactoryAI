from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge


class ProductAgent(BaseAgent):


    def __init__(self):

        super().__init__("ProductAgent")

        self.add_capability("product_creation")
        self.add_capability("ebook")
        self.add_capability("course")
        self.add_capability("digital_product")



    async def execute_task(self, task: str):


        # Memória da execução atual
        research_context = memory.get_latest_result(
            "ResearchAgent"
        )


        # Conhecimento persistente
        knowledge_context = knowledge.latest()



        result = {

            "status": "success",

            "agent": self.name,

            "task": task,

            "research_memory_used": research_context,

            "knowledge_used": knowledge_context,

            "message": "Produto digital criado com sucesso."

        }



        memory.save(

            agent=self.name,

            task=task,

            status="completed",

            result=result

        )


        return result