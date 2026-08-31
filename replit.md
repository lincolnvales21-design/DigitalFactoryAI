# DigitalFactoryAI

## Run on Replit

The project runs as a FastAPI application using the `Start application` workflow:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

The service is available on port `5000`. Useful endpoints for a quick check:

- `/` — service health response
- `/registry` — loaded agent capabilities
- `/docs` — interactive FastAPI documentation
- `/openapi.json` — generated API schema

## Environment

The API can start without third-party credentials. AI-powered research uses
`OPENAI_API_KEY` and optionally `OPENAI_MODEL`. Payment operations may require
`MERCADOPAGO_ACCESS_TOKEN` and the gateway settings documented in
`app/payments/config.py`; add these through Replit Secrets when those features
are needed.