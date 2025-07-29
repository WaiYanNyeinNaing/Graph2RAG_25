"""
Authentication routes for Bosch Graph2RAG
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from ..auth import auth_handler
from ..user_manager import user_manager

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str
    workspace: str

class UserResponse(BaseModel):
    username: str
    email: str
    workspace: str
    is_active: bool

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with username and password"""
    user = user_manager.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create JWT token
    token = auth_handler.create_token(
        username=user.username,
        role="user",
        metadata={
            "email": user.email,
            "workspace": user.workspace
        }
    )
    
    # Save updated user (with last_login)
    await user_manager._save_users()
    
    return LoginResponse(
        access_token=token,
        username=user.username,
        email=user.email,
        workspace=user.workspace
    )

@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        user = user_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        await user_manager._save_users()
        
        return UserResponse(
            username=user.username,
            email=user.email,
            workspace=user.workspace,
            is_active=user.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    token_data = auth_handler.validate_token(credentials.credentials)
    user = user_manager.get_user(token_data["username"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        username=user.username,
        email=user.email,
        workspace=user.workspace,
        is_active=user.is_active
    )

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout (client should remove token)"""
    # Validate token
    auth_handler.validate_token(credentials.credentials)
    
    # In a real implementation, you might want to blacklist the token
    # For now, just return success
    return {"message": "Logged out successfully"}

@router.put("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Change user password"""
    token_data = auth_handler.validate_token(credentials.credentials)
    username = token_data["username"]
    
    # Verify old password
    user = user_manager.authenticate(username, old_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Update password
    user_manager.update_user(username, password=new_password)
    await user_manager._save_users()
    
    return {"message": "Password changed successfully"}