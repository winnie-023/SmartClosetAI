from pydantic import BaseModel

class WardrobeCreate(BaseModel):
    filename: str
    category: str
    width: int
    height: int

class WardrobeRead(WardrobeCreate):
    id: int

    class Config:
        orm_mode = True