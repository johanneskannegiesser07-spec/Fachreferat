// frontend/common.js - Gemeinsame Funktionen
const API_BASE = 'http://localhost:8000';
let debugEnabled = false;

// --- AUTH SYSTEM ---
async function checkAuthentication(redirectIfMissing = true) {
    const token = localStorage.getItem('token');
    if (!token) {
        if (redirectIfMissing) window.location.href = '/login';
        return null;
    }

    try {
        // Wir prüfen nur lokal auf Token-Existenz um Ladezeiten zu sparen,
        // echte Prüfung passiert beim ersten API Call.
        // Optional: /api/check-auth aufrufen
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            updateUserDisplay(user.username);
            return user;
        }
    } catch (e) {
        console.error("Auth Fehler:", e);
        logout();
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

function updateUserDisplay(username) {
    const display = document.getElementById('usernameDisplay');
    if (display) display.textContent = username;
}

// --- API SYSTEM ---
async function apiCall(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('token');
    
    if (!token && endpoint !== '/api/login' && endpoint !== '/api/register') {
        window.location.href = '/login';
        return;
    }

    try {
        debugLog(`API ${method}: ${endpoint}`);
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            }
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (response.status === 401) {
            logout(); // Token abgelaufen
            return;
        }
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Unbekannter Fehler');
        }
        
        return result;
    } catch (error) {
        showOutput(`❌ Fehler: ${error.message}`, 'error-msg');
        debugLog('API Error: ' + error.message);
        throw error;
    }
}

// --- UTILS ---
function showOutput(message, className = '') {
    const output = document.getElementById('output');
    // Suche nach globalem Output oder lokalem Message-Div
    const target = output || document.getElementById('message');
    if (target) {
        target.innerHTML = `<div class="${className}">${message}</div>`;
        target.style.display = 'block';
    }
    console.log(`[APP] ${message}`);
}

function debugLog(message) {
    if (!debugEnabled) return;
    const debugDiv = document.getElementById('debug');
    if (debugDiv) {
        debugDiv.innerHTML += `<div>${new Date().toLocaleTimeString()}: ${message}</div>`;
        debugDiv.scrollTop = debugDiv.scrollHeight;
    }
    console.log(`[DEBUG] ${message}`);
}

function toggleDebug() {
    debugEnabled = !debugEnabled;
    const debugDiv = document.getElementById('debug');
    if (debugDiv) debugDiv.style.display = debugEnabled ? 'block' : 'none';
}