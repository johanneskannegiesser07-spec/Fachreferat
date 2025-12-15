// frontend/dashboard.js - Logik für das Dashboard

document.addEventListener('DOMContentLoaded', async function() {
    await checkAuthentication();
    loadSchoolContext();
    loadTestHistory(); // Historie laden beim Start
});

async function loadSchoolContext() {
    try {
        const result = await apiCall('/api/school-context');
        const schoolInfo = document.getElementById('schoolInfo');
        
        if (result.data && result.data.school_type) {
            schoolInfo.innerHTML = `
                <div style="font-size: 1.1em;">🏫 <strong>${result.data.school_type}</strong></div>
                <div>Klasse ${result.data.grade} • ${result.data.state}</div>
                <div style="color: #666; font-size: 0.9em; margin-top:5px;">Fokus: ${result.data.curriculum_focus}</div>
            `;
        } else {
            schoolInfo.innerHTML = `
                <p>Noch keine Schule konfiguriert.</p>
                <button class="school" onclick="window.location.href='/school-setup'" style="margin-top:5px;">Jetzt einrichten</button>
            `;
        }
    } catch (error) {
        console.error(error);
    }
}

async function generateExercises() {
    const subject = document.getElementById('subject').value;
    const topic = document.getElementById('topic').value;
    
    if(!subject || !topic) return showOutput("Bitte Fach und Thema wählen", "error-msg");

    try {
        const result = await apiCall('/api/generate-exercises', 'POST', {
            subject, topic, count: 2
        });
        
        if (result.data && result.data.exercises) {
            let html = `<h3>✅ Generierte Vorschau:</h3>`;
            result.data.exercises.forEach((ex, i) => {
                html += `<div class="exercise"><p><strong>${i+1}. ${ex.question}</strong></p></div>`;
            });
            showOutput(html);
        }
    } catch(e) { /* Error handled in apiCall */ }
}

async function trackSession() {
    const subject = document.getElementById('sessionSubject').value;
    const duration = document.getElementById('duration').value;
    const topics = document.getElementById('sessionTopics').value.split(',');
    const performance = document.getElementById('performance').value;

    try {
        // Hier müsste noch ein API Endpunkt implementiert werden,
        // oder wir zeigen vorerst nur eine Meldung:
        showOutput(`Session gespeichert: ${subject} (${duration}min)`, "success-msg");
        // apiCall('/api/track-session', 'POST', { ... }); 
    } catch(e) {
        console.error(e);
    }
}

async function loadTestHistory() {
    const container = document.getElementById('testHistory');
    if (!container) return;
    
    try {
        const result = await apiCall('/api/test-history');
        if (result.success && result.data.length > 0) {
            let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
            result.data.forEach(test => {
                const date = new Date(test.date).toLocaleDateString('de-DE');
                const color = test.score >= 80 ? '#28a745' : (test.score >= 50 ? '#ffc107' : '#dc3545');
                
                html += `
                    <div class="history-item" style="border-left-color: ${color};">
                        <div>
                            <strong>${test.subject}</strong>: ${test.topic}
                            <div style="font-size: 0.85em; color: #666;">
                                📅 ${date} • 🎯 ${Math.round(test.score)}%
                            </div>
                        </div>
                        <button onclick="retakeTest('${test.test_id}')" class="secondary" style="padding: 5px 10px; font-size: 0.8em;">
                            🔄 Wiederholen
                        </button>
                    </div>`;
            });
            container.innerHTML = html + '</div>';
        } else {
            container.innerHTML = '<p style="text-align:center; color:#888;">Noch keine Tests absolviert.</p>';
        }
    } catch (e) {
        container.innerHTML = '<p class="error-msg">Fehler beim Laden der Historie.</p>';
    }
}

function retakeTest(testId) {
    localStorage.setItem('retakeTestId', testId);
    window.location.href = '/test';
}

// --- NAVIGATION ---

function showSchoolSetup() {
    window.location.href = '/school-setup';
}

function goToTest() {
    window.location.href = '/test';
}

// --- PLATZHALTER ---
function showAnalytics() { showOutput("Analytics Feature kommt bald! (Daten werden bereits gesammelt)", "success-msg"); }
function showProfile() { showOutput("Profil-Analyse läuft im Hintergrund.", "success-msg"); }
function showRecommendations() { showOutput("Basierend auf deinen Tests: Mehr Mathe üben! 😉", "success-msg"); }

// loadKnowledgeGraph();

async function loadKnowledgeGraph() {
    const container = document.getElementById('knowledgeGraph');
    if (!container) return;

    try {
        const result = await apiCall('/api/knowledge-graph');
        
        if (result.success && result.data.nodes.length > 0) {
            const data = {
                nodes: new vis.DataSet(result.data.nodes),
                edges: new vis.DataSet(result.data.edges)
            };
            
            const options = {
                nodes: {
                    shape: 'dot',
                    font: { size: 16, face: 'Segoe UI' },
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    width: 2,
                    smooth: { type: 'continuous' }
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 95
                    }
                },
                interaction: { hover: true }
            };
            
            container.innerHTML = ''; // Lade-Text entfernen
            new vis.Network(container, data, options);
        } else {
            container.innerHTML = `
                <div style="text-align:center; padding-top:150px; color:#888;">
                    <p>Noch nicht genügend Daten für den Graphen.</p>
                    <p style="font-size:0.9em;">Absolviere Tests in verschiedenen Fächern!</p>
                </div>`;
        }
    } catch (e) {
        console.error("Graph Error:", e);
        container.innerHTML = '<p style="color:red; text-align:center; padding-top:150px;">Fehler beim Laden des Graphen.</p>';
    }
}