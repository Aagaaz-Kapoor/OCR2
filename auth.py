import json
import bcrypt
import os
from config import USERS_FILE

class AuthManager:
    def __init__(self):
        self.users_file = USERS_FILE
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users file if it doesn't exist"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def _load_users(self):
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def hash_password(self, password):
        """Hash a password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def signup(self, username, password, email):
        """Register a new user"""
        users = self._load_users()
        
        if username in users:
            return False, "Username already exists"
        
        users[username] = {
            "password": self.hash_password(password),
            "email": email
        }
        
        self._save_users(users)
        return True, "Registration successful"
    
    def login(self, username, password):
        """Authenticate a user"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        if self.verify_password(password, users[username]["password"]):
            return True, "Login successful"
        else:
            return False, "Incorrect password"