#!/usr/bin/env python3
"""
Bosch Graph2RAG Server with Authentication
Enhanced version with user management and workspace isolation
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lightrag.api.lightrag_server import create_app, global_args
from lightrag.api.workspace_middleware import WorkspaceMiddleware
from lightrag.api.routers.auth_routes import router as auth_router
from lightrag.api.user_manager import user_manager
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
import uvicorn

# Store RAG instances per workspace
rag_instances = {}

async def get_or_create_rag(workspace: str = None):
    """Get or create a RAG instance for a specific workspace"""
    if workspace is None:
        workspace = "default"
    
    if workspace not in rag_instances:
        # Create workspace-specific directory
        working_dir = os.path.join(global_args.working_dir, workspace)
        os.makedirs(working_dir, exist_ok=True)
        
        # Create RAG instance with workspace-specific storage
        rag = LightRAG(
            working_dir=working_dir,
            workspace=workspace,
            **global_args.rag_config  # Pass other RAG configuration
        )
        
        # Initialize RAG
        await rag.initialize_storages()
        rag_instances[workspace] = rag
    
    return rag_instances[workspace]

# Override the original create_app to add authentication
def create_authenticated_app():
    """Create FastAPI app with authentication enabled"""
    app = create_app()
    
    # Add authentication routes
    app.include_router(auth_router)
    
    # Add workspace middleware
    app.add_middleware(
        WorkspaceMiddleware,
        whitelist_paths=[
            "/health", "/auth/", "/docs", "/openapi.json", 
            "/webui", "/static", "/favicon"
        ]
    )
    
    # Override document routes to use workspace
    from fastapi import Request, Depends
    from lightrag.api.routers.document_routes import router as doc_router
    
    @app.middleware("http")
    async def inject_workspace_rag(request: Request, call_next):
        """Inject workspace-specific RAG instance"""
        if hasattr(request.state, "workspace"):
            workspace = request.state.workspace
            request.state.rag = await get_or_create_rag(workspace)
        response = await call_next(request)
        return response
    
    return app

def main():
    """Main entry point with authentication"""
    # Set environment variable to enable auth
    os.environ["ENABLE_USER_AUTH"] = "true"
    
    # Create app with authentication
    app = create_authenticated_app()
    
    # Display startup message
    print("\n" + "="*60)
    print("🚀 Bosch Graph2RAG Server with Authentication")
    print("="*60)
    print(f"📍 Server URL: http://localhost:{global_args.port}")
    print(f"📚 API Docs: http://localhost:{global_args.port}/docs")
    print(f"🌐 Web UI: http://localhost:{global_args.port}/webui")
    print(f"🔐 Authentication: ENABLED")
    print("="*60 + "\n")
    
    # Run server
    uvicorn.run(
        app,
        host=global_args.host,
        port=global_args.port,
        reload=False
    )

if __name__ == "__main__":
    main()