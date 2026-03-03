// frontend/flashcards.js
let cards = [];
let currentIndex = 0;

document.addEventListener('DOMContentLoaded', async () => {
    await checkAuthentication();
    loadHistory();
});

async function startFlashcards() {
    const subject = document.getElementById('fcSubject').value;
    const topic = document.getElementById('fcTopic').value;
    
    if(!subject || !topic) return alert("Bitte Fach & Thema eingeben!");

    // Lade-Animation zeigen
    document.getElementById('setup').innerHTML = `
        <div style="text-align:center; padding:40px;">
            <div style="font-size:3rem; animation: spin 2s linear infinite;">🪄</div>
            <p>KI generiert & speichert Karten...</p>
        </div>`;

    try {
        const result = await apiCall('/api/start-flashcards', 'POST', {
            subject, topic, count: 10
        });

        if(result.success) {
            initPlayer(result.data);
        } else {
            // Falls Fehler, Seite neu laden um Setup wiederherzustellen
            location.reload(); 
        }
    } catch(e) {
        console.error("Fehler beim Starten:", e);
        location.reload();
    }
}

async function loadHistory() {
    const container = document.getElementById('historyList');
    if(!container) return;

    try {
        const result = await apiCall('/api/flashcard-history');
        if(result.success && result.data.length > 0) {
            container.innerHTML = result.data.map(set => `
                <div class="set-item" onclick="loadSet(${set.id})" 
                     style="cursor:pointer; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="font-size: 1.1em; color: #333;">${set.subject}</strong> <span style="color: #667eea;">•</span> ${set.topic}
                        <div style="font-size:0.85em; color:#888; margin-top: 5px;">
                            🗂️ ${set.card_count} Karten | 📅 ${new Date(set.date).toLocaleDateString()}
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <span style="font-size: 1.2rem; color: #667eea;">➡️</span>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color:#999; padding:10px;">Noch keine Sets gespeichert.</p>';
        }
    } catch(e) {
        console.error("History Error:", e);
        container.innerHTML = '<p style="color:red;">Fehler beim Laden der Historie.</p>';
    }
}

async function loadSet(setId) {
    try {
        const result = await apiCall(`/api/flashcards/${setId}`);
        if(result.success) {
            initPlayer(result.data);
        }
    } catch(e) { 
        console.error(e);
        alert("Fehler beim Laden des Sets"); 
    }
}

function initPlayer(data) {
    if (!data.cards || data.cards.length === 0) {
        alert("Dieses Set enthält keine Karten!");
        return;
    }

    cards = data.cards;
    
    // UI umschalten
    document.getElementById('setup').classList.add('hidden');
    const historyCard = document.getElementById('historyCard');
    if(historyCard) historyCard.classList.add('hidden');
    
    document.getElementById('player').classList.remove('hidden');
    
    // Header Info setzen (falls Element existiert, sonst ignorieren)
    const topicDisplay = document.getElementById('topicDisplay');
    if (topicDisplay) topicDisplay.textContent = `${data.subject} • ${data.topic}`;
    
    currentIndex = 0;
    showCard(0);
}

function showCard(index) {
    const cardEl = document.getElementById('currentCard');
    
    // Erst zurückdrehen, falls gedreht
    cardEl.classList.remove('flipped');

    // Kurze Verzögerung für Animation
    setTimeout(() => {
        const card = cards[index];
        
        // --- FIX: Daten-Normalisierung ---
        // Wir prüfen, ob die Keys 'front'/'back' ODER 'question'/'answer' heißen
        const textFront = card.front || card.question || "Fehler: Datenformat";
        const textBack = card.back || card.answer || "Fehler: Datenformat";

        document.getElementById('cardFrontText').textContent = textFront;
        document.getElementById('cardBackText').textContent = textBack;
        
        document.getElementById('counter').textContent = `${index + 1} / ${cards.length}`;
        
        // --- FIX: Sicherer Render-Call ---
        // Prüfen, ob common.js geladen wurde und renderMath existiert
        if (typeof renderMath === 'function') {
            renderMath('currentCard');
        } else if (window.renderMathInElement) {
             renderMathInElement(document.getElementById('currentCard'));
        }
        
    }, 150);
}

function flipCard() {
    document.getElementById('currentCard').classList.toggle('flipped');
}

function nextCard() {
    if(currentIndex < cards.length - 1) {
        currentIndex++;
        showCard(currentIndex);
    }
}

function prevCard() {
    if(currentIndex > 0) {
        currentIndex--;
        showCard(currentIndex);
    }
}
