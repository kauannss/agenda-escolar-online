from datetime import date

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    data: date
    id_turmas: list[str] = Field(min_length=1)

    @field_validator("nome")
    @classmethod
    def strip_event_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome do evento não pode ficar vazio.")
        return value

    @field_validator("id_turmas")
    @classmethod
    def normalize_class_ids(cls, values: list[str]) -> list[str]:
        class_ids = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not class_ids:
            raise ValueError("Selecione ao menos uma turma.")
        return class_ids
