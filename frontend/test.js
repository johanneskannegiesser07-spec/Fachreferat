// frontend/test.js - Logik für den Test-Modus
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
        document.getElementById('testSubject').value = autoSubject;
        document.getElementById('testTopic').value = autoTopic;
        localStorage.removeItem('autoStartSubject');
        localStorage.removeItem('autoStartTopic');
        setTimeout(startTest, 500);
    }
    
    // Event Listener für Checkboxen initialisieren (delegiert)
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

    // UI Reset
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
        window.location.href = '/test'; // Bei Fehler zurück zum Setup
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
    // Sicheres Laden der Fragen-Liste
    let questions = [];
    if(currentTest.exercises.exercises) questions = currentTest.exercises.exercises;
    else if(Array.isArray(currentTest.exercises)) questions = currentTest.exercises;
    
    const question = questions[index];
    if(!question) return;

    // UI Update
    document.getElementById('questionNumber').textContent = `Frage ${index + 1} von ${questions.length}`;
    document.getElementById('questionText').textContent = question.question;
    document.getElementById('testInfo').textContent = `${currentTest.subject} - ${currentTest.topic}`;
    
    // Optionen rendern
    const optionsContainer = document.getElementById('mcOptions');
    optionsContainer.innerHTML = ''; // Reset
    
    Object.entries(question.options || {}).forEach(([key, text]) => {
        const isSelected = (userAnswers[index] || []).includes(key);
        if(isSelected) selectedOptions.add(key); // State sync
        
        optionsContainer.innerHTML += `
            <div class="mc-option ${isSelected ? 'selected' : ''}" onclick="toggleOption('${key}')">
                <input type="checkbox" value="${key}" ${isSelected ? 'checked' : ''} style="pointer-events:none;">
                <label><strong>${key})</strong> ${text}</label>
            </div>
        `;
    });

    // Fortschrittsbalken
    const progress = ((index + 1) / questions.length) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;

    // Buttons
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
        // Visuelles Update erzwingen
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
    
    // Background Save
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
            document.getElementById('timer').textContent = `${min}:${sec}`;
            if(timeRemaining <= 0) finishTest();
        }
    }, 1000);
}

async function finishTest() {
    await saveCurrentAnswer();
    clearInterval(testTimer);
    
    // UI sofort umschalten
    document.getElementById('activeTest').classList.add('hidden');
    const resultDiv = document.getElementById('testResult');
    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = `
        <div class="result-content" style="padding:50px;">
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

function renderResults(data) {
    const container = document.getElementById('testResult');
    
    // Wir bauen das HTML explizit in der richtigen Reihenfolge auf
    let html = `
        <div class="result-content" style="max-width: 800px; margin: 0 auto; padding: 20px;">
            
            <div style="text-align: center; margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 20px;">
                <h2 style="margin-bottom: 20px; color: #333;">📊 Dein Testergebnis</h2>
                
                <div style="display: flex; justify-content: center; align-items: center; gap: 30px; flex-wrap: wrap;">
                    <div class="score-circle">
                        ${Math.round(data.score)}%
                    </div>
                    
                    <div style="text-align: left;">
                        <div class="performance-badge ${getPerformanceClass(data.score)}" style="font-size: 1.2rem; margin-bottom: 10px; display: inline-block;">
                            ${data.performance_level}
                        </div>
                        <div style="font-size: 1.1rem; color: #555; line-height: 1.6;">
                            ✅ <strong>${data.correct_answers}</strong> von ${data.total_questions} Richtig<br>
                            ⏱️ Zeit: ${Math.round(data.time_spent_seconds / 60)} min
                        </div>
                    </div>
                </div>
            </div>

            <div class="feedback-section" style="margin-bottom: 40px; background: #f8f9fa; border-radius: 12px; padding: 5px;">
                <h3 style="margin: 15px 0 15px 20px;">🚀 Coach-Feedback</h3>
                <div class="feedback-container">
                    ${renderAiFeedback(data.comprehensive_feedback)}
                </div>
            </div>

            <div class="details-section" style="margin-bottom: 40px;">
                <h3 style="margin-bottom: 20px; border-left: 5px solid #667eea; padding-left: 10px;">📋 Detaillierte Auswertung</h3>
                <div class="results-list" style="display: flex; flex-direction: column; gap: 15px;">
                    ${renderDetailedAnswers(data.detailed_answers)}
                </div>
            </div>

            <div style="display: flex; gap: 15px; justify-content: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                <button onclick="window.location.reload()" class="success">🔄 Test wiederholen</button>
                <button onclick="goToDashboard()" class="secondary">🏠 Zum Dashboard</button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Scrollen nach oben, damit man das Ergebnis sieht
    window.scrollTo({ top: 0, behavior: 'smooth' });
}


function renderAiFeedback(fb) {
    if(!fb) return '<p>Kein Feedback verfügbar.</p>';
    
    return `
        <div style="background:#f0f4ff; padding:20px; border-radius:10px; border-left:5px solid #667eea; text-align:left;">
            <h3 style="margin-top:0;">🚀 Coach-Feedback</h3>
            <p style="font-size:1.1em; font-weight:bold;">${fb.overall_assessment}</p>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin:15px 0;">
                <div style="background:#d4edda; padding:10px; border-radius:5px;">
                    <strong>💪 Stärken:</strong>
                    <ul>${(fb.key_strengths||[]).map(s=>`<li>${s}</li>`).join('')}</ul>
                </div>
                <div style="background:#fff3cd; padding:10px; border-radius:5px;">
                    <strong>🚧 Fokus:</strong>
                    <ul>${(fb.main_weaknesses||[]).map(w=>`<li>${w}</li>`).join('')}</ul>
                </div>
            </div>
            
            <p><em>"${fb.encouragement}"</em></p>
        </div>
    `;
}

function renderDetailedAnswers(details) {
    return (details||[]).map((d, i) => `
        <div class="question-result ${d.is_correct ? 'correct' : 'incorrect'}">
            <h4>Frage ${i+1} ${d.is_correct ? '✅' : '❌'}</h4>
            <p>${d.question}</p>
            <div style="font-size:0.9em; color:#666;">
                <p>Deine Antwort: <strong>${d.user_answers.join(', ')}</strong></p>
                <p>Richtig: <strong>${d.correct_answers.join(', ')}</strong></p>
            </div>
            <p style="margin-top:10px; font-style:italic;">💡 ${d.explanation}</p>
        </div>
    `).join('');
}

function getPerformanceClass(score) {
    if(score >= 90) return 'excellent';
    if(score >= 75) return 'good';
    if(score >= 60) return 'average';
    return 'poor';
}

// Hilfsfunktion für den statischen Button in test.html
function goToDashboard() {
    window.location.href = '/';
}