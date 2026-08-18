import json
import os
from threading import Lock


SECURITY_FILE = "digitalfactory_emergency.json"


class EmergencyStop:

    def __init__(self):

        self._lock = Lock()

        self._stopped = False
        self._reason = None

        self._load()


    def _load(self):

        if os.path.exists(SECURITY_FILE):

            with open(SECURITY_FILE, "r") as file:

                data = json.load(file)

                self._stopped = data.get(
                    "active",
                    False
                )

                self._reason = data.get(
                    "reason"
                )


    def _save(self):

        with open(SECURITY_FILE, "w") as file:

            json.dump(
                {
                    "active": self._stopped,
                    "reason": self._reason
                },
                file,
                indent=4
            )


    def activate(
        self,
        reason="Emergency stop activated"
    ):

        with self._lock:

            self._stopped = True
            self._reason = reason

            self._save()


        return {
            "status": "stopped",
            "reason": self._reason
        }



    def deactivate(self):

        with self._lock:

            self._stopped = False
            self._reason = None

            self._save()


        return {
            "status": "running"
        }



    def is_active(self):

        self._load()

        return self._stopped



    def status(self):

        self._load()

        return {
            "active": self._stopped,
            "reason": self._reason
        }



emergency_stop = EmergencyStop()