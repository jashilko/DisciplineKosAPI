from fastapi import APIRouter, HTTPException, status
from users.auth import get_password_hash
from users.schemas import SUserRegister, SUserAuth
from users.models import User
from fastapi import Depends
from sqlalchemy.orm import sessionmaker, Session
from setting import get_db_url
from sqlalchemy import create_engine
from users.auth import authenticate_user, create_access_token
from fastapi.responses import Response
from users.dependencies import get_current_user


router = APIRouter(prefix='/auth', tags=['Auth'])

engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me/")
def get_me(user_data: User = Depends(get_current_user)):
    return user_data

@router.post("/logout/")
def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}

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

@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        check = authenticate_user(password=user_data.password, hash_pass=user.password)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Неверная почта или пароль')
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    access_token = create_access_token({"sub": str(user.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}
