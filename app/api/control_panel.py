from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Factory Control Panel"])

HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>DigitalFactoryAI — Controle</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    font-family: Arial, sans-serif;
    background: #0f172a;
    color: #f8fafc;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.panel {
    width: 100%;
    max-width: 780px;
    background: #111827;
    border: 1px solid #334155;
    border-radius: 18px;
    padding: 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,.35);
}

h1 {
    margin: 0;
    font-size: 30px;
}

.subtitle {
    color: #94a3b8;
    margin: 8px 0 28px;
}

.status {
    background: #020617;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 25px;
}

.status-label {
    color: #94a3b8;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.status-value {
    font-size: 24px;
    font-weight: bold;
    margin-top: 8px;
}

.section {
    margin-top: 25px;
}

.section-title {
    font-size: 14px;
    font-weight: bold;
    color: #cbd5e1;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

button {
    border: 0;
    border-radius: 12px;
    padding: 17px 12px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    background: #334155;
    color: white;
}

button:hover {
    opacity: .88;
}

.start {
    background: #15803d;
}

.emergency {
    margin-top: 32px;
    padding-top: 26px;
    border-top: 2px solid #7f1d1d;
}

.emergency-box {
    background: #2b0b0b;
    border: 2px solid #991b1b;
    border-radius: 14px;
    padding: 20px;
}

.emergency-title {
    color: #fca5a5;
    font-size: 19px;
    font-weight: bold;
}

.emergency-text {
    color: #fecaca;
    font-size: 14px;
    line-height: 1.5;
    margin: 10px 0 16px;
}

.emergency button {
    width: 100%;
    background: #dc2626;
}

.release {
    margin-top: 12px;
    width: 100%;
    background: #7f1d1d;
}

.message {
    margin-top: 20px;
    min-height: 24px;
    text-align: center;
    color: #cbd5e1;
}

.security-state {
    margin-top: 15px;
    padding: 12px;
    border-radius: 10px;
    background: #020617;
    color: #94a3b8;
    font-size: 13px;
}

.footer {
    margin-top: 25px;
    text-align: center;
    color: #64748b;
    font-size: 12px;
}

@media (max-width: 560px) {
    .buttons {
        grid-template-columns: 1fr;
    }

    .panel {
        padding: 20px;
    }
}
</style>
</head>

<body>

<div class="panel">

    <h1>DigitalFactoryAI</h1>

    <div class="subtitle">
        Painel de Controle da Fábrica Autônoma
    </div>

    <div class="status">

        <div class="status-label">
            Estado da fábrica
        </div>

        <div id="status" class="status-value">
            Consultando...
        </div>

        <div id="security" class="security-state">
            Segurança: consultando...
        </div>

    </div>


    <div class="section">

        <div class="section-title">
            🔐 Controle operacional
        </div>

        <div class="buttons">

            <button class="start"
                    onclick="operational('/factory/start')">
                🟢 INICIAR
            </button>

            <button onclick="operational('/factory/pause')">
                ⏸ PAUSAR
            </button>

            <button onclick="operational('/factory/resume')">
                ▶ RETOMAR
            </button>

            <button onclick="operational('/factory/stop')">
                ⏹ PARAR
            </button>

        </div>

    </div>


    <div class="emergency">

        <div class="section-title">
            🚨 SEGURANÇA MÁXIMA
        </div>

        <div class="emergency-box">

            <div class="emergency-title">
                DESLIGAR + ZERAR EVOLUÇÃO
            </div>

            <div class="emergency-text">
                Este comando interrompe a inteligência autônoma,
                zera a memória de evolução e bloqueia o reinício.
                Produtos, pedidos, pagamentos e dados financeiros
                permanecem preservados.
            </div>

            <button onclick="emergencyShutdown()">
                🔴 DESLIGAR / RESET DE EMERGÊNCIA
            </button>

            <button class="release"
                    onclick="releaseEmergency()">
                🔐 LIBERAR APÓS EMERGÊNCIA
            </button>

        </div>

    </div>


    <div id="message" class="message"></div>

    <div class="footer">
        Controle protegido do proprietário
    </div>

</div>


<script>

async function getStatus() {

    try {

        const response =
            await fetch('/factory/status');

        const data =
            await response.json();

        const status =
            document.getElementById('status');

        const security =
            document.getElementById('security');


        if (data.emergency_off) {

            status.textContent =
                '🔴 DESLIGADA — SEGURANÇA MÁXIMA';

            security.textContent =
                '🚨 Kill Switch ativo — reinício bloqueado';

            return;
        }


        if (data.running) {

            status.textContent =
                '🟢 EM EXECUÇÃO';

        } else if (data.paused) {

            status.textContent =
                '⏸ PAUSADA';

        } else {

            status.textContent =
                '⚪ PARADA';
        }


        security.textContent =
            '🔐 Controles protegidos';

    } catch (error) {

        document.getElementById('status').textContent =
            '⚠️ INDISPONÍVEL';

        document.getElementById('security').textContent =
            'Segurança: não foi possível consultar';

    }
}


async function operational(endpoint) {

    const code = prompt(
        '🔐 Digite seu código de segurança operacional:'
    );

    if (code === null || code === '') {
        return;
    }


    try {

        const response =
            await fetch(
                endpoint,
                {
                    method: 'POST',
                    headers: {
                        'X-Factory-Control-Code': code
                    }
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail || 'Acesso negado.'
            );
        }


        showMessage(
            '✅ Comando executado.'
        );

        await getStatus();

    } catch (error) {

        showMessage(
            '❌ ' + error.message
        );
    }
}


async function emergencyShutdown() {

    const confirmation =
        confirm(
            '🚨 SEGURANÇA MÁXIMA\n\n' +
            'O sistema irá:\n\n' +
            '• parar a inteligência autônoma\n' +
            '• zerar a memória de evolução\n' +
            '• bloquear o reinício automático\n\n' +
            'Produtos, pedidos, pagamentos e dados financeiros serão preservados.\n\n' +
            'CONFIRMA O DESLIGAMENTO?'
        );


    if (!confirmation) {
        return;
    }


    const code =
        prompt(
            '🚨 CÓDIGO DE EMERGÊNCIA\n\n' +
            'Digite o código secreto de segurança máxima:'
        );


    if (code === null || code === '') {
        return;
    }


    try {

        const response =
            await fetch(
                '/emergency/shutdown',
                {
                    method: 'POST',
                    headers: {
                        'X-Factory-Stop-Code': code
                    }
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                'Código de emergência incorreto.'
            );
        }


        showMessage(
            '🚨 DESLIGAMENTO DE EMERGÊNCIA EXECUTADO.'
        );

        await getStatus();

    } catch (error) {

        showMessage(
            '❌ ' + error.message
        );
    }
}


async function releaseEmergency() {

    const confirmation =
        confirm(
            '🔐 LIBERAÇÃO DE SEGURANÇA\n\n' +
            'Isso NÃO recupera a memória apagada.\n\n' +
            'Apenas libera a fábrica para que você possa iniciá-la novamente.\n\n' +
            'Deseja continuar?'
        );


    if (!confirmation) {
        return;
    }


    const code =
        prompt(
            '🔐 CÓDIGO DE EMERGÊNCIA\n\n' +
            'Digite o código de segurança máxima para liberar a fábrica:'
        );


    if (code === null || code === '') {
        return;
    }


    try {

        const response =
            await fetch(
                '/emergency/release',
                {
                    method: 'POST',
                    headers: {
                        'X-Factory-Stop-Code': code
                    }
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                'Liberação negada.'
            );
        }


        showMessage(
            '🔐 Fábrica liberada pelo proprietário.'
        );

        await getStatus();

    } catch (error) {

        showMessage(
            '❌ ' + error.message
        );
    }
}


function showMessage(text) {

    document.getElementById(
        'message'
    ).textContent = text;
}


getStatus();

setInterval(
    getStatus,
    5000
);

</script>

</body>
</html>
"""


@router.get(
    "/factory/control",
    response_class=HTMLResponse
)
def factory_control_panel():

    return HTML
