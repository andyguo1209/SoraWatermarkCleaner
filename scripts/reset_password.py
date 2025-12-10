import sys
import os
import asyncio
from pathlib import Path

# Add project root to path so we can import from sorawm
sys.path.append(str(Path(__file__).parent.parent))

from sorawm.server.db import get_session
from sorawm.server.models import User
from sorawm.server.auth_utils import hash_password
from sqlalchemy import select

async def reset_password(username, new_password):
    if not username or not new_password:
        print("Usage: python scripts/reset_password.py <username> <new_password>")
        return

    print(f"Resetting password for user: {username}")
    
    async with get_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User '{username}' not found.")
            # Option to create user if not exists? For now, just error.
            return

        user.password_hash = hash_password(new_password)
        # Ensure user is active/admin if needed to login
        user.is_approved = True 
        user.is_admin = True # Grant admin privileges
        session.add(user)
        # Session commit is handled by get_session context manager
        print("Password updated successfully.")
        print(f"User '{username}' is now approved and can login.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/reset_password.py <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    try:
        asyncio.run(reset_password(username, password))
    except Exception as e:
        print(f"An error occurred: {e}")
