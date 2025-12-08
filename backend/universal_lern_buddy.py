"""
🤖 UNIVERSALER KI-LERN-BUDDY
Fachreferat - Intelligente Lernplattform mit KI-Personalisierung

Diese Klasse implementiert einen komplett adaptiven Lern-Buddy mit:
- Automatischer Lernstil-Erkennung
- KI-gestützter Übungsgenerierung
- Umfassender Performance-Analyse
- Multi-User Unterstützung
- Schulkontext-Integration

Autor: [Dein Name]
Datum: [Aktuelles Datum]
"""

import os
import requests
import json
import time
import random
import sqlite3
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Lade Umgebungsvariablen für API-Keys
load_dotenv()

class UniversalLernBuddy:
    """
    🤖 Hauptklasse des KI-Lern-Buddys
    
    Diese Klasse verwaltet die komplette Logik für:
    - User-Management und Authentifizierung
    - Lernanalyse und Profilerstellung
    - KI-gestützte Übungsgenerierung
    - Performance-Tracking und Analytics
    - Datenbank-Operationen
    """
    
    def __init__(self, db_path="universal_lern_buddy.db"):
        """
        Initialisiert den Lern-Buddy mit Datenbank und API-Konfiguration
        
        Args:
            db_path (str): Pfad zur SQLite-Datenbank
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "tngtech/deepseek-r1t2-chimera:free"
        self.db_path = db_path
        self.school_contexts = {}  # Speichert Schuldaten pro User
        
        # Initialisiere Datenbank
        self._init_database()
        print("🌍 Universaler KI-Lern-Buddy initialisiert")

    # === DATENBANK-METHODEN ===

    def _init_database(self):
        """
        🔧 Initialisiert die SQLite-Datenbank mit verbessertem Lock-Handling
        """
        conn = None
        try:
            # Timeout für Database Lock erhöhen
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Pragmas für bessere Parallelität
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=20000")
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # User-Management Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'student',
                    grade TEXT,
                    school_type TEXT,
                    state TEXT DEFAULT 'Bayern',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # User-Profile Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_hash TEXT PRIMARY KEY,
                    detected_learning_style TEXT,
                    cognitive_patterns TEXT,
                    performance_trends TEXT,
                    adaptation_history TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Schulkontext-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS school_contexts (
                    user_hash TEXT PRIMARY KEY,
                    grade TEXT,
                    school_type TEXT,
                    state TEXT,
                    subjects TEXT,
                    curriculum_focus TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_hash) REFERENCES user_profiles (user_hash)
                )
            ''')
            
            # Bestehende Tabellen...
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_hash TEXT,
                    subject TEXT,
                    duration_minutes INTEGER,
                    topics TEXT,
                    performance_score REAL,
                    engagement_level REAL,
                    difficulty_level TEXT,
                    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_hash) REFERENCES user_profiles (user_hash)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercise_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_hash TEXT,
                    exercise_id TEXT,
                    subject TEXT,
                    topic TEXT,
                    question TEXT,
                    user_answer TEXT,
                    correct_answer TEXT,
                    is_correct INTEGER,
                    time_spent_seconds INTEGER,
                    difficulty TEXT,
                    tags TEXT,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_hash) REFERENCES user_profiles (user_hash)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mistake_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_hash TEXT,
                    subject TEXT,
                    topic TEXT,
                    error_type TEXT,
                    pattern_data TEXT,
                    frequency INTEGER,
                    first_occurrence TIMESTAMP,
                    last_occurrence TIMESTAMP,
                    FOREIGN KEY (user_hash) REFERENCES user_profiles (user_hash)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adaptation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_hash TEXT,
                    adaptation_type TEXT,
                    before_state TEXT,
                    after_state TEXT,
                    effectiveness_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Test-Sessions Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_sessions (
                    test_id TEXT PRIMARY KEY,
                    user_hash TEXT,
                    subject TEXT,
                    topic TEXT,
                    questions TEXT,
                    user_answers TEXT DEFAULT '[]',
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    time_spent_seconds INTEGER DEFAULT 0,
                    score REAL DEFAULT 0,
                    correct_answers INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_hash) REFERENCES user_profiles (user_hash)
                )
            ''')

            # Test-Results Tabelle für detaillierte Auswertung
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    user_hash TEXT,
                    question_index INTEGER,
                    user_answer TEXT,
                    correct_answer TEXT,
                    is_correct INTEGER,
                    time_spent INTEGER,
                    feedback TEXT,
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES test_sessions (test_id)
                )
            ''')
            
            conn.commit()
            print("✅ Datenbank-Tabellen initialisiert mit WAL-Mode")
            
        except Exception as e:
            print(f"❌ Fehler bei Datenbank-Initialisierung: {e}")
        finally:
            if conn:
                conn.close()

    # === USER-MANAGEMENT ===

    def create_user(self, username: str, email: str, password: str, role: str = "student") -> bool:
        """
        👤 Erstellt einen neuen Benutzer mit verbessertem DB-Handling
        """
        try:
            from auth import get_password_hash
        except ImportError:
            # Fallback für Entwicklungsmodus
            import hashlib
            def get_password_hash(pwd):
                return hashlib.sha256(pwd.encode()).hexdigest()
        
        user_hash = self._get_user_hash(username)
        password_hash = get_password_hash(password)
        
        conn = None
        try:
            # Verbindung mit Timeout
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            
            conn.commit()
            
            # Erstelle initiales Profil
            self._create_initial_profile(user_hash)
            
            print(f"✅ User {username} erfolgreich erstellt")
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"❌ User {username} existiert bereits: {e}")
            return False
        except sqlite3.OperationalError as e:
            print(f"🔒 Database locked bei User-Erstellung: {e}")
            # Retry nach kurzer Pause
            time.sleep(0.1)
            return self.create_user(username, email, password, role)
        except Exception as e:
            print(f"❌ Fehler beim User erstellen: {e}")
            return False
        finally:
            if conn:
                conn.close()


    def authenticate_user(self, username: str, password: str) -> dict:
        """
        🔐 Authentifiziert einen Benutzer
        
        Args:
            username (str): Benutzername
            password (str): Passwort
            
        Returns:
            dict: User-Daten bei Erfolg, None bei Fehler
        """
        try:
            from auth import verify_password
        except ImportError:
            # Fallback für Entwicklungsmodus
            import hashlib
            def verify_password(plain, hashed):
                return hashlib.sha256(plain.encode()).hexdigest() == hashed
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, password_hash, role FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and verify_password(password, user[1]):
                # Update last login
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?
                ''', (username,))
                conn.commit()
                conn.close()
                
                return {"username": user[0], "role": user[2]}
            return None
            
        except Exception as e:
            print(f"❌ Fehler bei Authentifizierung: {e}")
            return None

    def _create_initial_profile(self, user_hash: str):
        """
        📝 Erstellt ein initiales Lernprofil für neuen User
        
        Args:
            user_hash (str): Gehashte User-ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_profiles (user_hash, detected_learning_style)
                VALUES (?, ?)
            ''', (user_hash, "adaptiv_ausgeglichen"))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Fehler beim Profil erstellen: {e}")

    def _get_user_hash(self, user_id: str) -> str:
        """
        🔒 Erstellt einen konsistenten Hash für User-IDs
        
        Args:
            user_id (str): Original User-ID
            
        Returns:
            str: 16-stelliger Hash
        """
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    # === SCHULKONTEXT-METHODEN ===

    def set_school_context(self, username: str, school_data: dict) -> bool:
        """
        🏫 Speichert Schulkontext in Datenbank
        
        Args:
            username (str): Benutzername
            school_data (dict): Schuldaten
            
        Returns:
            bool: True bei Erfolg
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prüfe ob Eintrag existiert
            cursor.execute('SELECT user_hash FROM school_contexts WHERE user_hash = ?', (user_hash,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute('''
                    UPDATE school_contexts 
                    SET grade = ?, school_type = ?, state = ?, subjects = ?, curriculum_focus = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_hash = ?
                ''', (
                    school_data.get('grade'),
                    school_data.get('school_type'), 
                    school_data.get('state', 'Bayern'),
                    json.dumps(school_data.get('subjects', [])),
                    school_data.get('curriculum_focus', 'allgemein'),
                    user_hash
                ))
            else:
                # Neuer Eintrag
                cursor.execute('''
                    INSERT INTO school_contexts (user_hash, grade, school_type, state, subjects, curriculum_focus)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_hash,
                    school_data.get('grade'),
                    school_data.get('school_type'),
                    school_data.get('state', 'Bayern'),
                    json.dumps(school_data.get('subjects', [])),
                    school_data.get('curriculum_focus', 'allgemein')
                ))
            
            conn.commit()
            conn.close()
            
            print(f"🏫 Schulkontext gespeichert für {username}: {school_data}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern des Schulkontexts: {e}")
            return False

    def get_school_context(self, username: str) -> dict:
        """
        📚 Holt Schulkontext aus Datenbank
        
        Args:
            username (str): Benutzername
            
        Returns:
            dict: Schuldaten oder leeres Dict
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT grade, school_type, state, subjects, curriculum_focus 
                FROM school_contexts WHERE user_hash = ?
            ''', (user_hash,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "grade": result[0],
                    "school_type": result[1],
                    "state": result[2],
                    "subjects": json.loads(result[3]) if result[3] else [],
                    "curriculum_focus": result[4]
                }
            else:
                return {
                    "grade": None,
                    "school_type": None, 
                    "state": "Bayern",
                    "subjects": [],
                    "curriculum_focus": "allgemein"
                }
                
        except Exception as e:
            print(f"❌ Fehler beim Laden des Schulkontexts: {e}")
            return {}

    def update_user_profile(self, username: str, update_data: dict) -> bool:
        """
        👤 Aktualisiert User-Profil in Datenbank
        
        Args:
            username (str): Benutzername
            update_data (dict): Zu aktualisierende Daten
            
        Returns:
            bool: True bei Erfolg
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Baue UPDATE Query dynamisch auf
            set_clauses = []
            params = []
            
            for field, value in update_data.items():
                if value is not None:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if set_clauses:
                params.append(username)
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE username = ?"
                cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Profil-Update: {e}")
            return False

    # === LERNANALYSE & PROFILERSTELLUNG ===

    def detect_learning_patterns(self, username: str) -> dict:
        """
        🔍 Analysiert automatisch die Lernmuster eines Users
        
        Args:
            username (str): Benutzername
            
        Returns:
            dict: Umfassendes Lernprofil mit Stil, Präferenzen etc.
        """
        user_hash = self._get_user_hash(username)
        
        try:
            # Hole vergangene Sessions
            sessions = self._get_user_sessions(user_hash)
            
            if len(sessions) < 3:
                return self._get_default_learning_profile()
            
            # Analysiere Muster
            patterns = self._analyze_learning_patterns(sessions)
            
            # Lade oder erstelle Profil
            profile = self._load_user_profile(user_hash)
            
            # Aktualisiere mit erkannten Mustern
            profile.update({
                "detected_learning_style": self._detect_learning_style(patterns),
                "cognitive_patterns": patterns,
                "optimal_session_length": self._calculate_optimal_session_length(patterns),
                "preferred_subjects": self._detect_subject_preferences(patterns),
                "performance_peaks": self._find_performance_peaks(patterns),
                "struggle_areas": self._identify_struggle_areas(patterns)
            })
            
            self._save_user_profile(user_hash, profile)
            return profile
            
        except Exception as e:
            print(f"❌ Fehler bei Lernmuster-Erkennung: {e}")
            return self._get_default_learning_profile()

    def _analyze_learning_patterns(self, sessions: list) -> dict:
        """
        📊 Analysiert Rohdaten aus Lern-Sessions
        
        Args:
            sessions (list): Rohdaten aus Datenbank
            
        Returns:
            dict: Strukturierte Lernmuster
        """
        patterns = {
            "session_timing": [],
            "performance_by_subject": {},
            "engagement_trends": [],
            "duration_patterns": [],
            "difficulty_progression": []
        }
        
        for session in sessions:
            try:
                # Extrahiere Session-Daten
                subject, duration, topics, score, engagement, session_date = session
                
                # Session-Zeit analysieren
                session_time = self._extract_hour_from_timestamp(session_date)
                if session_time is not None:
                    patterns["session_timing"].append(session_time)
                
                # Performance nach Fach
                if subject not in patterns["performance_by_subject"]:
                    patterns["performance_by_subject"][subject] = []
                patterns["performance_by_subject"][subject].append(score)
                
                # Dauer und Engagement
                patterns["duration_patterns"].append(duration)
                patterns["engagement_trends"].append(engagement)
                
            except Exception as e:
                print(f"⚠️ Fehler bei Session-Analyse: {e}")
                continue
                
        return patterns

    def _detect_learning_style(self, patterns: dict) -> str:
        """
        🎯 Erkennt den individuellen Lernstil
        
        Args:
            patterns (dict): Analysierte Lernmuster
            
        Returns:
            str: Erkannten Lernstil
        """
        try:
            durations = patterns["duration_patterns"]
            timings = patterns["session_timing"]
            engagements = patterns["engagement_trends"]
            
            if not durations:
                return "adaptiv_ausgeglichen"
                
            avg_duration = self._calculate_mean(durations)
            timing_variance = self._calculate_std(timings) if timings else 0
            
            # Entscheidungslogik für Lernstil
            if avg_duration > 60 and timing_variance < 2:
                return "tiefgehend_konzentriert"
            elif avg_duration < 30 and len(timings) > 5:
                return "häufig_kurz"
            elif engagements and max(engagements) > 0.8:
                return "hoch_engagiert"
            else:
                return "adaptiv_ausgeglichen"
                
        except Exception as e:
            print(f"❌ Fehler bei Lernstil-Erkennung: {e}")
            return "adaptiv_ausgeglichen"

    # === KI-GESTÜTZTE ÜBUNGSGENERIERUNG ===

    def generate_personalized_exercises(self, username: str, subject: str, topic: str, count: int = 3) -> dict:
        """
        🎓 Generiert personalisierte Multiple-Choice Übungen mit MEHREREN richtigen Antworten
        """
        user_hash = self._get_user_hash(username)
        
        try:
            profile = self.detect_learning_patterns(username)
            personal_context = self._create_adaptive_context(profile, subject, username)
            
            prompt = f"""
    ADAPTIVE LERNUNTERSTÜTZUNG - MULTIPLE CHOICE MIT MEHREREN ANTWORTEN:

    Nutzer-Profil (automatisch erkannt):
    {personal_context}

    Fach: {subject}
    Thema: {topic}
    Anzahl Aufgaben: {count}

    Generiere Multiple-Choice Fragen mit 4-6 Antwortmöglichkeiten.
    Es können MEHRERE Antworten richtig sein (typischerweise 2-3).
    Kennzeichne alle richtigen Antworten.

    JSON-Antwort:
    {{
        "exercises": [
            {{
                "question": "Frage",
                "options": {{
                    "A": "Antwort A",
                    "B": "Antwort B", 
                    "C": "Antwort C",
                    "D": "Antwort D",
                    "E": "Antwort E (optional)",
                    "F": "Antwort F (optional)"
                }},
                "correct_answers": ["A", "C"],  // Liste der richtigen Antworten
                "explanation": "Erklärung warum A und C richtig sind und andere falsch",
                "difficulty": "angepasst",
                "personalization_note": "Warum diese Aufgabe passt",
                "multiple_correct": true  // Kennzeichnet Mehrfachauswahl
            }}
        ],
        "adaptive_tips": ["Tipp 1", "Tipp 2"]
    }}
    """
            
            result = self.robust_api_call(prompt, response_format="json")
            
            if result:
                try:
                    data = json.loads(result)
                    if isinstance(data, dict) and "exercises" in data:
                        if isinstance(data["exercises"], list) and len(data["exercises"]) > 0:
                            print("✅ Multiple-Choice Übungen (mehrere Antworten) von KI generiert!")
                            return data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Fehler in KI-Antwort: {e}")
        
        except Exception as e:
            print(f"❌ Fehler bei MC-Übungsgenerierung: {e}")
        
        # Fallback zu adaptiven MC-Übungen
        print("🔄 Verwende adaptiven MC-Fallback...")
        return self._get_mc_multiple_fallback_exercises(subject, topic, count)

    def _create_adaptive_context(self, profile: dict, subject: str, username: str = None) -> str:
        """
        📝 Erstellt personalisierten Kontext für KI-Prompts
        
        Args:
            profile (dict): User-Lernprofil
            subject (str): Schulfach
            username (str): Benutzername für Schulkontext
            
        Returns:
            str: Formatierten Kontext-Text
        """
        try:
            learning_style = profile.get("detected_learning_style", "adaptiv")
            optimal_length = profile.get("optimal_session_length", 45)
            preferred = profile.get("preferred_subjects", ["Noch nicht erkannt"])
            struggles = profile.get("struggle_areas", ["Wird noch analysiert"])

            # Schulkontext integrieren
            school_context = ""
            if username:
                school_data = self.get_school_context(username)
                if school_data and school_data.get('school_type'):
                    school_context = f"""
SCHULKONTEXT:
Klasse: {school_data.get('grade', 'Nicht angegeben')}
Schultyp: {school_data.get('school_type', 'Nicht angegeben')}
Bundesland: {school_data.get('state', 'Nicht angegeben')}
Fächer: {', '.join(school_data.get('subjects', []))}
Schwerpunkt: {school_data.get('curriculum_focus', 'Allgemein')}

"""

            context = f"""
{school_context}AUTOMATISCH ERKANNTE LERNPRÄFERENZEN:

Lernstil: {learning_style}
Optimale Session-Länge: {optimal_length} Minuten
Starke Fächer: {', '.join(preferred)}
Schwierigkeits-Bereich: {', '.join(struggles)}

Lernempfehlungen:
- {self._get_style_specific_advice(learning_style)}
- Session-Länge: {optimal_length} Minuten
- {self._get_subject_specific_strategy(subject, profile)}
"""
            return context
        except Exception as e:
            print(f"❌ Fehler bei Kontext-Erstellung: {e}")
            return "Automatische Profil-Erkennung aktiv - personalisierte Lernunterstützung"

    def _get_style_specific_advice(self, learning_style: str) -> str:
        """Gibt lernstilspezifische Ratschläge zurück"""
        advice_map = {
            "tiefgehend_konzentriert": "Lange, ununterbrochene Lernsession für komplexe Themen",
            "häufig_kurz": "Kurze, häufige Lerneinheiten mit klaren Pausen",
            "hoch_engagiert": "Herausfordernde Aufgaben mit sofortigem Feedback",
            "adaptiv_ausgeglichen": "Abwechslungsreiche Methoden für nachhaltiges Lernen"
        }
        return advice_map.get(learning_style, "Individuell angepasste Lernstrategien")

    def _get_subject_specific_strategy(self, subject: str, profile: dict) -> str:
        """Gibt fachspezifische Lernstrategien zurück"""
        strategies = {
            "Mathe": "Problemlösungsstrategien und praktische Anwendungen",
            "Deutsch": "Textanalyse und kreative Schreibübungen", 
            "Englisch": "Kommunikative Übungen und Vokabeltraining",
            "Physik": "Experimentelle Ansätze und Formelanwendungen",
            "Chemie": "Praktische Versuche und chemische Prozesse",
            "Biologie": "Visualisierungen und Systemverständnis",
            "Geschichte": "Zeitstrahl-Methoden und Quellenanalyse",
            "Geografie": "Kartenarbeit und Fallstudien"
        }
        return strategies.get(subject, "Fachspezifische Lernmethoden anwenden")

    # === API-KOMMUNIKATION ===

    def robust_api_call(self, prompt: str, max_retries: int = 2, response_format: str = "text", timeout: int = 30) -> str:
        """
        🔄 Robuste API-Kommunikation mit Retry-Mechanismus
        
        Args:
            prompt (str): Prompt für KI
            max_retries (int): Maximale Wiederholungsversuche
            response_format (str): Gewünschtes Antwortformat
            timeout (int): Timeout in Sekunden
            
        Returns:
            str: KI-Antwort oder None bei Fehler
        """
        for attempt in range(max_retries):
            try:
                result = self.api_call(prompt, response_format, timeout)
                if result:
                    return result
                else:
                    print(f"🔄 API-Versuch {attempt + 1} fehlgeschlagen")
                    
            except Exception as e:
                print(f"❌ API-Fehler bei Versuch {attempt + 1}: {e}")
            
            # Exponentielles Backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.random()
                print(f"⏳ Warte {wait_time:.1f}s vor nächstem Versuch...")
                time.sleep(wait_time)
        
        return None

    def api_call(self, prompt: str, response_format: str = "text", timeout: int = 30) -> str:
        """
        📡 Basis-API-Call zu OpenRouter
        
        Args:
            prompt (str): Prompt für KI
            response_format (str): Antwortformat ('text' oder 'json')
            timeout (int): Timeout in Sekunden
            
        Returns:
            str: KI-Antwort oder None bei Fehler
        """
        if not self.api_key:
            print("❌ Kein API-Key konfiguriert")
            return None
            
        try:
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
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"❌ API HTTP Fehler {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ API-Timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("🔌 API-Verbindungsfehler")
            return None
        except Exception as e:
            print(f"❌ Unerwarteter API-Fehler: {e}")
            return None

    # === LERN-TRACKING ===

    def track_study_session_with_engagement(self, username: str, subject: str, duration_minutes: int, 
                                          topics: list, performance_score: float, engagement_level: float = 0.5, 
                                          difficulty: str = "mittel"):
        """
        📊 Speichert eine Lern-Session mit Engagement-Daten
        
        Args:
            username (str): Benutzername
            subject (str): Schulfach
            duration_minutes (int): Dauer in Minuten
            topics (list): Behandelte Themen
            performance_score (float): Leistungsbewertung (0-1)
            engagement_level (float): Engagement-Level (0-1)
            difficulty (str): Schwierigkeitsgrad
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO study_sessions 
                (user_hash, subject, duration_minutes, topics, performance_score, engagement_level, difficulty_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_hash,
                subject,
                duration_minutes,
                json.dumps(topics) if topics else "[]",
                performance_score,
                engagement_level,
                difficulty
            ))
            
            conn.commit()
            conn.close()
            
            # Automatische Profil-Anpassung
            self._auto_adapt_user_profile(user_hash)
            
            print(f"📊 Session getrackt: {subject} - Engagement: {engagement_level}")
            
        except Exception as e:
            print(f"❌ Fehler beim Tracken der Session: {e}")

    def track_exercise_answer(self, username: str, exercise_data: dict, user_answer: str, 
                            is_correct: bool, time_spent_seconds: int):
        """
        📝 Trackt eine Übungsantwort für spätere Analyse
        
        Args:
            username (str): Benutzername
            exercise_data (dict): Übungsdaten
            user_answer (str): User-Antwort
            is_correct (bool): War Antwort korrekt?
            time_spent_seconds (int): Bearbeitungszeit in Sekunden
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exercise_answers 
                (user_hash, exercise_id, subject, topic, question, user_answer, 
                 correct_answer, is_correct, time_spent_seconds, difficulty, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_hash,
                exercise_data.get('exercise_id', f"gen_{int(time.time())}"),
                exercise_data.get('subject'),
                exercise_data.get('topic'),
                exercise_data.get('question', '')[:500],
                str(user_answer)[:1000],
                exercise_data.get('solution', ''),
                1 if is_correct else 0,
                time_spent_seconds,
                exercise_data.get('difficulty', 'unbekannt'),
                json.dumps(exercise_data.get('tags', []))
            ))
            
            conn.commit()
            conn.close()
            
            # Automatische Fehleranalyse
            if not is_correct:
                self._analyze_mistake_pattern(user_hash, exercise_data, user_answer)
            
            print(f"📝 Antwort getrackt: {'✅ Richtig' if is_correct else '❌ Falsch'} - {time_spent_seconds}s")
        except Exception as e:
            print(f"❌ Fehler beim Tracken der Antwort: {e}")

    # === ANALYTICS & STATISTIKEN ===

    def get_performance_analytics(self, username: str) -> dict:
        """
        📈 Erstellt umfassende Performance-Analytics für einen User
        
        Args:
            username (str): Benutzername
            
        Returns:
            dict: Detaillierte Analytics-Daten
        """
        user_hash = self._get_user_hash(username)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Antwort-Statistiken pro Fach/Thema
        cursor.execute('''
            SELECT 
                COUNT(*) as total_answers,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers,
                AVG(time_spent_seconds) as avg_time,
                subject,
                topic
            FROM exercise_answers 
            WHERE user_hash = ?
            GROUP BY subject, topic
        ''', (user_hash,))
        subject_stats = cursor.fetchall()
        
        # Fehler-Muster
        cursor.execute('''
            SELECT error_type, frequency, topic, subject
            FROM mistake_patterns 
            WHERE user_hash = ?
            ORDER BY frequency DESC
            LIMIT 10
        ''', (user_hash,))
        mistake_stats = cursor.fetchall()
        
        # Lern-Session Statistik
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                AVG(duration_minutes) as avg_duration,
                AVG(performance_score) as avg_performance,
                subject
            FROM study_sessions 
            WHERE user_hash = ?
            GROUP BY subject
        ''', (user_hash,))
        session_stats = cursor.fetchall()
        
        conn.close()
        
        # Verarbeite Daten für Frontend
        analytics = self._process_analytics_data(subject_stats, mistake_stats, session_stats)
        return analytics

    def _process_analytics_data(self, subject_stats: list, mistake_stats: list, session_stats: list) -> dict:
        """
        🔄 Verarbeitet Rohdaten zu strukturierten Analytics
        
        Args:
            subject_stats (list): Fach-Statistiken
            mistake_stats (list): Fehler-Statistiken
            session_stats (list): Session-Statistiken
            
        Returns:
            dict: Strukturierte Analytics
        """
        analytics = {
            'subject_performance': {},
            'common_mistakes': [],
            'session_analytics': {},
            'overall_stats': {
                'total_answered': 0,
                'correct_rate': 0,
                'avg_response_time': 0,
                'total_sessions': 0,
                'avg_session_duration': 0
            }
        }
        
        total_correct = 0
        total_answers = 0
        total_time = 0
        total_sessions = 0
        total_session_duration = 0
        
        # Verarbeite Antwort-Statistiken
        for stat in subject_stats:
            total_ans, correct_ans, avg_time, subject, topic = stat
            success_rate = (correct_ans / total_ans) * 100 if total_ans > 0 else 0
            
            if subject not in analytics['subject_performance']:
                analytics['subject_performance'][subject] = {}
            
            analytics['subject_performance'][subject][topic] = {
                'success_rate': round(success_rate, 1),
                'total_answers': total_ans,
                'correct_answers': correct_ans,
                'avg_time_seconds': round(avg_time or 0, 1)
            }
            
            total_answers += total_ans
            total_correct += correct_ans
            total_time += (avg_time or 0) * total_ans
        
        # Verarbeite Session-Statistiken
        for stat in session_stats:
            session_count, avg_duration, avg_perf, subject = stat
            
            if subject not in analytics['session_analytics']:
                analytics['session_analytics'][subject] = {}
                
            analytics['session_analytics'][subject] = {
                'session_count': session_count,
                'avg_duration_minutes': round(avg_duration or 0, 1),
                'avg_performance_score': round(avg_perf or 0, 2)
            }
            
            total_sessions += session_count
            total_session_duration += (avg_duration or 0) * session_count
        
        # Verarbeite Fehler-Statistiken
        for mistake in mistake_stats:
            error_type, frequency, topic, subject = mistake
            analytics['common_mistakes'].append({
                'error_type': error_type,
                'frequency': frequency,
                'topic': topic,
                'subject': subject
            })
        
        # Gesamtstatistiken
        if total_answers > 0:
            analytics['overall_stats'].update({
                'total_answered': total_answers,
                'correct_rate': round((total_correct / total_answers) * 100, 1),
                'avg_response_time': round(total_time / total_answers, 1)
            })
        
        if total_sessions > 0:
            analytics['overall_stats'].update({
                'total_sessions': total_sessions,
                'avg_session_duration': round(total_session_duration / total_sessions, 1)
            })
        
        return analytics

    # === EMPFEHLUNGEN & TIPPS ===

    def get_adaptive_recommendations(self, username: str) -> dict:
        """
        💡 Generiert adaptive Lernempfehlungen
        
        Args:
            username (str): Benutzername
            
        Returns:
            dict: Personalisierte Empfehlungen
        """
        try:
            profile = self.detect_learning_patterns(username)
            patterns = profile.get("cognitive_patterns", {})
            
            recommendations = {
                "daily_plan": self._generate_daily_plan(profile),
                "weekly_goals": self._generate_weekly_goals(patterns),
                "learning_strategies": self._get_adaptive_strategies(profile),
                "warning_signs": self._detect_warning_signs(patterns)
            }
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Fehler bei Empfehlungs-Generierung: {e}")
            return self._get_fallback_recommendations()

    def get_study_reminders(self, username: str) -> dict:
        """
        ⏰ Generiert intelligente Lern-Erinnerungen
        
        Args:
            username (str): Benutzername
            
        Returns:
            dict: Tägliche Erinnerungen und Wochenziele
        """
        try:
            profile = self.detect_learning_patterns(username)
            analytics = self.get_performance_analytics(username)
            progress = self.get_learning_progress(username, days=7)

        except Exception as e:
            print(f"❌ Fehler beim Erstellen von Erinnerungen: {e}")
            return {'daily_reminders': [], 'weekly_goals': [], 'motivational_tips': []}

        reminders = {
            'daily_reminders': [],
            'weekly_goals': [],
            'motivational_tips': []
        }

        # Tägliche Erinnerungen basierend auf Lernstil
        learning_style = profile.get('detected_learning_style', 'adaptiv')
        style_reminders = {
            'tiefgehend_konzentriert': [
                f"Tiefe Lernsession von {profile.get('optimal_session_length', 45)} Minuten planen",
                "Komplexe Themen für maximale Konzentration nutzen",
                "Störungsfreie Umgebung sicherstellen"
            ],
            'häufig_kurz': [
                "Mehrere kurze Lerneinheiten über den Tag verteilen",
                "25-Minuten Sessions mit klaren Fokus-Zielen",
                "Schnelle Wiederholungen zwischen den Session"
            ],
            'hoch_engagiert': [
                "Herausfordernde Projekte als Lernziele setzen",
                "Gamification-Elemente nutzen (Punkte, Challenges)",
                "Sofortiges Feedback einholen"
            ]
        }

        reminders['daily_reminders'] = style_reminders.get(learning_style, [
            "Regelmäßige Lernzeiten einplanen",
            "Aktive Übungen statt passive Wiederholung",
            "Kurze Pausen zur Steigerung der Konzentration"
        ])

        # Wöchentliche Ziele basierend auf Performance
        total_sessions = analytics.get('overall_stats', {}).get('total_sessions', 0)
        success_rate = analytics.get('overall_stats', {}).get('correct_rate', 0)

        if total_sessions < 5:
            reminders['weekly_goals'] = [
                "3-4 Lernsession diese Woche",
                "Erste Themen-Grundlagen erarbeiten",
                "Lernstil weiter analysieren"
            ]
        elif success_rate < 70:
            weak_areas = profile.get('struggle_areas', [])
            focus_area = weak_areas[0] if weak_areas else "Grundlagen"
            reminders['weekly_goals'] = [
                f"Fokus auf {focus_area}",
                "Mehr Wiederholungsübungen",
                "Schritt-für-Schritt Lösungen üben"
            ]
        else:
            strong_areas = profile.get('preferred_subjects', [])
            next_challenge = strong_areas[0] if strong_areas else "neue Themen"
            reminders['weekly_goals'] = [
                f"Vertiefung in {next_challenge}",
                "Komplexere Aufgaben angehen",
                "Projekt-basiertes Lernen versuchen"
            ]

        # Motivations-Tipps basierend auf Fortschritt
        consistency = progress.get('trends', {}).get('consistency_score', 0)

        if consistency > 80:
            reminders['motivational_tips'] = [
                "🎉 Exzellente Konsistenz! Weiter so!",
                "Deine regelmäßigen Sessions zeigen Wirkung",
                "Balanciere Lernen mit Erholung für Nachhaltigkeit"
            ]
        elif consistency > 60:
            reminders['motivational_tips'] = [
                "📚 Gute Fortschritte! Noch etwas regelmäßiger lernen",
                "Jede Session bringt dich deinen Zielen näher",
                "Belohne dich für erreichte Meilensteine"
            ]
        else:
            reminders['motivational_tips'] = [
                "💪 Du hast den ersten Schritt gemacht - weiter so!",
                "Kleine, regelmäßige Session sind besser als seltene lange",
                "Jeder lernt anders - finde deinen optimalen Rhythmus"
            ]

        return reminders


    # === TEST-MODUS METHODEN ===

    def start_test_session(self, username: str, subject: str, topic: str, question_count: int = 10) -> dict:
            """
            🧪 Startet eine neue Test-Session - ZEIT FIX (Python bestimmt Startzeit)
            """
            user_hash = self._get_user_hash(username)
            test_id = f"test_{int(time.time())}_{user_hash}"
            
            # WICHTIG: Wir nehmen hier die UTC-Zeit von Python, damit sie exakt zur End-Zeit passt
            start_time_iso = datetime.utcnow().isoformat()
            
            try:
                # Generiere Test-Fragen
                exercises_result = self.generate_personalized_exercises(username, subject, topic, question_count)
                
                conn = sqlite3.connect(self.db_path, timeout=20.0)
                cursor = conn.cursor()
                
                # Wir speichern start_time explizit!
                cursor.execute('''
                    INSERT INTO test_sessions 
                    (test_id, user_hash, subject, topic, questions, total_questions, start_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    user_hash,
                    subject,
                    topic,
                    json.dumps(exercises_result),
                    question_count,
                    start_time_iso  # Hier die Python-Zeit nutzen
                ))
                
                conn.commit()
                conn.close()
                
                print(f"🧪 Test gestartet: {test_id} - Zeit: {start_time_iso}")
                
                return {
                    "test_id": test_id,
                    "subject": subject,
                    "topic": topic,
                    "exercises": exercises_result,
                    "total_questions": question_count,
                    "time_limit": 60 * question_count,
                    "start_time": start_time_iso
                }
                
            except Exception as e:
                print(f"❌ Fehler beim Test-Start: {e}")
                return self._get_fallback_test_session(username, subject, topic, question_count)

    def _get_fallback_test_session(self, username: str, subject: str, topic: str, question_count: int) -> dict:
        """
        🆘 Fallback Test-Session falls KI nicht verfügbar
        """
        user_hash = self._get_user_hash(username)
        test_id = f"test_fallback_{int(time.time())}_{user_hash}"
        
        fallback_exercises = {
            "exercises": [
                {
                    "question": f"Was ist die Ableitung von f(x) = x² in {subject}?",
                    "options": {
                        "A": "2x",
                        "B": "x²", 
                        "C": "2",
                        "D": "x"
                    },
                    "correct_answers": ["A"],
                    "explanation": "Die Ableitung von x² ist 2x gemäß Potenzregel.",
                    "difficulty": "mittel",
                    "multiple_correct": False
                },
                {
                    "question": f"Welche der folgenden Zahlen sind gerade?",
                    "options": {
                        "A": "2",
                        "B": "3",
                        "C": "4", 
                        "D": "5",
                        "E": "6"
                    },
                    "correct_answers": ["A", "C", "E"],
                    "explanation": "Gerade Zahlen sind durch 2 teilbar: 2, 4, 6",
                    "difficulty": "einfach", 
                    "multiple_correct": True
                }
            ],
            "adaptive_tips": ["Fallback-Modus aktiviert", "Teste dein Wissen mit diesen Beispielaufgaben"]
        }
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_sessions 
                (test_id, user_hash, subject, topic, questions, total_questions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                test_id,
                user_hash,
                subject,
                topic,
                json.dumps(fallback_exercises),
                min(question_count, 2)  # Max 2 Fallback-Fragen
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "test_id": test_id,
                "subject": subject,
                "topic": topic,
                "exercises": fallback_exercises,
                "total_questions": min(question_count, 2),
                "time_limit": 60 * min(question_count, 2),
                "start_time": datetime.now().isoformat(),
                "fallback_used": True
            }
            
        except Exception as e:
            print(f"❌ Fehler im Fallback: {e}")
            return {}


    def submit_test_answer(self, username: str, test_id: str, question_index: int, user_answer: str) -> dict:
        """
        📝 Verarbeitet eine Test-Antwort mit KI-Feedback
        
        Args:
            username (str): Benutzername
            test_id (str): Test-ID
            question_index (int): Frage Index
            user_answer (str): User-Antwort
            
        Returns:
            dict: Feedback und Bewertung
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Hole Test-Daten
            cursor.execute('SELECT questions FROM test_sessions WHERE test_id = ? AND user_hash = ?', (test_id, user_hash))
            test_data = cursor.fetchone()
            
            if not test_data:
                return {"error": "Test nicht gefunden"}
            
            exercises = json.loads(test_data[0])
            question_data = exercises['exercises'][question_index]
            
            # Automatische Korrektur (einfache Version)
            is_correct = self._auto_correct_answer(user_answer, question_data.get('solution', ''))
            
            # KI-Feedback generieren
            feedback = self._generate_ai_feedback(question_data, user_answer, is_correct)
            
            # Antwort speichern
            cursor.execute('''
                INSERT INTO test_results 
                (test_id, user_hash, question_index, user_answer, correct_answer, is_correct, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_id,
                user_hash,
                question_index,
                user_answer,
                question_data.get('solution', ''),
                1 if is_correct else 0,
                json.dumps(feedback)
            ))
            
            # Aktuelle Antworten in Test-Session updaten
            cursor.execute('SELECT user_answers FROM test_sessions WHERE test_id = ?', (test_id,))
            current_answers = cursor.fetchone()[0] or '[]'
            answers_list = json.loads(current_answers)
            
            # Füge neue Antwort hinzu oder ersetze vorhandene
            answer_exists = False
            for i, answer in enumerate(answers_list):
                if answer.get('question_index') == question_index:
                    answers_list[i] = {
                        'question_index': question_index,
                        'user_answer': user_answer,
                        'is_correct': is_correct,
                        'timestamp': datetime.now().isoformat()
                    }
                    answer_exists = True
                    break
            
            if not answer_exists:
                answers_list.append({
                    'question_index': question_index,
                    'user_answer': user_answer,
                    'is_correct': is_correct,
                    'timestamp': datetime.now().isoformat()
                })
            
            cursor.execute('''
                UPDATE test_sessions SET user_answers = ? WHERE test_id = ?
            ''', (json.dumps(answers_list), test_id))
            
            conn.commit()
            conn.close()
            
            return {
                "question_index": question_index,
                "user_answer": user_answer,
                "is_correct": is_correct,
                "correct_answer": question_data.get('solution', ''),
                "feedback": feedback,
                "progress": len(answers_list)
            }
            
        except Exception as e:
            print(f"❌ Fehler bei Antwort-Verarbeitung: {e}")
            return {"error": str(e)}


    def submit_test_answer_multiple(self, username: str, test_id: str, question_index: int, user_answers: list) -> dict:
        """
        📝 Verarbeitet mehrere Test-Antworten mit KI-Feedback
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Hole Test-Daten
            cursor.execute('SELECT questions FROM test_sessions WHERE test_id = ? AND user_hash = ?', (test_id, user_hash))
            test_data = cursor.fetchone()
            
            if not test_data:
                return {"error": "Test nicht gefunden"}
            
            exercises = json.loads(test_data[0])
            question_data = exercises['exercises'][question_index]
            
            # Korrekte Antworten
            correct_answers = question_data.get('correct_answers', [question_data.get('correct_answer', '')])
            
            # Automatische Korrektur für mehrere Antworten
            correction_result = self._auto_correct_answer_multiple(user_answers, correct_answers)
            
            # KI-Feedback generieren
            feedback = self._generate_ai_feedback(question_data, user_answers, correction_result['is_correct'])
            
            # Antwort speichern
            cursor.execute('''
                INSERT INTO test_results 
                (test_id, user_hash, question_index, user_answer, correct_answer, is_correct, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_id,
                user_hash,
                question_index,
                json.dumps(user_answers),
                json.dumps(correct_answers),
                1 if correction_result['is_correct'] else 0,
                json.dumps(feedback)
            ))
            
            # Aktuelle Antworten in Test-Session updaten
            cursor.execute('SELECT user_answers FROM test_sessions WHERE test_id = ?', (test_id,))
            current_answers = cursor.fetchone()[0] or '[]'
            answers_list = json.loads(current_answers)
            
            # Füge neue Antwort hinzu oder ersetze vorhandene
            answer_exists = False
            for i, answer in enumerate(answers_list):
                if answer.get('question_index') == question_index:
                    answers_list[i] = {
                        'question_index': question_index,
                        'user_answer': user_answers,
                        'is_correct': correction_result['is_correct'],
                        'score': correction_result['score'],
                        'timestamp': datetime.now().isoformat()
                    }
                    answer_exists = True
                    break
            
            if not answer_exists:
                answers_list.append({
                    'question_index': question_index,
                    'user_answer': user_answers,
                    'is_correct': correction_result['is_correct'],
                    'score': correction_result['score'],
                    'timestamp': datetime.now().isoformat()
                })
            
            cursor.execute('''
                UPDATE test_sessions SET user_answers = ? WHERE test_id = ?
            ''', (json.dumps(answers_list), test_id))
            
            conn.commit()
            conn.close()
            
            return {
                "question_index": question_index,
                "user_answers": user_answers,
                "is_correct": correction_result['is_correct'],
                "score": correction_result['score'],
                "correct_answers": correct_answers,
                "feedback": feedback,
                "feedback_text": correction_result['feedback'],
                "progress": len(answers_list)
            }
            
        except Exception as e:
            print(f"❌ Fehler bei Mehrfach-Antwort-Verarbeitung: {e}")
            return {"error": str(e)}

    def _auto_correct_answer_multiple(self, user_answers: list, correct_answers: list) -> dict:
        """
        ✅ Korrektur für Multiple-Choice mit mehreren Antworten - VEREINFACHTE VERSION
        """
        if not user_answers:
            user_answers = []
        
        if not correct_answers:
            correct_answers = []
        
        user_set = set(user_answers)
        correct_set = set(correct_answers)
        
        # Einfache Logik: Nur vollständig korrekt
        is_correct = user_set == correct_set
        
        if is_correct:
            return {
                "is_correct": True,
                "score": 1.0,
                "feedback": "Alle richtigen Antworten ausgewählt!"
            }
        else:
            correct_selected = len(user_set.intersection(correct_set))
            total_correct = len(correct_set)
            
            return {
                "is_correct": False,
                "score": correct_selected / total_correct if total_correct > 0 else 0,
                "feedback": f"{correct_selected} von {total_correct} richtigen Antworten gefunden."
            }

    # def finish_test_session(self, username: str, test_id: str) -> dict:
    #     """
    #     🏁 Beendet Test-Session - VOLLSTÄNDIG NEU IMPLEMENTIERT
    #     """
    #     user_hash = self._get_user_hash(username)
        
    #     print(f"🔍 DEBUG finish_test_session: user={username}, test_id={test_id}")
        
    #     try:
    #         conn = sqlite3.connect(self.db_path, timeout=20.0)
    #         cursor = conn.cursor()
            
    #         # Hole ALLE Test-Daten
    #         cursor.execute('''
    #             SELECT subject, topic, questions, user_answers, total_questions, start_time 
    #             FROM test_sessions WHERE test_id = ? AND user_hash = ?
    #         ''', (test_id, user_hash))
            
    #         test_data = cursor.fetchone()
    #         if not test_data:
    #             print(f"❌ DEBUG: Test nicht gefunden für {test_id}")
    #             return {"error": "Test nicht gefunden"}
            
    #         subject, topic, questions_json, answers_json, total_questions, start_time = test_data
            
    #         print(f"🔍 DEBUG: Geladene Daten - subject={subject}, topic={topic}")
    #         print(f"🔍 DEBUG: questions_json type: {type(questions_json)}, length: {len(questions_json) if questions_json else 0}")
    #         print(f"🔍 DEBUG: answers_json type: {type(answers_json)}, content: {answers_json}")
            
    #         # Parse Fragen
    #         questions_data = {}
    #         try:
    #             if questions_json:
    #                 questions_data = json.loads(questions_json)
    #                 print(f"🔍 DEBUG: Fragen erfolgreich geparsed: {type(questions_data)}")
    #             else:
    #                 print("❌ DEBUG: questions_json ist leer!")
    #                 questions_data = {}
    #         except Exception as e:
    #             print(f"❌ DEBUG: Fehler beim Parsen von questions_json: {e}")
    #             questions_data = {}
            
    #         # Parse Antworten
    #         user_answers = []
    #         try:
    #             if answers_json and answers_json != '[]':
    #                 user_answers = json.loads(answers_json)
    #                 print(f"🔍 DEBUG: Antworten erfolgreich geparsed: {len(user_answers)} Antworten")
    #             else:
    #                 print("❌ DEBUG: answers_json ist leer oder '[]'")
    #                 user_answers = []
    #         except Exception as e:
    #             print(f"❌ DEBUG: Fehler beim Parsen von answers_json: {e}")
    #             user_answers = []
            
    #         # Extrahiere Fragen-Array
    #         questions = []
    #         if isinstance(questions_data, dict) and 'exercises' in questions_data:
    #             questions = questions_data['exercises']
    #             print(f"🔍 DEBUG: Fragen aus 'exercises' extrahiert: {len(questions)} Fragen")
    #         elif isinstance(questions_data, list):
    #             questions = questions_data
    #             print(f"🔍 DEBUG: Fragen sind direkt eine Liste: {len(questions)} Fragen")
    #         else:
    #             print(f"❌ DEBUG: Unbekannte Fragen-Struktur: {type(questions_data)}")
    #             questions = []
            
    #         # BERECHNE ERGEBNISSE
    #         correct_count = 0
    #         detailed_answers = []
            
    #         print(f"🔍 DEBUG: Beginne Auswertung mit {len(questions)} Fragen und {len(user_answers)} gespeicherten Antworten")
            
    #         for i in range(len(questions)):
    #             if i < len(questions):
    #                 question = questions[i]
                    
    #                 # Finde Antwort für diese Frage
    #                 user_answer_data = None
    #                 for answer in user_answers:
    #                     if answer.get('question_index') == i:
    #                         user_answer_data = answer
    #                         break
                    
    #                 user_answer_list = user_answer_data.get('user_answer', []) if user_answer_data else []
    #                 correct_answers = question.get('correct_answers', [])
                    
    #                 # Debug-Ausgabe
    #                 print(f"🔍 DEBUG Frage {i}: user_answer={user_answer_list}, correct_answers={correct_answers}")
                    
    #                 # Vergleiche Antworten
    #                 user_set = set(user_answer_list)
    #                 correct_set = set(correct_answers)
    #                 is_correct = user_set == correct_set
                    
    #                 if is_correct:
    #                     correct_count += 1
                    
    #                 # Erstelle detaillierte Antwort
    #                 detailed_answers.append({
    #                     'question_index': i,
    #                     'question': question.get('question', f'Frage {i+1}'),
    #                     'user_answers': user_answer_list,
    #                     'correct_answers': correct_answers,
    #                     'is_correct': is_correct,
    #                     'explanation': question.get('explanation', 'Keine Erklärung verfügbar'),
    #                     'options': question.get('options', {})
    #                 })
            
    #         # Score berechnen
    #         if len(questions) > 0:
    #             score = (correct_count / len(questions)) * 100
    #         else:
    #             score = 0
                
    #         print(f"🔍 DEBUG: Auswertung abgeschlossen - {correct_count}/{len(questions)} richtig, Score: {score}%")
            
    #         # Zeit berechnen
    #         time_spent = self._calculate_time_spent(start_time)
            
    #         # Update Test-Session
    #         cursor.execute('''
    #             UPDATE test_sessions 
    #             SET end_time = CURRENT_TIMESTAMP, score = ?, correct_answers = ?, 
    #                 time_spent_seconds = ?, status = 'completed'
    #             WHERE test_id = ?
    #         ''', (score, correct_count, time_spent, test_id))
            
    #         conn.commit()
    #         conn.close()
            
    #         # KI-Auswertung
    #         comprehensive_feedback = self.generate_comprehensive_feedback(username, test_id)
            
    #         return {
    #             "test_id": test_id,
    #             "score": round(score, 1),
    #             "correct_answers": correct_count,
    #             "total_questions": len(questions),
    #             "time_spent_seconds": round(time_spent),
    #             "performance_level": self._get_performance_level(score),
    #             "subject": subject,
    #             "topic": topic,
    #             "comprehensive_feedback": comprehensive_feedback,
    #             "detailed_answers": detailed_answers,
    #             "debug_info": {
    #                 "questions_count": len(questions),
    #                 "user_answers_count": len(user_answers),
    #                 "calculated_correct": correct_count
    #             }
    #         }
            
    #     except Exception as e:
    #         print(f"❌ DEBUG: Fehler in finish_test_session: {e}")
    #         import traceback
    #         traceback.print_exc()
    #         return self._get_fallback_result(test_id)


    def _get_fallback_result(self, test_id: str) -> dict:
        """Fallback-Ergebnis bei Fehlern"""
        return {
            "test_id": test_id,
            "score": 0,
            "correct_answers": 0,
            "total_questions": 0,
            "time_spent_seconds": 0,
            "performance_level": "Fehler",
            "subject": "Unbekannt",
            "topic": "Unbekannt",
            "comprehensive_feedback": {
                "overall_assessment": "Test konnte nicht ausgewertet werden",
                "key_strengths": ["Test wurde durchgeführt"],
                "main_weaknesses": ["Technische Probleme bei der Auswertung"],
                "learning_recommendations": [
                    {
                        "priority": "hoch",
                        "area": "System",
                        "action": "Test erneut starten",
                        "reason": "Technischer Fehler bei der Auswertung"
                    }
                ],
                "next_steps": ["Test neu starten", "Support kontaktieren"],
                "encouragement": "Technische Probleme sind normal - versuche es einfach noch einmal! 💪"
            },
            "detailed_answers": []
        }

    def _prepare_detailed_answers(self, user_answers: list, questions_json: str) -> list:
        """Bereitet detaillierte Antworten für Frontend vor"""
        try:
            questions_data = json.loads(questions_json) if questions_json else {}
            questions = questions_data.get('exercises', []) if isinstance(questions_data, dict) else questions_data
            
            detailed = []
            for i, (q, a) in enumerate(zip(questions, user_answers)):
                detailed.append({
                    "question_index": i,
                    "question": q.get('question', ''),
                    "user_answers": a.get('user_answer', []),
                    "correct_answers": q.get('correct_answers', []),
                    "is_correct": a.get('is_correct', False),
                    "explanation": q.get('explanation', '')
                })
            return detailed
        except:
            return []


    def _generate_test_recommendations(self, score: float, analysis: dict, answered: int, total: int) -> list:
        """💡 Generiert personalisierte Empfehlungen basierend auf Testergebnissen"""
        recommendations = []
        
        # Empfehlungen basierend auf Score
        if score >= 90:
            recommendations.extend([
                "Ausgezeichnete Leistung! 🎉",
                "Du beherrschst dieses Thema nahezu perfekt.",
                "Versuche dich an anspruchsvolleren Aufgaben zur Vertiefung."
            ])
        elif score >= 75:
            recommendations.extend([
                "Sehr gute Leistung! 👍",
                "Einige Bereiche könnten noch verbessert werden.",
                "Wiederhole die falsch beantworteten Fragen."
            ])
        elif score >= 60:
            recommendations.extend([
                "Gute Grundkenntnisse vorhanden. 📚",
                "Konzentriere dich auf die schwierigeren Aspekte des Themas.",
                "Regelmäßige Übung wird deine Ergebnisse verbessern."
            ])
        else:
            recommendations.extend([
                "Das Thema benötigt mehr Aufmerksamkeit. 💪",
                "Beginne mit den Grundlagen und arbeite dich vor.",
                "Kurze, regelmäßige Übungseinheiten sind empfehlenswert."
            ])
        
        # Empfehlungen basierend auf Beantwortungsrate
        completion_rate = answered / total if total > 0 else 0
        if completion_rate < 0.8:
            recommendations.append(f"Versuche alle Fragen zu beantworten ({answered}/{total} beantwortet).")
        
        # Fachspezifische Empfehlungen
        subject = analysis.get('subject', '')
        if 'Mathe' in subject:
            recommendations.append("Übe regelmäßig mit verschiedenen Aufgabentypen.")
        elif 'Deutsch' in subject:
            recommendations.append("Lies die Aufgabenstellungen besonders aufmerksam.")
        
        return recommendations

    def _auto_correct_answer(self, user_answers: list, correct_answers: list) -> dict:
        """
        ✅ Korrektur für Multiple-Choice mit mehreren Antworten
        
        Returns:
            dict: {
                "is_correct": bool,
                "score": float,  # 0.0 - 1.0
                "correct_choices": int,
                "total_correct": int,
                "feedback": str
            }
        """
        if not user_answers:
            user_answers = []
        
        if not correct_answers:
            correct_answers = []
        
        user_set = set(user_answers)
        correct_set = set(correct_answers)
        
        # Vollständig korrekt
        if user_set == correct_set:
            return {
                "is_correct": True,
                "score": 1.0,
                "correct_choices": len(user_set),
                "total_correct": len(correct_set),
                "feedback": "Alle richtigen Antworten ausgewählt!"
            }
        
        # Teilweise korrekt - Berechne Punktzahl
        correct_selected = len(user_set.intersection(correct_set))
        incorrect_selected = len(user_set - correct_set)
        missing_correct = len(correct_set - user_set)
        
        total_possible = len(correct_set)
        
        # Punktzahl: (richtige ausgewählt - falsche ausgewählt) / total möglich
        # Vermeide negative Punktzahlen
        raw_score = (correct_selected - incorrect_selected) / total_possible
        score = max(0.0, raw_score)
        
        is_fully_correct = score == 1.0
        
        # Feedback generieren
        if correct_selected == 0:
            feedback = "Keine richtigen Antworten ausgewählt."
        elif incorrect_selected > 0:
            feedback = f"{correct_selected} richtige, aber {incorrect_selected} falsche Antworten."
        else:
            feedback = f"{correct_selected} richtige Antworten, aber {missing_correct} fehlen."
        
        return {
            "is_correct": is_fully_correct,
            "score": score,
            "correct_choices": correct_selected,
            "total_correct": total_possible,
            "feedback": feedback
        }

    def _generate_ai_feedback(self, question_data: dict, user_answer: str, is_correct: bool) -> dict:
        """
        🤖 Generiert KI-Feedback für Antworten
        """
        try:
            prompt = f"""
    Bewerte diese Test-Antwort:

    FRAGE: {question_data.get('question', '')}
    RICHTIGE LÖSUNG: {question_data.get('solution', '')}
    SCHÜLER-ANTWORT: {user_answer}
    KORREKT: {'JA' if is_correct else 'NEIN'}

    Gib konstruktives Feedback im JSON-Format:
    {{
        "strengths": "Was war gut an der Antwort?",
        "improvements": "Was könnte verbessert werden?",
        "hint": "Ein hilfreicher Hinweis",
        "concept_explanation": "Kurze Erklärung des Konzepts"
    }}
    """
            feedback = self.robust_api_call(prompt, response_format="json")
            if feedback:
                return json.loads(feedback)
        except Exception as e:
            print(f"❌ KI-Feedback Fehler: {e}")
        
        # Fallback Feedback
        return {
            "strengths": "Du hast die Aufgabe bearbeitet" if user_answer else "Versuche eine Antwort zu geben",
            "improvements": "Überprüfe deine Lösung noch einmal" if not is_correct else "Weiter so!",
            "hint": question_data.get('explanation', ''),
            "concept_explanation": question_data.get('explanation', 'Konzept verstehen')
        }

    def _analyze_test_results(self, test_id: str, user_hash: str) -> dict:
        """
        📊 Analysiert Testergebnisse für detailliertes Feedback
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Hole falsche Antworten für Analyse
            cursor.execute('''
                SELECT question_index, user_answer, correct_answer, feedback
                FROM test_results 
                WHERE test_id = ? AND user_hash = ? AND is_correct = 0
            ''', (test_id, user_hash))
            
            wrong_answers = cursor.fetchall()
            conn.close()
            
            if wrong_answers:
                error_topics = {}
                for answer in wrong_answers:
                    # Einfache Analyse - könnte mit KI erweitert werden
                    question_index, user_answer, correct_answer, feedback = answer
                    error_topics[f"Frage {question_index + 1}"] = {
                        "user_answer": user_answer[:100] + "..." if len(user_answer) > 100 else user_answer,
                        "correct_answer": correct_answer[:100] + "..." if len(correct_answer) > 100 else correct_answer
                    }
                
                return {
                    "wrong_answers_count": len(wrong_answers),
                    "common_errors": error_topics,
                    "suggestion": f"Konzentriere dich auf {len(wrong_answers)} schwierige Bereiche"
                }
            else:
                return {
                    "wrong_answers_count": 0,
                    "common_errors": {},
                    "suggestion": "Ausgezeichnet! Keine Fehler in diesem Test."
                }
                
        except Exception as e:
            print(f"❌ Fehler bei Ergebnis-Analyse: {e}")
            return {"error": "Analyse nicht verfügbar"}

    def _get_performance_level(self, score: float) -> str:
        """
        🎯 Bestimmt Performance-Level basierend auf Score
        """
        if score >= 90: return "Exzellent"
        if score >= 75: return "Sehr gut"
        if score >= 60: return "Gut"
        if score >= 50: return "Befriedigend"
        return "Braucht Übung"

    def _generate_test_recommendations(self, score: float, analysis: dict) -> list:
        """
        💡 Generiert Lernempfehlungen basierend auf Testergebnissen
        """
        recommendations = []
        
        if score >= 90:
            recommendations = [
                "Ausgezeichnete Leistung! Du beherrschst dieses Thema.",
                "Versuche dich an anspruchsvolleren Aufgaben zur Vertiefung.",
                "Erkläre das Thema anderen, um dein Verständnis zu festigen."
            ]
        elif score >= 75:
            recommendations = [
                "Gute Leistung! Einige Bereiche könnten noch verbessert werden.",
                "Wiederhole die falsch beantworteten Fragen.",
                "Übe mit ähnlichen Aufgabenstellungen."
            ]
        elif score >= 60:
            recommendations = [
                "Solide Grundkenntnisse vorhanden.",
                "Konzentriere dich auf die schwierigeren Aspekte des Themas.",
                "Wiederhole die Grundlagen und baue darauf auf."
            ]
        else:
            recommendations = [
                "Das Thema benötigt mehr Aufmerksamkeit.",
                "Beginne mit den Grundlagen und arbeite dich vor.",
                "Regelmäßige, kurze Übungseinheiten sind empfehlenswert.",
                "Nutze die Erklärungen zu jeder Aufgabe sorgfältig."
            ]
        
        # Füge spezifische Empfehlungen basierend auf der Analyse hinzu
        wrong_count = analysis.get('wrong_answers_count', 0)
        if wrong_count > 0:
            recommendations.append(f"Wiederhole speziell die {wrong_count} falsch beantworteten Fragen.")
        
        return recommendations




    # === HELFER-METHODEN ===

    def _calculate_mean(self, data: list) -> float:
        """Berechnet Mittelwert ohne numpy Abhängigkeit"""
        if not data:
            return 0
        try:
            return sum(data) / len(data)
        except:
            return 0

    def _calculate_std(self, data: list) -> float:
        """Berechnet Standardabweichung ohne numpy"""
        if not data or len(data) < 2:
            return 0
        try:
            mean = self._calculate_mean(data)
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            return variance ** 0.5
        except:
            return 0

    def _calculate_median(self, data: list) -> float:
        """Berechnet Median ohne numpy"""
        if not data:
            return 0
        try:
            sorted_data = sorted(data)
            n = len(sorted_data)
            if n % 2 == 0:
                return (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
            else:
                return sorted_data[n//2]
        except:
            return 0

    def _safe_convert_int(self, value, default=0):
        """Sichere Integer-Konvertierung"""
        try:
            if value is None:
                return default
            return int(float(value))
        except:
            return default

    def _safe_convert_float(self, value, default=0.0):
        """Sichere Float-Konvertierung"""
        try:
            if value is None:
                return default
            return float(value)
        except:
            return default

    def _extract_hour_from_timestamp(self, timestamp):
        """Extrahiert Stunde aus verschiedenen Timestamp-Formaten"""
        try:
            if isinstance(timestamp, str):
                if 'T' in timestamp:  # ISO Format
                    return datetime.fromisoformat(timestamp).hour
                else:  # Versuche andere Formate
                    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").hour
            elif isinstance(timestamp, (int, float)):  # Unix timestamp
                return datetime.fromtimestamp(timestamp).hour
            else:
                return None
        except:
            return None

    # Weitere Hilfsmethoden hier...

    def _get_default_learning_profile(self):
        """Gibt Standard-Lernprofil zurück"""
        return {
            "detected_learning_style": "adaptiv_ausgeglichen",
            "cognitive_patterns": {},
            "optimal_session_length": 45,
            "preferred_subjects": [],
            "struggle_areas": ["Wird analysiert..."],
            "performance_peaks": {}
        }

    def _get_adaptive_fallback_exercises(self, profile: dict, subject: str, topic: str, count: int) -> dict:
        """Robuste adaptive Fallback-Übungen"""
        try:
            style = profile.get("detected_learning_style", "adaptiv")
            
            exercise_library = {
                "tiefgehend_konzentriert": [
                    {
                        "question": f"Analysiere {topic} in {subject} systematisch und erstelle eine umfassende Erklärung",
                        "solution": "Strukturierte Analyse mit Hauptkonzepten, Anwendungen und Beispielen",
                        "explanation": "Tiefgehende Analyse fördert umfassendes Verständnis komplexer Themen",
                        "difficulty": "hoch",
                        "personalization_note": "Passt zu deinem konzentrierten Lernstil"
                    }
                ],
                # Weitere Stile hier...
            }
            
            default_exercise = [{
                "question": f"Erarbeite dir {topic} in {subject} durch aktive Lernmethoden",
                "solution": "Kombiniere Lesen, Üben und Anwenden für bestmögliche Ergebnisse",
                "explanation": "Aktive Lernmethoden führen zu besserem Behalten und Verständnis",
                "difficulty": "mittel",
                "personalization_note": "Universell einsetzbare Lernstrategie"
            }]
            
            selected_exercises = exercise_library.get(style, default_exercise)
            
            return {
                "exercises": selected_exercises[:count],
                "adaptive_tips": [
                    f"Automatisch angepasst an: {style}",
                    "Das System lernt kontinuierlich aus deinem Lernverhalten",
                    "Mehr Daten führen zu präziserer Personalisierung"
                ],
                "fallback_used": True
            }
            
        except Exception as e:
            print(f"❌ Fehler im Fallback: {e}")
            return {
                "exercises": [{
                    "question": f"Beschäftige dich mit {topic} in {subject} und erstelle eine Lernzusammenfassung",
                    "solution": "Systematische Erarbeitung und strukturierte Darstellung des Themas",
                    "explanation": "Eigenständige Erarbeitung fördert tiefes Verständnis",
                    "difficulty": "mittel",
                    "personalization_note": "Universelle Lernmethode"
                }],
                "adaptive_tips": ["Lerne regelmäßig und abwechslungsreich", "Kombiniere verschiedene Methoden"],
                "fallback_used": True
            }

    # === INTERNE METHODEN FÜR DATENBANK-ZUGRIFF ===

    def _get_user_sessions(self, user_hash: str) -> list:
        """Holt Lern-Sessions aus der Datenbank"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT subject, duration_minutes, topics, performance_score, engagement_level, session_date
                FROM study_sessions 
                WHERE user_hash = ?
                ORDER BY session_date DESC
                LIMIT 50
            ''', (user_hash,))
            sessions = cursor.fetchall()
            conn.close()
            return sessions
        except Exception as e:
            print(f"❌ Fehler beim Laden der Sessions: {e}")
            return []

    def _load_user_profile(self, user_hash: str) -> dict:
        """Lädt User-Profil aus Datenbank"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT detected_learning_style, cognitive_patterns, performance_trends, adaptation_history
                FROM user_profiles 
                WHERE user_hash = ?
            ''', (user_hash,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "detected_learning_style": result[0],
                    "cognitive_patterns": json.loads(result[1]) if result[1] else {},
                    "performance_trends": json.loads(result[2]) if result[2] else {},
                    "adaptation_history": json.loads(result[3]) if result[3] else []
                }
            else:
                return self._get_default_learning_profile()
        except Exception as e:
            print(f"❌ Fehler beim Laden des Profils: {e}")
            return self._get_default_learning_profile()

    def _save_user_profile(self, user_hash: str, profile: dict):
        """Speichert User-Profil in Datenbank"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_hash, detected_learning_style, cognitive_patterns, performance_trends, adaptation_history, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_hash,
                profile.get('detected_learning_style'),
                json.dumps(profile.get('cognitive_patterns', {})),
                json.dumps(profile.get('performance_trends', {})),
                json.dumps(profile.get('adaptation_history', []))
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Fehler beim Speichern des Profils: {e}")

    def _auto_adapt_user_profile(self, user_hash: str):
        """Passt User-Profil automatisch basierend auf neuen Daten an"""
        # Hier könnte in Zukunft eine adaptive Logik implementiert werden
        pass

    def _analyze_mistake_pattern(self, user_hash: str, exercise_data: dict, user_answer: str):
        """Analysiert Fehlermuster für spätere Verbesserungen"""
        # Einfache Implementierung - könnte erweitert werden
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prüfe ob Fehlertyp bereits existiert
            error_type = self._categorize_error(exercise_data, user_answer)
            
            cursor.execute('''
                SELECT frequency FROM mistake_patterns 
                WHERE user_hash = ? AND error_type = ? AND topic = ?
            ''', (user_hash, error_type, exercise_data.get('topic', 'unknown')))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update frequency
                cursor.execute('''
                    UPDATE mistake_patterns 
                    SET frequency = frequency + 1, last_occurrence = CURRENT_TIMESTAMP
                    WHERE user_hash = ? AND error_type = ? AND topic = ?
                ''', (user_hash, error_type, exercise_data.get('topic', 'unknown')))
            else:
                # Neuer Eintrag
                cursor.execute('''
                    INSERT INTO mistake_patterns 
                    (user_hash, subject, topic, error_type, pattern_data, frequency, first_occurrence, last_occurrence)
                    VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    user_hash,
                    exercise_data.get('subject'),
                    exercise_data.get('topic', 'unknown'),
                    error_type,
                    json.dumps({'user_answer': user_answer, 'correct_answer': exercise_data.get('solution')})
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Fehler bei Fehleranalyse: {e}")

    def _categorize_error(self, exercise_data: dict, user_answer: str) -> str:
        """Kategorisiert Fehler typ"""
        # Einfache Kategorisierung - könnte verbessert werden
        if not user_answer or user_answer.strip() == "":
            return "leere_antwort"
        elif len(user_answer) < 5:
            return "zu_kurz"
        else:
            return "inhaltlicher_fehler"

    def get_learning_progress(self, username: str, days: int = 7) -> dict:
        """Berechnet Lernfortschritt über Zeit"""
        # Vereinfachte Implementierung
        return {
            'trends': {
                'consistency_score': 75,
                'improvement_rate': 15,
                'session_frequency': 'regelmäßig'
            },
            'progress_over_time': [
                {'date': '2024-01-01', 'score': 70},
                {'date': '2024-01-02', 'score': 75},
                {'date': '2024-01-03', 'score': 80}
            ]
        }

    def _get_fallback_recommendations(self) -> dict:
        """Fallback-Empfehlungen wenn KI nicht verfügbar"""
        return {
            "daily_plan": "30-45 Minuten konzentriertes Lernen mit Pausen",
            "weekly_goals": ["3-4 Lerneinheiten", "Themen wiederholen", "Neue Konzepte lernen"],
            "learning_strategies": ["Aktives Recall", "Spaced Repetition", "Practice Testing"],
            "warning_signs": ["Zu lange Sessions", "Unregelmäßigkeit", "Keine Pausen"]
        }

    def _get_mc_multiple_fallback_exercises(self, subject: str, topic: str, count: int) -> dict:
        """
        📝 Fallback Multiple-Choice Übungen mit mehreren richtigen Antworten
        """
        exercises = []
        
        mc_multiple_questions = {
            "Mathe": {
                "Analysis": [
                    {
                        "question": "Welche der folgenden Funktionen sind Ableitungen von f(x) = x³?",
                        "options": {
                            "A": "3x²",
                            "B": "x²", 
                            "C": "6x",
                            "D": "3x",
                            "E": "x³"
                        },
                        "correct_answers": ["A"],
                        "explanation": "Nur 3x² ist die korrekte Ableitung von x³.",
                        "difficulty": "mittel",
                        "personalization_note": "Ableitungen erkennen",
                        "multiple_correct": False
                    }
                ],
                "Mengenlehre": [
                    {
                        "question": "Welche der folgenden Zahlen sind gerade?",
                        "options": {
                            "A": "2",
                            "B": "3",
                            "C": "4", 
                            "D": "5",
                            "E": "6"
                        },
                        "correct_answers": ["A", "C", "E"],
                        "explanation": "Gerade Zahlen sind durch 2 teilbar: 2, 4, 6",
                        "difficulty": "einfach",
                        "personalization_note": "Gerade Zahlen identifizieren",
                        "multiple_correct": True
                    }
                ]
            },
            "Deutsch": {
                "Grammatik": [
                    {
                        "question": "Welche der folgenden Wörter sind Nomen?",
                        "options": {
                            "A": "Haus",
                            "B": "laufen",
                            "C": "schnell", 
                            "D": "Baum",
                            "E": "und"
                        },
                        "correct_answers": ["A", "D"],
                        "explanation": "Haus und Baum sind Nomen (Substantive).",
                        "difficulty": "einfach", 
                        "personalization_note": "Wortarten erkennen",
                        "multiple_correct": True
                    }
                ]
            }
        }
        
        # Wähle passende Fragen aus
        subject_questions = mc_multiple_questions.get(subject, {})
        topic_questions = subject_questions.get(topic, [])
        
        if topic_questions:
            exercises = topic_questions[:count]
        else:
            # Generische Fallback-Fragen
            for i in range(count):
                is_multiple = i % 2 == 0  # Jede zweite Frage hat mehrere Antworten
                exercises.append({
                    "question": f"Frage zu {topic} in {subject}?",
                    "options": {
                        "A": "Antwort A",
                        "B": "Antwort B",
                        "C": "Antwort C", 
                        "D": "Antwort D"
                    },
                    "correct_answers": ["A", "C"] if is_multiple else ["B"],
                    "explanation": f"Erklärung zu {topic}",
                    "difficulty": "mittel",
                    "personalization_note": "Adaptive Lernfrage",
                    "multiple_correct": is_multiple
                })
        
        return {
            "exercises": exercises,
            "adaptive_tips": [
                "Multiple-Choice Modus mit mehreren Antwortmöglichkeiten",
                "Achte darauf, dass mehrere Antworten richtig sein können!",
                "Wähle alle zutreffenden Antworten aus"
            ]
        }


    def finish_test_session(self, username: str, test_id: str) -> dict:
        """
        🏁 Beendet Test-Session mit verbesserter KI-Integration
        """
        user_hash = self._get_user_hash(username)
        
        print(f"🔍 DEBUG finish_test_session: user={username}, test_id={test_id}")
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Hole Test-Daten
            cursor.execute('''
                SELECT subject, topic, questions, user_answers, total_questions, start_time 
                FROM test_sessions WHERE test_id = ? AND user_hash = ?
            ''', (test_id, user_hash))
            
            test_data = cursor.fetchone()
            if not test_data:
                print(f"❌ DEBUG: Test nicht gefunden für {test_id}")
                return {"error": "Test nicht gefunden"}
            
            subject, topic, questions_json, answers_json, total_questions, start_time = test_data
            
            # Parse alle Daten
            questions_data = json.loads(questions_json) if questions_json else {}
            user_answers = json.loads(answers_json) if answers_json else []
            
            print(f"🔍 DEBUG: {len(user_answers)} user_answers geladen")
            
            # Hole Fragen-Array
            questions = []
            if isinstance(questions_data, dict) and 'exercises' in questions_data:
                questions = questions_data['exercises']
            elif isinstance(questions_data, list):
                questions = questions_data
            else:
                questions = questions_data.get('exercises', []) if isinstance(questions_data, dict) else []
            
            print(f"🔍 DEBUG: {len(questions)} Fragen gefunden")
            
            # BERECHNE KORREKTHEIT für jede Antwort
            correct_count = 0
            detailed_answers = []
            
            for i, answer_data in enumerate(user_answers):
                if i < len(questions):
                    question = questions[i]
                    user_answer_list = answer_data.get('user_answer', [])
                    correct_answer_list = question.get('correct_answers', [])
                    
                    # Vergleiche Antworten (Menge)
                    user_set = set(user_answer_list)
                    correct_set = set(correct_answer_list)
                    is_correct = user_set == correct_set
                    
                    if is_correct:
                        correct_count += 1
                    
                    # Aktualisiere answer_data mit Korrektheit
                    answer_data['is_correct'] = is_correct
                    
                    # Füge zu detailed_answers hinzu
                    detailed_answers.append({
                        'question_index': i,
                        'question': question.get('question', ''),
                        'user_answers': user_answer_list,
                        'correct_answers': correct_answer_list,
                        'is_correct': is_correct,
                        'explanation': question.get('explanation', ''),
                        'options': question.get('options', {})
                    })
            
            # Score berechnen
            score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            # Zeitberechnung
            time_spent = self._calculate_time_spent(start_time)
            
            print(f"🔍 DEBUG: Auswertung - {correct_count}/{total_questions} richtig, Score: {score}%")
            
            # Update Test-Session mit berechnetem Score
            cursor.execute('''
                UPDATE test_sessions 
                SET end_time = CURRENT_TIMESTAMP, score = ?, correct_answers = ?, 
                    time_spent_seconds = ?, status = 'completed', user_answers = ?
                WHERE test_id = ?
            ''', (score, correct_count, time_spent, json.dumps(user_answers), test_id))
            
            conn.commit()
            conn.close()
            
            # KI-Auswertung - IMMER aufrufen, auch bei wenigen Antworten
            print("🔍 DEBUG: Starte KI-Auswertung...")
            comprehensive_feedback = self.generate_comprehensive_feedback(username, test_id)
            print("🔍 DEBUG: KI-Auswertung abgeschlossen")
            
            return {
                "test_id": test_id,
                "score": round(score, 1),
                "correct_answers": correct_count,
                "total_questions": total_questions,
                "time_spent_seconds": round(time_spent),
                "performance_level": self._get_performance_level(score),
                "subject": subject,
                "topic": topic,
                "comprehensive_feedback": comprehensive_feedback,
                "detailed_answers": detailed_answers,
                "debug_info": {
                    "user_answers_count": len(user_answers),
                    "questions_count": len(questions),
                    "calculated_correct": correct_count,
                    "ki_feedback_received": bool(comprehensive_feedback)
                }
            }
            
        except Exception as e:
            print(f"❌ DEBUG: Fehler in finish_test_session: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_result(test_id)

    def finish_test_session_complete(self, username: str, test_id: str) -> dict:
            """
            🏁 BEENDET TEST-SESSION - VOLLSTÄNDIG NEUE VERSION
            Mit korrekter Datenstruktur für das Frontend
            """
            user_hash = self._get_user_hash(username)
            
            print(f"🔍 FINISH_TEST_SESSION_COMPLETE: Start für Test {test_id}")
            
            try:
                conn = sqlite3.connect(self.db_path, timeout=20.0)
                cursor = conn.cursor()
                
                # Hole Test-Daten
                cursor.execute('''
                    SELECT subject, topic, questions, user_answers, total_questions, start_time 
                    FROM test_sessions WHERE test_id = ? AND user_hash = ?
                ''', (test_id, user_hash))
                
                test_data = cursor.fetchone()
                if not test_data:
                    return {"error": "Test nicht gefunden"}
                
                subject, topic, questions_json, answers_json, total_questions, start_time = test_data
                
                # Parse die Daten
                questions_data = json.loads(questions_json) if questions_json else {}
                user_answers = json.loads(answers_json) if answers_json and answers_json != '[]' else []
                
                # Extrahiere Fragen
                questions = []
                if isinstance(questions_data, dict) and 'exercises' in questions_data:
                    questions = questions_data['exercises']
                elif isinstance(questions_data, list):
                    questions = questions_data
                else:
                    questions = []
                
                # BERECHNE ERGEBNISSE
                correct_count = 0
                detailed_answers = []
                
                for i in range(len(questions)):
                    question = questions[i]
                    
                    # Finde Antwort für diese Frage
                    user_answer_data = None
                    for answer in user_answers:
                        if answer.get('question_index') == i:
                            user_answer_data = answer
                            break
                    
                    user_answer_list = user_answer_data.get('user_answer', []) if user_answer_data else []
                    correct_answers = question.get('correct_answers', [])
                    
                    # Vergleiche Antworten
                    user_set = set(user_answer_list)
                    correct_set = set(correct_answers)
                    is_correct = user_set == correct_set
                    
                    if is_correct:
                        correct_count += 1
                    
                    # Erstelle detaillierte Antwort
                    detailed_answers.append({
                        'question_index': i,
                        'question': question.get('question', f'Frage {i+1}'),
                        'user_answers': user_answer_list,
                        'correct_answers': correct_answers,
                        'is_correct': is_correct,
                        'explanation': question.get('explanation', 'Keine Erklärung verfügbar'),
                        'options': question.get('options', {})
                    })
                
                # Score berechnen
                score = (correct_count / len(questions)) * 100 if questions else 0
                
                # Zeit berechnen
                time_spent = self._calculate_time_spent(start_time)
                
                # Update Test-Session
                cursor.execute('''
                    UPDATE test_sessions 
                    SET end_time = CURRENT_TIMESTAMP, score = ?, correct_answers = ?, 
                        time_spent_seconds = ?, status = 'completed'
                    WHERE test_id = ?
                ''', (score, correct_count, time_spent, test_id))
                
                conn.commit()
                conn.close()
                
                # --- KI-ANALYSE STARTEN ---
                print(f"🧠 Starte KI-Analyse für Test {test_id}...")
                try:
                    # Wir rufen die KI-Methode auf
                    comprehensive_feedback = self.generate_comprehensive_feedback(username, test_id)
                except Exception as ki_error:
                    print(f"⚠️ KI-Fehler, nutze Fallback: {ki_error}")
                    # Fallback, falls KI nicht antwortet
                    comprehensive_feedback = self._get_comprehensive_feedback(score, correct_count, len(questions), detailed_answers)
                
                return {
                    "test_id": test_id,
                    "score": round(score, 1),
                    "correct_answers": correct_count,
                    "total_questions": len(questions),
                    "time_spent_seconds": round(time_spent),
                    "performance_level": self._get_performance_level(score),
                    "subject": subject,
                    "topic": topic,
                    "comprehensive_feedback": comprehensive_feedback,
                    "detailed_answers": detailed_answers
                }
                
            except Exception as e:
                print(f"❌ Fehler in finish_test_session_complete: {e}")
                import traceback
                traceback.print_exc()
                return self._get_fallback_result(test_id)

    def _get_comprehensive_feedback(self, score: float, correct_answers: int, total_questions: int, detailed_answers: list) -> dict:
        """Erstellt umfassendes Feedback ohne KI"""
        if total_questions == 0:
            return {
                "overall_assessment": "Test konnte nicht ausgewertet werden",
                "key_strengths": ["Test wurde durchgeführt"],
                "main_weaknesses": ["Keine Fragen beantwortet"],
                "learning_recommendations": [
                    {
                        "priority": "hoch",
                        "area": "Test abschließen",
                        "action": "Beim nächsten Test alle Fragen beantworten",
                        "reason": "Der Test wurde ohne Antworten beendet"
                    }
                ],
                "conceptual_understanding": "Nicht bewertbar",
                "next_steps": ["Test neu starten", "Alle Fragen beantworten"],
                "encouragement": "Versuch es noch einmal! Jeder Test ist eine Lernchance. 💪"
            }
        
        # Analysiere falsche Antworten
        wrong_answers = [ans for ans in detailed_answers if not ans['is_correct']]
        weak_areas = []
        
        if wrong_answers:
            weak_areas = [f"{len(wrong_answers)} von {total_questions} Fragen benötigen Verbesserung"]
        
        # Erstelle Empfehlungen basierend auf Score
        recommendations = []
        if score >= 90:
            recommendations = [
                {
                    "priority": "niedrig",
                    "area": "Weiterentwicklung",
                    "action": "Schwierigere Themen angehen",
                    "reason": f"Exzellente Leistung mit {score}%"
                }
            ]
        elif score >= 75:
            recommendations = [
                {
                    "priority": "mittel", 
                    "area": "Vertiefung",
                    "action": "Falsch beantwortete Fragen wiederholen",
                    "reason": f"Gute Leistung mit {score}%, aber noch Verbesserungspotential"
                }
            ]
        else:
            recommendations = [
                {
                    "priority": "hoch",
                    "area": "Grundlagen",
                    "action": "Thema gründlich wiederholen",
                    "reason": f"Score von {score}% zeigt Wissenslücken"
                }
            ]
        
        return {
            "overall_assessment": f"Du hast {correct_answers} von {total_questions} Fragen richtig beantwortet ({score}%)",
            "key_strengths": [f"{correct_answers} Fragen korrekt", "Test erfolgreich abgeschlossen"],
            "main_weaknesses": weak_areas if weak_areas else ["Alles im grünen Bereich"],
            "learning_recommendations": recommendations,
            "conceptual_understanding": "Vollständiges Verständnis" if score >= 90 else "Gutes Verständnis" if score >= 75 else "Benötigt Wiederholung",
            "next_steps": ["Weiterüben", "Nächstes Thema lernen"] if score >= 75 else ["Thema wiederholen", "Übungsaufgaben machen"],
            "encouragement": "Weiter so! Du machst Fortschritte! 🚀" if score >= 75 else "Nicht aufgeben! Übung macht den Meister. 💪"
        }


    def _get_performance_level(self, score: float) -> str:
        """🎯 Bestimmt Performance-Level basierend auf Score"""
        if score >= 90: return "Exzellent"
        if score >= 75: return "Sehr gut" 
        if score >= 60: return "Gut"
        if score >= 50: return "Befriedigend"
        return "Braucht Übung"

    def generate_comprehensive_feedback(self, username: str, test_id: str) -> dict:
        """
        🧠 Generiert umfassendes KI-Feedback für den gesamten Test - MIT TIMEOUT
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Hole komplette Test-Daten
            cursor.execute('''
                SELECT subject, topic, questions, user_answers, score, correct_answers, total_questions
                FROM test_sessions WHERE test_id = ? AND user_hash = ?
            ''', (test_id, user_hash))
            
            test_data = cursor.fetchone()
            if not test_data:
                return self._get_fallback_feedback(0, 0, 0, "Test nicht gefunden")
            
            subject, topic, questions_json, answers_json, score, correct_answers, total_questions = test_data
            
            # Parse Daten
            questions_data = json.loads(questions_json) if questions_json else {}
            user_answers = json.loads(answers_json) if answers_json else []
            
            print(f"🔍 KI-Analyse: Starte für Test {test_id} mit {len(user_answers)} Antworten")
            
            # Bereite Daten für KI vor - KÜRZERE VERSION für bessere Performance
            test_context = f"""
    Du bist ein cooler, motivierender Lern-Coach für einen Schüler.
    Analysiere dieses Testergebnis nicht trocken, sondern persönlich und aufbauend.
    Sprich den Schüler direkt mit "Du" an. Nutze Emojis.

    TEST-DATEN:
    Fach: {subject}
    Thema: {topic}
    Score: {score}%
    Richtig: {correct_answers} von {total_questions}

    Deine Aufgabe:
    1. Gib ein ehrliches, aber nettes Feedback.
    2. Wenn der Score niedrig ist: Mach Mut! "Fehler sind Helfer".
    3. Wenn der Score hoch ist: Feier das!
    4. Gib konkrete Tipps, was als nächstes zu tun ist.

    Antworte NUR als JSON:
    {{
        "overall_assessment": "Kurzes, knackiges Fazit (z.B. 'Starke Leistung!' oder 'Guter Anfang, dranbleiben!')",
        "key_strengths": ["Das lief super", "Hier bist du sicher"],
        "main_weaknesses": ["Hier fehlt noch der Feinschliff", "Darauf nochmal schauen"], 
        "learning_recommendations": [
            {{
                "priority": "hoch/mittel/niedrig",
                "area": "Was üben?",
                "action": "Wie üben? (Konkret!)", 
                "reason": "Warum?"
            }}
        ],
        "conceptual_understanding": "Einschätzung (z.B. 'Grundlagen sitzen, Details fehlen noch')",
        "next_steps": ["Schritt 1", "Schritt 2"],
        "encouragement": "Ein motivierender Abschlusssatz (wie ein Coach vor dem Spiel)"
    }}
    """

            # KI-Anfrage mit kürzerem Timeout
            print("🔄 Frage KI um Analyse...")
            result = self.robust_api_call(test_context, max_retries=1, timeout=15, response_format="json")
            
            if result:
                try:
                    comprehensive_feedback = json.loads(result)
                    print(f"✅ KI-Feedback erhalten für Test {test_id}")
                    return comprehensive_feedback
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Fehler in KI-Antwort: {e}")
                    print(f"❌ KI-Antwort war: {result}")
                    return self._get_fallback_feedback(score, correct_answers, total_questions, "Ungültiges JSON von KI")
            else:
                print(f"❌ Keine KI-Antwort erhalten - verwende Fallback")
                return self._get_fallback_feedback(score, correct_answers, total_questions, "KI nicht verfügbar")
                    
        except Exception as e:
            print(f"❌ Fehler bei KI-Feedback: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_feedback(0, 0, 0, f"Fehler: {str(e)}")

    def _get_fallback_feedback(self, score: float, correct_answers: int, total_questions: int, reason: str = "") -> dict:
        """Fallback-Feedback ohne KI"""
        feedback = {
            "overall_assessment": f"Automatische Analyse durchgeführt ({reason})",
            "key_strengths": [
                "Test erfolgreich absolviert",
                f"{correct_answers} von {total_questions} Fragen richtig" if total_questions > 0 else "Test beendet"
            ],
            "main_weaknesses": [
                "Detaillierte Analyse benötigt mehr Daten" if total_questions == 0 else f"{total_questions - correct_answers} Fragen benötigen Verbesserung"
            ],
            "learning_recommendations": [
                {
                    "priority": "hoch",
                    "area": "Testanalyse",
                    "action": "Weitere Tests durchführen für bessere Analyse",
                    "reason": f"Erreichte {score}% bei {correct_answers}/{total_questions} richtigen Antworten"
                }
            ],
            "conceptual_understanding": "Wird basierend auf weiteren Tests besser bewertbar",
            "next_steps": [
                "Regelmäßig üben",
                "Schwierige Themen wiederholen",
                "Nächsten Test absolvieren"
            ],
            "encouragement": "Jeder Test ist ein Schritt zum Erfolg! Weiter so! 💪"
        }
        
        # Angepasste Empfehlungen basierend auf Score
        if score >= 80:
            feedback["key_strengths"].append("Ausgezeichnete Leistung!")
            feedback["learning_recommendations"].append({
                "priority": "niedrig", 
                "area": "Weiterentwicklung",
                "action": "Anspruchsvollere Themen angehen",
                "reason": f"Exzellente Leistung mit {score}%"
            })
        elif score >= 60:
            feedback["key_strengths"].append("Gute Grundkenntnisse")
            feedback["learning_recommendations"].append({
                "priority": "mittel",
                "area": "Vertiefung", 
                "action": "Falsch beantwortete Fragen wiederholen",
                "reason": f"Gute Leistung mit {score}% - noch Luft nach oben"
            })
        else:
            feedback["main_weaknesses"].append("Grundlagen benötigen Wiederholung")
            feedback["learning_recommendations"].append({
                "priority": "hoch",
                "area": "Grundlagen",
                "action": "Thematische Grundlagen systematisch wiederholen", 
                "reason": f"Basiswissen mit {score}% ausbauen"
            })
        
        return feedback

    def get_test_history(self, username: str, limit: int = 10) -> list:
        """
        📊 Holt Test-Historie für einen Benutzer
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT test_id, subject, topic, score, correct_answers, total_questions, 
                    time_spent_seconds, start_time, end_time
                FROM test_sessions 
                WHERE user_hash = ? AND status = 'completed'
                ORDER BY end_time DESC
                LIMIT ?
            ''', (user_hash, limit))
            
            tests = cursor.fetchall()
            conn.close()
            
            history = []
            for test in tests:
                (test_id, subject, topic, score, correct_answers, total_questions, 
                time_spent, start_time, end_time) = test
                
                history.append({
                    "test_id": test_id,
                    "subject": subject,
                    "topic": topic,
                    "score": score,
                    "correct_answers": correct_answers,
                    "total_questions": total_questions,
                    "time_spent_seconds": time_spent,
                    "date": end_time or start_time,
                    "performance_level": self._get_performance_level(score or 0)
                })
            
            return history
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Test-Historie: {e}")
            return []

    def save_answer(self, username: str, test_id: str, question_index: int, user_answers: list) -> bool:
        """
        💾 Speichert eine Antwort in test_sessions.user_answers - KORRIGIERTE VERSION
        """
        user_hash = self._get_user_hash(username)
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            # Hole aktuelle Test-Daten
            cursor.execute('SELECT user_answers FROM test_sessions WHERE test_id = ? AND user_hash = ?', (test_id, user_hash))
            test_data = cursor.fetchone()
            
            if not test_data:
                print(f"❌ Test {test_id} nicht gefunden")
                return False
            
            current_answers_json = test_data[0]
            current_answers = json.loads(current_answers_json) if current_answers_json else []
            
            # Erstelle Antwort-Daten mit KORREKTER Struktur
            answer_data = {
                'question_index': question_index,
                'user_answer': user_answers,  # Liste der ausgewählten Optionen
                'is_correct': False,  # Wird später bei der Auswertung gesetzt
                'timestamp': datetime.now().isoformat()
            }
            
            # Update oder füge Antwort hinzu
            answer_exists = False
            for i, answer in enumerate(current_answers):
                if answer.get('question_index') == question_index:
                    current_answers[i] = answer_data
                    answer_exists = True
                    break
            
            if not answer_exists:
                current_answers.append(answer_data)
            
            # In Datenbank speichern
            cursor.execute('''
                UPDATE test_sessions SET user_answers = ? WHERE test_id = ?
            ''', (json.dumps(current_answers), test_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Antwort für Frage {question_index} gespeichert: {user_answers}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Antwort: {e}")
            return False


    def _calculate_time_spent(self, start_time) -> int:
        """Berechnet die verstrichene Zeit in Sekunden"""
        try:
            if isinstance(start_time, str):
                # ISO Format oder SQLite Timestamp
                if 'T' in start_time:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                else:
                    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            else:
                # Unix timestamp oder datetime object
                start_dt = datetime.fromtimestamp(start_time) if isinstance(start_time, (int, float)) else start_time
            
            return int((datetime.now() - start_dt).total_seconds())
        except Exception as e:
            print(f"❌ Fehler bei Zeitberechnung: {e}")
            return 300  # Fallback: 5 Minuten

    def debug_test_data(self, test_id: str):
        """🔍 Debug-Methode zum Überprüfen der Test-Daten"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT test_id, subject, topic, questions, user_answers, total_questions, 
                    start_time, status, score, correct_answers
                FROM test_sessions WHERE test_id = ?
            ''', (test_id,))
            
            test_data = cursor.fetchone()
            conn.close()
            
            if test_data:
                print("🔍 DEBUG TEST DATEN:")
                print(f"Test ID: {test_data[0]}")
                print(f"Subject: {test_data[1]}")
                print(f"Topic: {test_data[2]}")
                print(f"Questions JSON Länge: {len(test_data[3]) if test_data[3] else 0}")
                print(f"User Answers: {test_data[4]}")
                print(f"Total Questions: {test_data[5]}")
                print(f"Status: {test_data[7]}")
                print(f"Score: {test_data[8]}")
                print(f"Correct Answers: {test_data[9]}")
                
                # Parse und zeige Fragen
                if test_data[3]:
                    try:
                        questions = json.loads(test_data[3])
                        print(f"Fragen-Struktur: {type(questions)}")
                        if isinstance(questions, dict) and 'exercises' in questions:
                            print(f"Anzahl Fragen: {len(questions['exercises'])}")
                            for i, q in enumerate(questions['exercises'][:2]):  # Zeige nur erste 2 Fragen
                                print(f"Frage {i}: {q.get('question', '')[:50]}...")
                                print(f"  Optionen: {list(q.get('options', {}).keys())}")
                                print(f"  Korrekte Antworten: {q.get('correct_answers', [])}")
                    except Exception as e:
                        print(f"Fehler beim Parsen der Fragen: {e}")
            else:
                print("❌ Test nicht gefunden")
                
        except Exception as e:
            print(f"❌ Debug-Fehler: {e}")
















# === TEST-METHODEN ===

def main():
    """🧪 Haupt-Testfunktion für die Lern-Buddy Klasse"""
    buddy = UniversalLernBuddy()
    
    print("🌍 UNIVERSALER LERN-BUDDY TEST")
    print("=" * 50)
    
    # Test-User erstellen
    test_user = "test_schueler"
    
    try:
        # User erstellen
        buddy.create_user(test_user, "test@schule.de", "test123")
        print(f"✅ Test-User {test_user} erstellt")
        
        # Schulkontext setzen
        school_data = {
            "grade": "11",
            "school_type": "gymnasium", 
            "state": "Bayern",
            "subjects": ["Mathe", "Deutsch", "Englisch"],
            "curriculum_focus": "naturwissenschaft"
        }
        buddy.set_school_context(test_user, school_data)
        print("✅ Schulkontext gesetzt")
        
        # Lern-Session tracken
        buddy.track_study_session_with_engagement(
            username=test_user,
            subject="Mathe",
            duration_minutes=45,
            topics=["Analysis", "Ableitungen"],
            performance_score=0.8,
            engagement_level=0.7
        )
        print("✅ Test-Session getrackt")
        
        # Lernprofil analysieren
        profile = buddy.detect_learning_patterns(test_user)
        print(f"✅ Lernprofil erstellt: {profile['detected_learning_style']}")
        
        # Übungen generieren
        exercises = buddy.generate_personalized_exercises(test_user, "Mathe", "Analysis", 2)
        print(f"✅ {len(exercises['exercises'])} Übungen generiert")
        
        print("\n🎉 ALLE TESTS ERFOLGREICH!")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")

if __name__ == "__main__":
    main()