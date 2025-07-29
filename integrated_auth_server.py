#!/usr/bin/env python3
"""
Integrated authentication server for Bosch Graph2RAG
Combines auth server with redirect to main LightRAG UI
"""
import os
import sys
import json
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    message: str
    redirect_url: str

# Create app
app = FastAPI(
    title="Bosch Graph2RAG Secure Portal",
    description="Authentication portal for Bosch Graph2RAG",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("TOKEN_SECRET", "bosch-graph2rag-secret-2025")
ALGORITHM = "HS256"

# User storage
USERS = {
    "admin": {
        "password": "admin123",
        "email": "admin@bosch.com",
        "workspace": "user_admin"
    },
    "demo": {
        "password": "demo123", 
        "email": "demo@bosch.com",
        "workspace": "user_demo"
    },
    "waiyan": {
        "password": "password123",
        "email": "waiyan@bosch.com", 
        "workspace": "user_waiyan"
    }
}

def create_token(username: str) -> str:
    """Create JWT token"""
    expire = datetime.utcnow() + timedelta(hours=48)
    payload = {
        "sub": username,
        "exp": expire,
        "workspace": USERS[username]["workspace"],
        "email": USERS[username]["email"]
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Enhanced login page with redirect
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bosch Graph2RAG - Secure Login</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .login-container {
            background: white;
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            width: 350px;
        }
        .logo {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .logo img {
            width: 150px;
            height: auto;
        }
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
            font-size: 14px;
        }
        .bosch-logo {
            text-align: center;
            font-size: 48px;
            color: #c8102e;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 2px solid #e1e4e8;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #c8102e;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #c8102e;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #a00922;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .message {
            margin-top: 15px;
            padding: 12px;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #c8102e;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
            vertical-align: middle;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .test-users {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            font-size: 14px;
            border-left: 4px solid #c8102e;
        }
        .test-users strong {
            color: #c8102e;
        }
        .redirect-info {
            text-align: center;
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="bosch-logo">BOSCH</div>
        <h2>Graph2RAG</h2>
        <div class="subtitle">Knowledge Graph System</div>
        
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required autocomplete="username">
            <input type="password" id="password" placeholder="Password" required autocomplete="current-password">
            <button type="submit" id="loginButton">Login</button>
        </form>
        
        <div id="message"></div>
        <div id="redirectInfo" class="redirect-info" style="display: none;">
            Redirecting to Graph2RAG Dashboard...
        </div>
        
        <div class="test-users">
            <strong>Demo Accounts:</strong><br>
            • admin / admin123<br>
            • demo / demo123<br>
            • waiyan / password123
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        const MAIN_UI_URL = 'http://localhost:9621/webui';  // Main LightRAG UI
        
        // Check if already logged in
        const savedToken = localStorage.getItem('graph2rag_token');
        if (savedToken) {
            // Optionally auto-redirect if token exists
            // window.location.href = MAIN_UI_URL;
        }
        
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            const loginButton = document.getElementById('loginButton');
            const redirectInfo = document.getElementById('redirectInfo');
            
            // Disable button and show loading
            loginButton.disabled = true;
            loginButton.innerHTML = 'Logging in... <span class="loading"></span>';
            
            try {
                const response = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    messageDiv.className = 'message success';
                    messageDiv.textContent = 'Login successful! Preparing your workspace...';
                    
                    // Store authentication data
                    localStorage.setItem('graph2rag_token', data.access_token);
                    localStorage.setItem('graph2rag_username', data.username);
                    localStorage.setItem('graph2rag_workspace', data.workspace || `user_${data.username}`);
                    
                    // Show redirect info
                    redirectInfo.style.display = 'block';
                    
                    // Set auth header for future requests
                    window.graph2ragAuth = {
                        token: data.access_token,
                        username: data.username,
                        workspace: data.workspace
                    };
                    
                    // Redirect to dashboard after short delay
                    setTimeout(() => {
                        // Redirect to authenticated dashboard
                        window.location.href = data.redirect_url;
                    }, 1500);
                    
                } else {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = data.detail || 'Invalid username or password';
                    redirectInfo.style.display = 'none';
                    
                    // Re-enable button
                    loginButton.disabled = false;
                    loginButton.textContent = 'Login';
                }
            } catch (error) {
                messageDiv.className = 'message error';
                messageDiv.textContent = 'Connection error: ' + error.message;
                redirectInfo.style.display = 'none';
                
                // Re-enable button
                loginButton.disabled = false;
                loginButton.textContent = 'Login';
            }
        });
        
        // Auto-focus username field
        document.getElementById('username').focus();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve login page"""
    return LOGIN_HTML

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve login page"""
    return LOGIN_HTML

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    if request.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if USERS[request.username]["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = create_token(request.username)
    
    return LoginResponse(
        access_token=token,
        username=request.username,
        message=f"Welcome {request.username}!",
        redirect_url=f"http://localhost:9622/dashboard?token={token}&user={request.username}",
        workspace=USERS[request.username]["workspace"]
    )

@app.get("/auth/verify")
async def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token and return user info"""
    payload = verify_token(credentials.credentials)
    return {
        "valid": True,
        "username": payload["sub"],
        "workspace": payload["workspace"],
        "email": payload["email"]
    }

@app.get("/auth/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Please remove token from client storage"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(token: str = None, user: str = None):
    """Serve authenticated dashboard wrapper"""
    if not token:
        return RedirectResponse(url="/login")
    
    # Read the auth_injector.html file
    with open("auth_injector.html", "r") as f:
        html_content = f.read()
    
    return html_content

# Proxy endpoints to inject authentication
@app.get("/webui")
async def redirect_to_main_ui(token: str = None):
    """Redirect to main UI with authentication"""
    if token:
        # Verify token first
        try:
            payload = verify_token(token)
            # Redirect to dashboard wrapper
            return RedirectResponse(url=f"/dashboard?token={token}&user={payload['sub']}")
        except:
            return RedirectResponse(url="/login")
    else:
        return RedirectResponse(url="/login")

if __name__ == "__main__":
    print("\n🔐 Bosch Graph2RAG Integrated Authentication Server")
    print("==================================================")
    print(f"📍 Login Portal: http://localhost:9622")
    print(f"🌐 Main UI: http://localhost:9621/webui (requires authentication)")
    print(f"📚 API Docs: http://localhost:9622/docs")
    print("\n✨ Features:")
    print("  - Login at http://localhost:9622")
    print("  - Automatic redirect to Graph2RAG UI after login")
    print("  - Token stored in browser localStorage")
    print("  - User workspace isolation")
    print("\n📋 Test Users:")
    for username, info in USERS.items():
        print(f"  - {username} / {info['password']}")
    print("\n")
    
    uvicorn.run(app, host="0.0.0.0", port=9622)