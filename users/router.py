from fastapi import APIRouter, HTTPException, status
from users.auth import get_password_hash
from users.schemas import SUserRegister
from users.models import User
from fastapi import Depends
from sqlalchemy.orm import sessionmaker, Session
from setting import get_db_url
from sqlalchemy import create_engine


router = APIRouter(prefix='/auth', tags=['Auth'])

engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register/")
def register_user(user_data: SUserRegister, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == user_data.email).all()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь уже существует'
        )

    user_pass = get_password_hash(user_data.password)

    new_user = User(public_name = user_data.public_name, first_name = user_data.first_name, email = user_data.email,
                    password = user_pass)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {'message': 'Вы успешно зарегистрированы!'}
