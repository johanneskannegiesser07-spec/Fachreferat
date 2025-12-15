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

    document.getElementById('setup').innerHTML = '<div style="text-align:center; padding:40px;"><div class="spinning" style="font-size:3rem">🪄</div><p>KI generiert & speichert Karten...</p></div>';

    try {
        const result = await apiCall('/api/start-flashcards', 'POST', {
            subject, topic, count: 10
        });

        if(result.success) {
            initPlayer(result.data);
        }
    } catch(e) {
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
                <div class="set-item" onclick="loadSet(${set.id})">
                    <div>
                        <strong>${set.subject}</strong>: ${set.topic}
                        <div style="font-size:0.8em; color:#666;">${set.card_count} Karten • ${new Date(set.date).toLocaleDateString()}</div>
                    </div>
                    <span>➡️</span>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color:#999; padding:10px;">Noch keine Sets gespeichert.</p>';
        }
    } catch(e) {
        console.error(e);
    }
}

async function loadSet(setId) {
    try {
        const result = await apiCall(`/api/flashcards/${setId}`);
        if(result.success) {
            // Setup ausblenden, Player starten
            document.getElementById('setup').classList.add('hidden');
            document.getElementById('historyCard').classList.add('hidden'); // Historie auch ausblenden
            initPlayer(result.data);
        }
    } catch(e) { alert("Fehler beim Laden"); }
}

function initPlayer(data) {
    cards = data.cards;
    document.getElementById('setup').classList.add('hidden');
    document.getElementById('historyCard')?.classList.add('hidden');
    document.getElementById('player').classList.remove('hidden');
    document.getElementById('topicDisplay').textContent = `${data.subject} • ${data.topic}`;
    
    currentIndex = 0;
    showCard(0);
}

function showCard(index) {
    const cardEl = document.getElementById('currentCard');
    cardEl.classList.remove('flipped');

    setTimeout(() => {
        document.getElementById('cardFrontText').textContent = cards[index].front;
        document.getElementById('cardBackText').textContent = cards[index].back;
        document.getElementById('counter').textContent = `${index + 1} / ${cards.length}`;
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