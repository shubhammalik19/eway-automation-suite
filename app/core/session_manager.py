"""
Enhanced Session Manager for E-way Bill Portal
Handles session persistence, validation, and reuse
"""

import json
import pickle
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio

from app.core.logging import logger, log_automation_step


@dataclass
class SessionInfo:
    """Session information structure"""
    session_id: str
    created_at: datetime
    expires_at: datetime
    user_info: Dict[str, Any]
    cookies: List[Dict]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    last_url: str
    user_agent: str
    is_active: bool = True
    login_method: str = "manual"  # manual, auto, captcha
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    def time_remaining(self) -> timedelta:
        """Get remaining time for session"""
        if self.is_expired():
            return timedelta(0)
        return self.expires_at - datetime.now()


class EwaySessionManager:
    """
    Enhanced session manager for E-way Bill portal
    """
    
    def __init__(self, sessions_dir: str = "data/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_session: Optional[SessionInfo] = None
        
        # Session settings
        self.default_session_duration = timedelta(hours=8)  # 8 hours
        self.max_session_duration = timedelta(hours=24)     # 24 hours
        
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = int(time.time())
        return f"eway_session_{timestamp}"
    
    async def create_session(self, 
                           page, 
                           user_info: Dict = None, 
                           login_method: str = "manual",
                           duration: timedelta = None) -> SessionInfo:
        """
        Create a new session from browser state
        """
        try:
            log_automation_step("SESSION_CREATE", f"Creating new session via {login_method}")
            
            # Generate session info
            session_id = self.generate_session_id()
            now = datetime.now()
            expires = now + (duration or self.default_session_duration)
            
            # Get browser state
            cookies = await page.context.cookies()
            current_url = page.url
            user_agent = await page.evaluate("navigator.userAgent")
            
            # Get storage data
            local_storage = await page.evaluate("""() => {
                const storage = {};
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                } catch(e) {
                    console.log('LocalStorage access error:', e);
                }
                return storage;
            }""")
            
            session_storage = await page.evaluate("""() => {
                const storage = {};
                try {
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }
                } catch(e) {
                    console.log('SessionStorage access error:', e);
                }
                return storage;
            }""")
            
            # Extract user info from page if not provided
            if not user_info:
                user_info = await self._extract_user_info(page)
            
            # Create session object
            session_info = SessionInfo(
                session_id=session_id,
                created_at=now,
                expires_at=expires,
                user_info=user_info or {},
                cookies=cookies,
                local_storage=local_storage,
                session_storage=session_storage,
                last_url=current_url,
                user_agent=user_agent,
                login_method=login_method
            )
            
            # Save session
            await self.save_session(session_info)
            self.active_session = session_info
            
            log_automation_step("SESSION_CREATE", f"Session {session_id} created successfully")
            return session_info
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    async def _extract_user_info(self, page) -> Dict[str, Any]:
        """
        Extract user information from the page
        """
        user_info = {}
        
        try:
            # Look for common user info elements
            user_selectors = [
                "text=/Welcome/i",
                "text=/Hello/i", 
                "[class*='user']",
                "[class*='profile']",
                "[id*='user']",
                ".navbar-text",
                ".user-info"
            ]
            
            for selector in user_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text and text.strip():
                            user_info["display_name"] = text.strip()
                            break
                except:
                    continue
            
            # Get page title for context
            user_info["page_title"] = await page.title()
            user_info["current_url"] = page.url
            
        except Exception as e:
            logger.warning(f"Could not extract user info: {str(e)}")
        
        return user_info
    
    async def save_session(self, session_info: SessionInfo):
        """
        Save session to disk
        """
        try:
            session_file = self.sessions_dir / f"{session_info.session_id}.json"
            
            # Convert to serializable format
            session_data = {
                "session_id": session_info.session_id,
                "created_at": session_info.created_at.isoformat(),
                "expires_at": session_info.expires_at.isoformat(),
                "user_info": session_info.user_info,
                "cookies": session_info.cookies,
                "local_storage": session_info.local_storage,
                "session_storage": session_info.session_storage,
                "last_url": session_info.last_url,
                "user_agent": session_info.user_agent,
                "is_active": session_info.is_active,
                "login_method": session_info.login_method
            }
            
            # Save as JSON
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Also save as pickle for Python objects
            pickle_file = self.sessions_dir / f"{session_info.session_id}.pkl"
            with open(pickle_file, 'wb') as f:
                pickle.dump(session_info, f)
            
            log_automation_step("SESSION_SAVE", f"Session saved: {session_file}")
            
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            raise
    
    def load_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Load session from disk
        """
        try:
            # Try pickle first (preserves Python objects)
            pickle_file = self.sessions_dir / f"{session_id}.pkl"
            if pickle_file.exists():
                with open(pickle_file, 'rb') as f:
                    session_info = pickle.load(f)
                    return session_info
            
            # Fallback to JSON
            json_file = self.sessions_dir / f"{session_id}.json"
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Convert back to SessionInfo
                session_info = SessionInfo(
                    session_id=session_data["session_id"],
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    expires_at=datetime.fromisoformat(session_data["expires_at"]),
                    user_info=session_data["user_info"],
                    cookies=session_data["cookies"],
                    local_storage=session_data["local_storage"],
                    session_storage=session_data.get("session_storage", {}),
                    last_url=session_data["last_url"],
                    user_agent=session_data["user_agent"],
                    is_active=session_data.get("is_active", True),
                    login_method=session_data.get("login_method", "manual")
                )
                
                return session_info
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
            return None
    
    def list_sessions(self) -> List[SessionInfo]:
        """
        List all available sessions
        """
        sessions = []
        
        try:
            # Get all session files
            json_files = list(self.sessions_dir.glob("eway_session_*.json"))
            
            for json_file in json_files:
                session_id = json_file.stem
                session_info = self.load_session(session_id)
                
                if session_info:
                    sessions.append(session_info)
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda s: s.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
        
        return sessions
    
    def get_active_sessions(self) -> List[SessionInfo]:
        """
        Get all non-expired sessions
        """
        return [s for s in self.list_sessions() if not s.is_expired()]
    
    def get_latest_session(self) -> Optional[SessionInfo]:
        """
        Get the most recently created active session
        """
        active_sessions = self.get_active_sessions()
        return active_sessions[0] if active_sessions else None
    
    async def restore_session(self, session_info: SessionInfo, page):
        """
        Restore a session to a browser page
        """
        try:
            log_automation_step("SESSION_RESTORE", f"Restoring session {session_info.session_id}")
            
            # Check if session is still valid
            if session_info.is_expired():
                raise ValueError(f"Session {session_info.session_id} has expired")
            
            # Set cookies
            if session_info.cookies:
                await page.context.add_cookies(session_info.cookies)
                log_automation_step("SESSION_RESTORE", f"Restored {len(session_info.cookies)} cookies")
            
            # Navigate to last URL
            await page.goto(session_info.last_url or "https://ewaybillgst.gov.in")
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Restore local storage
            if session_info.local_storage:
                await page.evaluate("""(storage) => {
                    for (const [key, value] of Object.entries(storage)) {
                        try {
                            localStorage.setItem(key, value);
                        } catch(e) {
                            console.log('Error setting localStorage:', key, e);
                        }
                    }
                }""", session_info.local_storage)
                log_automation_step("SESSION_RESTORE", f"Restored {len(session_info.local_storage)} localStorage items")
            
            # Restore session storage
            if session_info.session_storage:
                await page.evaluate("""(storage) => {
                    for (const [key, value] of Object.entries(storage)) {
                        try {
                            sessionStorage.setItem(key, value);
                        } catch(e) {
                            console.log('Error setting sessionStorage:', key, e);
                        }
                    }
                }""", session_info.session_storage)
                log_automation_step("SESSION_RESTORE", f"Restored {len(session_info.session_storage)} sessionStorage items")
            
            # Refresh page to apply all changes
            await page.reload()
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            self.active_session = session_info
            log_automation_step("SESSION_RESTORE", "Session restored successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore session: {str(e)}")
            return False
    
    async def validate_session(self, page) -> bool:
        """
        Validate if current session is still active
        """
        try:
            # Check URL - should not be on login page
            current_url = page.url
            if "login" in current_url.lower():
                return False
            
            # Check for logged-in indicators
            logged_in_selectors = [
                "text=/logout/i",
                "text=/sign out/i",
                "text=/dashboard/i",
                "text=/welcome/i",
                "[href*='logout']",
                "[onclick*='logout']"
            ]
            
            for selector in logged_in_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self):
        """
        Remove expired session files
        """
        try:
            cleaned_count = 0
            
            for session_info in self.list_sessions():
                if session_info.is_expired():
                    # Remove files
                    json_file = self.sessions_dir / f"{session_info.session_id}.json"
                    pickle_file = self.sessions_dir / f"{session_info.session_id}.pkl"
                    
                    json_file.unlink(missing_ok=True)
                    pickle_file.unlink(missing_ok=True)
                    
                    cleaned_count += 1
            
            if cleaned_count > 0:
                log_automation_step("SESSION_CLEANUP", f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Session cleanup error: {str(e)}")
            return 0
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of all sessions
        """
        sessions = self.list_sessions()
        active_sessions = [s for s in sessions if not s.is_expired()]
        
        return {
            "total_sessions": len(sessions),
            "active_sessions": len(active_sessions),
            "expired_sessions": len(sessions) - len(active_sessions),
            "latest_session": active_sessions[0].session_id if active_sessions else None,
            "sessions": [
                {
                    "session_id": s.session_id,
                    "created": s.created_at.isoformat(),
                    "expires": s.expires_at.isoformat(),
                    "expired": s.is_expired(),
                    "time_remaining": str(s.time_remaining()),
                    "login_method": s.login_method,
                    "user_info": s.user_info
                }
                for s in sessions
            ]
        }


# Utility functions
def get_session_manager() -> EwaySessionManager:
    """Get singleton session manager instance"""
    if not hasattr(get_session_manager, "_instance"):
        get_session_manager._instance = EwaySessionManager()
    return get_session_manager._instance