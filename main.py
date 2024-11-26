from hmac import new

import psycopg2
import os
from fastapi import FastAPI, Depends
from sqlalchemy.sql import text
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, Session
from model import (User, Skill, Score, ActionJournal, ActionSkill, ActionCharacteristic, Characteristic, Action,
                   SkillResults, CharacteristicResults)
from schemas import (SSkill, SSkillAdd, SAction, SActionJournal, SActionAddWithLinkSkillsAndCharact,
                     SCharactiristic, SSkillWAction, SCharacteristicWAction, SActionEditWithLinkSkillsAndCharact,
                     SShortAction, SAllSkillCharScores)
from os import environ
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
# import datetime
from datetime import date, timedelta
from users.router import router as router_users

from routers.today import router as today_router

dotenv_path = 'env.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# создаем движок SqlAlchemy
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



app = FastAPI()
app.include_router(router_users)

@app.get("/")
async def main():
    return FileResponse("public/index.html")

# app.include_router(today_router)
@app.get('/hello')
def hello_world1():
    return "<h1>Hello, FastAPI!<h1>"

@app.get('/db')
def hello_world(db: Session = Depends(get_db)):
    db_version = db.execute("SELECT version();").fetchone()
    return f"Hello, World! Database version: {db_version}"

@app.get("/api/skills", description="",
         summary="Только скилы", tags=["Посмотреть"])
def get_skills(db: Session = Depends(get_db)) -> list[SSkill]:
    return db.query(Skill).filter(Skill.user_id == 1).all()


@app.get("/api/skills_w_action", description="",
         summary="Скилы с действиями, которые их качают", tags=["Посмотреть"])
def get_skills_w_action(db: Session = Depends(get_db)) -> list[SSkillWAction]:
    list_skill_w_action = []
    skills = db.query(Skill.id, Skill.skill).filter(Skill.user_id == 1).all()
    for one_skills in skills:
        act_list = (db.query(Action.id, Action.action, Score.score).
                    join(Score, Action.score_id == Score.id).
                    join(ActionSkill, Action.id == ActionSkill.action_id).
                    filter(and_(Action.user_id == 1, Action.is_active == True, ActionSkill.skill_id == one_skills[0])).
                    all())
        actl = []
        for one_act in act_list:
            act = SAction(id=one_act[0], action=one_act[1], score=one_act[2])
            actl.append(act)
        skill = SSkillWAction(id_skill=one_skills[0], skill=one_skills[1], actions=actl)
        list_skill_w_action.append(skill)
    return list_skill_w_action


@app.post("/api/skills/add", description="",
          summary="Добавить скилл", tags=["Записать"])
def add_skill(newskill: SSkillAdd, db: Session = Depends(get_db)):
    new_skill = Skill(user_id=1, skill=newskill.skill)
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill


# TODO 1. mvp get: показать все активности
@app.get("/api/actions", description="",
         summary="Действия", tags=["Посмотреть"])
def get_action(db: Session = Depends(get_db)) -> list[SAction]:
    actionn = []
    # временный пример данных
    # actionn = [SAction(id=1, user_id=1, action="Пробежка11", score=2),
    #            SAction(id=2, user_id=1, action="Сериал на английском", score=2),
    #            SAction(id=3, user_id=1, action="Алкоголь", score=-1)]
    # Реальный запрос данных
    all_action = db.query(Action.id, Action.user_id, Action.action, Score.score).join(
        Score, Action.score_id == Score.id, isouter=True).filter(
        and_(Action.is_active == True, Action.user_id == 1)).all()
    for one_action in all_action:
        temp_action = SAction(id=one_action[0], user_id=one_action[1], action=one_action[2], score=one_action[3])
        actionn.append(temp_action)
    # print(all_action)
    return actionn


@app.post("/api/action/addwith", description="",
          summary="Добавить действие и его влияние на скилы и характеристики", tags=["Записать"])
