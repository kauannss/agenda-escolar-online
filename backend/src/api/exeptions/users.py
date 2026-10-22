from fastapi import HTTPException
def login_wrong():
    raise HTTPException(
        status_code=401,
        detail="Credenciais inválidas"
    )