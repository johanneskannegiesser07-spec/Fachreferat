"""
🧠 AI ENGINE (Hybrid: Cloud & Local)
Kapselt die Kommunikation mit der KI.
Unterstützt OpenRouter (Cloud) UND Ollama (Lokal via VPN).
"""

import os
import json
import time
import requests
from dotenv import load_dotenv
import sys
import threading
import ast

load_dotenv()

class AIEngine:
    def __init__(self):
        # Wir lesen aus der .env, ob wir CLOUD oder LOCAL wollen
        self.mode = os.getenv("AI_PROVIDER", "cloud").lower()
        
        if self.mode == "local":
            # === LOKALER MODUS (Dein Monster-PC) ===
            print(f"🏠 Nutze lokalen Heim-Server (Ollama)")
            
            # IP deines PCs im VPN (aus .env laden oder Fallback)
            home_ip = os.getenv("OLLAMA_IP", "127.0.0.1") 
            
            # WICHTIG: Ollama ist OpenAI-Kompatibel unter /v1/chat/completions
            self.base_url = f"http://{home_ip}:11434/v1/chat/completions"
            self.api_key = "ollama" # Ollama braucht keinen echten Key
            
            # Wähle hier dein Modell: "llama3.1" (schnell) oder "llama3.1:70b" (schlau)
            # Du kannst das auch in der .env steuern!
            self.model = os.getenv("OLLAMA_MODEL", "llama3.1")
            
        else:
            # === CLOUD MODUS (OpenRouter) ===
            print("☁️ Nutze OpenRouter Cloud")
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = "tngtech/deepseek-r1t2-chimera:free"

        print(f"🤖 KI-Engine geladen: {self.model} via {self.mode.upper()}")

    def _robust_api_call(self, prompt, max_retries=2, response_format="text", timeout=60):
        """Robust Request mit System-Prompt und aggressivem JSON-Fixing"""
        
        if not self.api_key and self.mode == "cloud":
            print("❌ Kein API-Key")
            return None
            
        headers = { "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json" }
        
        # 1. SYSTEM PROMPT: Macht das Modell "gehorsam"
        messages = [
            {"role": "system", "content": "You are a strict JSON generator. Output ONLY valid JSON. No markdown, no intro text, no explanations."},
            {"role": "user", "content": prompt}
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5 # Etwas kreativer als 0, aber strikter als 0.7
        }

        if response_format == "json":
            if self.mode == "local":
                data["format"] = "json"
                data["stream"] = False
            else:
                data["response_format"] = {"type": "json_object"}

        current_timeout = 180 if (self.mode == "local" and "70b" in self.model) else timeout

        for attempt in range(max_retries):
            try:
                # --- LADEBALKEN ---
                start_time = time.time()
                stop_loading = threading.Event()
                def loader():
                    chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                    i = 0
                    while not stop_loading.is_set():
                        sys.stdout.write(f"\r{chars[i]} KI arbeitet... ({time.time()-start_time:.1f}s)")
                        sys.stdout.flush()
                        time.sleep(0.1)
                        i = (i + 1) % len(chars)
                
                t = threading.Thread(target=loader)
                t.daemon = True
                t.start()
                
                # REQUEST
                resp = requests.post(self.base_url, headers=headers, json=data, timeout=current_timeout)
                
                stop_loading.set()
                t.join()
                
                if resp.status_code == 200:
                    result_json = resp.json()
                    content = result_json['choices'][0]['message']['content']
                    
                    # Statistik (nur für Terminal-Show)
                    duration = time.time() - start_time
                    tps = (len(content)/3.5) / duration
                    sys.stdout.write(f"\r🚀 FERTIG: {duration:.2f}s | {self.mode} | {tps:.1f} T/s\n")
                    
                    if response_format == "json":
                        # === AGGRESSIVE REINIGUNG ===
                        # 1. Markdown entfernen
                        clean_content = content.replace("```json", "").replace("```", "").strip()
                        
                        try:
                            # Versuch 1: Normales JSON
                            return json.loads(clean_content)
                        except:
                            pass
                            
                        try:
                            # Versuch 2: Suche nach { und } (falls Text davor/danach)
                            start = clean_content.find('{')
                            end = clean_content.rfind('}') + 1
                            if start != -1 and end != -1:
                                json_str = clean_content[start:end]
                                return json.loads(json_str)
                        except:
                            pass
                            
                        try:
                            # Versuch 3: Python Eval (Rettung für 'Single Quotes')
                            # Lokale Modelle nutzen oft ' statt " -> Python versteht das, JSON nicht.
                            return ast.literal_eval(clean_content)
                        except Exception as e:
                            print(f"\n⚠️ JSON-Rettung gescheitert: {e}")
                            print(f"RAW: {clean_content[:100]}...")
                            continue # Retry loop
                            
                    return content
                else:
                    stop_loading.set()
                    print(f"\n❌ API Fehler {resp.status_code}: {resp.text}")
                    
            except Exception as e:
                if 'stop_loading' in locals(): stop_loading.set()
                print(f"\n⚠️ Fehler: {e}")
                time.sleep(1)
        
        return None


    # --- HIER FOLGEN DEINE GENERATOR-FUNKTIONEN (bleiben gleich) ---
    # Kopiere einfach generate_exercises, generate_feedback, etc. hier rein.
    # Sie nutzen alle self._robust_api_call, daher funktionieren sie automatisch!
    
    def generate_exercises(self, subject, topic, count, context_info=""):
        """
        🎓 Generiert Übungen basierend auf Parametern
        """
        prompt = fr"""
    ADAPTIVE LERNUNTERSTÜTZUNG:
    {context_info}

    Generiere {count} Multiple-Choice Fragen für {subject} zum Thema {topic}.

    WICHTIG FÜR MATHE/PHYSIK:
    Wenn du Formeln verwendest, schreibe sie im LaTeX-Format und umschließe sie IMMER mit einem Dollarzeichen $.
    Beispiel: "Berechne $\\frac{{1}}{{2}}$" oder "Was ist $\\sqrt{{x}}$?"
    
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

    def generate_flashcards(self, subject, topic, count=5):
        """
        🃏 Generiert Lern-Karteikarten (Vorderseite/Rückseite)
        """
        prompt = fr"""
        LERN-KARTEIKARTEN GENERATOR:
        Fach: {subject}
        Thema: {topic}
        Anzahl: {count}

        Erstelle Karteikarten zum effektiven Lernen.
        - Vorderseite: Ein wichtiger Begriff, eine kurze Frage oder eine Formel.
        - Rückseite: Die prägnante Definition, Antwort oder Lösung (max 2-3 Sätze).

        WICHTIG FÜR MATHE/PHYSIK:
        Wenn du Formeln verwendest, schreibe sie im LaTeX-Format und umschließe sie IMMER mit einem Dollarzeichen $.
        Beispiel: "Berechne $\\frac{{1}}{{2}}$" oder "Was ist $\\sqrt{{x}}$?"

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