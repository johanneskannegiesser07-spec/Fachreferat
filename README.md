# 🤖 KI-Lern-Buddy

Ein adaptiver, KI-gestützter Lernbegleiter für Schüler. Entwickelt im Rahmen eines Fachreferats (FOS 12).

## 📋 Über das Projekt

Der KI-Lern-Buddy ist eine Webanwendung, die Schülern hilft, effizienter zu lernen. Anders als statische Lernprogramme nutzt dieses System künstliche Intelligenz (LLMs), um:
1.  Den individuellen **Lernstil** zu erkennen.
2.  **Maßgeschneiderte Übungen** zu generieren.
3.  Tests intelligent auszuwerten und **motivierendes Feedback** zu geben (wie ein Coach).

## ✨ Features

* **Adaptives Test-System:** Generiert Fragen basierend auf dem Wissensstand.
* **KI-Coach:** Gibt nicht nur Noten, sondern erklärt Fehler und motiviert ("Gamification").
* **Review & Retry:** Wiederholung spezifischer Tests zur Fehlerkorrektur.
* **Analytics Dashboard:** Visualisierung von Lernfortschritt und Schwachstellen.
* **Technologie:** Modernes Backend mit FastAPI & SQLite, Frontend mit Vanilla JS.

## 🛠️ Technologie-Stack

* **Backend:** Python 3.x, FastAPI, Uvicorn
* **Datenbank:** SQLite (mit WAL-Mode für Performance)
* **Frontend:** HTML5, CSS3, JavaScript (Asynchron)
* **KI-Engine:** OpenRouter API (DeepSeek Model)
* **Security:** JWT-Tokens & Bcrypt Password Hashing

## 🚀 Installation & Start

1.  **Repository klonen**
    ```bash
    git clone [https://github.com/DeinUser/fachreferat.git](https://github.com/DeinUser/fachreferat.git)
    cd fachreferat
    ```

2.  **Abhängigkeiten installieren**
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Environment Variablen setzen**
    Erstelle eine `.env` Datei im `backend/` Ordner:
    ```env
    OPENROUTER_API_KEY=dein_api_key_hier
    SECRET_KEY=ein_sicherer_zufalls_string
    ```

4.  **Server starten**
    ```bash
    python backend/main.py
    ```
    Der Server läuft unter: `http://localhost:8000`

## 📂 Projektstruktur

* `/backend`
    * `main.py`: API-Endpunkte und Routing
    * `database.py`: Datenbank-Manager (SQL-Logik)
    * `universal_lern_buddy.py`: Geschäftslogik & KI-Steuerung
    * `auth.py`: Sicherheitsfunktionen (Hashing, Tokens)
* `/frontend`: Benutzeroberfläche (HTML/CSS/JS)

## 👨‍💻 Autor

[Dein Name] - FOS 12 Fachreferat