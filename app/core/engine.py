from datetime import datetime


class DigitalFactoryEngine:

    def __init__(self):
        self.name = "DigitalFactoryAI Engine"
        self.status = "initialized"
        self.created_at = datetime.now()

    def start(self):
        self.status = "running"

        return {
            "engine": self.name,
            "status": self.status,
            "started_at": self.created_at.isoformat()
        }


engine = DigitalFactoryEngine()