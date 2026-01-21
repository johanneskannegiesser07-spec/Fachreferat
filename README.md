# 🤖 KI-Lern-Buddy & Gravity Defender

> **Fachreferat FOS 12** > Eine adaptive Lernplattform mit integrierter Gamification und hybrider KI-Engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Modern-green)
![AI](https://img.shields.io/badge/AI-Hybrid%20(Cloud%2FLocal)-purple)
![Gamification](https://img.shields.io/badge/Game-Gravity%20Defender-orange)

## 📋 Projektbeschreibung

Der **KI-Lern-Buddy** ist mehr als nur ein Vokabeltrainer. Es ist ein intelligentes Ökosystem, das Schülern hilft, effizienter zu lernen, indem es Lerninhalte personalisiert und Erfolge spielerisch belohnt.

Das System verbindet drei Kernkomponenten:
1.  **Lern-Engine:** Analysiert Noten & Uploads (PDFs), um maßgeschneiderte Übungen zu erstellen.
2.  **Hybrid AI Engine:** Nutzt Cloud-LLMs (OpenRouter) oder lokale Modelle (Ollama) für Datenschutz & Flexibilität.
3.  **Gamification (Gravity Defender):** Ein integriertes Arcade-Spiel, das mit "Gems" (durch Lernen verdient) freigeschaltet wird.

## ✨ Haupt-Features

### 🧠 Intelligentes Lernen
* **Adaptives Test-System:** Generiert Fragen basierend auf dem aktuellen Wissensstand.
* **PDF-Analyse (RAG):** Schüler können Hefteinträge hochladen; die KI erstellt daraus Zusammenfassungen und Fragen.
* **KI-Coach:** Gibt motivierendes Feedback statt nur "Falsch/Richtig".

### 🎮 Gamification
* **Währungssystem:** Löse Aufgaben -> Erhalte **Gems** 💎 und **XP** ✨.
* **Gravity Defender:** Ein WebSocket-basiertes Echtzeit-Spiel im Browser.
    * *Mechanik:* Steuere eine Rakete, weiche Aliens aus und lande sicher.
    * *Belohnung:* Siege im Spiel bringen massive XP-Boni.
* **Wissens-Graph:** Visualisierung der verknüpften Fächer und Kompetenzen.

## 🛠️ Technologie-Stack

| Bereich | Technologie | Details |
| :--- | :--- | :--- |
| **Backend** | Python, FastAPI | Asynchrone API, WebSockets für das Spiel |
| **Datenbank** | SQLite | Speichert User, Noten, Lernfortschritt (WAL-Mode aktiv) |
| **Frontend** | HTML5, CSS3, JS | Vanilla JS (kein Framework-Overhead), Canvas API für das Spiel |
| **KI / AI** | Hybrid Engine | Support für OpenRouter (Cloud) & Ollama (Local/VPN) |
| **Security** | OAuth2 / JWT | Sichere Authentifizierung & Password Hashing |

## 🚀 Installation & Start

### Voraussetzungen
* Python 3.10 oder höher
* (Optional) Ollama für lokalen KI-Betrieb

### Schritt 1: Repository klonen
```bash
git clone [https://github.com/DeinUser/fachreferat.git](https://github.com/DeinUser/fachreferat.git)
cd fachreferat