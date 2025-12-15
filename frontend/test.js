// frontend/test.js - Logik für den Test-Modus (Mit vollständigem Feedback-Design)
let currentTest = null;
let testTimer = null;
let timeRemaining = 0;
let currentQuestionIndex = 0;
let userAnswers = {};
let selectedOptions = new Set();
let isPaused = false;

document.addEventListener('DOMContentLoaded', async function() {
    await checkAuthentication();
    
    // Prüfe auf Wiederholung (Retake)
    const retakeId = localStorage.getItem('retakeTestId');
    if (retakeId) {
        localStorage.removeItem('retakeTestId');
        startRetake(retakeId);
        return;
    }

    // Prüfe auf Auto-Start (vom Dashboard)
    const autoSubject = localStorage.getItem('autoStartSubject');
    const autoTopic = localStorage.getItem('autoStartTopic');
    
    if (autoSubject && autoTopic) {
        const subjInput = document.getElementById('testSubject');
        const topicInput = document.getElementById('testTopic');
        if(subjInput) subjInput.value = autoSubject;
        if(topicInput) topicInput.value = autoTopic;
        
        localStorage.removeItem('autoStartSubject');
        localStorage.removeItem('autoStartTopic');
        setTimeout(startTest, 500);
    }
    
    // Event Listener für Checkboxen
    document.addEventListener('change', function(e) {
        if(e.target.matches('.mc-option input[type="checkbox"]')) {
            handleOptionChange(e.target);
        }
    });
});

async function startTest() {
    const subject = document.getElementById('testSubject').value;
    const topic = document.getElementById('testTopic').value;
    const count = document.getElementById('questionCount').value;

    if (!subject || !topic) return showOutput("Bitte Fach/Thema wählen", "error-msg");

    document.getElementById('testSetup').classList.add('hidden');
    document.getElementById('testLoading').classList.remove('hidden');
    document.getElementById('loadingSubject').textContent = subject;
    document.getElementById('loadingTopic').textContent = topic;

    try {
        const result = await apiCall('/api/start-test', 'POST', {
            subject, topic, question_count: parseInt(count)
        });

        if (result.success) {
            setupTestUI(result.data);
        } else {
            throw new Error("Konnte Test nicht starten");
        }
    } catch (error) {
        document.getElementById('testSetup').classList.remove('hidden');
        document.getElementById('testLoading').classList.add('hidden');
    }
}

async function startRetake(testId) {
    document.getElementById('testSetup').classList.add('hidden');
    document.getElementById('testLoading').classList.remove('hidden');
    document.getElementById('loadingSubject').textContent = "Wiederholung";
    
    try {
        const result = await apiCall('/api/retake-test', 'POST', { test_id: testId });
        if (result.success) setupTestUI(result.data);
    } catch (e) {
        window.location.href = '/test'; 
    }
}

function setupTestUI(testData) {
    currentTest = testData;
    timeRemaining = currentTest.time_limit || (currentTest.total_questions * 60);
    currentQuestionIndex = 0;
    userAnswers = {};
    selectedOptions = new Set();
    
    document.getElementById('testLoading').classList.add('hidden');
    document.getElementById('activeTest').classList.remove('hidden');
    
    startTimer();
    loadQuestion(0);
}

function loadQuestion(index) {
    let questions = [];
    if(currentTest.exercises.exercises) questions = currentTest.exercises.exercises;
    else if(Array.isArray(currentTest.exercises)) questions = currentTest.exercises;
    
    const question = questions[index];
    if(!question) return;

    // Header Updates
    const qNumDisplay = document.getElementById('questionNumber');
    if(qNumDisplay) qNumDisplay.textContent = `Frage ${index + 1} von ${currentTest.total_questions}`;

    document.getElementById('questionText').textContent = question.question;
    document.getElementById('testInfo').textContent = `${currentTest.subject || 'Test'} - ${currentTest.topic || ''}`;
    
    const optionsContainer = document.getElementById('mcOptions');
    optionsContainer.innerHTML = ''; 
    
    Object.entries(question.options || {}).forEach(([key, text]) => {
        const isSelected = (userAnswers[index] || []).includes(key);
        if(isSelected) selectedOptions.add(key); 
        
        optionsContainer.innerHTML += `
            <div class="mc-option ${isSelected ? 'selected' : ''}" onclick="toggleOption('${key}')">
                <input type="checkbox" value="${key}" ${isSelected ? 'checked' : ''} style="pointer-events:none;">
                <label><strong>${key})</strong> ${text}</label>
            </div>
        `;
    });

    const progress = ((index + 1) / questions.length) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;

    document.getElementById('prevBtn').disabled = (index === 0);
    const isLast = (index === questions.length - 1);
    document.getElementById('nextBtn').classList.toggle('hidden', isLast);
    document.getElementById('finishBtn').classList.toggle('hidden', !isLast);
    
    currentQuestionIndex = index;
}

