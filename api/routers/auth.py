import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
import hashlib
from config import AUTH_DB_FILE

def init_db():
    conn = sqlite3.connect(AUTH_DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password, salt):
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

def verify_user(email, password):
    conn = sqlite3.connect(AUTH_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, email, salt, password_hash FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    if user:
        user_id, name, user_email, salt, password_hash = user
        if password_hash == hash_password(password, salt):
            return {"id": user_id, "name": name, "email": user_email}
    return None

def register_user(name, email, password):
    conn = sqlite3.connect(AUTH_DB_FILE)
    c = conn.cursor()
    try:
        import os
        salt = os.urandom(16).hex()
        pwd_hash = hash_password(password, salt)
        created_at = datetime.now().isoformat(timespec="seconds")
        c.execute(
            "INSERT INTO users (name, email, salt, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, salt, pwd_hash, created_at),
        )
        conn.commit()
        return True, "Akun berhasil dibuat. Silakan login."
    except sqlite3.IntegrityError:
        return False, "Email sudah terdaftar."
    finally:
        conn.close()

import os

router = APIRouter()
init_db()

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-maggot-key-for-local-dev-only")
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
def login(req: LoginRequest):
    user = verify_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email atau password salah")
    
    access_token = create_access_token(data={"sub": user["email"], "name": user["name"], "user_id": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/register")
def register(req: RegisterRequest):
    success, msg = register_user(req.name, req.email, req.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}
