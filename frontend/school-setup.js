// frontend/school-setup.js

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Prüfen ob eingeloggt
    await checkAuthentication();
    
    // 2. Event Listener für das Formular
    const form = document.getElementById('schoolForm');
    if (form) {
        form.addEventListener('submit', saveSchoolConfig);
    }

    // 3. Event Listener für Schulart-Filter (Klassen)
    const schoolTypeSelect = document.getElementById('schoolType');
    if (schoolTypeSelect) {
        schoolTypeSelect.addEventListener('change', filterGrades);
    }
});

async function saveSchoolConfig(e) {
    e.preventDefault();
    
    const formData = {
        school_type: document.getElementById('schoolType').value,
        grade: document.getElementById('grade').value,
        state: document.getElementById('state').value,
        curriculum_focus: document.getElementById('focus').value,
        subjects: [] // Platzhalter für spätere Erweiterungen
    };
    
    // Nachricht-Element holen
    const messageDiv = document.getElementById('message');
    
    try {
        // Wir nutzen jetzt die saubere apiCall Funktion aus common.js!
        const result = await apiCall('/api/set-school-context', 'POST', formData);
        
        if (result.success) {
            showMessage('✅ Schulkonfiguration gespeichert!', 'success');
            
            // Weiterleitung nach kurzer Zeit
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        }
    } catch (error) {
        // apiCall wirft einen Fehler bei Problemen, den wir hier fangen
        showMessage('❌ Fehler: ' + error.message, 'error');
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`; // 'message success' oder 'message error'
        messageDiv.style.display = 'block';
    }
}

function goToDashboard() {
    window.location.href = '/';
}

function skipSetup() {
    if (confirm('Möchtest du wirklich ohne Schulkonfiguration fortfahren? Die Personalisierung wird eingeschränkt sein.')) {
        window.location.href = '/';
    }
}

function filterGrades() {
    const gradeSelect = document.getElementById('grade');
    const schoolType = this.value;
    
    // Filtere Klassen je nach Schulart
    for (let option of gradeSelect.options) {
        if (option.value === '') continue; // "Bitte wählen" immer anzeigen

        if (schoolType === 'fos') {
            // Zeige nur FOS-relevante Klassen (beginnen mit 'fos')
            option.style.display = option.value.startsWith('fos') ? '' : 'none';
        } else if (schoolType === 'bos') {
            // Zeige nur BOS-relevante Klassen
            option.style.display = option.value.startsWith('bos') ? '' : 'none';
        } else {
            // Bei anderen Schulen: Verstecke FOS/BOS Klassen
            option.style.display = (option.value.startsWith('fos') || option.value.startsWith('bos')) ? 'none' : '';
        }
    }
    
    // Reset selection falls unsichtbare Option gewählt war
    if (gradeSelect.selectedOptions[0].style.display === 'none') {
        gradeSelect.value = "";
    }
}