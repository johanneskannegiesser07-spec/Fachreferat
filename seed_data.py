"""
🌋 ULTIMATE SEED DATA SCRIPT
Füllt die Datenbank mit ALLEM: Tests, Noten, Flashcards und Graph-Verbindungen.
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
    "Mathe": ["Analysis", "Lineare Algebra", "Stochastik", "Geometrie", "Ableitungen", "Integrale"],
    "Physik": ["Mechanik", "Optik", "Elektrodynamik", "Thermodynamik", "Quantenphysik", "Kinematik"],
    "Chemie": ["Organik", "Anorganik", "Redoxreaktionen", "Säuren & Basen"],
    "Deutsch": ["Gedichtanalyse", "Epoche der Romantik", "Erörterung", "Faust"],
    "Englisch": ["Grammar", "Shakespeare", "Creative Writing", "American Dream"],
    "Informatik": ["Python Basics", "Datenbanken", "Netzwerke", "Algorithmen"],
    "Geschichte": ["Französische Revolution", "Weimarer Republik", "Mittelalter"],
    "Biologie": ["Genetik", "Evolution", "Ökologie", "Neurobiologie"],
    "Wirtschaft": ["Marktwirtschaft", "Recht", "Bilanzierung"],
    "Geografie": ["Klimawandel", "Bevölkerung", "Plattentektonik"]
}

# Manuelle "KI"-Verbindungen für den Graphen
GRAPH_CONNECTIONS = [
    ("Mathe", "Ableitungen", "Physik", "Kinematik", "Geschwindigkeit ist die Ableitung des Ortes"),
    ("Mathe", "Integrale", "Physik", "Thermodynamik", "Berechnung von Arbeit durch Integration"),
    ("Chemie", "Organik", "Biologie", "Genetik", "DNA besteht aus organischen Molekülen"),
    ("Informatik", "Algorithmen", "Mathe", "Stochastik", "Wahrscheinlichkeiten in Suchalgorithmen"),
    ("Geschichte", "Französische Revolution", "Deutsch", "Epoche der Romantik", "Historischer Kontext beeinflusst Literatur"),
    ("Geografie", "Klimawandel", "Biologie", "Ökologie", "Auswirkung auf Ökosysteme"),
    ("Wirtschaft", "Marktwirtschaft", "Geschichte", "Weimarer Republik", "Inflation und Wirtschaftskrise"),
    ("Informatik", "Datenbanken", "Wirtschaft", "Bilanzierung", "Speicherung von Finanzdaten")
]

def get_user_hash(username):
    return hashlib.sha256(username.encode()).hexdigest()[:16]

def seed_massive():
    print(f"🌋 Starte ULTIMATE DATA INJECTION für '{USERNAME}'...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. User Check & Update (XP/Gems)
    user_hash = get_user_hash(USERNAME)
    cursor.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
    if not cursor.fetchone():
        print(f"⚠️ User '{USERNAME}' nicht gefunden. Bitte erst registrieren!")
        return
    else:
        # Gönn dem User mal ordentlich Gems und XP für den Start
        print("💎 Fülle Konto mit Gems & XP...")
        cursor.execute("UPDATE users SET gems = 50, xp = 1250 WHERE username = ?", (USERNAME,))

    # 2. Alte Daten bereinigen (optional, damit Graphen sauber sind)
    tables = ["test_sessions", "study_sessions", "grades", "flashcard_sets", "topic_connections"]
    for t in tables:
        try:
            cursor.execute(f"DELETE FROM {t} WHERE user_hash = ?", (user_hash,))
        except: pass
    print("🧹 Alte Demo-Daten bereinigt.")

    # 3. Noten generieren (Grades)
    print("📊 Schreibe Noten...")
    for subj in SUBJECTS:
        # 2-4 Noten pro Fach
        for _ in range(random.randint(2, 4)):
            grade = random.choice([1, 2, 2, 3, 3, 4, 1, 5]) # Tendenz zu guten Noten
            g_type = random.choice(["schulaufgabe", "ex", "muendlich"])
            weight = 2.0 if g_type == "schulaufgabe" else 1.0
            date = (datetime.now() - timedelta(days=random.randint(10, 200))).isoformat()
            
            cursor.execute('''
                INSERT INTO grades (user_hash, subject, grade_value, grade_type, weight, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_hash, subj, grade, g_type, weight, date))

    # 4. Flashcards generieren
    print("🃏 Erstelle Flashcard-Sets...")
    for i in range(5):
        subj = random.choice(list(SUBJECTS.keys()))
        topic = random.choice(SUBJECTS[subj])
        cards = [
            {"front": f"Was ist das wichtigste an {topic}?", "back": "Dass man es versteht!"},
            {"front": "Definition Begriff A", "back": "Erklärung A"},
            {"front": "Formel / Datum", "back": "x = y^2"},
            {"front": "Zusammenhang", "back": "Komplex"}
        ]
        cursor.execute('''
            INSERT INTO flashcard_sets (user_hash, subject, topic, cards, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_hash, subj, topic, json.dumps(cards), datetime.now().isoformat()))

    # 5. Graph-Verbindungen (Das Highlight!)
    print("🕸️ Knüpfe Wissens-Netzwerk...")
    for conn_data in GRAPH_CONNECTIONS:
        s_sub, s_top, t_sub, t_top, reason = conn_data
        cursor.execute('''
            INSERT INTO topic_connections 
            (user_hash, source_subject, source_topic, target_subject, target_topic, strength, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_hash, s_sub, s_top, t_sub, t_top, 5, reason))

    # 6. Massen-Tests & Sessions (Historie)
    start_date = datetime.now() - timedelta(days=180) # Halbes Jahr Rückblick
    count_tests = 0
    
    print("🚀 Generiere Tests & Sessions Timeline...")

    current_date = start_date
    while current_date < datetime.now():
        if random.random() < 0.4: # 40% Lerntage
            subj = random.choice(list(SUBJECTS.keys()))
            topic = random.choice(SUBJECTS[subj])
            
            # Session
            duration = random.randint(20, 60)
            cursor.execute('''
                INSERT INTO study_sessions 
                (user_hash, subject, duration_minutes, topics, performance_score, engagement_level, difficulty_level, session_date)
                VALUES (?, ?, ?, ?, 0.8, 0.9, 'mittel', ?)
            ''', (user_hash, subj, duration, json.dumps([topic]), current_date.isoformat()))

            # Test (damit Punkte im Graph erscheinen!)
            # WICHTIG: Damit die Connections oben funktionieren, müssen diese Topics auch als "gelernt" (Test gemacht) gelten.
            if random.random() < 0.6:
                test_id = f"seed_{int(time.time())}_{random.randint(1000,9999)}"
                score = random.randint(50, 100)
                cursor.execute('''
                    INSERT INTO test_sessions 
                    (test_id, user_hash, subject, topic, score, total_questions, correct_answers, status, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?, 10, ?, 'completed', ?, ?)
                ''', (test_id, user_hash, subj, topic, score, int(score/10), current_date.isoformat(), current_date.isoformat()))
                count_tests += 1
        
        current_date += timedelta(days=1)

    # Sicherstellen, dass die Topics aus den GRAPH_CONNECTIONS auch wirklich existierende Tests haben
    # (Sonst zeigt der Graph Nodes an, die keine Farbe/Score haben)
    print("🔧 Fixiere Graph-Knoten...")
    for conn_data in GRAPH_CONNECTIONS:
        for i in [0, 2]: # Source und Target Subject
            subj = conn_data[i]
            topic = conn_data[i+1]
            # Prüfen ob Test existiert
            exists = cursor.execute("SELECT 1 FROM test_sessions WHERE user_hash=? AND subject=? AND topic=?", (user_hash, subj, topic)).fetchone()
            if not exists:
                test_id = f"fix_{int(time.time())}_{random.randint(100,999)}"
                cursor.execute('''
                    INSERT INTO test_sessions 
                    (test_id, user_hash, subject, topic, score, total_questions, correct_answers, status, start_time, end_time)
                    VALUES (?, ?, ?, ?, 90, 10, 9, 'completed', ?, ?)
                ''', (test_id, user_hash, subj, topic, datetime.now().isoformat(), datetime.now().isoformat()))

    conn.commit()
    conn.close()
    
    print(f"✅ FERTIG! Alles drin.")
    print(f"   - {count_tests} Tests generiert")
    print(f"   - {len(GRAPH_CONNECTIONS)} Cross-Connections erstellt")
    print("👉 Starte jetzt den Server neu und bewundere dein Dashboard!")

if __name__ == "__main__":
    seed_massive()