def add_action_with(action_with: SActionAddWithLinkSkillsAndCharact, db: Session = Depends(get_db)):
    score_id = db.query(Score.id).filter(Score.score == action_with.score).first()
    if score_id == None:
        return JSONResponse(content={"message": "Нет такой оценки. "}, status_code=400)
    else:
        action = Action(action=action_with.action, user_id=1, is_active=True, score_id=score_id[0])
        db.add(action)
        db.commit()
        db.refresh(action)
        print(action.id)
        for one_skill in action_with.skills_list:
            db.add(ActionSkill(skill_id=one_skill, action_id=action.id, user_id=1))
            db.commit()
        for one_characteristic in action_with.characteristic:
            db.add(ActionCharacteristic(characteristic_id=one_characteristic, action_id=action.id, user_id=1))
            db.commit()
    return JSONResponse(content={"message": "Действие добавлено"})


@app.put("/api/action/editwith", description="",
         summary="Изменить действие и его влияние на скилы и характеристики", tags=["Записать"])
def edit_action_with(action_with: SActionEditWithLinkSkillsAndCharact, db: Session = Depends(get_db)):
    score_id = db.query(Score.id).filter(Score.score == action_with.score).first()
    one_action = db.query(Action).filter(Action.id == action_with.id).first()
    if one_action is None:
        return JSONResponse(content={"message": "Нет такого действия."}, status_code=400)
    if score_id is None:
        return JSONResponse(content={"message": "Нет такой оценки."}, status_code=400)

    one_action.id = action_with.id
    one_action.action = action_with.action
    one_action.score_id = score_id[0]
    # db.commit()
    # db.refresh(one_action)
    db.query(ActionSkill).filter(ActionSkill.action_id == action_with.id).delete(synchronize_session=False)

    # db.commit()
    db.query(ActionCharacteristic).filter(ActionCharacteristic.action_id == action_with.id).delete(
        synchronize_session=False)
    # db.commit()
    for one_skill in action_with.skills_list:
        db.add(ActionSkill(skill_id=one_skill, action_id=one_action.id, user_id=1))
        db.commit()
    for one_characteristic in action_with.characteristic:
        db.add(ActionCharacteristic(characteristic_id=one_characteristic, action_id=one_action.id, user_id=1))
        db.commit()
    return JSONResponse(content={"message": "Action edit sucsessful"})


@app.get("/api/characteristics", description="",
         summary="Только характеристики", tags=["Посмотреть"])
def get_characteristics(db: Session = Depends(get_db)) -> list[SCharactiristic]:
    return db.query(Characteristic).filter(Characteristic.user_id == 1).all()


@app.get("/api/characteristics_w_action", description="",
         summary="Характеристики с действиями, которые их качают", tags=["Посмотреть"])
def get_characteristics_w_action(db: Session = Depends(get_db)) -> list[SCharacteristicWAction]:
    list_char_w_action = []
    chars = db.query(Characteristic.id, Characteristic.characteristic).filter(Characteristic.user_id == 1).all()
    print(chars)
    for one_char in chars:
        act_list = (db.query(Action.id, Action.action, Score.score).
                    join(Score, Action.score_id == Score.id).
                    join(ActionCharacteristic, Action.id == ActionCharacteristic.action_id).
                    filter(
            and_(Action.user_id == 1, Action.is_active == True, ActionCharacteristic.characteristic_id == one_char[0])).
                    all())
        actl = []
        for one_act in act_list:
            act = SAction(id=one_act[0], action=one_act[1], score=one_act[2])
            actl.append(act)
        char = SCharacteristicWAction(id=one_char[0], characteristic=one_char[1], actions=actl)
        list_char_w_action.append(char)
    return list_char_w_action


# TODO 2. mvp post: записать данные в журнал
@app.post("/api/journal/add", description="",
          summary="Добавить действие сегодняшнее", tags=["Записать"])
