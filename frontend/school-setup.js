// frontend/school-setup.js - Logik für die Schulkonfiguration

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Prüfen ob eingeloggt
    await checkAuthentication();
    
    // 2. Event Listener für das Formular (Speichern)
    const form = document.getElementById('schoolForm');
    if (form) {
        form.addEventListener('submit', saveSchoolConfig);
    }

    // 3. Event Listener für Schulart-Filter (Klassen dynamisch filtern)
    const schoolTypeSelect = document.getElementById('schoolType');
    if (schoolTypeSelect) {
        schoolTypeSelect.addEventListener('change', filterGrades);
    }
});

async function saveSchoolConfig(e) {
    e.preventDefault();
    
    // Daten aus dem Formular sammeln
    const formData = {
        school_type: document.getElementById('schoolType').value,
        grade: document.getElementById('grade').value,
        state: document.getElementById('state').value,
        curriculum_focus: document.getElementById('focus').value,
        subjects: [] // Platzhalter, falls du später Checkboxen für Fächer hinzufügst
    };
    
    try {
        // API Aufruf an das Backend
        const result = await apiCall('/api/set-school-context', 'POST', formData);
        
        if (result.success) {
            showMessage('✅ Schulkonfiguration erfolgreich gespeichert!', 'success-msg');
            
            // Kurze Wartezeit, dann ab zum Dashboard
            setTimeout(() => {
                window.location.href = '/'; // Dashboard/Index
            }, 1500);
        }
    } catch (error) {
        showMessage('❌ Fehler beim Speichern: ' + error.message, 'error-msg');
    }
}

// --- WICHTIGE HELFER-FUNKTIONEN FÜR DIE BUTTONS ---

function goToDashboard() {
    window.location.href = '/'; // Leitet zurück zur Startseite (index.html)
}

function skipSetup() {
    if (confirm('Möchtest du die Konfiguration wirklich überspringen? Die KI kann dir dann weniger gut helfen.')) {
        window.location.href = '/';
    }
}

function showMessage(text, className) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = className; // z.B. 'success-msg' oder 'error-msg' aus style.css
        messageDiv.style.display = 'block';
    } else {
        alert(text); // Fallback falls das Div fehlt
    }
}

function filterGrades() {
    // Diese Funktion filtert die Klassen-Optionen basierend auf der Schulart
    // (z.B. zeigt sie bei "FOS" nur Klassen 11-13 an)
    const gradeSelect = document.getElementById('grade');
    const schoolType = document.getElementById('schoolType').value; // 'this' kann hier tricky sein, lieber explizit holen
    
    if (!gradeSelect) return;

    for (let option of gradeSelect.options) {
        if (option.value === '') continue; // "Bitte wählen" immer anzeigen

        if (schoolType === 'fos') {
            // Zeige nur FOS-relevante Klassen (beginnen mit 'fos' oder sind 11, 12, 13)
            const isFos = option.value.startsWith('fos') || ['11', '12', '13'].includes(option.value);
            option.style.display = isFos ? '' : 'none';
        } else if (schoolType === 'bos') {
            // Zeige nur BOS-relevante Klassen
            const isBos = option.value.startsWith('bos') || ['12', '13'].includes(option.value);
            option.style.display = isBos ? '' : 'none';
        } else {
            // Bei anderen Schulen (Gymnasium etc.) alles anzeigen
            option.style.display = '';
        }
    }
    
    // Reset der Auswahl, falls die gewählte Klasse jetzt unsichtbar ist
    if (gradeSelect.selectedOptions[0] && gradeSelect.selectedOptions[0].style.display === 'none') {
        gradeSelect.value = "";
    }
}