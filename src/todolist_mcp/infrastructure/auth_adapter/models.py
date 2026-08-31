"""
Auth Adapter Models

SQLAlchemy models for auth tokens.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class AuthTokenModel(Base):
    """
    SQLAlchemy model for auth tokens.
    
    Maps to the auth_tokens table in SQLite.
    """
    __tablename__ = "auth_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
