"""
CLI for Todolist MCP Server

Provides command-line interface for token generation and management.
"""

import argparse
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from todolist_mcp.infrastructure.auth_adapter.token_manager import TokenManager


def generate_token():
    """Generate a new authentication token."""
    token_manager = TokenManager()

    # Check if token already exists
    import asyncio
    async def check_existing():
        existing = await token_manager.get_token()
        return existing is not None

    has_existing = asyncio.run(check_existing())

    if has_existing:
        print("⚠️  Warning: A token already exists and will be replaced.")
        response = input("Do you want to generate a new token anyway? (y/N): ")
        if response.lower() != 'y':
            print("Token generation cancelled.")
            return

    # Generate new token
    token = token_manager.generate_token()

    print("\n✅ New token generated successfully!")
    print(f"\nToken: {token}")
    print("\n⚠️  IMPORTANT: Save this token. It will not be displayed again.")
    print("   Use it as the 'token' parameter for all MCP tool calls.")
    print(f"\n   Example: create_task(title='Test', token='{token[:8]}...')")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Todolist MCP Server - CLI for token management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  todolist-mcp generate-token    Generate a new authentication token
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate token command
    token_parser = subparsers.add_parser(
        'generate-token',
        help='Generate a new authentication token',
        description='Generate a new authentication token for MCP server access'
    )
    token_parser.set_defaults(func=generate_token)
    
    # Run server command
    server_parser = subparsers.add_parser(
        'run',
        help='Run the MCP server',
        description='Run the Todolist MCP server with configurable transport'
    )
    server_parser.add_argument(
        '--transport',
        choices=['stdio', 'http', 'both'],
        default='stdio',
        help='Transport protocol: stdio (default), http, or both'
    )
    server_parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='HTTP port when using http or both transport (default: 8080)'
    )
    server_parser.set_defaults(func=run_server)


def run_server():
    """Run the MCP server."""
    from todolist_mcp import main
    import sys
    
    # Pass arguments to main function
    sys.argv = ['todolist-mcp'] + sys.argv[1:]
    main()

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