def create_action(action_journal: SActionJournal, db: Session = Depends(get_db)):
    if not action_journal.pdt:
        act_jor = ActionJournal(user_id=1, action_id=action_journal.action_id)
    else:
        act_jor = ActionJournal(user_id=1, action_id=action_journal.action_id, dt = action_journal.pdt)
    db.add(act_jor)
    db.commit()
    db.refresh(act_jor)
    return act_jor


# TODO 3. mvp get: получить Dashboard по навыкам и способностям
@app.get("/api/today/action", description="Что делал сегодня",
         summary="Что делал сегодня", tags=["Статистика дня"])
def get_today_action(db: Session = Depends(get_db)) -> list[SShortAction]:
    all_action = (
        db.query(ActionJournal.action_id.label('id'), Action.action)
        .join(Action)
        .filter(and_(ActionJournal.dt >= date.today(), ActionJournal.user_id == 1)).all()

    )
    # dict_a = [SShortAction(id=one_action[0], action=one_action[1]) for one_action in all_action]
    dict_a = [SShortAction.model_validate(one_action) for one_action in all_action]
    return dict_a


@app.get("/api/today/skills/used", description="Навыки, которые качались сегодня",
         summary="Навыки, которые качались сегодня", tags=["Статистика дня"])
def get_today_skills_used(db: Session = Depends(get_db)):
    all_skills = (db.query(Skill)
                  .filter(and_(Skill.is_active == True, Skill.user_id == 1))).all()
    print(all_skills)
    dict_skill = []
    for one_skill in all_skills:

        skill_active = (
            db.query(func.count(Score.id), func.sum(Score.score)).
            join(Action, Score.id == Action.score_id).
            join(ActionJournal, ActionJournal.action_id == Action.id).
            join(ActionSkill, ActionSkill.action_id == Action.id).
            having(func.count(Score.id) > 0).
            filter(and_(ActionSkill.skill_id == one_skill.id, ActionJournal.user_id == 1,
                        ActionJournal.dt >= date.today()))
        )
        if skill_active.first():
            dict_skill.append({"skill_id": one_skill.id, "skill": one_skill.skill,
                               "count": skill_active.first()[0], "sum_score": skill_active.first()[1]})
        print(dict_skill)
    return dict_skill


@app.get("/api/today/characteristic/used", description="Характеристики, которые качались сегодня",
         summary="Характеристики, которые качались сегодня", tags=["Статистика дня"])
def get_today_characteristic_used(db: Session = Depends(get_db)):
    all_char = (db.query(Characteristic)
                .filter(and_(Characteristic.is_active == True, Characteristic.user_id == 1))).all()
    print(all_char)
    dict_skill = []
    for one_char in all_char:

        skill_active = (
            db.query(func.count(Score.id), func.sum(Score.score)).
            join(Action, Score.id == Action.score_id).
            join(ActionJournal, ActionJournal.action_id == Action.id).
            join(ActionCharacteristic, ActionCharacteristic.action_id == Action.id).
            having(func.count(Score.id) > 0).
            filter(and_(ActionCharacteristic.characteristic_id == one_char.id, ActionJournal.user_id == 1,
                        ActionJournal.dt >= date.today()))
        )
        if skill_active.first():
            dict_skill.append({"characteristic_id": one_char.id, "characteristic": one_char.characteristic,
                               "count": skill_active.first()[0], "sum_score": skill_active.first()[1]})
        print(dict_skill)
    return dict_skill


@app.get("/api/today/skills/failed", description="Проваленные навыки сегодня",
         summary="Проваленные навыки сегодня", tags=["Статистика дня"])
def get_today_skills_failed(db: Session = Depends(get_db)):
    all_skills = (db.query(Skill)
                  .filter(and_(Skill.is_active == True, Skill.user_id == 1))).all()
    print(all_skills)
    dict_skill = []
    for one_skill in all_skills:

        skill_active = (
            db.query(func.count(Score.id), func.sum(Score.score)).
            join(Action, Score.id == Action.score_id).
            join(ActionJournal, ActionJournal.action_id == Action.id).
            join(ActionSkill, ActionSkill.action_id == Action.id).
            having(func.count(Score.id) == 0).
            filter(and_(ActionSkill.skill_id == one_skill.id, ActionJournal.user_id == 1,
                        ActionJournal.dt >= date.today()))
        )
        if skill_active.first():
            dict_skill.append({"skill_id": one_skill.id, "skill": one_skill.skill})
        print(dict_skill)
    return dict_skill


