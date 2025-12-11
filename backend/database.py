"""
💾 DATABASE MANAGER
Kapselt alle Datenbank-Operationen für den KI-Lern-Buddy.
Zuständig für: SQLite-Verbindung, Tabellen-Setup, CRUD-Operationen.
"""

import sqlite3
import json
import time
import hashlib
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="universal_lern_buddy.db"):
        self.db_path = db_path
        self._init_database()

    def get_connection(self):
        """Erstellt eine Verbindung mit optimierten Einstellungen"""
        conn = sqlite3.connect(self.db_path, timeout=20.0)
        # WAL-Mode für bessere Performance bei gleichzeitigen Zugriffen
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_database(self):
        """Initialisiert alle Tabellen, falls sie nicht existieren"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. User & Auth
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
            
            # 2. Profile & Lernstile
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
            
            # 3. Schulkontext
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
            
            # 4. Lern-Sessions (Tracking)
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
                    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 5. Einzelne Übungsantworten
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
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 6. Fehlermuster
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
                    last_occurrence TIMESTAMP
                )
            ''')
            
            # 7. Test-Sessions (Ganze Tests)
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
                    status TEXT DEFAULT 'active'
                )
            ''')

            # 8. Test-Ergebnisse (Detail)
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
                    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ Datenbank: Tabellen initialisiert")
            
        except Exception as e:
            print(f"❌ Datenbank-Init Fehler: {e}")
        finally:
            conn.close()

    # === HELPER ===
    
    def get_user_hash(self, username: str) -> str:
        """Erstellt konsistenten Hash für User-IDs (für Privacy/Verknüpfung)"""
        return hashlib.sha256(username.encode()).hexdigest()[:16]

    # === USER MANAGEMENT ===

    def create_user(self, username, email, password_hash, role):
        conn = self.get_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user_by_username(self, username):
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT username, password_hash, role FROM users WHERE username = ?', (username,))
            return cursor.fetchone()
        finally:
            conn.close()

    def update_last_login(self, username):
        conn = self.get_connection()
        conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?', (username,))
        conn.commit()
        conn.close()

    def update_user_profile_data(self, username, update_data):
        conn = self.get_connection()
        try:
            set_clauses = [f"{k} = ?" for k in update_data.keys()]
            params = list(update_data.values())
            params.append(username)
            
            if set_clauses:
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE username = ?"
                conn.execute(query, params)
                conn.commit()
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False
        finally:
            conn.close()

    # === PROFIL & SCHULE ===

    def get_profile(self, user_hash):
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT detected_learning_style, cognitive_patterns, performance_trends, adaptation_history
                FROM user_profiles WHERE user_hash = ?
            ''', (user_hash,))
            return cursor.fetchone()
        finally:
            conn.close()

    def save_profile(self, user_hash, profile_data):
        conn = self.get_connection()
        try:
            conn.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_hash, detected_learning_style, cognitive_patterns, performance_trends, adaptation_history, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_hash,
                profile_data.get('detected_learning_style'),
                json.dumps(profile_data.get('cognitive_patterns', {})),
                json.dumps(profile_data.get('performance_trends', {})),
                json.dumps(profile_data.get('adaptation_history', []))
            ))
            conn.commit()
        finally:
            conn.close()

    def save_school_context(self, user_hash, data):
        conn = self.get_connection()
        try:
            # Check existiert?
            exists = conn.execute('SELECT 1 FROM school_contexts WHERE user_hash = ?', (user_hash,)).fetchone()
            
            if exists:
                conn.execute('''
                    UPDATE school_contexts 
                    SET grade=?, school_type=?, state=?, subjects=?, curriculum_focus=?, updated_at=CURRENT_TIMESTAMP
                    WHERE user_hash=?
                ''', (data['grade'], data['school_type'], data['state'], data['subjects'], data['curriculum_focus'], user_hash))
            else:
                conn.execute('''
                    INSERT INTO school_contexts (user_hash, grade, school_type, state, subjects, curriculum_focus)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_hash, data['grade'], data['school_type'], data['state'], data['subjects'], data['curriculum_focus']))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_school_context(self, user_hash):
        conn = self.get_connection()
        try:
            return conn.execute('''
                SELECT grade, school_type, state, subjects, curriculum_focus 
                FROM school_contexts WHERE user_hash = ?
            ''', (user_hash,)).fetchone()
        finally:
            conn.close()

    # === TRACKING & ANALYTICS ===

    def log_session(self, user_hash, subject, duration, topics, score, engagement, difficulty):
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO study_sessions 
            (user_hash, subject, duration_minutes, topics, performance_score, engagement_level, difficulty_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_hash, subject, duration, json.dumps(topics), score, engagement, difficulty))
        conn.commit()
        conn.close()

    def get_sessions(self, user_hash, limit=50):
        conn = self.get_connection()
        try:
            return conn.execute('''
                SELECT subject, duration_minutes, topics, performance_score, engagement_level, session_date
                FROM study_sessions WHERE user_hash = ? ORDER BY session_date DESC LIMIT ?
            ''', (user_hash, limit)).fetchall()
        finally:
            conn.close()

    def get_analytics_raw_data(self, user_hash):
        """Holt aggregierte Daten für Analytics"""
        conn = self.get_connection()
        try:
            # 1. Antworten Stats
            subject_stats = conn.execute('''
                SELECT COUNT(*), SUM(CASE WHEN is_correct THEN 1 ELSE 0 END), AVG(time_spent_seconds), subject, topic
                FROM exercise_answers WHERE user_hash = ? GROUP BY subject, topic
            ''', (user_hash,)).fetchall()
            
            # 2. Fehler
            mistakes = conn.execute('''
                SELECT error_type, frequency, topic, subject FROM mistake_patterns 
                WHERE user_hash = ? ORDER BY frequency DESC LIMIT 10
            ''', (user_hash,)).fetchall()
            
            # 3. Sessions
            sessions = conn.execute('''
                SELECT COUNT(*), AVG(duration_minutes), AVG(performance_score), subject
                FROM study_sessions WHERE user_hash = ? GROUP BY subject
            ''', (user_hash,)).fetchall()
            
            return subject_stats, mistakes, sessions
        finally:
            conn.close()

    # === TESTS ===

    def create_test_session(self, test_id, user_hash, subject, topic, questions_json, count, start_time):
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO test_sessions 
            (test_id, user_hash, subject, topic, questions, total_questions, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_id, user_hash, subject, topic, questions_json, count, start_time))
        conn.commit()
        conn.close()

    def get_test_session(self, test_id, user_hash):
        conn = self.get_connection()
        try:
            return conn.execute('''
                SELECT subject, topic, questions, user_answers, total_questions, start_time, score, correct_answers 
                FROM test_sessions WHERE test_id = ? AND user_hash = ?
            ''', (test_id, user_hash)).fetchone()
        finally:
            conn.close()

    def update_test_answer(self, test_id, answers_json):
        conn = self.get_connection()
        conn.execute('UPDATE test_sessions SET user_answers = ? WHERE test_id = ?', (answers_json, test_id))
        conn.commit()
        conn.close()

    def complete_test(self, test_id, score, correct, time_spent, answers_json):
        conn = self.get_connection()
        conn.execute('''
            UPDATE test_sessions 
            SET end_time = CURRENT_TIMESTAMP, score = ?, correct_answers = ?, 
                time_spent_seconds = ?, status = 'completed', user_answers = ?
            WHERE test_id = ?
        ''', (score, correct, time_spent, answers_json, test_id))
        conn.commit()
        conn.close()

    def save_test_result_detail(self, test_id, user_hash, idx, u_ans, c_ans, is_corr, feedback):
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO test_results 
            (test_id, user_hash, question_index, user_answer, correct_answer, is_correct, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_id, user_hash, idx, u_ans, c_ans, 1 if is_corr else 0, feedback))
        conn.commit()
        conn.close()

    def get_test_history(self, user_hash, limit=10):
        conn = self.get_connection()
        try:
            return conn.execute('''
                SELECT test_id, subject, topic, score, correct_answers, total_questions, 
                    time_spent_seconds, start_time, end_time
                FROM test_sessions WHERE user_hash = ? AND status = 'completed'
                ORDER BY end_time DESC LIMIT ?
            ''', (user_hash, limit)).fetchall()
        finally:
            conn.close()