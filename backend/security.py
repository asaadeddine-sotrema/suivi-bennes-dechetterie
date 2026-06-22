"""Primitives de sécurité : hachage de mot de passe (bcrypt) et jetons JWT."""
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from backend.config import settings

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Décode et valide le jeton. Lève jwt.PyJWTError si invalide/expiré."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
