# 🔐 Authentication Guide for Bosch Graph2RAG

This guide explains how to set up and use authentication with user-specific workspaces.

## Features

- 👤 **User Authentication**: Username/password based login
- 📁 **Workspace Isolation**: Each user has their own document storage
- 🔒 **JWT Tokens**: Secure token-based authentication
- 📊 **User Management**: CLI tool for managing users
- 🗂️ **Document Persistence**: Users can save and revisit their documents

## Quick Start

### 1. Configure Authentication

```bash
# Copy the authentication template
cp .env.auth.sample .env.auth

# Edit with your settings
nano .env.auth
```

Key settings:
- `TOKEN_SECRET`: Change this to a secure random string
- `AUTH_ACCOUNTS`: Initial users (format: `username:password`)

### 2. Start Server with Authentication

```bash
./start_auth_server.sh
```

This will:
- Create a default admin user if none exist
- Start the server with authentication enabled
- Show registered users

### 3. Manage Users

```bash
# List all users
./manage_users.py list

# Add a new user (interactive)
./manage_users.py add

# Reset password
./manage_users.py reset-password

# Delete user
./manage_users.py delete

# Enable/disable user
./manage_users.py toggle
```

## API Usage

### Login

```bash
curl -X POST http://localhost:9621/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "username": "admin",
  "email": "admin@bosch.com",
  "workspace": "user_admin"
}
```

### Use Token for Requests

```bash
# Upload document
curl -X POST http://localhost:9621/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# Query
curl -X POST http://localhost:9621/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Graph2RAG?"}'
```

## User Workspaces

Each user has their own isolated workspace:

```
rag_storage/
├── user_admin/          # Admin's documents and graphs
│   ├── kv_store.json
│   ├── vector_db/
│   └── graph_storage/
├── user_demo/           # Demo user's workspace
│   └── ...
└── user_john/           # John's workspace
    └── ...
```

## Docker Setup

### Using Docker Compose

```yaml
# docker-compose.auth.yml
version: '3.8'

services:
  graph2rag-auth:
    image: bosch/graph2rag:latest
    ports:
      - "9621:9621"
    environment:
      - ENABLE_USER_AUTH=true
      - TOKEN_SECRET=${TOKEN_SECRET}
    volumes:
      - ./users.json:/app/users.json
      - ./rag_storage:/app/rag_storage
      - ./inputs:/app/inputs
    env_file:
      - .env.auth
```

Run with:
```bash
docker-compose -f docker-compose.auth.yml up
```

## Security Best Practices

1. **Change Default Passwords**: Always change default admin password
2. **Secure Token Secret**: Use a strong, random TOKEN_SECRET
3. **HTTPS in Production**: Use reverse proxy with SSL
4. **Regular Backups**: Backup users.json and user workspaces
5. **Access Logs**: Monitor authentication logs

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_USER_AUTH` | Enable authentication | `false` |
| `TOKEN_SECRET` | JWT signing secret | `lightrag-jwt-default-secret` |
| `TOKEN_EXPIRE_HOURS` | Token expiration time | `48` |
| `AUTH_ACCOUNTS` | Initial user accounts | `""` |
| `USERS_FILE` | User database location | `./users.json` |

## Troubleshooting

### Can't login
- Check username/password
- Verify user is active: `./manage_users.py list`
- Check server logs for errors

### Token expired
- Login again to get new token
- Adjust `TOKEN_EXPIRE_HOURS` if needed

### Lost admin password
- Use CLI to reset: `./manage_users.py reset-password`
- Or edit users.json directly (restart server)

## Integration with Frontend

The authentication system works with any frontend that supports JWT:

```javascript
// Login
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username, password})
});
const {access_token} = await response.json();

// Store token
localStorage.setItem('token', access_token);

// Use token
fetch('/documents', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

## Advanced Configuration

### Custom User Fields

Edit `user_manager.py` to add custom fields:
- Department
- Role/Permissions
- Quota limits
- API rate limits

### External Authentication

The system can be extended to support:
- LDAP/Active Directory
- OAuth2/OIDC
- SAML
- Multi-factor authentication