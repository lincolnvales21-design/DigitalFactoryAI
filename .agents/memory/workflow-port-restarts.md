---
name: Workflow port restarts
description: Environment-specific behavior when restarting the FastAPI workflow.
---

When the FastAPI workflow reports that port 5000 is already in use after a restart, inspect the running Uvicorn process before retrying; a prior workflow child can remain alive even while the workflow is marked failed.

**Why:** Repeated restarts can create a port conflict instead of fixing the application, while the already-running process may still serve the previous code.

**How to apply:** Check the workflow log and the process listening on port 5000, stop only the identified stale Uvicorn process, then restart the configured workflow once.