from pydantic import BaseModel, EmailStr, ConfigDict


class RegisterRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str
