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


        # Memória da execução atual
        product_context = memory.get_latest_result(
            "ProductAgent"
        )


        # Conhecimento persistente
        knowledge_context = knowledge.latest()



        result = {

            "status": "success",

            "agent": self.name,

            "task": task,

            "product_memory_used": product_context,

            "knowledge_used": knowledge_context,

            "message": "Estratégia de marketing criada com sucesso."

        }



        memory.save(

            agent=self.name,

            task=task,

            status="completed",

            result=result

        )


        return result