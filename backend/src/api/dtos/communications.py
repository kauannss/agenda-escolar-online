from pydantic import BaseModel, Field, field_validator


class CommunicationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    id_turmas: list[str] = Field(min_length=1)

    @field_validator("title", "description")
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
