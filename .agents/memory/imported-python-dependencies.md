---
name: Imported Python dependency checks
description: A lightweight startup check for imported Python services before workflow setup
---

For imported Python services, test the actual application module import before configuring the long-running workflow. Imports often reveal runtime dependencies that are not listed in the original dependency file.

**Why:** A workflow can appear configured while failing immediately during application startup, making the preview diagnosis less clear.

**How to apply:** Install only the dependencies reported by the import traceback, keep the dependency file deduplicated, and repeat the import check before starting the workflow.