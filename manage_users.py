#!/usr/bin/env python3
"""
User Management CLI for Bosch Graph2RAG
Manage users without starting the server
"""
import argparse
import asyncio
import getpass
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from lightrag.api.user_manager import user_manager

def list_users():
    """List all users"""
    users = user_manager.list_users()
    if not users:
        print("No users found.")
        return
    
    print("\n📋 Registered Users:")
    print("-" * 60)
    print(f"{'Username':<20} {'Email':<30} {'Active':<10}")
    print("-" * 60)
    for user in users:
        status = "✅" if user.is_active else "❌"
        print(f"{user.username:<20} {user.email:<30} {status:<10}")
    print("-" * 60)
    print(f"Total: {len(users)} users\n")

def add_user():
    """Add a new user interactively"""
    print("\n➕ Add New User")
    print("-" * 40)
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return
    
    email = input("Email: ").strip()
    if not email:
        email = f"{username}@bosch.com"
        print(f"Using default email: {email}")
    
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm Password: ")
    
    if password != confirm:
        print("❌ Passwords do not match")
        return
    
    try:
        user = user_manager.create_user(username, email, password)
        # Save synchronously
        asyncio.run(user_manager._save_users())
        print(f"✅ User '{username}' created successfully!")
        print(f"   Workspace: {user.workspace}")
    except Exception as e:
        print(f"❌ Error: {e}")

def delete_user():
    """Delete a user"""
    username = input("Username to delete: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return
    
    confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    if user_manager.delete_user(username):
        asyncio.run(user_manager._save_users())
        print(f"✅ User '{username}' deleted successfully!")
    else:
        print(f"❌ User '{username}' not found")

def reset_password():
    """Reset user password"""
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return
    
    user = user_manager.get_user(username)
    if not user:
        print(f"❌ User '{username}' not found")
        return
    
    password = getpass.getpass("New Password: ")
    confirm = getpass.getpass("Confirm Password: ")
    
    if password != confirm:
        print("❌ Passwords do not match")
        return
    
    user_manager.update_user(username, password=password)
    asyncio.run(user_manager._save_users())
    print(f"✅ Password reset successfully for user '{username}'!")

def toggle_user_status():
    """Enable/disable a user"""
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return
    
    user = user_manager.get_user(username)
    if not user:
        print(f"❌ User '{username}' not found")
        return
    
    new_status = not user.is_active
    user_manager.update_user(username, is_active=new_status)
    asyncio.run(user_manager._save_users())
    
    status_text = "enabled" if new_status else "disabled"
    print(f"✅ User '{username}' has been {status_text}!")

def main():
    parser = argparse.ArgumentParser(
        description="Bosch Graph2RAG User Management"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List users
    subparsers.add_parser('list', help='List all users')
    
    # Add user
    subparsers.add_parser('add', help='Add a new user')
    
    # Delete user
    subparsers.add_parser('delete', help='Delete a user')
    
    # Reset password
    subparsers.add_parser('reset-password', help='Reset user password')
    
    # Toggle user status
    subparsers.add_parser('toggle', help='Enable/disable a user')
    
    args = parser.parse_args()
    
    print("\n🔐 Bosch Graph2RAG User Management")
    print("=" * 40)
    
    if args.command == 'list':
        list_users()
    elif args.command == 'add':
        add_user()
    elif args.command == 'delete':
        delete_user()
    elif args.command == 'reset-password':
        reset_password()
    elif args.command == 'toggle':
        toggle_user_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()