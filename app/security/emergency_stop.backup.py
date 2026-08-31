from threading import Lock


class EmergencyStop:

    def __init__(self):

        self._stopped = False
        self._reason = None
        self._lock = Lock()


    def activate(self, reason="Emergency stop activated"):

        with self._lock:

            self._stopped = True
            self._reason = reason

        return {
            "status": "stopped",
            "reason": self._reason
        }


    def deactivate(self):

        with self._lock:

            self._stopped = False
            self._reason = None

        return {
            "status": "running"
        }


    def is_active(self):

        return self._stopped


    def status(self):

        return {
            "active": self._stopped,
            "reason": self._reason
        }


emergency_stop = EmergencyStop()
