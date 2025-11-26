"""
🚀 FASTAPI WEB-SERVER FÜR KI-LERN-BUDDY
MIT SCHULKONTEXT-ENDPOINTS
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from auth import create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta
import sys
import os
import json
import sqlite3

# 🔧 Konfiguration
sys.path.append(os.path.dirname(__file__))

try:
    from universal_lern_buddy import UniversalLernBuddy
    buddy = UniversalLernBuddy()
    print("✅ KI-Lern-Buddy erfolgreich geladen!")
except Exception as e:
    print(f"❌ Fehler beim Laden des Lern-Buddys: {e}")
    buddy = None

app = FastAPI(
    title="🤖 KI-Lern-Buddy API",
    description="Intelligente Lernplattform mit KI-Personalisierung",
    version="2.0.0"
)

# CORS für Frontend-Kommunikation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Setup
security = HTTPBearer()

# === DATA MODELS ===

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    username: str
    password: str

    # Test-Modus Data Models
class TestRequest(BaseModel):
    subject: str
    topic: str
    question_count: int = 10

class TestAnswer(BaseModel):
    test_id: str
    question_index: int
    user_answer: str
    answer_type: str = "free_text"  # free_text, multiple_choice

class TestAnswerMultiple(BaseModel):
    test_id: str
    question_index: int
    user_answers: List[str]  # Liste von Antworten
    answer_type: str = "multiple_choice_multiple"

class TestSubmit(BaseModel):
    test_id: str
    answers: List[TestAnswer] = []

class ExerciseRequest(BaseModel):
    subject: str
    topic: str
    count: int = 3

class SchoolContext(BaseModel):
    grade: str
    school_type: str
    state: str = "Bayern"
    subjects: List[str] = []
    curriculum_focus: str = "allgemein"

class UserProfileUpdate(BaseModel):
    grade: Optional[str] = None
    school_type: Optional[str] = None
    state: Optional[str] = None

# === AUTHENTIFIZIERUNG ===

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """🔐 Authentifiziert User anhand JWT Token"""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    return payload

# === FRONTEND ROUTES ===

@app.get("/")
async def serve_root():
    """🏠 Serve Haupt-Frontend"""
    return FileResponse("../frontend/index.html")

@app.get("/frontend")
async def serve_frontend():
    """Alternative Route für Frontend"""
    return FileResponse("../frontend/index.html")

@app.get("/app")
async def serve_app():
    """Alternative Route für App"""
    return FileResponse("../frontend/index.html")

@app.get("/login")
async def serve_login():
    """🔐 Serve Login-Seite"""
    return FileResponse("../frontend/login.html")

@app.get("/school-setup")
async def serve_school_setup():
    """🏫 Serve Schulkonfigurations-Seite"""
    return FileResponse("../frontend/school-setup.html")

# Static Files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# === API ENDPOINTS ===

@app.get("/api/health")
async def health_check():
    """❤️ Health Check für API"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "buddy_loaded": buddy is not None
    }

