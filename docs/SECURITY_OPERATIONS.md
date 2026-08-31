# DigitalFactoryAI
# Manual Operacional de Segurança

Versão: 1.0

---

# 1. Objetivo

Este documento descreve os procedimentos para operar, proteger, bloquear e recuperar o sistema DigitalFactoryAI.

O módulo de segurança controla:

- Secrets
- Vault criptografado
- Audit Log
- Permissões
- Agent Guard
- Emergency Stop

---

# 2. Iniciar o DigitalFactoryAI

Entrar no projeto:

```bash
cd /workspaces/DigitalFactoryAI

Ativar ambiente:

source /opt/conda/etc/profile.d/conda.sh && conda activate base

Iniciar API:

uvicorn app.main:app --reload

Sistema iniciado quando aparecer:

Application startup complete.
3. Verificar sistema

Teste:

curl http://localhost:8000/

Resposta esperada:

{
 "system":"DigitalFactoryAI",
 "status":"online"
}
4. Verificar segurança

Comando:

curl http://localhost:8000/admin/security/status

Sistema normal:

{
 "security":"online",
 "emergency_stop":{
    "active":false,
    "reason":null
 }
}
5. Emergency Stop
Objetivo

Bloquear imediatamente qualquer execução de agente.

Quando ativado:

Usuário
   |
AgentManager
   |
AgentGuard
   |
Emergency Stop
   |
BLOQUEADO
Ativar bloqueio

Comando:

curl -X POST http://localhost:8000/admin/security/shutdown \
-H "Content-Type: application/json" \
-d '{"secret":"SEU_SECRET","reason":"Motivo do bloqueio"}'

Exemplo:

{
 "status":"stopped",
 "reason":"Teste de segurança"
}
6. Testar bloqueio

Executar agente:

python -c "import asyncio; from app.agents.loader import load_agents; from app.agents.manager import manager; from app.security.permissions import Role; load_agents(); print(asyncio.run(manager.execute(Role.OWNER,'execute_agents','ResearchAgent','Teste')))"

Resultado esperado:

{
 "allowed":false,
 "status":"blocked",
 "reason":"Emergency Stop ativo."
}
7. Liberar sistema

Comando:

curl -X POST http://localhost:8000/admin/security/start \
-H "Content-Type: application/json" \
-d '{"secret":"SEU_SECRET"}'

Resposta:

{
 "status":"running"
}
8. Execução autorizada

Teste:

python -c "import asyncio; from app.agents.loader import load_agents; from app.agents.manager import manager; from app.security.permissions import Role; load_agents(); print(asyncio.run(manager.execute(Role.OWNER,'execute_agents','ResearchAgent','Analisar mercado de IA')))"

Resultado esperado:

{
 "status":"success"
}
9. Audit Log

Consultar eventos:

python -c "from app.security.audit import audit; print(audit.latest())"

Eventos registrados:

SECRET_STORED
SECRET_ROTATION
EMERGENCY_SHUTDOWN
SYSTEM_UNLOCK
AGENT_AUTHORIZED
AGENT_BLOCKED
10. Vault de Secrets

Os secrets são armazenados criptografados.

Arquivo:

digitalfactory_vault.json

Nunca editar manualmente.

Exemplo:

{
 "master_secret":{
    "value":"gAAAAAB..."
 }
}

O conteúdo criptografado não deve ser alterado.

11. Parar o sistema

No terminal da API:

CTRL + C
12. Derrubar processo manualmente

Ver processos:

ps aux | grep uvicorn

Encerrar:

kill PID

Exemplo:

kill 15297
13. Recuperação de emergência

Caso o sistema fique travado:

Encerrar API
CTRL + C
Ver processos:
ps aux | grep uvicorn
Encerrar processo:
kill PID
Verificar Emergency Stop:
cat digitalfactory_emergency.json
Liberar sistema:
curl -X POST http://localhost:8000/admin/security/start \
-H "Content-Type: application/json" \
-d '{"secret":"SEU_SECRET"}'
14. Regras de segurança
Nunca:
Remover AgentGuard
Executar agentes ignorando AgentManager
Alterar secrets manualmente
Apagar Vault sem backup
Desativar Emergency Stop sem autorização
Sempre:
Conferir status antes de executar agentes
Consultar Audit Log após alterações
Manter backup dos arquivos de segurança
Testar bloqueios antes de liberar mudanças
15. Arquitetura de Segurança Atual
DigitalFactoryAI

Security Layer

├── Secret Manager
├── Vault Encryption
├── Audit Log
├── Permissions
├── Agent Guard
└── Emergency Stop Persistente


Agent Execution

Request
  |
AgentManager
  |
AgentGuard
  |
Permission Check
  |
Emergency Check
  |
Agent
Status

Segurança do DigitalFactoryAI:

✅ Vault criptografado
✅ Secrets protegidos
✅ Audit funcionando
✅ Permissions funcionando
✅ Agent Guard integrado
✅ Emergency Stop persistente
✅ Bloqueio entre processos validado