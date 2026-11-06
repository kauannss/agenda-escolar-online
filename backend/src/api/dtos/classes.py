from pydantic import BaseModel, Field, field_validator


class ClassCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    turno: str = Field(min_length=1, max_length=50)

    @field_validator("nome", "turno")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value
