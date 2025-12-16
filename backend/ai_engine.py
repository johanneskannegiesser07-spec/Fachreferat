"""
🧠 AI ENGINE
Kapselt die Kommunikation mit der KI (OpenRouter / DeepSeek).
Hier liegen die Prompts und die API-Logik.
"""

import os
import json
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "tngtech/deepseek-r1t2-chimera:free"
        print("🤖 KI-Engine initialisiert")

    def generate_exercises(self, subject, topic, count, context_info=""):
        """
        🎓 Generiert Übungen basierend auf Parametern
        """
        prompt = f"""
    ADAPTIVE LERNUNTERSTÜTZUNG:
    {context_info}

    Generiere {count} Multiple-Choice Fragen für {subject} zum Thema {topic}.
    
    JSON-Format strikt einhalten: 
    {{
        "exercises": [
            {{
                "question": "...", 
                "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, 
                "correct_answers": ["A", "C"], 
                "explanation": "...",
                "difficulty": "mittel"
            }}
        ],
        "adaptive_tips": ["Tipp 1", "Tipp 2"]
    }}
    Wichtig: Es können mehrere Antworten richtig sein. Kennzeichne das in 'correct_answers'.
    """
        return self._robust_api_call(prompt, response_format="json")

    def generate_feedback(self, subject, topic, score, correct, total):
        """
        🚀 Generiert das 'Cool Coach' Feedback für den gesamten Test
        """
        prompt = f"""
    Du bist ein energetischer, cooler Lern-Coach für Schüler. 
    Deine Mission: MOTIVATION PUR! 🚀
    
    Analysiere dieses Testergebnis. Sei nicht langweilig! Sei wie ein YouTuber oder Sport-Coach.
    Sprich den Schüler direkt mit "Du" an. Nutze viele Emojis.

    DATEN:
    Fach: {subject}
    Thema: {topic}
    Ergebnis: {score}% ({correct} von {total} richtig)

    DEINE AUFGABE:
    Antworte STRENG als JSON:
    {{
        "overall_assessment": "Dein motivierendes Fazit (kurz & knackig)",
        "key_strengths": ["Stärke 1", "Stärke 2"],
        "main_weaknesses": ["Hier kannst du noch punkten 1", "Hier leveln wir noch hoch 2"], 
        "learning_recommendations": [
            {{
                "priority": "hoch/mittel/niedrig",
                "area": "Was genau?",
                "action": "Konkreter Tipp", 
                "reason": "Warum hilft das?"
            }}
        ],
        "conceptual_understanding": "Einschätzung (z.B. 'Grundlagen sitzen')",
        "next_steps": ["Schritt 1", "Schritt 2"],
        "encouragement": "Dein finaler Motivations-Spruch"
    }}
    """
        return self._robust_api_call(prompt, response_format="json", timeout=20)

    def generate_single_answer_feedback(self, question, solution, user_answer, is_correct):
        """
        📝 Feedback für eine einzelne Antwort (sofort nach Eingabe)
        """
        prompt = f"""
    Du bist ein cooler Lern-Coach.
    
    SITUATION:
    Frage: {question}
    Richtige Lösung: {solution}
    Antwort des Schülers: {user_answer}
    Ergebnis: {'Richtig! 🎉' if is_correct else 'Leider falsch 😕'}

    DEINE AUFGABE:
    Antworte als JSON:
    {{
        "strengths": "Was war gut? (oder motivierender Zuspruch)",
        "improvements": "Wo lag der Fehler? (nett formuliert)",
        "hint": "Ein cooler Merksatz oder Tipp",
        "concept_explanation": "Die Erklärung in einfacher Sprache"
    }}
    """
        return self._robust_api_call(prompt, response_format="json")

    def _robust_api_call(self, prompt, max_retries=2, response_format="text", timeout=30):
        """Interne Methode für den eigentlichen Request mit Retry-Logik"""
        if not self.api_key:
            print("❌ Kein API-Key konfiguriert")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/universal-lern-buddy",
            "X-Title": "Universal Lern-Buddy"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if response_format == "json":
            data["response_format"] = {"type": "json_object"}
            
        for attempt in range(max_retries):
            try:
                resp = requests.post(self.base_url, headers=headers, json=data, timeout=timeout)
                if resp.status_code == 200:
                    content = resp.json()['choices'][0]['message']['content']
                    if response_format == "json":
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            print(f"⚠️ JSON-Fehler in Antwort: {content[:50]}...")
                            continue
                    return content
                else:
                    print(f"⚠️ API Fehler {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"⚠️ Netzwerkfehler Versuch {attempt+1}: {e}")
                time.sleep(1 + attempt) # Kurze Pause vor Retry
        
        return None

    def generate_flashcards(self, subject, topic, count=5):
        """
        🃏 Generiert Lern-Karteikarten (Vorderseite/Rückseite)
        """
        prompt = f"""
        LERN-KARTEIKARTEN GENERATOR:
        Fach: {subject}
        Thema: {topic}
        Anzahl: {count}

        Erstelle Karteikarten zum effektiven Lernen.
        - Vorderseite: Ein wichtiger Begriff, eine kurze Frage oder eine Formel.
        - Rückseite: Die prägnante Definition, Antwort oder Lösung (max 2-3 Sätze).

        Antworte STRENG als JSON:
        {{
            "flashcards": [
                {{ "front": "Begriff/Frage", "back": "Erklärung/Antwort" }},
                {{ "front": "...", "back": "..." }}
            ]
        }}
        """
        return self._robust_api_call(prompt, response_format="json")

    def generate_study_plan(self, subject, days_left):
        prompt = f"""
        Erstelle einen Lernplan für das Fach '{subject}'.
        Zeit bis zur Klausur: {days_left} Tage.
        
        Erstelle für JEDEN Tag (Tag 1 bis Tag {days_left}) einen Eintrag.
        Baue aufeinander auf: Erst Grundlagen, dann Vertiefung, am Ende Wiederholung.
        
        Antworte STRENG als JSON:
        {{
            "plan": [
                {{ "day": 1, "topic": "...", "activity": "..." }},
                {{ "day": 2, "topic": "...", "activity": "..." }}
            ]
        }}
        """
        return self._robust_api_call(prompt, response_format="json")