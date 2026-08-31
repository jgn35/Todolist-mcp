"""
SQLAlchemy Models

Database models for SQLite persistence.
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TaskModel(Base):
    """
    SQLAlchemy model for tasks.

    Maps to the tasks table in SQLite.
    """
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(50), nullable=True)
    priority = Column(String(20), nullable=True, default="medium")
    status = Column(String(20), nullable=True, default="pending")
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)


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
