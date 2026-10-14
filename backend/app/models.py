from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}', is_verified={self.is_verified})>"
