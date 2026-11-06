from datetime import date

from pydantic import BaseModel, Field, field_validator


class ActivityWrite(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=1, max_length=10000)
    materia: str = Field(min_length=1, max_length=200)
    data_limite: date
    id_turmas: list[str] = Field(min_length=1)
    professor_id: str | None = None

    @field_validator("nome", "descricao", "materia")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value

    @field_validator("id_turmas")
    @classmethod
    def normalize_class_ids(cls, values: list[str]) -> list[str]:
        class_ids = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not class_ids:
            raise ValueError("Selecione ao menos uma turma.")
        return class_ids

    @field_validator("professor_id")
    @classmethod
    def normalize_professor_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
