// frontend/game.js

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let ws = null;
let isGameRunning = false;

// Tasten-Status für Input
const keys = {
    ArrowUp: false,
    ArrowLeft: false,
    ArrowRight: false,
    Space: false
};

// Event Listeners für Tasten
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') keys.Space = true;
    if (e.code === 'ArrowUp') keys.ArrowUp = true;
    if (e.code === 'ArrowLeft') keys.ArrowLeft = true;
    if (e.code === 'ArrowRight') keys.ArrowRight = true;
    
    // Verhindert Scrollen bei Pfeiltasten
    if(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
        e.preventDefault();
    }
});

document.addEventListener('keyup', (e) => {
    if (e.code === 'Space') keys.Space = false;
    if (e.code === 'ArrowUp') keys.ArrowUp = false;
    if (e.code === 'ArrowLeft') keys.ArrowLeft = false;
    if (e.code === 'ArrowRight') keys.ArrowRight = false;
});

async function startGame() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    const errorMsg = document.getElementById('errorMsg');
    errorMsg.style.display = 'none';

    // Protokoll (ws oder wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/game`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        // 1. Authentifizierung senden
        ws.send(token);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Fehlerhandling (z.B. zu wenig Gems)
        if (data.error) {
            errorMsg.innerText = data.error;
            errorMsg.style.display = 'block';
            ws.close();
            return;
        }

        // Spielstart bestätigt?
        if (!isGameRunning && data.status === "playing") {
            isGameRunning = true;
            document.getElementById('startScreen').classList.add('hidden');
        }

        // Game Over / Sieg Handling
        if (data.status === "game_over" || data.status === "won") {
            handleGameEnd(data);
            return;
        }

        // === RENDERING LOOP ===
        if (isGameRunning) {
            drawGame(data);
            // Input senden (Einfachheitshalber senden wir den gesamten Key-State)
            sendInput();
            
            // HUD Update
            document.getElementById('scoreDisplay').innerText = data.score;
            document.getElementById('statusDisplay').innerText = data.platform_active ? "LANDEN! 🔽" : "ÜBERLEBEN 🛡️";
            if(data.platform_active) document.getElementById('statusDisplay').style.color = "#28a745";
        }
    };

    ws.onclose = () => {
        console.log("Verbindung getrennt");
        isGameRunning = false;
    };
    
    ws.onerror = (e) => {
        console.error("WebSocket Fehler", e);
        errorMsg.innerText = "Verbindungsfehler zum Server.";
        errorMsg.style.display = 'block';
    };
}

function sendInput() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Wir senden ein JSON mit den gedrückten Tasten
        ws.send(JSON.stringify(keys));
    }
}

function drawGame(state) {
    // 1. Hintergrund löschen
    ctx.fillStyle = '#0f0f1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Sterne (Optionaler Effekt, statisch oder vom Server gesendet)
    // Hier einfachheitshalber weggelassen oder einfache Punkte

    // 3. Rakete zeichnen
    ctx.save();
    ctx.translate(state.rocket.x, state.rocket.y);
    ctx.rotate(state.rocket.angle); // Rotation vom Server!
    
    // Raketenkörper
    ctx.fillStyle = '#00d2ff';
    ctx.beginPath();
    ctx.moveTo(0, -15);
    ctx.lineTo(10, 10);
    ctx.lineTo(-10, 10);
    ctx.fill();
    
    // Flamme (nur wenn Schub)
    if (keys.ArrowUp) {
        ctx.fillStyle = '#ff6b6b';
        ctx.beginPath();
        ctx.moveTo(-5, 10);
        ctx.lineTo(5, 10);
        ctx.lineTo(0, 20 + Math.random() * 5);
        ctx.fill();
    }
    ctx.restore();

    // 4. Aliens zeichnen
    ctx.fillStyle = '#ff4757';
    state.aliens.forEach(alien => {
        ctx.fillRect(alien.x, alien.y, alien.w, alien.h);
        // Kleine Augen
        ctx.fillStyle = 'white';
        ctx.fillRect(alien.x + 5, alien.y + 10, 5, 5);
        ctx.fillRect(alien.x + 20, alien.y + 10, 5, 5);
        ctx.fillStyle = '#ff4757'; // Zurücksetzen
    });

    // 5. Projektile zeichnen
    ctx.fillStyle = '#ffff00';
    state.bullets.forEach(bullet => {
        ctx.beginPath();
        ctx.arc(bullet.x, bullet.y, 3, 0, Math.PI * 2);
        ctx.fill();
    });

    // 6. Plattform zeichnen (wenn aktiv)
    if (state.platform && state.platform.active) {
        ctx.fillStyle = '#28a745';
        ctx.fillRect(state.platform.x, state.platform.y, state.platform.w, state.platform.h);
        
        // Landebereich markieren
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillRect(state.platform.x + 5, state.platform.y, state.platform.w - 10, 5);
        
        ctx.fillStyle = 'white';
        ctx.font = '12px Arial';
        ctx.fillText("LAND HERE", state.platform.x + 15, state.platform.y + 20);
    }
}

function handleGameEnd(data) {
    isGameRunning = false;
    const screen = document.getElementById('resultScreen');
    const title = document.getElementById('resultTitle');
    const details = document.getElementById('resultDetails');
    
    screen.classList.remove('hidden');
    
    if (data.status === "won") {
        title.innerText = "MISSION ERFÜLLT! 🏆";
        title.style.color = "#28a745";
        details.innerHTML = `
            <p>Sicher gelandet!</p>
            <p style="font-size: 1.5em; margin-top: 10px;">+42 XP erhalten!</p>
        `;
    } else {
        title.innerText = "ABGESTÜRZT 💥";
        title.style.color = "#dc3545";
        details.innerHTML = `
            <p>Score: ${data.score}</p>
            <p>Viel Glück beim nächsten Mal!</p>
        `;
    }
}