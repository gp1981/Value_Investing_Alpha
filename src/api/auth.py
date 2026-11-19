import os
import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import jwt

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "alpha-terminal-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

USERS_FILE = os.path.join(os.getenv("EDGAR_LOCAL_DATA_DIR", "output"), "users.json")

def _load_users() -> Dict[str, dict]:
    """Loads users from local JSON storage."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_users(users: Dict[str, dict]):
    """Saves users to local JSON storage."""
    os.makedirs(os.path.dirname(os.path.abspath(USERS_FILE)), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hashes a password with salt using PBKDF2 HMAC SHA-256."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verifies a password against its salt and PBKDF2 hash."""
    test_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(test_hash, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Looks up a user record by email."""
    users = _load_users()
    return users.get(email.lower().strip())

def register_user(email: str, password: str, full_name: str = "") -> dict:
    """Registers a new user."""
    clean_email = email.lower().strip()
    users = _load_users()
    if clean_email in users:
        raise ValueError("User with this email already exists")

    hashed_pw, salt = hash_password(password)
    user_record = {
        "email": clean_email,
        "full_name": full_name or clean_email.split("@")[0],
        "hashed_password": hashed_pw,
        "salt": salt,
        "tier": "FREE",  # FREE or PRO
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users[clean_email] = user_record
    _save_users(users)
    return user_record

# Seed demo user if no users exist
def initialize_default_users():
    users = _load_users()
    if not users:
        register_user("analyst@example.com", "valuealpha2026", "Lead Analyst")
