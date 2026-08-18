from datetime import datetime

from app.memory.agent_memory import memory


class TaskService:

    def execute(self, task: str, agent: str = "SystemAgent"):

        result = {
            "task": task,
            "status": "completed",
            "executed_at": datetime.now().isoformat()
        }


        memory.save(
            agent=agent,
            task=task,
            status="completed"
        )


        return result


task_service = TaskService()