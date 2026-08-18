from app.agents.base import BaseAgent
from app.memory.agent_memory import memory
from app.knowledge.knowledge_base import knowledge


class ResearchAgent(BaseAgent):

    def __init__(self):

        super().__init__("ResearchAgent")

        self.add_capability("market_research")
        self.add_capability("niche_analysis")
        self.add_capability("trend_analysis")


    async def execute_task(self, task: str):

        result = {
            "status": "success",
            "agent": self.name,
            "task": task,
            "message": "Pesquisa de mercado concluída."
        }


        # Salva histórico de execução
        memory.save(
            agent=self.name,
            task=task,
            status="completed",
            result=result
        )


        # Salva conhecimento extraído
        knowledge.add(
            agent=self.name,
            knowledge={
                "type": "market_research",
                "topic": task,
                "insight": "Mercado analisado com oportunidade para criação de produtos digitais."
            }
        )


        return result