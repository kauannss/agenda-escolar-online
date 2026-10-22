from pydantic import BaseModel

class userRegistration(BaseModel):
    name:str
    id:str
    type:str
    date_of_birth:str
    id_turma:str


class userLogin(BaseModel):
    id:str
    password:str
