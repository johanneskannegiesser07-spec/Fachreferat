// frontend/game.js

console.log("Game Script geladen! (High Fidelity Version)");

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// UI Elemente
const startScreen = document.getElementById('startScreen');
const resultScreen = document.getElementById('resultScreen');
const hud = document.getElementById('hud');
const errorMsg = document.getElementById('errorMsg');

let ws = null;
let isGameRunning = false;
let particles = [];
let stars = [];

// Sterne initialisieren
for (let i = 0; i < 80; i++) {
    stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2,
        alpha: Math.random()
    });
}

// Input Status
const keys = { ArrowUp: false, ArrowLeft: false, ArrowRight: false, Space: false };

document.addEventListener('keydown', (e) => {
    if (['ArrowUp', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
        e.preventDefault();
        keys[e.code] = true;
    }
});
document.addEventListener('keyup', (e) => {
    if (['ArrowUp', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
        keys[e.code] = false;
    }
});

// === HAUPTFUNKTION ===

async function startGame() {
    console.log("Start Button gedrückt...");
    try {
        const token = localStorage.getItem('token');
        errorMsg.style.display = 'none';

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/game`;

        if (ws) ws.close();
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            if (token) ws.send(token);
            startScreen.classList.add('hidden');
            resultScreen.classList.add('hidden');
            hud.classList.remove('hidden');
            isGameRunning = true;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.error) { showError(data.error); return; }

                if (isGameRunning) {
                    drawGame(data);
                    sendInput();
                    updateHUD(data);
                }

                if (data.status === "game_over" || data.status === "won") {
                    endGame(data);
                }
            } catch (e) { console.error(e); }
        };

        ws.onerror = (e) => showError("Verbindung fehlgeschlagen!");
        ws.onclose = () => { if (isGameRunning) isGameRunning = false; };

    } catch (err) {
        showError("Fehler: " + err.message);
    }
}
window.startGame = startGame;

// === HELFER ===

function sendInput() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(keys));
    }
}

function updateHUD(data) {
    document.getElementById('scoreDisplay').innerText = `SCORE: ${data.score}`;
    const statusEl = document.getElementById('statusDisplay');
    if (data.platform_active) {
        statusEl.innerText = "LANDEN! 🔽"; statusEl.style.color = "#2ecc71";
    } else {
        statusEl.innerText = "ÜBERLEBEN 🛡️"; statusEl.style.color = "#fff";
    }
}

function endGame(data) {
    isGameRunning = false;
    hud.classList.add('hidden');
    resultScreen.classList.remove('hidden');
    const title = document.getElementById('resultTitle');
    const details = document.getElementById('resultDetails');

    if (data.status === "won") {
        title.innerText = "MISSION ERFÜLLT! 🏆"; title.className = "win-text";
        details.innerHTML = `Perfekte Landung!<br>+42 XP erhalten.`;
    } else {
        title.innerText = "GESCHEITERT 💥"; title.className = "lose-text";
        details.innerHTML = `Score: ${data.score}`;
    }
}

function showError(msg) {
    if (ws) ws.close();
    isGameRunning = false;
    startScreen.classList.remove('hidden');
    hud.classList.add('hidden');
    errorMsg.innerText = msg;
    errorMsg.style.display = 'block';
}

// === RENDERING (High Fidelity Version) ===

class Particle {
    constructor(x, y) {
        this.x = x + (Math.random() - 0.5) * 10;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 2;
        this.vy = Math.random() * 4 + 2;
        this.life = 1.0;
        this.decay = Math.random() * 0.05 + 0.02;
    }
    update() { this.x += this.vx; this.y += this.vy; this.life -= this.decay; }
    draw(ctx) {
        ctx.globalAlpha = Math.max(0, this.life);
        ctx.fillStyle = `rgb(255, ${Math.floor(this.life * 200)}, 0)`;
        ctx.beginPath(); ctx.arc(this.x, this.y, 3, 0, Math.PI*2); ctx.fill();
        ctx.globalAlpha = 1.0;
    }
}

function drawGame(state) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Sterne
    ctx.fillStyle = "#fff";
    stars.forEach(s => {
        ctx.globalAlpha = Math.random() * 0.5 + 0.3;
        ctx.fillRect(s.x, s.y, s.size, s.size);
    });
    ctx.globalAlpha = 1.0;

    // Plattform (Mit Gradient & Glow)
    if (state.platform) {
        let p = state.platform;
        ctx.save();
        
        ctx.shadowBlur = 20;
        ctx.shadowColor = "#4caf50";

        let pGrad = ctx.createLinearGradient(0, p.y - p.height / 2, 0, p.y + p.height / 2);
        pGrad.addColorStop(0, "#2e7d32");
        pGrad.addColorStop(1, "#1b5e20");

        ctx.fillStyle = pGrad;
        // ZENTRIERT ZEICHNEN
        ctx.fillRect(p.x - p.width / 2, p.y - p.height / 2, p.width, p.height);

        // Lichter
        ctx.fillStyle = "#a5d6a7";
        ctx.fillRect(p.x - p.width / 2 + 5, p.y - p.height / 2 + 2, p.width - 10, 4);

        ctx.restore();
    }

    // Aliens (Mit Gradient & Glow)
    state.aliens.forEach(a => drawAlien(a.x, a.y, a.width, a.height));

    // Rakete (Mit Gradient)
    if (!state.rocket.dead) {
        if (keys.ArrowUp) { 
            for(let i=0; i<3; i++) particles.push(new Particle(state.rocket.x, state.rocket.y + 15));
        }
        drawRocket(state.rocket.x, state.rocket.y, state.rocket.angle);
    } else {
        // Explosion
        ctx.fillStyle = "orange";
        ctx.beginPath(); ctx.arc(state.rocket.x, state.rocket.y, 30, 0, Math.PI * 2); ctx.fill();
        for(let i=0; i<5; i++) particles.push(new Particle(state.rocket.x, state.rocket.y));
    }

    // Partikel
    particles.forEach((p, i) => {
        p.update();
        p.draw(ctx);
        if (p.life <= 0) particles.splice(i, 1);
    });

    // Bullets (Mit Glow)
    ctx.save();
    ctx.shadowBlur = 5;
    ctx.shadowColor = "#f00";
    ctx.fillStyle = "#ff5555";
    state.bullets.forEach(b => {
        ctx.beginPath(); ctx.arc(b.x, b.y, 4, 0, Math.PI*2); ctx.fill();
    });
    ctx.restore();
}

function drawRocket(x, y, angle) {
    ctx.save();
    ctx.translate(x, y);
    // Rotation ist wichtig!
    ctx.rotate(angle); 

    // 3D-Body Gradient (Das macht es zur Textur!)
    let grad = ctx.createLinearGradient(-10, 0, 10, 0);
    grad.addColorStop(0, '#ccc');
    grad.addColorStop(0.5, '#fff');
    grad.addColorStop(1, '#999');

    ctx.fillStyle = grad;

    // Rumpf
    ctx.beginPath();
    ctx.ellipse(0, 0, 10, 20, 0, 0, Math.PI * 2);
    ctx.fill();

    // Cockpit
    ctx.fillStyle = "#00a8ff";
    ctx.beginPath(); ctx.arc(0, -5, 4, 0, Math.PI * 2); ctx.fill();

    // Flügel
    ctx.fillStyle = "#d63031";
    ctx.beginPath();
    ctx.moveTo(-10, 10); ctx.lineTo(-15, 20); ctx.lineTo(-5, 15); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(10, 10); ctx.lineTo(15, 20); ctx.lineTo(5, 15); ctx.fill();

    // Düse
    ctx.fillStyle = "#333";
    ctx.fillRect(-5, 18, 10, 4);

    ctx.restore();
}

function drawAlien(x, y, w, h) {
    ctx.save();
    ctx.translate(x, y);

    // Glow Effekt (Grüner Schein)
    ctx.shadowBlur = 10;
    ctx.shadowColor = "#00ff00";

    // Kuppel mit Radial Gradient
    let domeGrad = ctx.createRadialGradient(0, -5, 0, 0, -5, 10);
    domeGrad.addColorStop(0, "#aaffaa");
    domeGrad.addColorStop(1, "#00aa00");
    ctx.fillStyle = domeGrad;
    ctx.beginPath(); ctx.arc(0, -5, 10, Math.PI, 0); ctx.fill();

    // Untertasse
    ctx.fillStyle = "#555";
    ctx.beginPath(); ctx.ellipse(0, 0, 18, 6, 0, 0, Math.PI * 2); ctx.fill();

    // Lichter
    ctx.fillStyle = "#ffff00";
    for (let i = -2; i <= 2; i++) {
        ctx.beginPath(); ctx.arc(i * 6, 2, 2, 0, Math.PI * 2); ctx.fill();
    }

    ctx.restore();
}