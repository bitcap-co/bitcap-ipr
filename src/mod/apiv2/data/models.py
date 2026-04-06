from pydantic import BaseModel, Field


class MinerConfPool(BaseModel):
    url: str = ""
    user: str = ""
    passwd: str = Field(default="", alias="pass")


class BlinkStatus(BaseModel):
    blink: bool


class ActionResponse(BaseModel):
    success: bool
    msg: str = ""