function toggleOption(key) {
    const checkbox = document.querySelector(`input[value="${key}"]`);
    if(checkbox) {
        checkbox.checked = !checkbox.checked;
        handleOptionChange(checkbox);
        const div = checkbox.closest('.mc-option');
        div.classList.toggle('selected', checkbox.checked);
    }
}

function handleOptionChange(checkbox) {
    const val = checkbox.value;
    if(checkbox.checked) selectedOptions.add(val);
    else selectedOptions.delete(val);
}

async function nextQuestion() {
    await saveCurrentAnswer();
    selectedOptions.clear();
    loadQuestion(currentQuestionIndex + 1);
}

async function previousQuestion() {
    await saveCurrentAnswer();
    selectedOptions.clear();
    loadQuestion(currentQuestionIndex - 1);
}

async function saveCurrentAnswer() {
    const answer = Array.from(selectedOptions);
    userAnswers[currentQuestionIndex] = answer;
    apiCall('/api/save-answer', 'POST', {
        test_id: currentTest.test_id,
        question_index: currentQuestionIndex,
        user_answers: answer
    }).catch(e => console.log("Auto-Save error (ignorable)"));
}

function togglePause() {
    isPaused = !isPaused;
    const btn = document.getElementById('pauseBtn');
    const content = document.querySelector('.question-container');
    
    if(isPaused) {
        btn.textContent = "▶️";
        content.style.opacity = 0.3;
        content.style.pointerEvents = 'none';
    } else {
        btn.textContent = "⏸️";
        content.style.opacity = 1;
        content.style.pointerEvents = 'auto';
    }
}

function startTimer() {
    if(testTimer) clearInterval(testTimer);
    testTimer = setInterval(() => {
        if(!isPaused) {
            timeRemaining--;
            const min = Math.floor(timeRemaining/60).toString().padStart(2,'0');
            const sec = (timeRemaining%60).toString().padStart(2,'0');
            const timerEl = document.getElementById('timer');
            if(timerEl) timerEl.textContent = `${min}:${sec}`;
            if(timeRemaining <= 0) finishTest();
        }
    }, 1000);
}

async function finishTest() {
    await saveCurrentAnswer();
    clearInterval(testTimer);
    
    document.getElementById('activeTest').classList.add('hidden');
    const resultDiv = document.getElementById('testResult');
    resultDiv.classList.remove('hidden');
    
    // Lade-Animation
    resultDiv.innerHTML = `
        <div class="result-content" style="padding:50px; text-align:center;">
            <div class="spinning" style="font-size:3rem">🧠</div>
            <h2>KI wertet aus...</h2>
            <p>Der Coach analysiert deine Leistung.</p>
        </div>
    `;

    try {
        const result = await apiCall('/api/finish-test', 'POST', { test_id: currentTest.test_id });
        if(result.success) renderResults(result.data);
    } catch(e) {
        showOutput("Fehler bei Auswertung", "error-msg");
    }
}

// === HIER IST DIE KORRIGIERTE DARSTELLUNG ===

