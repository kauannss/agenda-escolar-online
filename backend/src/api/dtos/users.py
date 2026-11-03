from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class userRegistration(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    id: str = Field(min_length=1, max_length=100)
    type: Literal["aluno", "professor", "gestor"]
    date_of_birth: date
    id_turma: str | None = None

    @field_validator("name", "id")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value


class userLogin(BaseModel):
    id:str
    password:str
