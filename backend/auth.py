import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# Konfiguration
SECRET_KEY = os.getenv("SECRET_KEY", "lern-buddy-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 Tage

# Password Hashing Konfiguration (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Sichere Überprüfung mit bcrypt"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Sicheres Hashing mit bcrypt.
    """
    # DEBUG-AUSGABE: Zeigt uns, wie lang das Passwort ist, das gehasht wird
    print(f"🔐 DEBUG: Hashing password... Länge: {len(password)} Zeichen")
    
    # WICHTIG: Hier darf NUR 'password' stehen, kein '+ SECRET_KEY'!
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Erstellt ein JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Überprüft ein JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None