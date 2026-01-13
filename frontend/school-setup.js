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


document.addEventListener('DOMContentLoaded', loadSetupSubjects);

async function loadSetupSubjects() {
    const list = document.getElementById('setupSubjectsList');
    if(!list) return; // Falls wir auf einer anderen Seite sind
    
    try {
        const res = await apiCall('/api/school-context');
        if (res.success && res.data && res.data.subjects) {
            list.innerHTML = '';
            
            // Fächer parsen (String oder Array)
            let subjects = res.data.subjects;
            if (typeof subjects === 'string') {
                subjects = subjects.replace(/[\[\]"]/g, '').split(',').filter(s => s.trim());
            }
            
            // Alphabetisch sortieren
            subjects.sort();

            subjects.forEach(subj => {
                const tag = document.createElement('div');
                tag.className = 'subject-tag';
                tag.style.cssText = `
                    background: #e9ecef; 
                    padding: 5px 12px; 
                    border-radius: 20px; 
                    display: flex; 
                    align-items: center; 
                    gap: 8px;
                    font-size: 0.9em;
                `;
                tag.innerHTML = `
                    <strong>${subj.trim()}</strong>
                    <span onclick="removeSubject('${subj.trim()}')" style="cursor: pointer; color: #dc3545; font-weight: bold;">&times;</span>
                `;
                list.appendChild(tag);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function addSubjectInSetup() {
    const input = document.getElementById('setupNewSubject');
    const subj = input.value.trim();
    if (!subj) return;

    await apiCall('/api/subjects', 'POST', { subject: subj });
    input.value = '';
    loadSetupSubjects(); // Liste neu laden
}

async function removeSubject(subjectToRemove) {
    if(!confirm(`Fach '${subjectToRemove}' wirklich aus der Liste entfernen?`)) return;
    
    // Wir müssen die aktuelle Liste holen, filtern und neu speichern
    // Da wir keinen expliziten DELETE Endpoint für einzelne Fächer im Array haben,
    // nutzen wir einen kleinen Trick: Liste holen -> Filtern -> Context Update senden.
    
    try {
        const res = await apiCall('/api/school-context');
        let currentSubjects = res.data.subjects;
        if (typeof currentSubjects === 'string') {
            currentSubjects = currentSubjects.replace(/[\[\]"]/g, '').split(',').map(s => s.trim());
        }
        
        // Filtern
        const newSubjects = currentSubjects.filter(s => s !== subjectToRemove);
        
        // Speichern (wir senden das komplette Context-Objekt zurück, nur mit neuen Fächern)
        const updateData = {
            grade: res.data.grade,
            school_type: res.data.school_type,
            state: res.data.state,
            subjects: newSubjects, // Die neue Liste
            curriculum_focus: res.data.curriculum_focus
        };
        
        await apiCall('/api/set-school-context', 'POST', updateData);
        loadSetupSubjects();
        
    } catch(e) {
        alert("Fehler beim Löschen: " + e);
    }
}