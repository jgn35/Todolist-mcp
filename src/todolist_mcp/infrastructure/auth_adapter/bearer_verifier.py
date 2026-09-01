"""
Bearer Token Verifier for FastMCP.

Bridges the existing TokenManager to FastMCP's auth provider system so that
the HTTP transport validates Bearer tokens from the Authorization header.
"""

from fastmcp.server.auth import AccessToken, TokenVerifier

from .token_manager import TokenManager


class BearerTokenVerifier(TokenVerifier):
    """Validate Bearer tokens against the TokenManager database."""

    def __init__(self, db_path: str | None = None):
        super().__init__()
        self._token_manager = TokenManager(db_path=db_path)

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token:
            return None

        if await self._token_manager.validate_token(token):
            return AccessToken(
                token=token,
                client_id="local",
                scopes=[],
                claims={},
            )
        return None
