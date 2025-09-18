import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "EwayAuto - Playwright Automation"
    debug: bool = False
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./data/ewayauto.db"
    
    # Eway Portal Configuration
    login_url: str = "https://ewaybillgst.gov.in/Login.aspx"
    user_name: Optional[str] = None
    password: Optional[str] = None
    
    # Auto-login Configuration - LEGAL COMPLIANCE
    auto_login: bool = False  # PERMANENTLY DISABLED - Only manual login supported for legal compliance
    save_credentials_on_success: bool = False  # PERMANENTLY DISABLED - No automatic credential saving
    automated_form_filling: bool = False  # PERMANENTLY DISABLED - All form filling must be manual
    legal_compliance_mode: bool = True  # ENFORCED - Ensures no automation of login process
    
    # Playwright Configuration
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    slow_mo: int = 0  # milliseconds
    timeout: int = 30000  # milliseconds
    
    # Session Configuration
    session_timeout_hours: int = 8  # Maximum session duration
    auto_refresh_session: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/ewayauto.log"
    
    # File Paths
    data_dir: Path = Path("./data")
    logs_dir: Path = Path("./logs")
    static_dir: Path = Path("./app/static")
    templates_dir: Path = Path("./app/templates")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)
settings.static_dir.mkdir(parents=True, exist_ok=True)
settings.templates_dir.mkdir(parents=True, exist_ok=True)
