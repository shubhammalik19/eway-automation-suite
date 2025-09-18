"""
Authentication API routes for web interface
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import asyncio

from app.automation.eway_automation import PlaywrightEwayAutomation
from app.core.logging import logger, log_operation
from app.core.credentials import credentials_manager

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str
    captcha: Optional[str] = None
    remember_session: bool = False

class LoginResponse(BaseModel):
    success: bool
    message: str
    requires_captcha: bool = False
    captcha_image_url: Optional[str] = None
    session_saved: bool = False

@router.post("/login", response_model=LoginResponse)
async def web_login(request: LoginRequest):
    """
    Web interface login endpoint with CAPTCHA support
    """
    try:
        log_operation("WEB_LOGIN", f"Login attempt for user: {request.username[:3]}***")
        
        async with PlaywrightEwayAutomation() as automation:
            # Try to login with provided credentials and CAPTCHA
            result = await automation.login_with_captcha(
                username=request.username,
                password=request.password,
                captcha_text=request.captcha
            )
            
            # Check if CAPTCHA is required
            captcha_required = result.get("captcha_required", False)
            captcha_url = None
            
            if captcha_required and result.get("captcha_image"):
                # Save CAPTCHA image to static directory
                import base64
                import os
                from datetime import datetime
                
                captcha_data = result["captcha_image"]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                captcha_filename = f"captcha_{timestamp}.png"
                captcha_path = f"/home/shubham/ewayauto/app/static/screenshots/{captcha_filename}"
                
                # Ensure screenshots directory exists
                os.makedirs("/home/shubham/ewayauto/app/static/screenshots", exist_ok=True)
                
                # Save the image
                with open(captcha_path, "wb") as f:
                    f.write(base64.b64decode(captcha_data))
                
                captcha_url = f"/static/screenshots/{captcha_filename}"
            
            # Save credentials if successful and remember session is checked
            if result.get("success") and request.remember_session:
                credentials_manager.save_credentials(request.username, request.password)
                logger.info("Credentials saved for future sessions")
            
            return LoginResponse(
                success=result.get("success", False),
                message=result.get("message", "Unknown error"),
                requires_captcha=captcha_required,
                captcha_image_url=captcha_url,
                session_saved=request.remember_session and result.get("success", False)
            )
            
    except Exception as e:
        logger.error(f"Web login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/captcha")
async def get_current_captcha():
    """
    Get current CAPTCHA image from the portal
    """
    try:
        log_operation("GET_CAPTCHA", "Fetching current CAPTCHA from portal")
        
        async with PlaywrightEwayAutomation() as automation:
            result = await automation.get_captcha_image()
            
            if result["success"]:
                # Save CAPTCHA image to static directory
                import base64
                import os
                from datetime import datetime
                
                captcha_data = result["captcha_image"]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                captcha_filename = f"captcha_{timestamp}.png"
                captcha_path = f"/home/shubham/ewayauto/app/static/screenshots/{captcha_filename}"
                
                # Ensure screenshots directory exists
                os.makedirs("/home/shubham/ewayauto/app/static/screenshots", exist_ok=True)
                
                # Save the image
                with open(captcha_path, "wb") as f:
                    f.write(base64.b64decode(captcha_data))
                
                return {
                    "success": True,
                    "captcha_image": captcha_data,  # Return base64 for direct display
                    "captcha_url": f"/static/screenshots/{captcha_filename}",
                    "message": "CAPTCHA retrieved successfully"
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Failed to get CAPTCHA")
                }
                
    except Exception as e:
        logger.error(f"CAPTCHA fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CAPTCHA fetch failed: {str(e)}")


@router.post("/manual-login")
async def start_manual_login():
    """
    Start manual login process - opens browser for user to login manually
    """
    try:
        automation = PlaywrightEwayAutomation()
        result = await automation.manual_login(headless=False)
        
        if result["success"]:
            return LoginResponse(
                success=True,
                message=result["message"],
                session_id=result.get("session_id"),
                captcha_required=False
            )
        else:
            return LoginResponse(
                success=False,
                message=result["message"],
                captcha_required=False
            )
            
    except Exception as e:
        logger.error(f"Manual login failed: {str(e)}")
        return LoginResponse(
            success=False,
            message=f"Manual login error: {str(e)}",
            captcha_required=False
        )

@router.get("/sessions")
async def list_sessions():
    """
    List all saved login sessions
    """
    try:
        automation = PlaywrightEwayAutomation()
        result = await automation.list_saved_sessions()
        return result
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

@router.post("/load-session/{session_id}")
async def load_session(session_id: str):
    """
    Load a previously saved session
    """
    try:
        automation = PlaywrightEwayAutomation()
        result = await automation.load_saved_session(session_id)
        
        if result["success"]:
            return LoginResponse(
                success=True,
                message=result["message"],
                session_id=result.get("session_id"),
                captcha_required=False
            )
        else:
            return LoginResponse(
                success=False,
                message=result["message"],
                captcha_required=False
            )
            
    except Exception as e:
        logger.error(f"Failed to load session: {str(e)}")
        return LoginResponse(
            success=False,
            message=f"Session load error: {str(e)}",
            captcha_required=False
        )

@router.post("/trigger-login")
async def trigger_web_ui_login():
    """
    Trigger login process from web UI - opens browser with auto-fill
    """
    try:
        logger.info("🚀 Starting web UI triggered login with auto-fill...")
        
        automation = PlaywrightEwayAutomation()
        
        # Use auto-fill login (always headful for user interaction)
        result = await automation.login_with_autofill(headless=False)
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Login process completed"),
            "session_id": result.get("session_id"),
            "browser_opened": True,
            "requires_manual_completion": True
        }
        
    except Exception as e:
        logger.error(f"Web UI login trigger failed: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to trigger login: {str(e)}"
        }


@router.get("/status")
async def get_auth_status():
    """
    Get current authentication status for web UI
    """
    try:
        from app.core.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        # Check active sessions
        active_sessions = session_manager.get_active_sessions()
        
        # Handle case where get_active_sessions returns a list instead of dict
        if isinstance(active_sessions, list):
            session_count = len(active_sessions)
            session_keys = [f"session_{i}" for i, _ in enumerate(active_sessions)]
        else:
            session_count = len(active_sessions)
            session_keys = list(active_sessions.keys()) if active_sessions else []
        
        is_logged_in = session_count > 0
        
        return {
            "success": True,
            "logged_in": is_logged_in,
            "active_sessions": session_count,
            "status": "logged_in" if is_logged_in else "logged_out",
            "session_info": {
                "count": session_count,
                "sessions": session_keys
            }
        }
        
    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        return {
            "success": False,
            "logged_in": False,
            "message": f"Status check failed: {str(e)}"
        }


@router.post("/logout")
async def logout_all_sessions():
    """
    Logout and clear all active sessions
    """
    try:
        from app.core.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        # Clear all sessions
        cleared_count = session_manager.clear_all_sessions()
        
        logger.info(f"🔐 Logged out via web UI - cleared {cleared_count} sessions")
        
        return {
            "success": True,
            "message": f"Successfully logged out and cleared {cleared_count} sessions",
            "cleared_sessions": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return {
            "success": False,
            "message": f"Logout failed: {str(e)}"
        }


@router.get("/session")
async def get_current_session():
    """
    Get current login session status
    """
    try:
        # Try to verify if there's an active session
        automation = PlaywrightEwayAutomation()
        
        # Check if we have any recent sessions
        sessions_result = await automation.list_saved_sessions()
        
        if sessions_result["success"] and sessions_result["sessions"]:
            valid_sessions = [s for s in sessions_result["sessions"] if not s["expired"]]
            if valid_sessions:
                latest_session = valid_sessions[0]
                return {
                    "success": True,
                    "session_active": True,
                    "session_id": latest_session["session_id"],
                    "expires": latest_session["expires"],
                    "created": latest_session["created"]
                }
        
        return {
            "success": True,
            "session_active": False,
            "message": "No active sessions found"
        }
        
    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}
async def get_session_status():
    """
    Check current session status
    """
    try:
        # For now, return a simple response
        # In a real implementation, you'd check for valid session cookies/tokens
        return {
            "authenticated": False,
            "message": "No active session"
        }
    except Exception as e:
        logger.error(f"Session check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session check failed: {str(e)}")
