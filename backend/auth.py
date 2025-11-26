# backend/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "lern-buddy-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 Tage

def verify_password(plain_password, hashed_password):
    """Vereinfachte Passwort-Überprüfung"""
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password):
    """Vereinfachtes Hashing - für Produktion bcrypt verwenden!"""
    return hashlib.sha256(f"{password}{SECRET_KEY}".encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_db_connection(db_path: str):
    """Sichere Datenbank-Verbindung mit Timeout"""
    return sqlite3.connect(db_path, timeout=20.0)