from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import json
import os
from dotenv import load_dotenv

# Lade den API Key aus deiner .env Datei
load_dotenv()

app = FastAPI()

# CORS für das Frontend erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuizRequest(BaseModel):
    thema: str

@app.get("/index")
async def read_index():
    return FileResponse("mini_frontend.html")

@app.post("/api/generate-quiz")
async def generate_quiz(request: QuizRequest):
    thema = request.thema
    
    # --- 1. PROMPT ENGINEERING ---
    prompt = f"""
    Erstelle EINE mittelschwere Multiple-Choice-Frage zum Thema '{thema}'.
    Antworte AUSSCHLIESSLICH in diesem exakten JSON-Format, ohne Markdown oder zusätzlichen Text:
    {{
        "frage": "Hier steht die Frage?",
        "antworten": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "korrekter_index": 2,
        "erklaerung": "Hier eine kurze Erklärung, warum das richtig ist."
    }}
    """
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "API Key fehlt! Bitte .env Datei prüfen."}

    # --- 2. DATENPAKET FÜR DIE API BAUEN ---
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Wir nutzen hier das kostenlose Deepseek-Modell über OpenRouter
    data = {
        "model": "openrouter/free", 
        "messages": [
            {"role": "system", "content": "You are a strict JSON generator. Output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    
    # --- 3. API AUFRUF UND JSON ROUTING ---
    try:
        print(f"📞 Kontaktiere KI für das Thema: {thema}...")
        
        # Sende die Daten an die externe API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status() # Prüft, ob der Server Fehler meldet (z.B. 401 Unauthorized)
        
        # Extrahiere den reinen Text der KI
        ki_text = response.json()['choices'][0]['message']['content']
        
        # Sicherheits-Reinigung: Falls die KI trotzdem Markdown (```json ... ```) mitschickt
        clean_text = ki_text.replace("```json", "").replace("```", "").strip()
        
        # String in ein echtes JSON/Python-Objekt umwandeln und ans Frontend senden
        quiz_daten = json.loads(clean_text)
        print("✅ Frage erfolgreich generiert und weitergeleitet!")
        return quiz_daten
        
    except Exception as e:
        print(f"❌ Fehler beim API-Aufruf: {e}")
        return {
            "error": "Die KI konnte die Frage nicht generieren.",
            "details": str(e)
        }