import os

from fastapi import Header, HTTPException


def verify_operational_code(
    x_factory_control_code: str | None = Header(default=None),
):
    """
    Segurança dos controles normais da fábrica.

    Protege:
    - iniciar
    - pausar
    - retomar
    - parar

    NÃO é o código do Kill Switch de emergência.
    """

    configured = os.getenv("FACTORY_CONTROL_CODE")

    if not configured:
        raise HTTPException(
            status_code=503,
            detail="Código operacional não configurado.",
        )

    if not x_factory_control_code:
        raise HTTPException(
            status_code=401,
            detail="Código operacional obrigatório.",
        )

    if x_factory_control_code != configured:
        raise HTTPException(
            status_code=403,
            detail="Acesso operacional negado.",
        )

    return True