function renderResults(data) {
    const container = document.getElementById('testResult');
    
    // Wir bauen das HTML explizit in der richtigen Reihenfolge auf
    // NEU: style="..." enthält jetzt background: white und box-shadow für den "Kasten"-Look
    let html = `
        <div class="result-content" style="max-width: 850px; margin: 20px auto; padding: 40px; background: white; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.15);">
            
            <div style="text-align: center; margin-bottom: 40px; border-bottom: 2px solid #f0f0f0; padding-bottom: 30px;">
                <h2 style="margin-bottom: 25px; color: #2d3748; font-size: 2rem;">📊 Dein Testergebnis</h2>
                
                <div style="display: flex; justify-content: center; align-items: center; gap: 40px; flex-wrap: wrap;">
                    <div class="score-circle" style="transform: scale(1.1);">
                        ${Math.round(data.score)}%
                    </div>
                    
                    <div style="text-align: left;">
                        <div class="performance-badge ${getPerformanceClass(data.score)}" style="font-size: 1.1rem; padding: 8px 16px; margin-bottom: 12px; display: inline-block;">
                            ${data.performance_level}
                        </div>
                        <div style="font-size: 1.2rem; color: #4a5568; line-height: 1.6;">
                            ✅ <strong>${data.correct_answers}</strong> von ${data.total_questions} Richtig<br>
                            ⏱️ Zeit: ${Math.round(data.time_spent_seconds / 60)} min
                        </div>
                    </div>
                </div>
            </div>

            <div class="feedback-section" style="margin-bottom: 40px; background: #f8faff; border-radius: 16px; padding: 5px; border: 1px solid #e2e8f0;">
                <h3 style="margin: 20px 0 15px 25px; color: #5a67d8;">🚀 Coach-Feedback</h3>
                <div class="feedback-container">
                    ${renderAiFeedback(data.comprehensive_feedback)}
                </div>
            </div>

            <div class="details-section" style="margin-bottom: 40px;">
                <h3 style="margin-bottom: 25px; border-left: 6px solid #667eea; padding-left: 15px; font-size: 1.5rem; color: #2d3748;">📋 Detaillierte Auswertung</h3>
                <div class="results-list" style="display: flex; flex-direction: column; gap: 20px;">
                    ${renderDetailedAnswers(data.detailed_answers)}
                </div>
            </div>

            <div style="display: flex; gap: 20px; justify-content: center; margin-top: 50px; padding-top: 30px; border-top: 2px solid #f0f0f0;">
                <button onclick="window.location.reload()" class="success" style="padding: 15px 30px; font-size: 1.1rem;">🔄 Test wiederholen</button>
                <button onclick="goToDashboard()" class="secondary" style="padding: 15px 30px; font-size: 1.1rem;">🏠 Zum Dashboard</button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Scrollen nach oben
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// === DIESE FUNKTION WAR VEREINFACHT, JETZT WIEDER VOLLSTÄNDIG ===
function renderAiFeedback(fb) {
    if(!fb) return '<p>Kein Feedback verfügbar.</p>';
    
    // Lernempfehlungen rendern (Boxen)
    let recommendationsHtml = '';
    if(fb.learning_recommendations && fb.learning_recommendations.length > 0) {
        recommendationsHtml = `
            <div style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px;">💡 Konkrete Tipps:</h4>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    ${fb.learning_recommendations.map(rec => `
                        <div style="background: white; padding: 12px; border-radius: 8px; border-left: 5px solid ${getPriorityColor(rec.priority)}; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <strong style="color: #333;">${rec.area || 'Tipp'}</strong>
                                <span style="font-size: 0.8em; background: #eee; padding: 2px 8px; border-radius: 10px; font-weight: bold; color: #555;">${(rec.priority||'').toUpperCase()}</span>
                            </div>
                            <div style="color: #333; margin-bottom: 5px;">👉 ${rec.action}</div>
                            <div style="font-size: 0.9em; color: #666; font-style: italic;">Warum? ${rec.reason}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    return `
        <div style="background:#f0f4ff; padding:25px; border-radius:10px; border-left:5px solid #667eea; text-align:left; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; color: #667eea;">🚀 Coach-Feedback</h3>
            <p style="font-size:1.2em; font-weight:bold; color: #333; margin-bottom: 20px;">${fb.overall_assessment}</p>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom: 20px;">
                <div style="background:#d4edda; padding:15px; border-radius:8px;">
                    <strong style="color: #155724; display:block; margin-bottom:10px;">💪 Deine Stärken</strong>
                    <ul style="margin: 0; padding-left: 20px; color: #155724;">${(fb.key_strengths||[]).map(s=>`<li>${s}</li>`).join('')}</ul>
                </div>
                <div style="background:#fff3cd; padding:15px; border-radius:8px;">
                    <strong style="color: #856404; display:block; margin-bottom:10px;">🚧 Hier kannst du punkten</strong>
                    <ul style="margin: 0; padding-left: 20px; color: #856404;">${(fb.main_weaknesses||[]).map(w=>`<li>${w}</li>`).join('')}</ul>
                </div>
            </div>
            
            ${recommendationsHtml}

            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #dce4f2; color: #555;">
                <strong>🎓 Verständnis:</strong> ${fb.conceptual_understanding || 'Wird analysiert...'}
            </div>
            
            <p style="margin-top: 25px; font-size: 1.1em; text-align: center; font-weight: bold; color: #667eea; font-style: italic;">
                "${fb.encouragement}"
            </p>
        </div>
    `;
}

