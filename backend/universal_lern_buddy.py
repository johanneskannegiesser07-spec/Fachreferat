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

# in backend/universal_lern_buddy.py

    def generate_personalized_exercises(self, username, subject, topic, count=3):
        """
        Generiert Übungen basierend auf Noten UND hochgeladenem Material.
        """
        user_hash = self.db.get_user_hash(username)
        
        # --- TEIL 1: Noten-Kontext (wie gehabt) ---
        grades = self.db.get_grades(user_hash)
        # Filter: Nur Noten für das gewählte Fach
        subj_grades = [float(g[2]) for g in grades if g[1].lower() == subject.lower()]
        
        grades_context = ""
        if subj_grades:
            avg = sum(subj_grades) / len(subj_grades)
            grades_context = f"Der Schüler steht in {subject} aktuell auf {avg:.2f}. Passe die Schwierigkeit an (bei schlechten Noten einfacher, bei guten schwerer)."
        else:
            grades_context = "Keine Noten bekannt. Wähle mittlere Schwierigkeit."

        # --- TEIL 2: Material-Kontext (NEU & WICHTIG) 📄 ---
        # Wir holen die 3 neuesten Zusammenfassungen zu diesem Fach
        materials = self.db.get_subject_materials(user_hash, subject, limit=3)
        
        material_context = ""
        if materials:
            # Datenbank gibt Liste von Tupeln zurück: [('Text A',), ('Text B',)]
            summaries_list = [m[0] for m in materials]
            joined_text = "\n\n".join(summaries_list)
            
            material_context = f"""
            WICHTIG - BASIERE DIE FRAGEN AUF DIESEM UNTERRICHTSMATERIAL:
            ------------------------------------------
            {joined_text}
            ------------------------------------------
            Stelle sicher, dass die Fragen die Konzepte aus diesem Material abprüfen!
            """
        else:
            material_context = "Kein spezifisches Unterrichtsmaterial vorhanden. Nutze allgemeines Lehrbuchwissen."

        # --- TEIL 3: Zusammenfügen & KI Fragen ---
        full_context_info = f"{grades_context}\n{material_context}"
        
        print(f"🧠 Generiere mit Kontext: {len(material_context)} Zeichen Material, Note: {avg if subj_grades else 'N/A'}")

        # Übergabe an AI Engine (diese nutzt den context_info Prompt)
        exercises = self.ai.generate_exercises(subject, topic, count, context_info=full_context_info)
        
        if exercises:
            return exercises
            
        # Fallback
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
        """Generiert Nodes und Edges basierend auf echten DB-Daten"""
        user_hash = self.db.get_user_hash(username)
        
        # 1. Echte Daten aus der DB holen
        stats = self.db.get_topic_performance(user_hash)
        
        nodes = []
        edges = []
        
        # 1. ROOT NODE (Das Zentrum)
        nodes.append({
            "id": "root", 
            "label": "🧠 Mein Wissen", 
            "color": "#ffffff", 
            "shape": "diamond",
            "size": 40,
            "font": {"size": 20, "color": "#ffffff"}
        })
        
        subjects_map = {} # Cache, damit wir Fächer-Nodes nicht doppelt erstellen
        
        for row in stats:
            subject, topic, avg_score, count = row
            
            # --- FACH NODE (Level 1) ---
            if subject not in subjects_map:
                subj_id = f"subj_{subject}"
                nodes.append({
                    "id": subj_id,
                    "label": subject,
                    "color": "#4facfe",  # Schönes Hellblau
                    "shape": "dot",
                    "size": 30,
                    "font": {"color": "#ffffff"}
                })
                # Verbindung zum Gehirn
                edges.append({"from": "root", "to": subj_id, "length": 150})
                subjects_map[subject] = True
            
            # --- THEMA NODE (Level 2) ---
            # Farbe basierend auf Note/Score (Ampel-System)
            if avg_score >= 80:
                color = "#28a745" # Grün (Super!)
            elif avg_score >= 50:
                color = "#ffc107" # Gelb (Okay)
            else:
                color = "#dc3545" # Rot (Lernbedarf!)
            
            topic_id = f"topic_{subject}_{topic}"
            
            # Label zeigt Thema + Prozentzahl
            label_text = f"{topic}\n{int(avg_score)}%"
            
            nodes.append({
                "id": topic_id,
                "label": label_text,
                "color": color,
                "shape": "dot",
                # Wichtiges Detail: Größe wächst mit Anzahl der Tests!
                "size": 15 + (count * 1.5), 
                "font": {"size": 14, "color": "#ffffff", "strokeWidth": 2, "strokeColor": "#000000"}
            })
            
            # Verbindung Fach -> Thema
            edges.append({"from": f"subj_{subject}", "to": topic_id})
            
        return {"nodes": nodes, "edges": edges}

    # === KARTEIKARTEN ===

    def start_flashcard_session(self, username, subject, topic, count=10):
        user_hash = self.db.get_user_hash(username)
        
        # --- NEU: Noten-Kontext bauen ---
        grades = self.db.get_grades(user_hash) # Holt alle Noten
        relevant_grade = "Keine Note bekannt"
        
        # Wir suchen die Note für das spezifische Fach (oder Durchschnitt)
        subj_grades = [float(g[2]) for g in grades if g[1].lower() == subject.lower()]
        if subj_grades:
            avg = sum(subj_grades) / len(subj_grades)
            relevant_grade = f"Durchschnittsnote in {subject}: {avg:.2f}"
        
        print(f"🃏 Generiere Karteikarten für {subject} (Kontext: {relevant_grade})...")
        
        # KI Generierung mit Context
        cards_data = self.ai.generate_flashcards(subject, topic, count, grades_context=relevant_grade)
        
        if not cards_data or 'flashcards' not in cards_data:
            cards_data = {
                "flashcards": [{"front": "Fehler", "back": "Konnte keine Karten generieren."}]
            }
        
        set_id = self.db.save_flashcard_set(user_hash, subject, topic, cards_data['flashcards'])
            
        return {
            "set_id": set_id, "subject": subject, "topic": topic, "cards": cards_data['flashcards']
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

# === NOTEN & FÄCHER VERWALTUNG ===

    def add_grade(self, username, subject, value, grade_type, weight):
        """Leitet das Speichern einer Note an die DB weiter"""
        user_hash = self.db.get_user_hash(username)
        # Achtung: Stelle sicher, dass add_grade in database.py existiert!
        return self.db.add_grade(user_hash, subject, value, grade_type, weight)

    def get_grades(self, username):
        """Holt Noten aus der DB"""
        user_hash = self.db.get_user_hash(username)
        return self.db.get_grades(user_hash)

    def add_custom_subject(self, username, subject):
        """Fügt ein neues Fach hinzu"""
        user_hash = self.db.get_user_hash(username)
        return self.db.add_custom_subject(user_hash, subject)

    def analyze_user_grades(self, username):
        """
        Holt Noten aus der DB, bereitet sie auf und 
        fragt die KI nach einer Analyse.
        """
        user_hash = self.db.get_user_hash(username)
        
        # 1. Noten holen (Rohe DB-Daten: Tuples)
        raw_grades = self.db.get_grades(user_hash)
        
        # 2. In schönes Format für die KI umwandeln
        # DB liefert meist: (id, subject, value, type, weight, date)
        grades_list = []
        for g in raw_grades:
            grades_list.append({
                "subject": g[1],
                "value": float(g[2]),
                "type": g[3],
                "date": str(g[5])
            })
            
        # 3. Schulkontext holen (für Schulart, z.B. Gymnasium vs Realschule)
        context = self.get_school_context(username)
        school_type = context.get('school_type', 'Allgemein')

        # 4. KI fragen (Methode muss in ai_engine.py existieren!)
        if hasattr(self.ai, 'analyze_grades'):
            return self.ai.analyze_grades(grades_list, school_type)
        else:
            return {
                "analysis_text": "KI-Funktion 'analyze_grades' noch nicht implementiert.",
                "alerts": [],
                "praise": ""
            }

    # Methode zum Löschen (am Ende der Klasse):
    def delete_grade(self, username, grade_id):
        user_hash = self.db.get_user_hash(username)
        return self.db.delete_grade(grade_id, user_hash)

    # Hilfsmethode PDF Upload Verarbeitung:
    
    def process_uploaded_material(self, username, subject, filename, raw_text):
        user_hash = self.db.get_user_hash(username)
        
        print(f"📄 Analysiere Material für {subject}...")
        
        # 1. KI fasst zusammen
        summary = self.ai.analyze_document_text(raw_text, subject)
        if not summary: summary = "Analyse fehlgeschlagen."
        
        # 2. Speichern (Wir raten das Thema basierend auf der ersten Zeile oder Dateiname, hier einfach "Upload")
        self.db.save_material_summary(user_hash, subject, "PDF Upload", filename, summary)
        
        return summary

    # === CHAT FUNKTION ===

    def chat_with_ai(self, username, message, subject, history=[]):
        user_hash = self.db.get_user_hash(username)
        
        # 1. Schul-Kontext holen
        context = self.get_school_context(username)
        school_info = f"{context.get('grade', 'Klasse ?')} - {context.get('school_type', 'Schule')}"
        
        # 2. Material holen (RAG - Retrieval Augmented Generation)
        # Wir nehmen einfach ALLES Wissen zu diesem Fach (oder die Top 5 neuesten Uploads)
        materials = self.db.get_subject_materials(user_hash, subject, limit=5)
        material_text = "Keine Unterlagen vorhanden. Nutze dein Allgemeinwissen."
        
        if materials:
            summary_list = [m[0] for m in materials]
            material_text = "\n---\n".join(summary_list)
            
        print(f"💬 Chat in {subject}: '{message}' (Material-Länge: {len(material_text)})")
        
        # 3. KI fragen
        response = self.ai.chat_tutor(message, subject, school_info, material_text, history)
        
        if not response:
            return "Entschuldigung, ich habe gerade Verbindungsprobleme. Frag mich gleich nochmal!"
            
        return response

    # === GAMIFICATION LOGIC ===

    def get_user_stats(self, username):
        """Holt XP und Gems"""
        res = self.db.get_user_gamification(username)
        if res:
            return {"xp": res[0], "gems": res[1]}
        return {"xp": 0, "gems": 0}

    def can_play_game(self, username):
        """Prüft ob genug Gems da sind"""
        stats = self.get_user_stats(username)
        return stats["gems"] > 0

    def pay_for_game(self, username):
        """Zieht 1 Gem ab"""
        if self.can_play_game(username):
            self.db.update_gamification(username, 0, -1) # -1 Gem
            return True
        return False

    def award_game_win(self, username):
        """Gibt XP bei Sieg"""
        self.db.update_gamification(username, 42, 0) # +42 XP