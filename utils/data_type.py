from pydantic import BaseModel

class RegistrationRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str

class User(RegistrationRequest):
    id: str

class LoginRequest(BaseModel):
    email:str
    password:str


class Token(BaseModel):
    access_token: str
    token_type: str
    message: str

class TokenData(BaseModel):
    email: str | None = None