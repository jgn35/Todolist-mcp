"""
Auth Service

Handles authentication logic for MCP tools.
"""

from typing import Optional
from todolist_mcp.infrastructure.auth_adapter.token_manager import TokenManager


class AuthService:
    """
    Service for handling token authentication.
    """
    
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
    
    async def validate_token(self, token: Optional[str]) -> bool:
        """
        Validate a token.
        
        Args:
            token: Token string to validate
        
        Returns:
            bool: True if token is valid
        """
        if token is None:
            return False
        
        return await self.token_manager.validate_token(token)
    
    async def get_token(self) -> Optional[str]:
        """
        Get the stored token.
        
        Returns:
            str: Token or None if not set
        """
        return await self.token_manager.get_token()
