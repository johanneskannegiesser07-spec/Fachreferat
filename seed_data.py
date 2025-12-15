"""
🌋 MASSIVE SEED DATA SCRIPT
Füllt die Datenbank mit einer EXTREMEN Menge an Daten für den absoluten Demo-Effekt.
"""
import sqlite3
import hashlib
import time
import random
import json
from datetime import datetime, timedelta

# Konfiguration
DB_PATH = "backend/universal_lern_buddy.db"
USERNAME = "demo"
PASSWORD = "demo123" 

# Erweiterte Fächer-Liste mit realistischen Themen
SUBJECTS = {
    "Mathe": ["Analysis", "Lineare Algebra", "Stochastik", "Geometrie"],
    "Physik": ["Mechanik", "Optik", "Elektrodynamik", "Thermodynamik", "Quantenphysik"],
    "Chemie": ["Organik", "Anorganik", "Redoxreaktionen"],
    "Deutsch": ["Gedichtanalyse", "Epoche der Romantik", "Erörterung", "Faust"],
    "Englisch": ["Grammar", "Shakespeare", "Creative Writing", "American Dream"],
    "Informatik": ["Python Basics", "Datenbanken", "Netzwerke", "Algorithmen"],
    "Geschichte": ["Französische Revolution", "Weimarer Republik", "Mittelalter"],
    "Biologie": ["Genetik", "Evolution", "Ökologie", "Neurobiologie"],
    "Wirtschaft": ["Marktwirtschaft", "Recht", "Bilanzierung"],
    "Geografie": ["Klimawandel", "Bevölkerung", "Plattentektonik"]
}

def get_user_hash(username):
    return hashlib.sha256(username.encode()).hexdigest()[:16]

def seed_massive():
    print(f"🌋 Starte MASSIVE DATA INJECTION für '{USERNAME}'...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. User Check
    user_hash = get_user_hash(USERNAME)
    cursor.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
    if not cursor.fetchone():
        print(f"⚠️ User '{USERNAME}' nicht gefunden. Bitte erst registrieren!")
        # Optional: Hier könnte man den User auch erstellen, aber wir verlassen uns auf Auth
    
    # 2. Aufräumen (optional: alte Demo-Daten löschen, damit es nicht doppelt wird)
    # cursor.execute("DELETE FROM test_sessions WHERE user_hash = ?", (user_hash,))
    # cursor.execute("DELETE FROM study_sessions WHERE user_hash = ?", (user_hash,))
    # print("🧹 Alte Daten bereinigt.")

    # 3. Massen-Daten generieren
    start_date = datetime.now() - timedelta(days=365) # Ein Jahr Rückblick
    count_tests = 0
    count_sessions = 0
    
    print("🚀 Generiere Daten... (das kann kurz dauern)")

    # Wir simulieren jeden Tag des letzten Jahres
    current_date = start_date
    while current_date < datetime.now():
        # 30% Chance, dass an einem Tag gelernt wurde
        if random.random() < 0.3:
            
            # Wähle zufälliges Fach
            subj = random.choice(list(SUBJECTS.keys()))
            topic = random.choice(SUBJECTS[subj])
            
            # SESSION GENERIEREN
            duration = random.randint(15, 90)
            score_trend = min(0.95, 0.4 + (current_date - start_date).days / 1000) # User wird langsam besser
            perf_score = random.uniform(score_trend - 0.2, score_trend + 0.1)
            perf_score = max(0.1, min(1.0, perf_score)) # Clamp 0.1 - 1.0
            
            cursor.execute('''
                INSERT INTO study_sessions 
                (user_hash, subject, duration_minutes, topics, performance_score, engagement_level, difficulty_level, session_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_hash, subj, duration, json.dumps([topic]), perf_score, random.random(), "mittel", current_date.isoformat()
            ))
            count_sessions += 1

            # 50% Chance, dass nach dem Lernen ein TEST gemacht wurde
            if random.random() < 0.5:
                test_id = f"mass_{int(time.time())}_{random.randint(10000,99999)}"
                
                # Score schwankt um den Trend herum
                test_score = perf_score * 100 + random.randint(-10, 10)
                test_score = max(10, min(100, test_score)) # Clamp 0-100
                
                cursor.execute('''
                    INSERT INTO test_sessions 
                    (test_id, user_hash, subject, topic, score, total_questions, correct_answers, status, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    user_hash,
                    subj,
                    topic,
                    test_score,
                    10,
                    int(test_score / 10),
                    'completed',
                    current_date.isoformat(),
                    (current_date + timedelta(minutes=20)).isoformat()
                ))
                count_tests += 1
        
        # Nächster Tag
        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    
    print(f"✅ FERTIG! Datenbank gefüttert mit:")
    print(f"   - {count_sessions} Lern-Sessions")
    print(f"   - {count_tests} absolvierten Tests")
    print("👉 Dein Graph sollte jetzt explodieren! 🕸️💥")

if __name__ == "__main__":
    seed_massive()