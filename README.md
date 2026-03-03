# 🤖 KI-Lern-Buddy & Gravity Defender
### Fachreferat FOS 12 – Eine adaptive Lernplattform mit integrierter Gamification und hybrider KI-Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Modern-green)
![AI-Hybrid](https://img.shields.io/badge/AI-Hybrid%20(Cloud%2FLocal)-purple)
![Game](https://img.shields.io/badge/Game-Gravity%20Defender-orange)

## 📋 Projektbeschreibung
Dieses Projekt entstand im Rahmen des Fachreferats der 12. Klasse (FOSBOSNES) im Fach Informatik/Technologie. 

Der **KI-Lern-Buddy** ist ein intelligentes Ökosystem, das demonstriert, wie moderne Softwarearchitektur (strikte Trennung von Frontend und Backend) mit externen KI-Schnittstellen orchestriert wird. Das System analysiert Noten, generiert personalisierte Lerninhalte und belohnt Erfolge spielerisch.

### Die drei Kernkomponenten:
1. **Lern-Engine:** Analysiert historische Noten & PDF-Uploads, um maßgeschneiderte Multiple-Choice-Tests und Karteikarten zu generieren.
2. **Hybrid AI Engine:** Eine abstrakte Schnittstelle, die dynamisch zwischen Cloud-LLMs (OpenRouter/Deepseek) und lokalen Modellen (Ollama) wechseln kann, um Datenschutz und Kosteneffizienz zu gewährleisten.
3. **Gamification (Gravity Defender):** Ein vollständig über WebSockets angebundenes Echtzeit-Spiel, bei dem die physikalische Logik im Backend und das Rendering im Frontend (HTML5 Canvas) stattfindet.

---

## ✨ System-Architektur & Features

### 🧠 Intelligentes Lernen
* **Adaptives Test-System:** Generiert Fragen dynamisch auf Basis des aktuellen Wissensstands und liefert ein detailliertes "Coach-Feedback" (JSON-strukturiert).
* **RAG-Ansatz (Retrieval-Augmented Generation):** Schüler laden Lernmaterialien hoch; die KI liest diese aus und erstellt daraus direkt Prüfungsfragen.
* **Wissens-Graph:** Eine visuelle Darstellung (via vis.js) der verknüpften Fächer und Kompetenzen zur Identifikation von Wissenslücken.

### 🎮 Gamification & Belohnung
* **Währungssystem:** Für das Abschließen von Tests erhalten Nutzer **Gems 💎** und **XP ✨**.
* **Gravity Defender:** Ein 2D Arcade-Spiel im Browser.
    * *Backend:* Python berechnet Kollisionslogik und Schwerkraft (60 Ticks/Sekunde).
    * *Frontend:* Empfängt reine Koordinaten und zeichnet Vektoren.
* **Dashboard:** Visualisiert den Lernfortschritt, Highscores und Gamification-Stats.

---

## 🛠️ Technologie-Stack

| Schicht | Technologie | Einsatzzweck |
| :--- | :--- | :--- |
| **Backend** | Python, FastAPI | Asynchrone REST-API, WebSocket-Server, Datenfluss-Steuerung |
| **Datenbank** | SQLite | Speichert User, Noten, Lernfortschritt (WAL-Mode aktiv) |
| **Frontend** | HTML5, CSS3, Vanilla JS | Rendering ohne Framework-Overhead, Canvas API, Chart.js |
| **KI / AI** | Hybrid Engine API | Support für OpenRouter (Cloud) & Ollama (Local/VPN) |
| **Security** | OAuth2 / JWT | Sichere Authentifizierung, Password Hashing |

---

## 🚀 Installation & Start

### Voraussetzungen
* Python 3.10 oder höher
* (Optional) [Ollama](https://ollama.com/) für lokalen, offline KI-Betrieb

### 1. Repository klonen & Abhängigkeiten installieren
```bash
git clone https://github.com/JohannesK07/fachreferat.git
cd fachreferat
pip install -r backend/requirements.txt
```

### 2. Konfiguration (.env)
Erstelle eine `.env` Datei im Ordner `backend/`. Kopiere folgenden Inhalt hinein und passe deinen API-Key an:

```env
# KI Provider: "cloud" oder "local"
AI_PROVIDER=cloud
OPENROUTER_API_KEY=dein_api_key_hier

# Falls Local (Ollama) genutzt wird:
OLLAMA_IP=127.0.0.1
OLLAMA_MODEL=llama3.1

# Security
SECRET_KEY=dein_geheimer_jwt_key
```

### 3. Server starten
```bash
python backend/main.py
```
* **Web-Interface:** [http://localhost:8000](http://localhost:8000)
* **API-Dokumentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 👨‍💻 Autor
Entwickelt von **Johannes Kannegießer** (Klasse 12 STC) für das Fachreferat im Schuljahr 2025/26 an der Fach- und Berufsoberschule Bad Neustadt.