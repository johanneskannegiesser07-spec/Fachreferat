import sqlite3
import sys
import os

# Pfad zur Datenbank (angenommen wir sind im backend ordner)
DB_PATH = "universal_lern_buddy.db"

def add_gems(username, amount):
    if not os.path.exists(DB_PATH):
        print(f"❌ Fehler: Datenbank '{DB_PATH}' nicht gefunden! Bist du im richtigen Ordner?")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. User suchen (Direkt über username, user_hash Spalte existiert hier nicht)
        # Wir holen auch XP dazu, nur zur Info
        cursor.execute("SELECT gems, xp FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ Fehler: User '{username}' nicht gefunden!")
            return

        current_gems = row[0] if row[0] is not None else 0
        current_xp = row[1] if row[1] is not None else 0
        
        new_gems = current_gems + amount
        
        # 2. Update durchführen (Wieder über username identifizieren)
        cursor.execute("UPDATE users SET gems = ? WHERE username = ?", (new_gems, username))
        conn.commit()
        
        print(f"✅ Erfolg! User '{username}'")
        print(f"   💎 Gems: {current_gems} -> {new_gems}")
        print(f"   ✨ XP:   {current_xp}")
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("--- CHEAT TOOL 💎 ---")
        print("Verwendung: python test.py [username] [anzahl_gems]")
        print("Beispiel:   python test.py Johannes 100")
        print("---------------------")
    else:
        # Argumente lesen
        user = sys.argv[1]
        try:
            amount = int(sys.argv[2])
            add_gems(user, amount)
        except ValueError:
            print("❌ Fehler: Die Anzahl muss eine ganze Zahl sein!")


def show_gems(username, show):
    if not os.path.exists(DB_PATH):
        print(f"❌ Fehler: Datenbank '{DB_PATH}' nicht gefunden! Bist du im richtigen Ordner?")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if show == true:
        try:
            # User suchen
            cursor.execute("SELECT gems, xp FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if not row:
                print(f"❌ Fehler: User '{username}' nicht gefunden!")
                return

            current_gems = row[0] if row[0] is not None else 0
            current_xp = row[1] if row[1] is not None else 0
            
            if show:
                print(f"ℹ️ User '{username}':")
                print(f"   💎 Gems: {current_gems}")
                print(f"   ✨ XP:   {current_xp}")
            
        except Exception as e:
            print(f"❌ Datenbank-Fehler: {e}")
        finally:
            conn.close()