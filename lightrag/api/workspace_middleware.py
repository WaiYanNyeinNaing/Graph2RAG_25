"""
Workspace middleware for user-specific document isolation
"""
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import auth_handler
from .user_manager import user_manager
from .config import global_args

class WorkspaceMiddleware(BaseHTTPMiddleware):
    """Middleware to set user-specific workspace based on authentication"""
    
    def __init__(self, app, whitelist_paths: list = None):
        super().__init__(app)
        self.whitelist_paths = whitelist_paths or [
            "/health", "/auth/", "/docs", "/openapi.json", "/webui"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip middleware for whitelisted paths
        path = request.url.path
        if any(path.startswith(wp) for wp in self.whitelist_paths):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                token_data = auth_handler.validate_token(token)
                username = token_data["username"]
                workspace = token_data["metadata"].get("workspace")
                
                if not workspace:
                    # Get workspace from user manager if not in token
                    workspace = user_manager.get_user_workspace(username)
                
                # Set workspace in request state
                request.state.username = username
                request.state.workspace = workspace
                request.state.user_authenticated = True
                
            except Exception as e:
                # If auth is enabled and token is invalid, reject
                if global_args.api_key:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication"
                    )
                else:
                    # Auth not required, use default workspace
                    request.state.username = "anonymous"
                    request.state.workspace = None
                    request.state.user_authenticated = False
        else:
            # No auth header
            if global_args.api_key:
                # Check if it's an API key auth
                api_key = request.headers.get("X-API-Key")
                if api_key == global_args.api_key:
                    request.state.username = "api_user"
                    request.state.workspace = None
                    request.state.user_authenticated = True
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
            else:
                # No auth required
                request.state.username = "anonymous"
                request.state.workspace = None
                request.state.user_authenticated = False
        
        response = await call_next(request)
        return response

def get_user_working_dir(request: Request) -> str:
    """Get user-specific working directory"""
    workspace = getattr(request.state, "workspace", None)
    base_dir = global_args.working_dir
    
    if workspace:
        # Create user-specific directory
        user_dir = os.path.join(base_dir, workspace)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    return base_dir

def get_user_input_dir(request: Request) -> str:
    """Get user-specific input directory"""
    workspace = getattr(request.state, "workspace", None)
    base_dir = global_args.input_dir
    
    if workspace:
        # Create user-specific input directory
        user_dir = os.path.join(base_dir, workspace)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    return base_dir