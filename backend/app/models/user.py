from sqlalchemy import Column, Integer, String, DateTime, JSON 
from sqlalchemy.orm import declarative_base 
from fastapi_users.db import SQLAlchemyBaseUserTable 
from datetime import datetime 
 
Base = declarative_base() 
 
class User(SQLAlchemyBaseUserTable[int], Base): 
    __tablename__ = "users" 
    id = Column(Integer, primary_key=True, index=True) 
    email = Column(String(255), unique=True, index=True, nullable=False) 
    hashed_password = Column(String(255), nullable=False) 
    name = Column(String(100), nullable=False) 
    profile_data = Column(JSON, nullable=True, default={}) 
    created_at = Column(DateTime, default=datetime.utcnow)