#models/wardrobe.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Wardrobe(Base):
    __tablename__ = "wardrobe"

    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    category = Column(String)
    color = Column(String)     
    material = Column(String)  
    style = Column(String)    
    width = Column(Integer)
    height = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="wardrobe")





