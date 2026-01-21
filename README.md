🤖 KI-Lern-Buddy & Gravity Defender
Fachreferat FOS 12 – Eine adaptive Lernplattform mit integrierter Gamification und hybrider KI-Engine

https://img.shields.io/badge/Python-3.10%252B-blue
https://img.shields.io/badge/FastAPI-Modern-green
https://img.shields.io/badge/AI-Hybrid%2520(Cloud%252FLocal)-purple
https://img.shields.io/badge/Game-Gravity%2520Defender-orange
https://img.shields.io/badge/License-MIT-yellow

📋 Projektbeschreibung
Der KI-Lern-Buddy ist mehr als nur ein Vokabeltrainer. Es ist ein intelligentes Ökosystem, das Schülerinnen und Schülern hilft, effizienter zu lernen, indem es Lerninhalte personalisiert und Erfolge spielerisch belohnt.

Das System verbindet drei Kernkomponenten:

Lern-Engine: Analysiert Noten & Uploads (PDFs), um maßgeschneiderte Übungen zu erstellen.

Hybrid AI Engine: Nutzt Cloud-LLMs (OpenRouter) oder lokale Modelle (Ollama) für Datenschutz & Flexibilität.

Gamification (Gravity Defender): Ein integriertes Arcade-Spiel, das mit "Gems" (durch Lernen verdient) freigeschaltet wird.

✨ Haupt-Features
🧠 Intelligentes Lernen
Adaptives Test-System: Generiert Fragen basierend auf dem aktuellen Wissensstand.

PDF-Analyse (RAG): Schüler können Hefteinträge hochladen; die KI erstellt daraus Zusammenfassungen und Fragen.

KI-Coach: Gibt motivierendes Feedback statt nur "Falsch/Richtig".

Wissens-Graph: Visualisierung der verknüpften Fächer und Kompetenzen.

🎮 Gamification
Währungssystem: Löse Aufgaben → Erhalte Gems 💎 und XP ✨.

Gravity Defender: Ein WebSocket-basiertes Echtzeit-Spiel im Browser.

Mechanik: Steuere eine Rakete, weiche Aliens aus und lande sicher.

Belohnung: Siege im Spiel bringen massive XP-Boni.

Profil-System: Zeige deine Erfolge, gesammelte Gems und Spiel-Highscores.

🛠️ Technologie-Stack
Bereich	Technologie	Details
Backend	Python, FastAPI	Asynchrone API, WebSockets für das Spiel
Datenbank	SQLite	Speichert User, Noten, Lernfortschritt (WAL-Mode aktiv)
Frontend	HTML5, CSS3, JS	Vanilla JS (kein Framework-Overhead), Canvas API für das Spiel
KI / AI	Hybrid Engine	Support für OpenRouter (Cloud) & Ollama (Local/VPN)
Security	OAuth2 / JWT	Sichere Authentifizierung & Password Hashing
🚀 Installation & Start
Voraussetzungen
Python 3.10 oder höher

(Optional) Ollama für lokalen KI-Betrieb

Schritt 1: Repository klonen
bash
git clone https://github.com/DeinUser/fachreferat.git
cd fachreferat
Schritt 2: Abhängigkeiten installieren
bash
pip install -r backend/requirements.txt
Schritt 3: Konfiguration (.env)
Erstelle eine .env Datei im Ordner backend/:

env
# Modus: "cloud" oder "local"
AI_PROVIDER=cloud

# Falls Cloud:
OPENROUTER_API_KEY=dein_api_key_hier

# Falls Local (Ollama):
OLLAMA_IP=127.0.0.1
OLLAMA_MODEL=llama3.1

# Security
SECRET_KEY=super_geheimer_key_fuer_jwt
Schritt 4: Starten
bash
# Server starten (im Hauptverzeichnis)
python backend/main.py
Zugriff:

Web-Interface: http://localhost:8000

API-Dokumentation: http://localhost:8000/docs

📂 Projektstruktur
text
/
├── backend/
│   ├── main.py              # Zentraler Einstiegspunkt, API-Routen & WebSocket-Manager
│   ├── ai_engine.py         # Wrapper für KI-Kommunikation (Cloud & Lokal)
│   ├── game_agent.py        # Physik-Engine & Logik für "Gravity Defender"
│   ├── universal_lern_buddy.py  # Controller/Business-Logik
│   ├── database.py          # SQL-Datenbank-Manager
│   └── requirements.txt     # Python-Abhängigkeiten
├── frontend/
│   ├── game.js              # Rendering-Engine (Canvas) für das Spiel
│   ├── dashboard.js         # Logik für Graphen und Statistiken
│   ├── style.css           # Styling der Webseite
│   ├── index.html          # Hauptseite
│   └── game.html           # Spielseite
└── README.md               # Diese Datei
👨‍💻 Autor
Entwickelt von [Dein Name] für das Fachreferat Klasse 12.