import json
import bcrypt
import os
import pandas as pd  # Add this import
from config import USERS_FILE, FAMILY_PROFILES_FILE

class AuthManager:
    def __init__(self):
        self.users_file = USERS_FILE
        self.family_profiles_file = FAMILY_PROFILES_FILE
        self._ensure_files()
    
    def _ensure_files(self):
        """Create files if they don't exist"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.family_profiles_file):
            with open(self.family_profiles_file, 'w') as f:
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
    
    def _load_family_profiles(self):
        """Load family profiles"""
        try:
            with open(self.family_profiles_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_family_profiles(self, profiles):
        """Save family profiles"""
        with open(self.family_profiles_file, 'w') as f:
            json.dump(profiles, f, indent=2)
    
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
            "email": email,
            "family_members": {}
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
    
    def add_family_member(self, username, member_name, age, gender, relationship):
        """Add a family member to user's profile"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        if "family_members" not in users[username]:
            users[username]["family_members"] = {}
        
        member_id = f"{member_name}_{len(users[username]['family_members']) + 1}"
        users[username]["family_members"][member_id] = {
            "name": member_name,
            "age": age,
            "gender": gender,
            "relationship": relationship,
            "created_at": str(pd.Timestamp.now())
        }
        
        self._save_users(users)
        return True, "Family member added successfully"
    
    def get_family_members(self, username):
        """Get all family members for a user"""
        users = self._load_users()
        
        if username in users and "family_members" in users[username]:
            return users[username]["family_members"]
        return {}
    
    def delete_family_member(self, username, member_id):
        """Delete a family member"""
        users = self._load_users()
        
        if username in users and "family_members" in users[username]:
            if member_id in users[username]["family_members"]:
                del users[username]["family_members"][member_id]
                self._save_users(users)
                return True, "Family member deleted successfully"
        return False, "Family member not found"