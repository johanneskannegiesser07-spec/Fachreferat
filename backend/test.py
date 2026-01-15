import sqlite3
import sys

# Konfiguration
DB_PATH = "universal_lern_buddy.db"

def add_gems(username, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User finden (wir brauchen den hash, aber suchen per Name)
    # Annahme: username ist in user_profiles oder wir suchen in users
    # In deiner DB Struktur speicherst du Hash -> Username mapping meist in user_profiles
    # Aber users Tabelle hat meist username spalte. Wir prüfen das kurz.
    
    # Wir suchen den User einfach direkt
    try:
        # 1. User suchen
        cursor.execute("SELECT user_hash, gems FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ Fehler: User '{username}' nicht gefunden!")
            return

        user_hash, current_gems = row
        new_gems = current_gems + amount
        
        # 2. Update durchführen
        cursor.execute("UPDATE users SET gems = ? WHERE user_hash = ?", (new_gems, user_hash))
        conn.commit()
        
        print(f"✅ Erfolg! {username} hat jetzt {new_gems} Gems (+{amount}).")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Verwendung: python cheat.py [username] [anzahl_gems]")
        print("Beispiel:   python cheat.py Johannes 100")
    else:
        add_gems(sys.argv[1], int(sys.argv[2]))