"""
🤖 UNIVERSALER KI-LERN-BUDDY (Controller)
Verbindet Datenbank, KI-Engine und Business-Logik.
"""

import json
import time
from datetime import datetime, timedelta
from database import DatabaseManager
from ai_engine import AIEngine  # Unsere neue KI-Klasse

class UniversalLernBuddy:
    def __init__(self, db_path="universal_lern_buddy.db"):
        # Initialisiere die Module
        self.db = DatabaseManager(db_path)
        self.ai = AIEngine()
        print("✅ KI-Lern-Buddy Controller bereit")

    # === USER & AUTH ===

    def create_user(self, username, email, password, role="student"):
        from auth import get_password_hash
        pwd_hash = get_password_hash(password)
        
        success = self.db.create_user(username, email, pwd_hash, role)
        if success:
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
        
        profile = self.db.get_profile(user_hash)
        current_profile = {
            "detected_learning_style": style,
            "cognitive_patterns": patterns,
            "performance_trends": {},
            "adaptation_history": []
        }
        self.db.save_profile(user_hash, current_profile)
        return current_profile

    def _analyze_learning_patterns(self, sessions):
        patterns = {"duration_patterns": [], "performance_by_subject": {}}
        for s in sessions:
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

    # === ÜBUNGEN & TEST MODUS ===

    def generate_personalized_exercises(self, username, subject, topic, count=3):
        # Versuche KI-Generierung
        exercises = self.ai.generate_exercises(subject, topic, count)
        
        if exercises:
            return exercises
            
        # Fallback wenn KI scheitert
        return self._get_mc_multiple_fallback_exercises(subject, topic, count)

    def start_test_session(self, username, subject, topic, count=10):
        user_hash = self.db.get_user_hash(username)
        test_id = f"test_{int(time.time())}_{user_hash}"
        
        print(f"⏳ Generiere Aufgaben für {subject}...")
        exercises_result = self.generate_personalized_exercises(username, subject, topic, count)
        
        # Zeit startet erst nach Generierung!
        start_time = datetime.utcnow().isoformat()
        
        self.db.create_test_session(test_id, user_hash, subject, topic, json.dumps(exercises_result), count, start_time)
        
        return {
            "test_id": test_id,
            "exercises": exercises_result,
            "total_questions": count,
            "time_limit": 60 * count,
            "start_time": start_time,
            "subject": subject,
            "topic": topic
        }

    def retake_test_session(self, username, old_test_id):
        user_hash = self.db.get_user_hash(username)
        old_data = self.db.get_test_session(old_test_id, user_hash)
        
        if not old_data: return {"error": "Test nicht gefunden"}
        
        subject, topic, questions_json = old_data[0], old_data[1], old_data[2]
        
        new_test_id = f"test_{int(time.time())}_{user_hash}"
        start_time = datetime.utcnow().isoformat()
        
        self.db.create_test_session(new_test_id, user_hash, subject, topic, questions_json, old_data[4], start_time)
        
        return {
            "test_id": new_test_id,
            "subject": subject,
            "topic": topic,
            "exercises": json.loads(questions_json),
            "total_questions": old_data[4],
            "time_limit": 60 * old_data[4],
            "start_time": start_time,
            "is_retake": True
        }

    def submit_test_answer_multiple(self, username, test_id, question_index, user_answers):
        # Speichern & KI-Feedback für die einzelne Antwort holen
        self.save_answer(username, test_id, question_index, user_answers)
        
        # Wir brauchen die Frage für das Feedback
        user_hash = self.db.get_user_hash(username)
        data = self.db.get_test_session(test_id, user_hash)
        if not data: return {}
        
        questions = json.loads(data[2])['exercises']
        question_data = questions[question_index]
        correct = question_data.get('correct_answers', [])
        
        is_correct = set(user_answers) == set(correct)
        
        # KI Einzel-Feedback
        feedback = self.ai.generate_single_answer_feedback(
            question_data.get('question'),
            str(correct),
            str(user_answers),
            is_correct
        )
        
        # Wenn KI failt, Fallback
        if not feedback:
            feedback = {"strengths": "Antwort gespeichert", "improvements": "", "hint": "", "concept_explanation": ""}
            
        return {
            "is_correct": is_correct,
            "feedback": feedback
        }
        
    def save_answer(self, username, test_id, q_index, answers):
        user_hash = self.db.get_user_hash(username)
        test_data = self.db.get_test_session(test_id, user_hash)
        if not test_data: return False
        
        current_list = json.loads(test_data[3]) if test_data[3] else []
        new_entry = {'question_index': q_index, 'user_answer': answers, 'timestamp': datetime.now().isoformat()}
        
        updated = False
        for i, item in enumerate(current_list):
            if item.get('question_index') == q_index:
                current_list[i] = new_entry
                updated = True
                break
        if not updated: current_list.append(new_entry)
        
        self.db.update_test_answer(test_id, json.dumps(current_list))
        return True

    def finish_test_session_complete(self, username, test_id):
        user_hash = self.db.get_user_hash(username)
        data = self.db.get_test_session(test_id, user_hash)
        if not data: return {"error": "Test nicht gefunden"}
        
        subject, topic, q_json, a_json, total, start_time, _, _ = data
        questions = json.loads(q_json).get('exercises', []) if q_json else []
        user_answers = json.loads(a_json) if a_json else []
        
        correct_count = 0
        detailed = []
        
        for i, q in enumerate(questions):
            u_ans_data = next((a for a in user_answers if a.get('question_index') == i), None)
            u_list = u_ans_data.get('user_answer', []) if u_ans_data else []
            c_list = q.get('correct_answers', [])
            
            is_correct = set(u_list) == set(c_list)
            if is_correct: correct_count += 1
            
            detailed.append({
                "question_index": i, "question": q.get('question'), 
                "user_answers": u_list, "correct_answers": c_list,
                "is_correct": is_correct, "explanation": q.get('explanation', ''),
                "options": q.get('options', {}) # Optionen wichtig für Anzeige!
            })

        score = (correct_count / total) * 100 if total else 0
        time_spent = self._calculate_time_spent(start_time)
        
        # Speichern
        self.db.complete_test(test_id, score, correct_count, time_spent, json.dumps(user_answers))
        
        # KI Gesamtauswertung
        print(f"🧠 Starte KI-Analyse für {test_id}...")
        feedback = self.ai.generate_feedback(subject, topic, score, correct_count, total)
        
        if not feedback:
            feedback = self._get_fallback_feedback(score, correct_count, total)
        
        return {
            "test_id": test_id, "score": round(score, 1), 
            "correct_answers": correct_count, "total_questions": total,
            "time_spent_seconds": time_spent,
            "performance_level": self._get_performance_level(score),
            "subject": subject, "topic": topic,
            "comprehensive_feedback": feedback,
            "detailed_answers": detailed
        }

    # === HELFER & FALLBACKS ===
    
    def _calculate_time_spent(self, start_time):
        try:
            if isinstance(start_time, str):
                start = datetime.fromisoformat(start_time)
            else:
                start = start_time
            return int((datetime.utcnow() - start).total_seconds())
        except:
            return 0

    def _get_performance_level(self, score):
        if score >= 90: return "Exzellent"
        if score >= 60: return "Gut"
        return "Braucht Übung"

    def _get_mc_multiple_fallback_exercises(self, subject, topic, count):
        # Einfaches Fallback, damit der Test nicht abstürzt
        return {
            "exercises": [{
                "question": f"Beispielfrage zu {topic} (KI nicht erreichbar)",
                "options": {"A": "Option 1", "B": "Option 2"},
                "correct_answers": ["A"],
                "explanation": "Dies ist ein Platzhalter.",
                "difficulty": "mittel",
                "multiple_correct": False
            }] * count,
            "adaptive_tips": ["Verbindung zur KI prüfen"]
        }
    
    def _get_fallback_feedback(self, score, correct, total):
        return {
            "overall_assessment": f"Test beendet! {correct}/{total} Punkte.",
            "key_strengths": ["Durchgehalten"],
            "main_weaknesses": [],
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
            history.append({
                "test_id": h[0], "subject": h[1], "topic": h[2], "score": h[3],
                "correct_answers": h[4], "total_questions": h[5],
                "time_spent_seconds": h[6], "date": h[8] or h[7],
                "performance_level": self._get_performance_level(h[3] or 0)
            })
        return history
    
    def submit_test_answer(self, u, t, q, a): return self.save_answer(u, t, q, a)

    # === GRAPH FEATURE ===

    def get_knowledge_graph_data(self, username):
        user_hash = self.db.get_user_hash(username)
        
        # 1. Daten holen
        test_data = self.db.get_subject_averages(user_hash)     # [(Mathe, 80.5, 5), ...]
        card_data = self.db.get_flashcard_counts(user_hash)     # [(Mathe, 3), ...]
        
        # 2. Daten zusammenführen (Dictionary für schnellen Zugriff)
        subjects = {}
        
        # Erst Testergebnisse verarbeiten
        for row in test_data:
            subj, score, count = row
            subjects[subj] = {
                "score": score, 
                "test_count": count, 
                "card_count": 0
            }
            
        # Dann Flashcards dazuaddieren
        for row in card_data:
            subj, count = row
            if subj not in subjects:
                # Fach existiert nur als Karteikarte (noch kein Test gemacht)
                subjects[subj] = {"score": 0, "test_count": 0, "card_count": count}
            else:
                subjects[subj]["card_count"] = count

        # 3. Nodes erstellen
        nodes = []
        for subj, data in subjects.items():
            score = data["score"]
            total_activity = data["test_count"] + data["card_count"]
            
            # Farbe basiert NUR auf Test-Score (Leistung)
            if data["test_count"] == 0:
                color = "#6c757d" # Grau (nur gelernt, nie getestet)
            elif score >= 80: color = "#28a745" # Grün
            elif score >= 50: color = "#ffc107" # Gelb
            else: color = "#dc3545" # Rot
            
            # Größe basiert auf Aktivität (Tests + Flashcards)
            # Basisgröße 20 + 5 pro Aktivität (max 60)
            size = min(60, 20 + (total_activity * 5))

            nodes.append({
                "id": subj,
                "label": f"{subj}\n({int(score)}%)" if data["test_count"] > 0 else f"{subj}\n(Lernen)",
                "value": size,  # Hier wirkt sich das Flashcard-Lernen aus!
                "color": color,
                "title": f"{data['test_count']} Tests, {data['card_count']} Lern-Sets" # Tooltip
            })

        # 4. Edges definieren (Logische Verbindungen bleiben gleich)
        defined_connections = [
            ("Mathe", "Physik"), ("Mathe", "Informatik"), ("Mathe", "Chemie"),
            ("Physik", "Chemie"), ("Biologie", "Chemie"),
            ("Deutsch", "Englisch"), ("Englisch", "Französisch"), ("Englisch", "Latein"),
            ("Geschichte", "Politik"), ("Geschichte", "Deutsch"),
            ("Wirtschaft", "Mathe"), ("Wirtschaft", "Politik"),
            ("Geografie", "Wirtschaft"), ("Biologie", "Geografie")
        ]
        
        edges = []
        for source, target in defined_connections:
            if source in subjects and target in subjects:
                # Wenn beide Fächer existieren, Linie zeichnen
                s1 = subjects[source]["score"]
                s2 = subjects[target]["score"]
                
                # Dicke der Linie (Nur wenn Tests da sind, sonst dünn)
                if s1 > 0 and s2 > 0:
                    width = (s1 + s2) / 40 # Dicke Linie bei guten Noten
                else:
                    width = 1 # Dünne Linie bei reinen Lernfächern
                    
                edges.append({
                    "from": source, 
                    "to": target,
                    "width": width,
                    "color": {"color": "#999", "opacity": 0.4}
                })

        return {"nodes": nodes, "edges": edges}

    # === KARTEIKARTEN ===

    def start_flashcard_session(self, username, subject, topic, count=10):
        user_hash = self.db.get_user_hash(username)
        print(f"🃏 Generiere Karteikarten für {subject}...")
        
        # KI Generierung
        cards_data = self.ai.generate_flashcards(subject, topic, count)
        
        if not cards_data or 'flashcards' not in cards_data:
            cards_data = {
                "flashcards": [{"front": "Fehler", "back": "Konnte keine Karten generieren."}]
            }
        
        # SPEICHERN IN DB
        set_id = self.db.save_flashcard_set(user_hash, subject, topic, cards_data['flashcards'])
            
        return {
            "set_id": set_id,
            "subject": subject,
            "topic": topic,
            "cards": cards_data['flashcards']
        }

    def get_flashcard_history(self, username):
        user_hash = self.db.get_user_hash(username)
        history = self.db.get_flashcard_history(user_hash)
        return [
            {
                "id": h[0], "subject": h[1], "topic": h[2], 
                "card_count": len(json.loads(h[3])), 
                "date": h[4]
            } 
            for h in history
        ]

    def load_flashcard_set(self, username, set_id):
        user_hash = self.db.get_user_hash(username)
        res = self.db.get_flashcard_set(set_id, user_hash)
        if res:
            return {
                "id": set_id, "subject": res[0], "topic": res[1], 
                "cards": json.loads(res[2])
            }
        return None

# === LERNPLANER ===

    def create_study_plan(self, username, subject, exam_date_str):
        user_hash = self.db.get_user_hash(username)
        
        # Tage berechnen
        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
            today = datetime.now()
            days_left = (exam_date - today).days + 1
            
            if days_left <= 0: return {"error": "Das Datum liegt in der Vergangenheit!"}
            if days_left > 60: return {"error": "Plan maximal für 60 Tage möglich."}
        except: return {"error": "Ungültiges Datum"}

        print(f"📅 Generiere Plan für {subject} ({days_left} Tage)...")
        
        # KI fragen
        ai_res = self.ai.generate_study_plan(subject, days_left)
        if not ai_res or 'plan' not in ai_res:
            return {"error": "KI konnte keinen Plan erstellen."}
            
        # Plan speichern
        self.db.save_study_plan(user_hash, subject, exam_date_str, ai_res['plan'])
        return {"success": True, "plan": ai_res['plan']}

    def get_user_study_plans(self, username):
        user_hash = self.db.get_user_hash(username)
        raw = self.db.get_study_plans(user_hash)
        return [
            {"id": r[0], "subject": r[1], "exam_date": r[2], "plan": json.loads(r[3])}
            for r in raw
        ]
        
    def delete_plan(self, username, plan_id):
        return self.db.delete_study_plan(plan_id, self.db.get_user_hash(username))