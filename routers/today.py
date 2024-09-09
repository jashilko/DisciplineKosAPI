import os
from fastapi import APIRouter, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from model import Characteristic

router = APIRouter(
    prefix="/api/today",
    tags=["Статистика дня"],
)

engine = create_engine('postgresql+psycopg2://{}:{}@{}/{}'.
                       format(os.environ.get('DB_USER'),
                              os.environ.get('DB_PASSWORD'),
                              os.environ.get('DB_HOST'),
                              os.environ.get('DB_NAME')))
SessionLocal = sessionmaker(autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/skills/used", description="Навыки, которые качались сегодня", summary="саммфри")
def get_today_skills_used(db: Session = Depends(get_db)):
    return db.query(Characteristic).filter(Characteristic.user_id == 1).all()