@app.post("/api/register")
async def register_user(user_data: UserRegister):
    """👤 Registriert einen neuen Benutzer"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        success = buddy.create_user(
            user_data.username,
            user_data.email,
            user_data.password,
            user_data.role
        )
        
        if success:
            return {
                "success": True, 
                "message": "User erfolgreich registriert"
            }
        else:
            raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registrierungsfehler: {str(e)}")

@app.post("/api/login")
async def login_user(user_data: UserLogin):
    """🔐 Authentifiziert Benutzer und gibt Token zurück"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    user = buddy.authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    
    # Erstelle JWT Token
    access_token = create_access_token(
        data={
            "sub": user["username"], 
            "role": user["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@app.get("/api/check-auth")
async def check_auth(current_user: dict = Depends(get_current_user)):
    """🔒 Prüft ob User authentifiziert ist"""
    return {
        "success": True,
        "authenticated": True,
        "user": current_user
    }

# === SCHULKONTEXT ENDPOINTS ===

@app.post("/api/set-school-context")
async def set_school_context(
    context: SchoolContext, 
    current_user: dict = Depends(get_current_user)
):
    """🏫 Setzt Schulkontext für User"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        success = buddy.set_school_context(current_user['sub'], context.dict())
        if success:
            return {
                "success": True, 
                "message": "Schulkonfiguration gespeichert"
            }
        else:
            raise HTTPException(status_code=500, detail="Fehler beim Speichern des Schulkontexts")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@app.get("/api/school-context")
async def get_school_context(current_user: dict = Depends(get_current_user)):
    """📚 Holt Schulkontext des Users"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        context = buddy.get_school_context(current_user['sub'])
        return {"success": True, "data": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@app.patch("/api/update-profile")
async def update_user_profile(
    update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """👤 Aktualisiert User-Profil"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        success = buddy.update_user_profile(current_user['sub'], update.dict())
        return {
            "success": success,
            "message": "Profil aktualisiert" if success else "Fehler beim Update"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

# === GESCHÜTZTE API ENDPOINTS ===

@app.post("/api/generate-exercises")
async def generate_exercises(
    request: ExerciseRequest, 
    current_user: dict = Depends(get_current_user)
):
    """🎓 Generiert personalisierte Übungen"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        exercises = buddy.generate_personalized_exercises(
            current_user['sub'],
            request.subject, 
            request.topic, 
            request.count
        )
        
        return {
            "success": True, 
            "data": exercises,
            "message": f"✅ {len(exercises.get('exercises', []))} Übungen generiert"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei Übungsgenerierung: {str(e)}")

@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """👤 Holt Lernprofil des Users"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        profile = buddy.detect_learning_patterns(current_user['sub'])
        
        return {
            "success": True, 
            "data": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Profil: {str(e)}")


# === TEST-MODUS API ENDPOINTS ===

@app.post("/api/start-test")
async def start_test_session(
    test_request: TestRequest,
    current_user: dict = Depends(get_current_user)
):
    """🧪 Startet eine neue Test-Session"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        test_session = buddy.start_test_session(
            current_user['sub'],
            test_request.subject,
            test_request.topic,
            test_request.question_count
        )
        return {
            "success": True,
            "data": test_session,
            "message": f"Test gestartet mit {test_request.question_count} Fragen"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test-Fehler: {str(e)}")

@app.post("/api/submit-answer")
async def submit_answer(
    answer: TestAnswer,
    current_user: dict = Depends(get_current_user)
):
    """📝 Nimmt eine Test-Antwort entgegen (Single oder Multiple)"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        # Konvertiere Single-Antwort zu Liste für Konsistenz
        user_answers = answer.user_answer
        if isinstance(user_answers, str):
            user_answers = [user_answers]
        
        result = buddy.submit_test_answer(
            current_user['sub'],
            answer.test_id,
            answer.question_index,
            user_answers  # Jetzt eine Liste
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Antwort-Fehler: {str(e)}")


@app.post("/api/submit-answer-multiple")
async def submit_answer_multiple(
    answer: TestAnswerMultiple,
    current_user: dict = Depends(get_current_user)
):
    """📝 Nimmt mehrere Test-Antworten entgegen"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        result = buddy.submit_test_answer_multiple(
            current_user['sub'],
            answer.test_id,
            answer.question_index,
            answer.user_answers
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Antwort-Fehler: {str(e)}")

@app.post("/api/finish-test")
async def finish_test(
    finish_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """🏁 Beendet Test mit der NEUEN Methode"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        test_id = finish_data.get('test_id')
        if not test_id:
            raise HTTPException(status_code=400, detail="Test-ID fehlt")
        
        # VERWENDE DIE NEUE METHODE
        result = buddy.finish_test_session_complete(current_user['sub'], test_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test-Abschluss Fehler: {str(e)}")

@app.get("/api/test-results/{test_id}")
async def get_test_results(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """📊 Holt Testergebnisse"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        # Hier könnten wir später die Ergebnisse aus der Datenbank holen
        return {"success": True, "data": {"test_id": test_id, "message": "Ergebnisse kommen bald"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergebnis-Fehler: {str(e)}")

@app.get("/test")
async def serve_test():
    """🧪 Serve Test-Modus Seite"""
    return FileResponse("../frontend/test.html")

@app.get("/api/test-history")
async def get_test_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """📊 Holt Test-Historie des Users"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        history = buddy.get_test_history(current_user['sub'], limit)
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@app.get("/api/test-details/{test_id}")
async def get_test_details(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """📋 Holt detaillierte Ergebnisse eines Tests"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        # Können wir später implementieren - zeigt Fragen + Antworten eines alten Tests
        return {"success": True, "data": {"test_id": test_id, "message": "Details kommen bald"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

@app.post("/api/save-answer")
async def save_answer(
    answer_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """💾 Speichert eine Antwort in der Datenbank"""
    if not buddy:
        raise HTTPException(status_code=500, detail="Lern-Buddy nicht geladen")
    
    try:
        success = buddy.save_answer(
            current_user['sub'],
            answer_data.get('test_id'),
            answer_data.get('question_index'),
            answer_data.get('user_answers', [])
        )
        return {"success": success, "message": "Antwort gespeichert" if success else "Fehler beim Speichern"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speicher-Fehler: {str(e)}")

@app.get("/api/debug-test/{test_id}")
async def debug_test(test_id: str):
    """🔍 Debug-Endpoint für Test-Daten (ohne Authentifizierung)"""
    try:
        print(f"🔍 DEBUG TEST AUFGERUFEN FÜR: {test_id}")
        
        # Direkter Datenbank-Zugriff für Debugging
        conn = sqlite3.connect("universal_lern_buddy.db", timeout=20.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_id, subject, topic, questions, user_answers, total_questions, 
                   start_time, status, score, correct_answers
            FROM test_sessions WHERE test_id = ?
        ''', (test_id,))
        
        test_data = cursor.fetchone()
        conn.close()
        
        if test_data:
            debug_info = {
                "test_id": test_data[0],
                "subject": test_data[1],
                "topic": test_data[2],
                "questions_length": len(test_data[3]) if test_data[3] else 0,
                "user_answers": test_data[4],
                "total_questions": test_data[5],
                "status": test_data[7],
                "score": test_data[8],
                "correct_answers": test_data[9]
            }
            
            # Versuche Fragen zu parsen
            if test_data[3]:
                try:
                    questions = json.loads(test_data[3])
                    debug_info["questions_type"] = type(questions).__name__
                    if isinstance(questions, dict) and 'exercises' in questions:
                        debug_info["exercises_count"] = len(questions['exercises'])
                        if questions['exercises']:
                            debug_info["sample_question"] = questions['exercises'][0].get('question', '')[:100] + "..."
                            debug_info["sample_options"] = list(questions['exercises'][0].get('options', {}).keys())[:3]
                            debug_info["sample_correct"] = questions['exercises'][0].get('correct_answers', [])
                    else:
                        debug_info["questions_structure"] = "Unbekannte Struktur"
                except Exception as e:
                    debug_info["questions_error"] = str(e)
            
            # Versuche Antworten zu parsen
            if test_data[4] and test_data[4] != '[]':
                try:
                    user_answers = json.loads(test_data[4])
                    debug_info["user_answers_parsed"] = user_answers
                    debug_info["user_answers_count"] = len(user_answers)
                except Exception as e:
                    debug_info["user_answers_error"] = str(e)
            
            return {"success": True, "debug_info": debug_info}
        else:
            return {"success": False, "error": "Test nicht gefunden"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# === START-SKRIPT ===

if __name__ == "__main__":
    import uvicorn
    
    print("🤖 Starte KI-Lern-Buddy Server...")
    print("📍 API Dokumentation: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000")
    print("🔐 Login: http://localhost:8000/login")
    print("🏫 Schulkonfig: http://localhost:8000/school-setup")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True
    )