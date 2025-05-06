from pydantic import BaseModel

class WardrobeCreate(BaseModel):
    filename: str
    category: str
    color: str
    material: str
    style: str
    width: int
    height: int
    user_id: int

class WardrobeRead(WardrobeCreate):
    id: int

    class Config:
        orm_mode = True