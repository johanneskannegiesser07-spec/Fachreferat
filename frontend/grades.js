document.addEventListener('DOMContentLoaded', async () => {
    await checkAuthentication();
    // Erst Kontext laden (für Punktesystem-Check), dann Noten
    await loadContextAndSubjects();
    loadGrades();
});

let isPointsSystem = false; // Standard: Noten 1-6

// Fächer & Kontext laden
async function loadContextAndSubjects() {
    try {
        const result = await apiCall('/api/school-context');
        const select = document.getElementById('subjectSelect');
        select.innerHTML = '<option value="">-- Fach wählen --</option>';

        if (result.success && result.data) {
            // 1. Check: Oberstufe? (Punkte statt Noten)
            const grade = String(result.data.grade || "").toLowerCase();
            // Klassen 11, 12, 13 oder FOS/BOS nutzen Punkte
            if (['11', '12', '13', 'fos11', 'fos12', 'fos13', 'bos12', 'bos13'].includes(grade)) {
                isPointsSystem = true;
                console.log("System: Punkte (Oberstufe)");
            } else {
                isPointsSystem = false;
                console.log("System: Noten 1-6");
            }

            // 2. Fächer Dropdown befüllen
            let subjects = result.data.subjects || [];
            if (typeof subjects === 'string') {
                // Fallback falls Datenbank noch Strings liefert
                subjects = subjects.replace(/[\[\]"]/g, '').split(',');
            }
            
            // Unikate Fächerliste erzwingen
            const uniqueSubjects = [...new Set(subjects.map(s => s.trim()).filter(s => s))];

            uniqueSubjects.forEach(subj => {
                const opt = document.createElement('option');
                opt.value = subj;
                opt.textContent = subj;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Fehler beim Laden des Kontexts", e);
    }
}

// Neues Fach hinzufügen
async function addNewSubject() {
    const newSubj = document.getElementById('newSubjectInput').value.trim();
    if (!newSubj) return;

    try {
        const res = await apiCall('/api/subjects', 'POST', { subject: newSubj });
        if (res.success) {
            showOutput(`Fach '${newSubj}' hinzugefügt!`, "success-msg");
            document.getElementById('newSubjectInput').value = '';
            loadContextAndSubjects(); // Reload für Dropdown
        }
    } catch (e) {
        showOutput("Fehler beim Hinzufügen", "error-msg");
    }
}

// Note speichern
async function saveGrade() {
    const subject = document.getElementById('subjectSelect').value;
    const value = parseFloat(document.getElementById('gradeValue').value);
    const type = document.getElementById('gradeType').value;

    if (!subject || isNaN(value)) {
        alert("Bitte Fach und gültige Note eingeben.");
        return;
    }

    let weight = 1.0;
    if (type === 'schulaufgabe') weight = 2.0;
    if (type === 'muendlich') weight = 0.5;

    try {
        const res = await apiCall('/api/grades', 'POST', {
            subject, value, type, weight
        });
        
        if (res.success) {
            showOutput("Note gespeichert!", "success-msg");
            loadGrades();
        }
    } catch (e) {
        showOutput("Fehler beim Speichern", "error-msg");
    }
}

// Noten anzeigen mit korrigierter Logik
async function loadGrades() {
    const list = document.getElementById('gradesList');
    try {
        const res = await apiCall('/api/grades');
        if (res.success && res.data.length > 0) {
            let html = '<table style="width:100%; border-collapse: collapse;">';
            html += '<tr style="text-align:left; border-bottom:1px solid #ddd;"><th>Fach</th><th>Wert</th><th>Art</th><th>Datum</th><th></th></tr>';
            
            res.data.forEach(g => {
                const id = g[0];
                const subj = g[1];
                const val = parseFloat(g[2]); // Sicherstellen, dass es eine Zahl ist
                const type = g[3];
                const date = new Date(g[5]).toLocaleDateString();

                // === FARBLOGIK ===
                let colorClass = 'grade-ok';

                if (isPointsSystem) {
                    // PUNKTE-SYSTEM (0-15)
                    // 15-13: Sehr gut (1)
                    // 12-10: Gut (2)
                    // 9-7: Befriedigend (3)
                    // 6-4: Ausreichend (4) -> ab 4 Punkten bestanden (Note 4-)
                    // < 4: Mangelhaft/Ungenügend -> Defizit
                    
                    if (val >= 10) colorClass = 'grade-good';      // 10-15 Punkte (1-2)
                    else if (val >= 5) colorClass = 'grade-ok';    // 5-9 Punkte (3-4)
                    else if (val === 4) colorClass = 'grade-ok';   // 4 Punkte ist genau 4- (noch ok, aber knapp)
                    else colorClass = 'grade-bad';                 // 0-3 Punkte (5-6)
                    
                    // Deine spezifische Beschwerde: "1 ist grün, 6 ist rot"
                    // Hier jetzt: 1 Punkt -> grade-bad (Rot). 6 Punkte -> grade-ok (Gelb).
                    
                } else {
                    // NOTEN-SYSTEM (1-6)
                    if (val <= 2.5) colorClass = 'grade-good';
                    else if (val >= 4.5) colorClass = 'grade-bad';
                    else colorClass = 'grade-ok';
                    
                    // Fallback: Falls jemand im Notenmodus versehentlich 13 eingibt
                    if (val > 6) colorClass = 'grade-good'; 
                }

                html += `
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;"><strong>${subj}</strong></td>
                        <td><span class="grade-badge ${colorClass}">${val}</span></td>
                        <td>${type}</td>
                        <td style="color:#888; font-size:0.8em;">${date}</td>
                        <td style="text-align:right;">
                            <button onclick="deleteGrade(${id})" style="background:none; border:none; cursor:pointer; font-size:1.2em;" title="Löschen">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `;
            });
            html += '</table>';
            list.innerHTML = html;
        } else {
            list.innerHTML = '<p>Noch keine Noten eingetragen.</p>';
        }
    } catch (e) {
        console.error(e);
        list.innerHTML = 'Fehler beim Laden.';
    }
}

async function deleteGrade(id) {
    if (!confirm("Möchtest du diese Note wirklich löschen?")) return;

    try {
        const res = await apiCall(`/api/grades/${id}`, 'DELETE');
        if (res.success) {
            showOutput("Note gelöscht.", "success-msg");
            loadGrades();
        }
    } catch (e) {
        showOutput("Fehler beim Löschen.", "error-msg");
    }
}

// KI Analyse Trigger bleibt gleich...
async function triggerAIAnalysis() {
    // ... (Code wie zuvor)
    const box = document.getElementById('aiAnalysisBox');
    box.style.display = 'block';
    document.getElementById('aiText').innerText = "KI denkt nach...";
    
    try {
        const res = await apiCall('/api/analyze-grades', 'POST', {});
        if (res.success) {
            const data = res.data;
            document.getElementById('aiText').innerText = data.analysis_text || "Analyse fertig.";
            
            let tipsHtml = '';
            if (data.alerts && data.alerts.length > 0) {
                tipsHtml += '<h3>⚠️ Handlungsbedarf:</h3>';
                data.alerts.forEach(alert => {
                    tipsHtml += `
                        <div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                            <strong>${alert.subject}</strong>: ${alert.advice}
                        </div>
                    `;
                });
            }
            if (data.praise) {
                tipsHtml += `<p style="color: green; margin-top:10px;">${data.praise}</p>`;
            }
            document.getElementById('aiTips').innerHTML = tipsHtml;
        }
    } catch (e) {
        document.getElementById('aiText').innerText = "Fehler bei der Analyse.";
    }
}