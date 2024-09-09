from pydantic import BaseModel, Field, ConfigDict, PastDate
from typing import List


class SSkillAdd(BaseModel):
    user_id: int
    skill: str = Field(max_length=100)


class SSkill(SSkillAdd):
    id: int


class SCharactiristicAdd(BaseModel):
    user_id: int
    characteristic: str = Field(max_length=100)


class SCharactiristic(SCharactiristicAdd):
    id: int

class SAction(BaseModel):
    id: int
    action: str = Field(max_length=100)
    score: int | None = None

class SShortAction(BaseModel):
    id: int
    action: str = Field(max_length=100)
    model_config = ConfigDict(from_attributes=True)

class SActionAddWithLinkSkillsAndCharact(BaseModel):
    action: str = Field(max_length=100)
    score: int
    skills_list: List[int]
    characteristic: List[int]

class SActionEditWithLinkSkillsAndCharact(SActionAddWithLinkSkillsAndCharact):
    id: int
    action: str = Field(max_length=100)
    score: int
    skills_list: List[int]
    characteristic: List[int]

class SActionJournal(BaseModel):
    action_id: int
    pdt: PastDate| None = None

class SSkillWAction(BaseModel):
    id_skill: int
    skill: str = Field(max_length=100)
    actions: List[SAction]

class SCharacteristicWAction(BaseModel):
    id: int
    characteristic: str = Field(max_length=100)
    actions: List[SAction]