@app.get("/api/today/characteristic/failed", description="Проваленные сегодня характеристики",
         summary="Проваленные сегодня характеристики", tags=["Статистика дня"])
def get_today_characteristic_failed(db: Session = Depends(get_db)):
    all_char = (db.query(Characteristic)
                .filter(and_(Characteristic.is_active == True, Characteristic.user_id == 1))).all()
    print(all_char)
    dict_skill = []
    for one_char in all_char:

        skill_active = (
            db.query(func.count(Score.id), func.sum(Score.score)).
            join(Action, Score.id == Action.score_id).
            join(ActionJournal, ActionJournal.action_id == Action.id).
            join(ActionCharacteristic, ActionCharacteristic.action_id == Action.id).
            having(func.count(Score.id) == 0).
            filter(and_(ActionCharacteristic.characteristic_id == one_char.id, ActionJournal.user_id == 1,
                        ActionJournal.dt >= date.today()))
        )
        if skill_active.first():
            dict_skill.append({"characteristic_id": one_char.id, "characteristic": one_char.characteristic})
        print(dict_skill)
    return dict_skill


def set_penalty(db, curr_date, curr_score, skill_id, failed_days):
    rec = db.query(SkillResults).filter(
        and_(SkillResults.skill_id == skill_id, SkillResults.dt == curr_date)).one_or_none()
    new_score = curr_score
    if failed_days == 180:
        new_score = 0
    elif failed_days == 120:
        new_score = curr_score - curr_score * 0.9
    elif failed_days == 60:
        new_score = curr_score - curr_score * 0.75
    elif failed_days == 30:
        new_score = curr_score - curr_score * 0.5
    elif failed_days == 21:
        new_score = curr_score - curr_score * 0.2
    elif failed_days == 14:
        new_score = curr_score - curr_score * 0.1
    elif failed_days == 7:
        new_score = curr_score - 1
    new_score = round(max(new_score, 0))
    print("set_penalty: Старый - {}, новый - {} скор".format(curr_score, new_score))
    if not rec:
        print("записываем новый штраф: ", skill_id, curr_date, new_score)
        if new_score < curr_score:
            new_rec = SkillResults(skill_id=skill_id, dt=curr_date, score_change=new_score, type_change="pen")
        else:
            new_rec = SkillResults(skill_id=skill_id, dt=curr_date, score_change=new_score)
        db.add(new_rec)
    else:
        print("правим штраф: ", skill_id, curr_date, new_score)
        if new_score < curr_score:
            rec.score_change = new_score
            rec.type_change = "pen"
            rec.changed = func.now()
        else:  # когда штраф не начислен
            if rec.type_change != "":
                rec.type_change = ""
                rec.changed = func.now()
    return new_score


# Записать балл
def set_reward(db, curr_date, add_score, curr_score, skill_id):
    rec = db.query(SkillResults).filter(
        and_(SkillResults.skill_id == skill_id, SkillResults.dt == curr_date)).one_or_none()
    new_score = curr_score + min(add_score, 2)
    print("Старый - {}, новый - {} скор, добавляемый - {}".format(curr_score, new_score, add_score))
    if not rec:
        print("записываем новый скор: ", skill_id, curr_date, new_score)
        new_rec = SkillResults(skill_id=skill_id, dt=curr_date, score_change=new_score, type_change="add")
        db.add(new_rec)

    else:
        print("правим скор: ", skill_id, curr_date, new_score)
        if rec.score_change != new_score or rec.type_change != "add":
            rec.score_change = new_score
            rec.type_change = "add"
            rec.changed = func.now()
    return new_score


