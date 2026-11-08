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


class userUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: Literal["aluno", "professor", "gestor"]
    date_of_birth: date
    id_turmas: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome não pode ficar vazio.")
        return value

    @field_validator("id_turmas")
    @classmethod
    def normalize_class_ids(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class userLogin(BaseModel):
    id:str
    password:str


class GuardianNameUpdate(BaseModel):
    nome_responsavel: str = Field(min_length=1, max_length=200)

    @field_validator("nome_responsavel")
    @classmethod
    def strip_guardian_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Informe o nome do responsável.")
        return value
