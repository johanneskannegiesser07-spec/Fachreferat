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

    def _robust_api_call(self, prompt, max_retries=2, response_format="text", timeout=60, system_prompt=None):
        """Robust Request mit System-Prompt und aggressivem JSON-Fixing"""
        
        if not self.api_key and self.mode == "cloud":
            print("❌ Kein API-Key")
            return None
            
        headers = { "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json" }
        
        # System Prompt Logik
        default_system = "You are a helpful AI assistant."
        if response_format == "json":
            default_system = "You are a strict JSON generator. Output ONLY valid JSON. No markdown, no intro text."
            
        final_system = system_prompt if system_prompt else default_system
        
        messages = [
            {"role": "system", "content": final_system},
            {"role": "user", "content": prompt}
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5
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
        Kontext/Notenlage: {context_info}

        Generiere {count} Multiple-Choice Fragen für {subject} zum Thema {topic}.
        Passe die Schwierigkeit an die Notenlage an! (Schlechte Noten -> Einfacherer Einstieg).

        JSON-Format strikt einhalten: 
        {{
            "exercises": [
                {{
                    "question": "...", 
                    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, 
                    "correct_answers": ["A"], 
                    "explanation": "...",
                    "difficulty": "mittel"
                }}
            ],
            "adaptive_tips": ["Tipp 1"]
        }}
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
        pass

    def generate_flashcards(self, subject, topic, count=5, grades_context=""):
        """
        🃏 Generiert Lern-Karteikarten (Vorderseite/Rückseite)
        """
        prompt = fr"""
        LERN-KARTEIKARTEN GENERATOR:
        Fach: {subject}
        Thema: {topic}
        Anzahl: {count}
        
        SCHÜLER-KONTEXT (Noten):
        {grades_context}
        
        ANWEISUNG:
        Erstelle Karteikarten. 
        - Wenn die Noten in diesem Fach SCHLECHT sind: Fokus auf Grundlagen, einfache Definitionen, Verständnis.
        - Wenn die Noten GUT sind: Fokus auf Details, Transferwissen, schwere Fragen.
        
        WICHTIG FÜR MATHE/PHYSIK:
        Formeln in LaTeX mit Dollarzeichen $. Bsp: "$\frac{{1}}{{2}}$".

        Antworte STRENG als JSON:
        {{
            "flashcards": [
                {{ "front": "Begriff/Frage", "back": "Erklärung/Antwort" }}
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

    # Analyse der Noten

    def analyze_grades(self, grades_list, school_type="Gymnasium"):
        """
        📊 Analysiert Noten und gibt strategische Tipps.
        grades_list ist eine Liste von dicts: [{'subject': 'Mathe', 'value': 4.5, ...}]
        """
        prompt = f"""
        Du bist der strategische Lern-Coach. 
        Analysiere die aktuellen Noten eines Schülers ({school_type}).
        
        NOTEN:
        {json.dumps(grades_list, indent=2)}
        
        AUFGABE:
        1. Identifiziere "Problemfächer" (Noten schlechter als 4 oder < 5 Punkte).
        2. Identifiziere "Stärken".
        3. Gib für die Problemfächer eine SOFORTIGE Handlungsempfehlung.
        
        Antworte als JSON:
        {{
            "analysis_text": "Dein motivierender Kommentar zum Gesamtbild (max 2 Sätze).",
            "alerts": [
                {{ "subject": "Fach", "issue": "Note 5", "advice": "Konkreter Lerntipp für dieses Fach" }}
            ],
            "praise": "Lob für gute Fächer"
        }}
        """
        return self._robust_api_call(prompt, response_format="json")

    def analyze_document_text(self, raw_text, subject):
        """
        📄 Liest rohen Text (aus PDF) und erstellt eine Wissens-Zusammenfassung.
        """
        # Text kürzen, falls PDF riesig ist (Sicherheitsnetz)
        safe_text = raw_text[:8000] 
        
        prompt = f"""
        ANALYSE SCHULMATERIAL ({subject}):
        
        Du bist ein intelligenter Assistent, der Schulunterlagen für eine Datenbank zusammenfasst.
        
        INPUT TEXT:
        "{safe_text}..."
        
        AUFGABE:
        Erstelle eine extrem dichte Zusammenfassung der wichtigsten Fakten, Definitionen und Formeln.
        Ignoriere Füllwörter. Das Ziel ist, dass eine KI später basierend hierauf Prüfungsfragen erstellen kann.
        
        FORMAT (Plain Text, keine Markdown-Überschriften):
        Thema: [Thema nennen] | Kernkonzepte: [Konzept 1, Konzept 2] | Wichtige Details: [Fakten...]
        """
        # Hier reicht einfacher Text als Antwort
        return self._robust_api_call(prompt, response_format="text")

    def chat_tutor(self, message, subject, school_context, material_context, chat_history=[]):
        """
        💬 Der interaktive Tutor-Modus.
        """
        history_text = "\n".join([f"User: {entry['user']}\nAI: {entry['ai']}" for entry in chat_history[-3:]])

        prompt = f"""
        ROLLE:
        Du bist ein geduldiger, schlauer Nachhilfe-Lehrer für einen Schüler ({school_context}).
        Fach: {subject}
        
        WISSENSBASIS (Aus den Heften des Schülers):
        {material_context}
        
        KONTEXT/VERLAUF:
        {history_text}
        
        NEUE FRAGE:
        "{message}"
        
        ANWEISUNG:
        1. Antworte kurz, prägnant und hilfreich.
        2. Nutze Markdown für Formatierung (**Fett**, *Kursiv*, Listen -).
        3. WICHTIG: Antworte NUR mit dem Text. KEIN JSON format! KEINE geschweiften Klammern {{ }} am Anfang/Ende.
        4. Wenn du aufzählen musst, nutze Bullet Points (-).
        
        Beziehe dich STARK auf die Wissensbasis oben, wenn relevant.
        """
        
        # Antwort als reiner Text
        return self._robust_api_call(prompt, response_format="text")

    def find_connections(self, subject, topic, existing_topics):
        """
        Sucht Verbindungen zwischen dem neuen Thema und der Liste bestehender Themen.
        existing_topics ist eine Liste von Strings: ["Mathe: Analysis", "Physik: Mechanik", ...]
        """
        if not existing_topics:
            return []

        prompt = f"""
        Ich lerne gerade '{topic}' im Fach '{subject}'.
        Hier ist eine Liste anderer Themen, die ich bereits gelernt habe:
        {json.dumps(existing_topics)}

        Welche dieser Themen haben eine direkte, logische Wissens-Verbindung zu '{topic}'?
        (z.B. Mathe:Integrale -> Physik:Kinematik).
        
        Antworte NUR mit einem validen JSON-Array von Objekten. Format:
        [{{"target": "Fach: Thema", "reason": "Kurze Begründung"}}]
        
        Wenn es keine offensichtliche Verbindung gibt, antworte mit [].
        """
        
        try:
            # Hier nutzen wir deine bestehende call_llm Funktion
            # (Passe den Modell-Namen an, falls du 'llama3.1' oder 'openrouter' nutzt)
            response = self._robust_api_call(prompt, system_prompt="Du bist ein Experte für interdisziplinäres Wissen.")
            
            # JSON Parsing
            clean_json = response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0]
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0]
                
            return json.loads(clean_json)
        except Exception as e:
            print(f"❌ Fehler bei Verbindungssuche: {e}")
            return []