function getPriorityColor(priority) {
    if(!priority) return '#ccc';
    const p = priority.toLowerCase();
    if(p.includes('hoch')) return '#dc3545'; // Rot
    if(p.includes('mittel')) return '#ffc107'; // Gelb
    return '#28a745'; // Grün
}

function renderDetailedAnswers(details) {
    return (details||[]).map((d, i) => {
        // Wir bauen die Optionen visuell nach
        let optionsHtml = '';
        
        if (d.options && Object.keys(d.options).length > 0) {
            optionsHtml = '<div style="display: flex; flex-direction: column; gap: 8px; margin: 15px 0;">';
            
            Object.entries(d.options).forEach(([key, text]) => {
                const isSelected = d.user_answers.includes(key);
                const isCorrect = d.correct_answers.includes(key);
                
                // Styling-Logik
                let style = 'padding: 12px; border-radius: 8px; border: 1px solid #eee; display: flex; align-items: center; justify-content: space-between;';
                let icon = '';
                let badge = '';

                if (isCorrect) {
                    // Richtig: Grün
                    style += 'background-color: #d4edda; border-color: #c3e6cb; color: #155724;';
                    icon = '✅';
                } else if (isSelected && !isCorrect) {
                    // Falsch gewählt: Rot
                    style += 'background-color: #f8d7da; border-color: #f5c6cb; color: #721c24;';
                    icon = '❌';
                } else {
                    // Neutral
                    style += 'background-color: #f8f9fa; color: #555;';
                }

                if (isSelected) {
                    style += ' border-width: 2px; font-weight: 500;';
                    badge = '<span style="font-size: 0.75em; background: rgba(0,0,0,0.1); padding: 2px 8px; border-radius: 12px; margin-left: 10px; text-transform: uppercase; font-weight: bold;">Deine Wahl</span>';
                }

                optionsHtml += `
                    <div style="${style}">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-weight: bold; min-width: 25px;">${key})</span>
                            <span>${text}</span>
                        </div>
                        <div style="display: flex; align-items: center;">
                            ${badge}
                            <span style="margin-left: 10px;">${icon}</span>
                        </div>
                    </div>
                `;
            });
            optionsHtml += '</div>';
        }

        // Das Karten-Layout
        return `
        <div class="question-result ${d.is_correct ? 'correct' : 'incorrect'}" style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 6px solid ${d.is_correct ? '#28a745' : '#dc3545'};">
            
            <div style="display:flex; justify-content:space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #f0f0f0; padding-bottom: 15px;">
                <h4 style="margin: 0; color: #333; font-size: 1.1em;">Frage ${i+1}</h4>
                <span style="font-weight: bold; color: ${d.is_correct ? '#155724' : '#721c24'}; background: ${d.is_correct ? '#d4edda' : '#f8d7da'}; padding: 6px 15px; border-radius: 20px; font-size: 0.9em;">
                    ${d.is_correct ? '✅ Richtig gelöst' : '❌ Leider falsch'}
                </span>
            </div>
            
            <p style="font-size: 1.2em; font-weight: 600; margin-bottom: 20px; line-height: 1.5; color: #2d3748;">${d.question}</p>
            
            ${optionsHtml}
            
            <div style="margin-top: 20px; padding: 15px; background: #eef2f7; border-radius: 8px; border-left: 4px solid #667eea;">
                <strong style="color: #667eea; display: block; margin-bottom: 5px;">💡 Erklärung / Hinweis:</strong>
                <p style="margin: 0; color: #4a5568; font-style: italic;">${d.explanation}</p>
            </div>
        </div>
    `}).join('');
}

function getPerformanceClass(score) {
    if(score >= 90) return 'excellent';
    if(score >= 75) return 'good';
    if(score >= 60) return 'average';
    return 'poor';
}

function goToDashboard() {
    window.location.href = '/';
}