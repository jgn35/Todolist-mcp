"""
Token Manager

Handles generation, storage, and validation of auth tokens.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta

from sqlalchemy import create_engine, delete, insert, select
from sqlalchemy.orm import sessionmaker

from .models import AuthTokenModel, Base


class TokenManager:
    """
    Manages authentication tokens for MCP server.

    Tokens are stored hashed in the database for security.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.path.expanduser("~/.todolist-mcp/todolist.db")
        self.engine = None
        self.Session = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the database engine and session."""
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Create sync engine
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.Session = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)

    def _hash_token(self, token: str) -> str:
        """Hash a token using SHA256."""
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_token(self) -> str:
        """
        Generate a new random token.

        Returns:
            str: New token (plain text)
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)

        # Store the hashed version
        hashed_token = self._hash_token(token)

        with self.Session() as session:
            # Delete any existing tokens (single-user, one token at a time)
            session.execute(delete(AuthTokenModel))

            # Insert new token
            session.execute(
                insert(AuthTokenModel).values(
                    token=hashed_token,
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=365),  # 1 year expiry
                )
            )
            session.commit()

        return token

    async def validate_token(self, token: str) -> bool:
        """
        Validate a token.

        Args:
            token: Token string to validate

        Returns:
            bool: True if token is valid
        """
        hashed_token = self._hash_token(token)

        with self.Session() as session:
            result = session.execute(
                select(AuthTokenModel).where(AuthTokenModel.token == hashed_token)
            )
            token_record = result.scalar_one_or_none()

            if token_record is None:
                return False

            # Check if token has expired
            if token_record.expires_at and token_record.expires_at < datetime.now():
                return False

            return True

    async def get_token(self) -> str | None:
        """
        Get the stored token (hashed).

        Returns:
            str: Hashed token or None if not set
        """
        with self.Session() as session:
            result = session.execute(
                select(AuthTokenModel)
            )
            token_record = result.scalar_one_or_none()

            if token_record is None:
                return None

            return token_record.token

    def clear_token(self) -> None:
        """Clear the stored token."""
        with self.Session() as session:
            session.execute(delete(AuthTokenModel))
            session.commit()
