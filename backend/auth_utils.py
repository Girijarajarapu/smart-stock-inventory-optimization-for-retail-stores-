# auth_utils.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

pwd_ctx = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)


def create_jwt(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=3)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
