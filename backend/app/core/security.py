import hashlib
import base64
from datetime import datetime, timedelta, timezone
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def _get_aes_key() -> bytes:
    return hashlib.sha256(settings.AES_KEY.encode()).digest()


def encrypt_api_key(plain: str) -> str:
    key = _get_aes_key()
    cipher = AES.new(key, AES.MODE_CBC, iv=key[:16])
    padded = pad(plain.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode()


def decrypt_api_key(encrypted: str) -> str:
    key = _get_aes_key()
    cipher = AES.new(key, AES.MODE_CBC, iv=key[:16])
    decrypted = cipher.decrypt(base64.b64decode(encrypted))
    return unpad(decrypted, AES.block_size).decode()


def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:3]}****{key[-4:]}"
