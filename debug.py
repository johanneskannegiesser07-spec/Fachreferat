import sys
import os
import json

# Pfade setzen, damit Python die Backend-Module findet
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from backend.universal_lern_buddy import UniversalLernBuddy
    from backend.database import DatabaseManager
except ImportError as e:
    print(f"❌ Import Fehler: {e}")
    print("Stelle sicher, dass du das Skript im Hauptordner 'Fachreferat' ausführst!")
    sys.exit(1)

# Benutzername (Hier deinen exakten Login-Namen eintragen!)
USERNAME = "demo"  # <--- ÄNDERE DAS ZU DEINEM NAMEN

def debug_knowledge_graph():
    print(f"🔍 DEBUGGING GRAPH FÜR: {USERNAME}")
    
    # 1. Datenbank Verbindung testen
    db_path = os.path.join(os.getcwd(), 'backend', 'universal_lern_buddy.db')
    print(f"📂 Datenbank: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ FEHLER: Datenbank-Datei nicht gefunden!")
        return

    # 2. Buddy initialisieren
    try:
        buddy = UniversalLernBuddy(db_path)
        print("✅ Buddy System geladen.")
    except Exception as e:
        print(f"❌ CRASH beim Laden von Buddy: {e}")
        return

    # 3. User Hash holen
    try:
        user_hash = buddy.db.get_user_hash(USERNAME)
        print(f"🔑 User Hash: {user_hash}")
    except Exception as e:
        print(f"❌ Fehler beim User-Hash: {e}")
        return

    # 4. Rohe Statistik aus DB holen (Test auf leere Daten)
    try:
        stats = buddy.db.get_topic_performance(user_hash)
        print(f"📊 Gefundene Themen-Einträge: {len(stats)}")
        for row in stats:
            print(f"   - {row[0]}: {row[1]} (Score: {row[2]})")
            
        if len(stats) == 0:
            print("⚠️ WARNUNG: Keine Test-Daten für diesen User gefunden!")
            print("   -> Hast du seed_data.py mit dem richtigen Namen ausgeführt?")
    except Exception as e:
        print(f"❌ CRASH bei DB-Abfrage get_topic_performance: {e}")
        return

    # 5. Die kritische Graph-Funktion aufrufen (Hier passiert der Fehler meistens!)
    print("\n🕸️ Versuche Graphen zu generieren...")
    try:
        graph_data = buddy.get_knowledge_graph_data(USERNAME)
        
        node_count = len(graph_data.get('nodes', []))
        edge_count = len(graph_data.get('edges', []))
        
        print(f"✅ ERFOLG! Graph generiert.")
        print(f"   - Knoten: {node_count}")
        print(f"   - Verbindungen: {edge_count}")
        
        if node_count <= 1:
            print("⚠️ Graph enthält nur den Root-Knoten. Frontend zeigt evtl. Fehler an.")
            
    except Exception as e:
        print(f"\n🔥🔥🔥 HIER IST DER FEHLER 🔥🔥🔥")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")

if __name__ == "__main__":
    debug_knowledge_graph()