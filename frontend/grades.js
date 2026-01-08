document.addEventListener('DOMContentLoaded', async () => {
    await checkAuthentication();
    loadSubjects();
    loadGrades();
});

// Fächer laden und Dropdown befüllen
async function loadSubjects() {
    try {
        const result = await apiCall('/api/school-context');
        const select = document.getElementById('subjectSelect');
        select.innerHTML = '<option value="">-- Fach wählen --</option>';

        if (result.success && result.data && result.data.subjects) {
            // String "Mathe, Deutsch" in Array wandeln, falls nötig
            let subjects = result.data.subjects;
            if (typeof subjects === 'string') {
                subjects = subjects.split(',').map(s => s.trim());
            }

            subjects.forEach(subj => {
                const opt = document.createElement('option');
                opt.value = subj;
                opt.textContent = subj;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Fehler beim Laden der Fächer", e);
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
            loadSubjects(); // Dropdown neu laden
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

    // Gewichtung grob schätzen (kann man später verfeinern)
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
            // Automatisch KI Analyse triggern wenn Note schlecht ist? 
            // Machen wir lieber manuell oder beim Neuladen.
        }
    } catch (e) {
        console.error(e);
        showOutput("Fehler beim Speichern", "error-msg");
    }
}

// Noten anzeigen
async function loadGrades() {
    const list = document.getElementById('gradesList');
    try {
        const res = await apiCall('/api/grades');
        if (res.success && res.data.length > 0) {
            let html = '<table style="width:100%; border-collapse: collapse;">';
            html += '<tr style="text-align:left; border-bottom:1px solid #ddd;"><th>Fach</th><th>Note</th><th>Art</th><th>Datum</th></tr>';
            
            res.data.forEach(g => {
                // g ist [id, subject, value, type, weight, date] (aus sqlite fetchall)
                // ODER dict, wenn der DatabaseManager dicts zurückgibt. 
                // Da wir raw SQL nutzen, sind es Tuples, außer wir nutzen row_factory.
                // Wir gehen von Tuples aus: 0=id, 1=subj, 2=val, 3=type, 5=date
                const id = g[0];
                
                const subj = g[1];
                const val = g[2];
                const type = g[3];
                const date = new Date(g[5]).toLocaleDateString();

                // Farbe bestimmen (1-6 System angenommen)
                let colorClass = 'grade-ok';
                if (val <= 2.5) colorClass = 'grade-good';
                if (val >= 4.5) colorClass = 'grade-bad';

                // Punkte System (0-15) Check
                if (val > 6) { 
                    if (val >= 10) colorClass = 'grade-good';
                    else if (val < 5) colorClass = 'grade-bad';
                    else colorClass = 'grade-ok';
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
        list.innerHTML = 'Fehler beim Laden.';
    }
}

// KI Analyse
async function triggerAIAnalysis() {
    const box = document.getElementById('aiAnalysisBox');
    box.style.display = 'block';
    document.getElementById('aiText').innerText = "KI denkt nach...";
    
    try {
        const res = await apiCall('/api/analyze-grades', 'POST', {});
        if (res.success) {
            const data = res.data;
            if (typeof data === 'string') {
                 // Fallback falls Plaintext
                 document.getElementById('aiText').innerText = data;
            } else {
                // JSON
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
        }
    } catch (e) {
        document.getElementById('aiText').innerText = "Fehler bei der Analyse.";
    }
}

async function deleteGrade(id) {
    if (!confirm("Möchtest du diese Note wirklich löschen?")) return;

    try {
        const res = await apiCall(`/api/grades/${id}`, 'DELETE');
        if (res.success) {
            showOutput("Note gelöscht.", "success-msg");
            loadGrades(); // Tabelle neu laden
        }
    } catch (e) {
        showOutput("Fehler beim Löschen.", "error-msg");
    }
}