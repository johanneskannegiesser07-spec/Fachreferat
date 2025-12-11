"""
🤖 UNIVERSALER KI-LERN-BUDDY (Refactored Logic Layer)
Intelligenz-Layer: Verbindet KI, Datenbank und Business-Logik.
"""

import os
import requests
import json
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from database import DatabaseManager  # Nutzt unsere neue Datenbank-Klasse

load_dotenv()

class UniversalLernBuddy:
    def __init__(self, db_path="universal_lern_buddy.db"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "tngtech/deepseek-r1t2-chimera:free"
        
        # Initialisiere den DB-Manager (kein direktes SQL mehr hier!)
        self.db = DatabaseManager(db_path)
        print("🧠 KI-Lern-Buddy Logik-Layer initialisiert")

    # === USER & AUTH ===

    def create_user(self, username, email, password, role="student"):
        # Import hier, um Zirkelbezüge zu vermeiden
        from auth import get_password_hash
        pwd_hash = get_password_hash(password)
        
        success = self.db.create_user(username, email, pwd_hash, role)
        if success:
            # Erstelle initiales Profil
            user_hash = self.db.get_user_hash(username)
            self.db.save_profile(user_hash, {"detected_learning_style": "adaptiv_ausgeglichen"})
            print(f"✅ User {username} angelegt")
        return success

    def authenticate_user(self, username, password):
        from auth import verify_password
        user_data = self.db.get_user_by_username(username)
        
        if user_data and verify_password(password, user_data[1]):
            self.db.update_last_login(username)
            return {"username": user_data[0], "role": user_data[2]}
        return None

    def update_user_profile(self, username, update_data):
        return self.db.update_user_profile_data(username, update_data)

    # === SCHULE & PROFIL ===

    def set_school_context(self, username, school_data):
        user_hash = self.db.get_user_hash(username)
        # Daten für DB aufbereiten
        db_data = {
            'grade': school_data.get('grade'),
            'school_type': school_data.get('school_type'),
            'state': school_data.get('state', 'Bayern'),
            'subjects': json.dumps(school_data.get('subjects', [])),
            'curriculum_focus': school_data.get('curriculum_focus', 'allgemein')
        }
        return self.db.save_school_context(user_hash, db_data)

    def get_school_context(self, username):
        user_hash = self.db.get_user_hash(username)
        res = self.db.get_school_context(user_hash)
        if res:
            return {
                "grade": res[0], "school_type": res[1], "state": res[2],
                "subjects": json.loads(res[3]) if res[3] else [], "curriculum_focus": res[4]
            }
        return {}

    # === LERNANALYSE ===

    def detect_learning_patterns(self, username):
        user_hash = self.db.get_user_hash(username)
        sessions = self.db.get_sessions(user_hash)
        
        # Logik: Muster erkennen
        patterns = self._analyze_learning_patterns(sessions)
        style = self._detect_learning_style(patterns)
        
        # Profil laden, updaten, speichern
        profile = self.db.get_profile(user_hash)
        current_profile = {
            "detected_learning_style": style,
            "cognitive_patterns": patterns,
            "performance_trends": {}, # Platzhalter für komplexere Analysen
            "adaptation_history": []
        }
        self.db.save_profile(user_hash, current_profile)
        return current_profile

    def _analyze_learning_patterns(self, sessions):
        patterns = {"duration_patterns": [], "performance_by_subject": {}}
        for s in sessions:
            # s = (subject, duration, topics, score, engagement, date)
            patterns["duration_patterns"].append(s[1])
            subj = s[0]
            if subj not in patterns["performance_by_subject"]:
                patterns["performance_by_subject"][subj] = []
            patterns["performance_by_subject"][subj].append(s[3])
        return patterns

    def _detect_learning_style(self, patterns):
        durations = patterns.get("duration_patterns", [])
        if not durations: return "adaptiv_ausgeglichen"
        avg = sum(durations) / len(durations)
        if avg > 60: return "tiefgehend_konzentriert"
        if avg < 30: return "häufig_kurz"
        return "adaptiv_ausgeglichen"

    # === KI & ÜBUNGEN ===

    def generate_personalized_exercises(self, username, subject, topic, count=3):
        """Generiert KI-Übungen"""
        try:
            profile = self.detect_learning_patterns(username)
            # Hier könnte man den komplexen Kontext bauen
            
            prompt = f"""
    Generiere {count} Multiple-Choice Fragen für {subject} zum Thema {topic}.
    Format JSON: {{"exercises": [ {{"question": "...", "options": {{"A": "..."}}, "correct_answers": ["A"], "explanation": "..."}} ] }}
    Wichtig: Es können mehrere Antworten richtig sein. Kennzeichne das mit "correct_answers": ["A", "C"].
    """
            result = self.robust_api_call(prompt, response_format="json")
            if result:
                data = json.loads(result)
                if "exercises" in data: return data
                
        except Exception as e:
            print(f"❌ KI Fehler: {e}")
            
        return self._get_mc_multiple_fallback_exercises(subject, topic, count)

    def robust_api_call(self, prompt, max_retries=2, response_format="text", timeout=30):
        if not self.api_key: return None
        
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
            
        for _ in range(max_retries):
            try:
                resp = requests.post(self.base_url, headers=headers, json=data, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()['choices'][0]['message']['content']
            except Exception as e:
                print(f"API Fehler: {e}")
                time.sleep(1)
        return None

    # === TRACKING & ANALYTICS ===

    def track_study_session_with_engagement(self, username, subject, duration, topics, score, engagement):
        user_hash = self.db.get_user_hash(username)
        self.db.log_session(user_hash, subject, duration, topics, score, engagement, "mittel")

    def get_performance_analytics(self, username):
        user_hash = self.db.get_user_hash(username)
        subject_stats, mistakes, sessions = self.db.get_analytics_raw_data(user_hash)
        
        # Daten verarbeiten
        analytics = {
            'subject_performance': {}, 
            'overall_stats': {'total_sessions': len(sessions), 'total_answered': sum(s[0] for s in subject_stats)},
            'common_mistakes': [{'error_type': m[0], 'frequency': m[1], 'topic': m[2]} for m in mistakes]
        }
        return analytics

    # === TEST MODUS ===

    def start_test_session(self, username, subject, topic, count=10):
        user_hash = self.db.get_user_hash(username)
        test_id = f"test_{int(time.time())}_{user_hash}"
        
        # 1. KI generiert Aufgaben
        print(f"⏳ Generiere Aufgaben für {subject}...")
        exercises_result = self.generate_personalized_exercises(username, subject, topic, count)
        
        # 2. Startzeit (UTC) - Erst NACH Generierung!
        start_time = datetime.utcnow().isoformat()
        
        # 3. DB Speichern
        self.db.create_test_session(test_id, user_hash, subject, topic, json.dumps(exercises_result), count, start_time)
        
        return {
            "test_id": test_id,
            "exercises": exercises_result,
            "total_questions": count,
            "time_limit": 60 * count,
            "start_time": start_time
        }

    def retake_test_session(self, username, old_test_id):
        """Kopiert einen alten Test für einen neuen Versuch"""
        user_hash = self.db.get_user_hash(username)
        old_data = self.db.get_test_session(old_test_id, user_hash)
        
        if not old_data: return {"error": "Test nicht gefunden"}
        
        # (subject, topic, questions_json, answers, total, start, score, correct)
        subject, topic, questions_json, _, total_questions, _, _, _ = old_data
        
        new_test_id = f"test_{int(time.time())}_{user_hash}"
        start_time = datetime.utcnow().isoformat()
        
        print(f"🔄 Kopiere Test {old_test_id} -> {new_test_id}")
        
        self.db.create_test_session(new_test_id, user_hash, subject, topic, questions_json, total_questions, start_time)
        
        return {
            "test_id": new_test_id,
            "subject": subject,
            "topic": topic,
            "exercises": json.loads(questions_json),
            "total_questions": total_questions,
            "time_limit": 60 * total_questions,
            "start_time": start_time,
            "is_retake": True
        }

    def save_answer(self, username, test_id, q_index, answers):
        user_hash = self.db.get_user_hash(username)
        test_data = self.db.get_test_session(test_id, user_hash)
        if not test_data: return False
        
        current_json = test_data[3] # user_answers Spalte
        current_list = json.loads(current_json) if current_json else []
        
        # Update Logik
        updated = False
        new_entry = {'question_index': q_index, 'user_answer': answers, 'timestamp': datetime.now().isoformat()}
        
        for i, item in enumerate(current_list):
            if item.get('question_index') == q_index:
                current_list[i] = new_entry
                updated = True
                break
        if not updated: current_list.append(new_entry)
        
        self.db.update_test_answer(test_id, json.dumps(current_list))
        return True

    def submit_test_answer(self, username, test_id, question_index, user_answer):
        # Wrapper für Einzelantworten (Kompatibilität)
        return self.save_answer(username, test_id, question_index, user_answer)

    def submit_test_answer_multiple(self, username, test_id, question_index, user_answers):
        # Wrapper für Mehrfachantworten
        return self.save_answer(username, test_id, question_index, user_answers)

    def finish_test_session_complete(self, username, test_id):
        """
        🏁 Beendet Test und holt KI-Feedback (Cooler Coach!)
        """
        user_hash = self.db.get_user_hash(username)
        data = self.db.get_test_session(test_id, user_hash)
        if not data: return {"error": "Test nicht gefunden"}
        
        subject, topic, q_json, a_json, total, start_time, _, _ = data
        
        questions = json.loads(q_json).get('exercises', []) if q_json else []
        user_answers = json.loads(a_json) if a_json else []
        
        # Auswerten
        correct_count = 0
        detailed = []
        
        for i, q in enumerate(questions):
            u_ans_data = next((a for a in user_answers if a.get('question_index') == i), None)
            u_list = u_ans_data.get('user_answer', []) if u_ans_data else []
            c_list = q.get('correct_answers', [])
            
            # Vergleich (Set-Logik für beliebige Reihenfolge)
            is_correct = set(u_list) == set(c_list)
            if is_correct: correct_count += 1
            
            detailed.append({
                "question_index": i, "question": q.get('question'), 
                "user_answers": u_list, "correct_answers": c_list,
                "is_correct": is_correct, "explanation": q.get('explanation', '')
            })

        score = (correct_count / total) * 100 if total else 0
        time_spent = self._calculate_time_spent(start_time)
        
        # Speichern
        self.db.complete_test(test_id, score, correct_count, time_spent, json.dumps(user_answers))
        
        # KI Feedback holen (Der Coole Coach!)
        print(f"🧠 Starte KI-Analyse für {test_id}...")
        try:
            comprehensive_feedback = self.generate_comprehensive_feedback(username, test_id, subject, topic, score, correct_count, total)
        except Exception as e:
            print(f"⚠️ KI-Fehler: {e}")
            comprehensive_feedback = self._get_fallback_feedback(score, correct_count, total)
        
        return {
            "test_id": test_id,
            "score": round(score, 1),
            "correct_answers": correct_count,
            "total_questions": total,
            "time_spent_seconds": time_spent,
            "performance_level": self._get_performance_level(score),
            "subject": subject, "topic": topic,
            "comprehensive_feedback": comprehensive_feedback,
            "detailed_answers": detailed
        }

    def generate_comprehensive_feedback(self, username, test_id, subject, topic, score, correct, total):
        """
        🚀 Der Coole Coach Prompt
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
        result = self.robust_api_call(prompt, response_format="json", timeout=15)
        if result:
            return json.loads(result)
        raise Exception("Keine Antwort")

    # === HELFER ===
    
    def _calculate_time_spent(self, start_time):
        try:
            # WICHTIG: utcnow() nutzen passend zu start_time
            if isinstance(start_time, str):
                start = datetime.fromisoformat(start_time)
            else:
                start = start_time
            return int((datetime.utcnow() - start).total_seconds())
        except:
            return 0

    def _get_performance_level(self, score):
        if score >= 90: return "Exzellent"
        if score >= 75: return "Sehr gut"
        if score >= 60: return "Gut"
        if score >= 50: return "Befriedigend"
        return "Braucht Übung"

    def _get_mc_multiple_fallback_exercises(self, subject, topic, count):
        return {
            "exercises": [{
                "question": f"Beispielfrage zu {topic}",
                "options": {"A": "Richtig", "B": "Falsch"},
                "correct_answers": ["A"],
                "explanation": "Dies ist eine generierte Fallback-Frage.",
                "difficulty": "mittel",
                "multiple_correct": False
            }] * count,
            "adaptive_tips": ["KI war gerade beschäftigt, hier sind Standard-Aufgaben."]
        }
    
    def _get_fallback_feedback(self, score, correct, total):
        return {
            "overall_assessment": f"Solider Test! {correct}/{total} Punkte.",
            "key_strengths": ["Test abgeschlossen"],
            "main_weaknesses": ["Analyse momentan nicht verfügbar"],
            "learning_recommendations": [],
            "conceptual_understanding": "Nicht bewertbar",
            "next_steps": ["Weiterüben"],
            "encouragement": "Dranbleiben! 💪"
        }

    def get_test_history(self, username, limit=10):
        user_hash = self.db.get_user_hash(username)
        raw_history = self.db.get_test_history(user_hash, limit)
        history = []
        for h in raw_history:
            # h = (id, sub, top, score, corr, tot, time, start, end)
            history.append({
                "test_id": h[0], "subject": h[1], "topic": h[2], "score": h[3],
                "correct_answers": h[4], "total_questions": h[5],
                "time_spent_seconds": h[6], "date": h[8] or h[7],
                "performance_level": self._get_performance_level(h[3] or 0)
            })
        return history