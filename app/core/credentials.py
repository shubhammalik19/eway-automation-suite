"""
Credentials Management Utility
Handles reading/writing credentials to .env file
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from app.core.logging import logger

class CredentialsManager:
    def __init__(self, env_file_path: str = ".env"):
        self.env_file_path = Path(env_file_path)
        self.ensure_env_file_exists()
        # Load environment variables from .env file
        load_dotenv(self.env_file_path)
    
    def ensure_env_file_exists(self):
        """Ensure .env file exists"""
        if not self.env_file_path.exists():
            self.env_file_path.touch()
            logger.info(f"Created .env file at {self.env_file_path}")
    
    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Get credentials from .env file"""
        try:
            # Read current environment
            username = os.getenv('USER_NAME')
            password = os.getenv('PASSWORD')
            
            if username and password:
                logger.info("Credentials loaded from environment variables")
                return username, password
            else:
                logger.info("No credentials found in environment variables")
                return None, None
                
        except Exception as e:
            logger.error(f"Error reading credentials: {str(e)}")
            return None, None
    
    def save_credentials(self, username: str, password: str) -> bool:
        """Save credentials to .env file"""
        try:
            # Read existing .env content
            env_content = {}
            if self.env_file_path.exists():
                with open(self.env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_content[key.strip()] = value.strip()
            
            # Update credentials
            env_content['USER_NAME'] = username
            env_content['PASSWORD'] = password
            
            # Ensure LOGIN_URL is set
            if 'LOGIN_URL' not in env_content:
                env_content['LOGIN_URL'] = 'https://ewaybillgst.gov.in/Login.aspx'
            
            # Write updated content
            with open(self.env_file_path, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            
            logger.info("Credentials saved successfully to .env file")
            
            # Update current environment variables
            os.environ['USER_NAME'] = username
            os.environ['PASSWORD'] = password
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            return False
    
    def has_credentials(self) -> bool:
        """Check if credentials are available"""
        username, password = self.get_credentials()
        return username is not None and password is not None
    
    def clear_credentials(self) -> bool:
        """Clear credentials from .env file"""
        try:
            # Read existing .env content
            env_content = {}
            if self.env_file_path.exists():
                with open(self.env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            if key.strip() not in ['USER_NAME', 'PASSWORD']:
                                env_content[key.strip()] = value.strip()
            
            # Write content without credentials
            with open(self.env_file_path, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            
            # Clear from current environment
            if 'USER_NAME' in os.environ:
                del os.environ['USER_NAME']
            if 'PASSWORD' in os.environ:
                del os.environ['PASSWORD']
            
            logger.info("Credentials cleared from .env file")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing credentials: {str(e)}")
            return False
    
    def update_env_variable(self, key: str, value: str) -> bool:
        """Update a single environment variable in .env file"""
        try:
            # Read existing .env content
            env_content = {}
            if self.env_file_path.exists():
                with open(self.env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            k, v = line.split('=', 1)
                            env_content[k.strip()] = v.strip()
            
            # Update the variable
            env_content[key] = value
            
            # Write updated content
            with open(self.env_file_path, 'w') as f:
                for k, v in env_content.items():
                    f.write(f"{k}={v}\n")
            
            # Update current environment
            os.environ[key] = value
            
            logger.info(f"Environment variable {key} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating environment variable {key}: {str(e)}")
            return False

# Global credentials manager instance
credentials_manager = CredentialsManager()
