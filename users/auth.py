from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from setting import get_auth_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from setting import get_db_url
from users.models import User
from fastapi import Depends

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt

def authenticate_user(password: str, hash_pass: str):

    if verify_password(plain_password=password, hashed_password=hash_pass) is False:
        return None
    return True

