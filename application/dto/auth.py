from pydantic import BaseModel, ConfigDict


class AuthRegisterRequest(BaseModel):
    email: str
    display_name: str
    password: str


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
