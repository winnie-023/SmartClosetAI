from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Wardrobe(Base):
    __tablename__ = "wardrobe"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    category = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="wardrobe")