# расчитать скор на каждый день по одному скилу
def calc_one_skill_all_date(id, skill_name, skill_start_date):
    db = SessionLocal()

    all_journal = (
        db.query(func.count(Score.id), func.sum(Score.score), func.date(ActionJournal.dt).label("dt")).
        join(Action, Score.id == Action.score_id).
        join(ActionJournal, ActionJournal.action_id == Action.id).
        join(ActionSkill, ActionSkill.action_id == Action.id).group_by(func.date(ActionJournal.dt)).
        filter(and_(ActionSkill.skill_id == id, ActionJournal.user_id == 1)).order_by(func.date(ActionJournal.dt))
    )
    curr_date = skill_start_date
    curr_srore = 0
    for one in all_journal:
        curr_failed_days = 0
        print("Запись журнала: ", one[2])
        # Проверяем какая дельта
        diff_day = (one[2] - curr_date).days
        if diff_day == 0:  # Были действия
            print("Были активности в дату: : ", curr_date)
            curr_srore = set_reward(db, curr_date, one[1], curr_srore, id)
            curr_date += timedelta(days=1)
        elif diff_day > 0:
            while curr_date < one[2]:
                print("Начисляем штраф за: ", curr_date)
                curr_failed_days += 1
                curr_srore = set_penalty(db, curr_date, curr_srore, id, curr_failed_days)
                curr_date += timedelta(days=1)
            if curr_date == one[2]:
                print("Были активности в дату 2: ", curr_date)
                curr_srore = set_reward(db, curr_date, one[1], curr_srore, id)
                curr_date += timedelta(days=1)
            continue
        else:
            curr_date += timedelta(days=1)
            print("Как мы тут блять???")
            continue
    db.commit()
    db.close()

    # [print(skill_name, skill_start_date, one[0], one[1], one[2]) for one in all_journal]


@app.get("/api/results/skill/recalc/all", description="Скилы: пересчитать все",
         summary="Скилы: пересчитать все", tags=["Результаты"])
def get_results_skill_recalc_all(db: Session = Depends(get_db)):
    all_skills = db.query(Skill.id, Skill.skill, Skill.start_from).filter(
        and_(Skill.user_id == 1, Skill.is_active)).all()
    for one_skill in all_skills:
        calc_one_skill_all_date(one_skill[0], one_skill[1], one_skill[2])
    return db.query(SkillResults).all()


def set_penalty_character(db, curr_date, curr_score, character_id, failed_days):
    rec = db.query(CharacteristicResults).filter(
        and_(CharacteristicResults.characteristic_id == character_id,
             CharacteristicResults.dt == curr_date)).one_or_none()
    new_score = curr_score
    if failed_days == 180:
        new_score = 0
    elif failed_days == 120:
        new_score = curr_score - curr_score * 0.9
    elif failed_days == 60:
        new_score = curr_score - curr_score * 0.75
    elif failed_days == 30:
        new_score = curr_score - curr_score * 0.5
    elif failed_days == 21:
        new_score = curr_score - curr_score * 0.2
    elif failed_days == 14:
        new_score = curr_score - curr_score * 0.1
    elif failed_days == 7:
        new_score = curr_score - 1
    new_score = round(max(new_score, 0))
    if not rec:
        if new_score < curr_score:
            new_rec = CharacteristicResults(characteristic_id=character_id, dt=curr_date, score_change=new_score, type_change="pen")
        else:
            new_rec = CharacteristicResults(characteristic_id=character_id, dt=curr_date, score_change=new_score)
        db.add(new_rec)
    else:
        if new_score < curr_score:
            rec.score_change = new_score
            rec.type_change = "pen"
            rec.changed = func.now()
        else:  # когда штраф не начислен
            if rec.type_change != "":
                rec.type_change = ""
                rec.changed = func.now()
    return new_score


