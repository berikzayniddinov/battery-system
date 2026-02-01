from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: str

    class Config:
        from_attributes = True


class BatteryIn(BaseModel):
    voltage: float
    current: float
    temperature: float
    capacity: float
    cycle_number: int
    battery_id: str = "default"