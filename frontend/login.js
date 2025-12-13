// frontend/login.js
document.addEventListener('DOMContentLoaded', async () => {
    // Wenn schon eingeloggt, direkt zum Dashboard
    const user = await checkAuthentication(false);
    if(user) window.location.href = '/';
});

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if(!username || !password) return showOutput("Bitte Daten eingeben", "error-msg");

    try {
        const result = await apiCall('/api/login', 'POST', { username, password });
        if(result.success) {
            localStorage.setItem('token', result.access_token);
            localStorage.setItem('user', JSON.stringify(result.user));
            window.location.href = '/';
        }
    } catch(e) {
        // Fehler wird in apiCall angezeigt
    }
}

async function register() {
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    const email = document.getElementById('regEmail').value;
    
    if(!username || !password) return showOutput("Bitte alles ausfüllen", "error-msg");

    try {
        const result = await apiCall('/api/register', 'POST', { username, password, email });
        if(result.success) {
            showOutput("Registrierung erfolgreich! Bitte einloggen.", "success-msg");
            toggleForms(); // Zum Login wechseln
        }
    } catch(e) {}
}

function toggleForms() {
    const loginForm = document.getElementById('loginForm');
    const regForm = document.getElementById('registerForm');
    
    if(loginForm.style.display === 'none') {
        loginForm.style.display = 'block';
        regForm.style.display = 'none';
    } else {
        loginForm.style.display = 'none';
        regForm.style.display = 'block';
    }
}