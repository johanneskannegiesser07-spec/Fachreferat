// frontend/school-setup.js

const germanStates = [
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
    "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
    "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
];

document.addEventListener('DOMContentLoaded', async () => {
    await checkAuthentication();
    
    // 1. Bundesländer Dropdown befüllen
    populateStates();
    
    // 2. Aktuelle Daten laden und Felder ausfüllen (Pre-Fill)
    await loadCurrentSettings();
    
    // 3. Fächerliste laden
    loadSetupSubjects();
});

function populateStates() {
    const select = document.getElementById('federalState');
    select.innerHTML = '<option value="">-- Bitte wählen --</option>';
    
    germanStates.forEach(state => {
        const opt = document.createElement('option');
        opt.value = state;
        opt.textContent = state;
        select.appendChild(opt);
    });
}

// === LÄDT GESPEICHERTE DATEN IN DIE FELDER ===
async function loadCurrentSettings() {
    try {
        const res = await apiCall('/api/school-context');
        if (res.success && res.data) {
            const d = res.data;
            
            // Felder vor-ausfüllen, falls Daten vorhanden sind
            if (d.school_type) document.getElementById('schoolType').value = d.school_type;
            if (d.grade) document.getElementById('schoolGrade').value = d.grade;
            if (d.state) document.getElementById('federalState').value = d.state;
            
            console.log("✅ Einstellungen geladen:", d);
        }
    } catch (e) {
        console.error("Konnte Einstellungen nicht laden", e);
    }
}

// === SPEICHERN ===
async function saveSchoolData() {
    const schoolType = document.getElementById('schoolType').value;
    const grade = document.getElementById('schoolGrade').value;
    const state = document.getElementById('federalState').value;

    if (!grade || !state) {
        alert("Bitte Klasse und Bundesland angeben!");
        return;
    }
    
    // Wir müssen die aktuellen Fächer mitgeben, sonst werden sie überschrieben (leeres Array),
    // oder wir ändern das Backend so, dass es partielle Updates erlaubt. 
    // Sicherer Weg aktuell: Fächer erst laden, dann mitsenden.
    
    let currentSubjects = [];
    try {
        // Kurz die aktuellen Fächer holen, damit wir sie nicht löschen
        const res = await apiCall('/api/school-context');
        if (res.data && res.data.subjects) {
            currentSubjects = res.data.subjects;
            if(typeof currentSubjects === 'string') {
                 currentSubjects = currentSubjects.replace(/[\[\]"]/g, '').split(',');
            }
        }
    } catch(e) { /* ignore */ }

    const data = {
        school_type: schoolType,
        grade: grade,
        state: state,
        subjects: currentSubjects, // Bestehende Fächer beibehalten!
        curriculum_focus: "allgemein"
    };

    try {
        const res = await apiCall('/api/set-school-context', 'POST', data);
        if (res.success) {
            showOutput("✅ Profil gespeichert! Der Lern-Buddy passt sich jetzt an.", "success-msg");
        } else {
            showOutput("Fehler beim Speichern.", "error-msg");
        }
    } catch (e) {
        showOutput("Verbindungsfehler.", "error-msg");
    }
}

// === FÄCHER LISTE LOGIK (Vom vorherigen Schritt) ===

async function loadSetupSubjects() {
    const list = document.getElementById('setupSubjectsList');
    if(!list) return;
    
    try {
        const res = await apiCall('/api/school-context');
        if (res.success && res.data && res.data.subjects) {
            list.innerHTML = '';
            
            let subjects = res.data.subjects;
            if (typeof subjects === 'string') {
                subjects = subjects.replace(/[\[\]"]/g, '').split(',').filter(s => s.trim());
            }
            subjects.sort();

            subjects.forEach(subj => {
                const tag = document.createElement('div');
                tag.className = 'subject-tag';
                // Inline Styles für Tags (oder in CSS auslagern)
                tag.style.cssText = `
                    background: #e9ecef; padding: 5px 12px; border-radius: 20px; 
                    display: flex; align-items: center; gap: 8px; font-size: 0.9em;
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
    loadSetupSubjects(); 
}

async function removeSubject(subjectToRemove) {
    if(!confirm(`Fach '${subjectToRemove}' entfernen?`)) return;
    
    try {
        const res = await apiCall('/api/school-context');
        let currentSubjects = res.data.subjects || [];
        if (typeof currentSubjects === 'string') {
            currentSubjects = currentSubjects.replace(/[\[\]"]/g, '').split(',').map(s => s.trim());
        }
        
        const newSubjects = currentSubjects.filter(s => s !== subjectToRemove);
        
        const updateData = {
            grade: res.data.grade,
            school_type: res.data.school_type,
            state: res.data.state,
            subjects: newSubjects,
            curriculum_focus: res.data.curriculum_focus
        };
        
        await apiCall('/api/set-school-context', 'POST', updateData);
        loadSetupSubjects();
        
    } catch(e) {
        alert("Fehler beim Löschen: " + e);
    }
}