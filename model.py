from rich.table import Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, SmallInteger, DateTime, func, Date


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "d_user"
    id = Column(Integer, primary_key=True, index=True)
    public_name = Column(String)


class Skill(Base):
    __tablename__ = "skill"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("d_user.id"))
    skill = Column(String)
    is_active = Column(Boolean)
    start_from = Column(Date)


class Characteristic(Base):
    __tablename__ = "characteristic"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("d_user.id"))
    characteristic = Column(String)
    is_active = Column(Boolean)
    start_from = Column(Date)


class Score(Base):
    __tablename__ = "score"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("d_user.id"))
    score = Column(SmallInteger)
    description = Column(String)


class Action(Base):
    __tablename__ = "action"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    user_id = Column(ForeignKey("d_user.id"))
    score_id = Column(ForeignKey("score.id"))
    is_active = Column(Boolean)


class ActionJournal(Base):
    __tablename__ = "action_journal"
    id = Column(Integer, primary_key=True, index=True)
    dt = Column(DateTime, default=func.now())
    user_id = Column(ForeignKey("d_user.id"))
    action_id = Column(ForeignKey("action.id"))


class ActionSkill(Base):
    __tablename__ = "action_skill"
    skill_id = Column(ForeignKey("skill.id"), primary_key=True)
    action_id = Column(ForeignKey("action.id"), primary_key=True)
    user_id = Column(ForeignKey("d_user.id"), primary_key=True)


class ActionCharacteristic(Base):
    __tablename__ = "action_characteristic"
    characteristic_id = Column(ForeignKey("characteristic.id"), primary_key=True)
    action_id = Column(ForeignKey("action.id"), primary_key=True)
    user_id = Column(ForeignKey("d_user.id"), primary_key=True)


class SkillResults(Base):
    __tablename__ = "skill_results"
    skill_id = Column(ForeignKey("skill.id"), primary_key=True)
    dt = Column(Date, primary_key=True)
    score_change = Column(String)
    type_change = Column(String)
    changed = Column(DateTime, default=func.now())

class CharacteristicResults(Base):
    __tablename__ = "characteristic_results"
    characteristic_id = Column(ForeignKey("characteristic.id"), primary_key=True)
    dt = Column(Date, primary_key=True)
    score_change = Column(String)
    type_change = Column(String)
    changed = Column(DateTime, default=func.now())
