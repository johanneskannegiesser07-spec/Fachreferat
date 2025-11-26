// frontend/app.js
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (!token || !user) {
        // Nicht eingeloggt - redirect zu Login
        window.location.href = '/login';
        return;
    }
    
    // Eingeloggt - User Info anzeigen
    try {
        const userData = JSON.parse(user);
        showUserInfo(userData);
        loadUserData(userData.username); // User-spezifische Daten laden
    } catch (e) {
        console.error('Fehler beim Laden der User-Daten:', e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
});

function showUserInfo(user) {
    // User-Info in der Navigation anzeigen
    const userInfoHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span>👤 <strong>${user.username}</strong></span>
            <button onclick="logout()" style="padding: 5px 10px; font-size: 14px;">Logout</button>
        </div>
    `;
    
    // Füge User-Info zum Header hinzu
    const header = document.querySelector('header');
    if (header) {
        header.innerHTML += userInfoHTML;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

function loadUserData(username) {
    // Alle API-Calls mit dem aktuellen User durchführen
    document.getElementById('userId').value = username;
    document.getElementById('sessionUserId').value = username;
    document.getElementById('analyticsUserId').value = username;
    document.getElementById('schoolUserId').value = username;
}



const API_BASE = 'http://localhost:8000';

function showOutput(message, className = '') {
    const output = document.getElementById('output');
    output.innerHTML = `<div class="${className}">${message}</div>`;
}

function showJsonOutput(data, title = 'Daten') {
    const output = document.getElementById('output');
    output.innerHTML = `
        <h3>${title}</h3>
        <pre>${JSON.stringify(data, null, 2)}</pre>
    `;
}

async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        showOutput('🔄 Lade...', 'loading');
        
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        // Wenn nicht autorisiert, zum Login redirecten
        if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Unbekannter Fehler');
        }
        
        return result;
    } catch (error) {
        showOutput(`❌ Fehler: ${error.message}`, 'error');
        throw error;
    }
}

// 🏫 Schulkontext setzen
async function setSchoolContext() {
    try {
        const data = {
            user_id: document.getElementById('schoolUserId').value,
            grade: document.getElementById('grade').value,
            school_type: document.getElementById('schoolType').value,
            state: document.getElementById('state').value,
            subjects: document.getElementById('subjects').value.split(',').map(s => s.trim()),
            curriculum_focus: 'Allgemein'
        };
        
        const result = await apiCall('/api/set-school-context', 'POST', data);
        showOutput(`✅ ${result.message}`, 'success');
    } catch (error) {
        // Fehler wird schon in apiCall angezeigt
    }
}

// 📚 Übungen generieren
async function generateExercises() {
    try {
        const data = {
            user_id: document.getElementById('userId').value,
            subject: document.getElementById('subject').value,
            topic: document.getElementById('topic').value,
            count: parseInt(document.getElementById('count').value)
        };
        
        const result = await apiCall('/api/generate-exercises', 'POST', data);
        
        if (result.data && result.data.exercises) {
            let html = `<h3>✅ ${result.message}</h3>`;
            result.data.exercises.forEach((exercise, index) => {
                html += `
                    <div class="exercise">
                        <h3>Aufgabe ${index + 1}</h3>
                        <p><strong>Frage:</strong> ${exercise.question}</p>
                        <p><strong>Lösung:</strong> ${exercise.solution}</p>
                        <p><strong>Erklärung:</strong> ${exercise.explanation}</p>
                        <p><strong>Schwierigkeit:</strong> ${exercise.difficulty}</p>
                        <p><em>${exercise.personalization_note || ''}</em></p>
                    </div>
                `;
            });
            
            if (result.data.adaptive_tips) {
                html += `<h4>💡 Tipps:</h4><ul>`;
                result.data.adaptive_tips.forEach(tip => {
                    html += `<li>${tip}</li>`;
                });
                html += `</ul>`;
            }
            
            document.getElementById('output').innerHTML = html;
        }
    } catch (error) {
        // Fehler wird schon in apiCall angezeigt
    }
}

// 📊 Session tracken
async function trackSession() {
    try {
        const data = {
            user_id: document.getElementById('sessionUserId').value,
            subject: document.getElementById('sessionSubject').value,
            duration_minutes: parseInt(document.getElementById('duration').value),
            topics: document.getElementById('sessionTopics').value.split(',').map(s => s.trim()),
            performance_score: parseFloat(document.getElementById('performance').value),
            engagement_level: 0.7
        };
        
        const result = await apiCall('/api/track-session', 'POST', data);
        showOutput(`✅ ${result.message}`, 'success');
    } catch (error) {
        // Fehler wird schon in apiCall angezeigt
    }
}

// 📈 Analytics anzeigen
async function showAnalytics() {
    try {
        const userId = document.getElementById('analyticsUserId').value;
        const result = await apiCall(`/api/analytics/${userId}`);
        showJsonOutput(result.data, '📊 Lern-Analytics');
    } catch (error) {
        // Fehler wird schon in apiCall angezeigt
    }
}

async function showProfile() {
    try {
        const userId = document.getElementById('analyticsUserId').value;
        const result = await apiCall(`/api/profile/${userId}`);
        showJsonOutput(result.data, '👤 Lern-Profil');
    } catch (error) {
        // Fehler wird schon in apiCall angezeigt
    }
}

async function showRecommendations() {
    try {
        const userId = document.getElementById('analyticsUserId').value;
        const result = await apiCall(`/api/recommendations/${userId}`);
        showJsonOutput(result.data, '🎯 Persönliche Empfehlungen');
    } catch (error) {
        // Fehler wird schon in apiCall angezeigt
    }
}


document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
        showUserInfo(JSON.parse(user));
    } else {
        // Redirect to login if not authenticated
        window.location.href = '/login';
    }
});

function showUserInfo(user) {
    document.getElementById('userInfo').style.display = 'block';
    document.getElementById('usernameDisplay').textContent = `Hallo ${user.username}!`;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}






// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    console.log('🤖 KI-Lern-Buddy Frontend geladen!');
});