# Записать балл
def set_reward_charact(db, curr_date, add_score, curr_score, character_id):
    rec = (db.query(CharacteristicResults)
           .filter(and_(CharacteristicResults.characteristic_id == character_id, CharacteristicResults.dt == curr_date))
           .one_or_none())
    new_score = curr_score + min(add_score, 2)
    if not rec:
        new_rec = CharacteristicResults(characteristic_id=character_id, dt=curr_date, score_change=new_score,
                                        type_change="add")
        db.add(new_rec)

    else:
        if rec.score_change != new_score or rec.type_change != "add":
            rec.score_change = new_score
            rec.type_change = "add"
            rec.changed = func.now()
    return new_score


# расчитать скор на каждый день по одному скилу
def calc_one_charact_all_date(id, characteristic_name, charact_start_date):
    db = SessionLocal()

    all_journal = (
        db.query(func.count(Score.id), func.sum(Score.score), func.date(ActionJournal.dt).label("dt")).
        join(Action, Score.id == Action.score_id).
        join(ActionJournal, ActionJournal.action_id == Action.id).
        join(ActionCharacteristic, ActionCharacteristic.action_id == Action.id).group_by(func.date(ActionJournal.dt)).
        filter(and_(ActionCharacteristic.characteristic_id == id, ActionJournal.user_id == 1)).order_by(func.date(ActionJournal.dt))
    )
    curr_date = charact_start_date
    curr_srore = 0
    for one in all_journal:
        curr_failed_days = 0
        # Проверяем какая дельта
        diff_day = (one[2] - curr_date).days
        if diff_day == 0:  # Были действия
            curr_srore = set_reward_charact(db, curr_date, one[1], curr_srore, id)
            curr_date += timedelta(days=1)
        elif diff_day > 0:
            while curr_date < one[2]:
                curr_failed_days += 1
                curr_srore = set_penalty_character(db, curr_date, curr_srore, id, curr_failed_days)
                curr_date += timedelta(days=1)
            if curr_date == one[2]:
                curr_srore = set_reward_charact(db, curr_date, one[1], curr_srore, id)
                curr_date += timedelta(days=1)
            continue
        else:
            curr_date += timedelta(days=1)
            print("Как мы тут блять???")
            continue
    db.commit()
    db.close()



@app.get("/api/results/characteristic/recalc/all", description="Характерисктики: пересчитать все",
         summary="Характерисктики: пересчитать все", tags=["Результаты"])
def get_results_charact_recalc_all(db: Session = Depends(get_db)):
    all_charact = db.query(Characteristic.id, Characteristic.characteristic, Characteristic.start_from).filter(
        and_(Characteristic.user_id == 1, Characteristic.is_active)).all()
    for one_charact in all_charact:
        calc_one_charact_all_date(one_charact[0], one_charact[1], one_charact[2])
    return db.query(CharacteristicResults).filter(CharacteristicResults.dt == date.today()).all()

@app.get("/api/results/all", description="Получить все скоры на сегодня",
          summary="Получить все скоры на сегодня", tags=["Посмотреть"])
def get_results(db: Session = Depends(get_db)) -> list[SAllSkillCharScores]:
    query = text('''
select s.id as id, score_change as score, s.skill as name, 'skill' as type 
from skill s 
join skill_results sk on s.id = sk.skill_id
where is_active and user_id =1 
and dt = (select max(dt) from skill_results where skill_id = sk.skill_id)
union all
select s.id as id, score_change as score, s.characteristic as name, 'characteristic' as type 
from characteristic s 
join characteristic_results sk on s.id = sk.characteristic_id
where is_active and user_id =1 
and dt = (select max(dt) from characteristic_results where characteristic_id = sk.characteristic_id)
;
    ''')
    score_list = []
    for one in db.execute(query).fetchall():
        act = SAllSkillCharScores(id=one[0], score=one[1], name=one[2], types=one[3])
        score_list.append(act)
    return score_list

# TODO 4. mvp: авторизация
# TODO 6. Роутер и репозиторий: https://habr.com/ru/companies/selectel/articles/796669/

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)