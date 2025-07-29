"""
User management system for Bosch Graph2RAG
Handles user authentication, workspace isolation, and document management
"""
import os
import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
import aiofiles
from fastapi import HTTPException, status

class User(BaseModel):
    username: str
    email: str
    password_hash: str
    salt: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    workspace: str  # User-specific workspace for document isolation
    metadata: Dict = {}

class UserManager:
    def __init__(self, users_file: str = "./users.json"):
        self.users_file = Path(users_file)
        self.users: Dict[str, User] = {}
        self._load_users()
        
    def _load_users(self):
        """Load users from JSON file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        # Convert datetime strings back to datetime objects
                        if 'created_at' in user_data:
                            user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                        if 'last_login' in user_data and user_data['last_login']:
                            user_data['last_login'] = datetime.fromisoformat(user_data['last_login'])
                        self.users[username] = User(**user_data)
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
        else:
            # Initialize with users from environment if no file exists
            self._init_from_env()
    
    def _init_from_env(self):
        """Initialize users from environment variables"""
        from .config import global_args
        
        auth_accounts = global_args.auth_accounts
        if auth_accounts:
            for account in auth_accounts.split(","):
                try:
                    username, password = account.split(":", 1)
                    # Check if email is included
                    if "@" in username:
                        email = username
                        username = email.split("@")[0]
                    else:
                        email = f"{username}@bosch.com"
                    
                    self.create_user(username, email, password)
                except Exception as e:
                    print(f"Error creating user from env: {e}")
    
    async def _save_users(self):
        """Save users to JSON file"""
        data = {}
        for username, user in self.users.items():
            user_dict = user.dict()
            # Convert datetime objects to ISO format strings
            user_dict['created_at'] = user.created_at.isoformat()
            if user.last_login:
                user_dict['last_login'] = user.last_login.isoformat()
            data[username] = user_dict
        
        async with aiofiles.open(self.users_file, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user"""
        if username in self.users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {username} already exists"
            )
        
        # Generate salt and hash password
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        
        # Create user-specific workspace
        workspace = f"user_{username}"
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            created_at=datetime.utcnow(),
            workspace=workspace
        )
        
        self.users[username] = user
        # Note: In async context, call await self._save_users()
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.users.get(username)
        if not user or not user.is_active:
            return None
        
        # Check password
        password_hash = self._hash_password(password, user.salt)
        if password_hash != user.password_hash:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        return user
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)
    
    def list_users(self) -> List[User]:
        """List all users"""
        return list(self.users.values())
    
    def update_user(self, username: str, **kwargs) -> Optional[User]:
        """Update user information"""
        user = self.users.get(username)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = ['email', 'is_active', 'metadata']
        for field in allowed_fields:
            if field in kwargs:
                setattr(user, field, kwargs[field])
        
        # Update password if provided
        if 'password' in kwargs:
            user.salt = secrets.token_hex(16)
            user.password_hash = self._hash_password(kwargs['password'], user.salt)
        
        return user
    
    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        if username in self.users:
            del self.users[username]
            return True
        return False
    
    def get_user_workspace(self, username: str) -> str:
        """Get user-specific workspace directory"""
        user = self.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        return user.workspace

# Global user manager instance
user_manager = UserManager()