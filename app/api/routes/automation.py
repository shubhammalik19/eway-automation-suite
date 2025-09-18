"""
API Routes for Automation Testing and Control
MCP (Model Context Protocol) endpoints for testing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from app.automation.eway_automation import PlaywrightEwayAutomation, run_automation_test, run_health_check
from app.core.logging import logger, log_operation
from app.core.credentials import credentials_manager
from app.core.config import settings

router = APIRouter()

class TestRequest(BaseModel):
    test_type: str = "login_flow"
    username: Optional[str] = None
    password: Optional[str] = None
    headless: bool = True

class LoginTestRequest(BaseModel):
    username: str
    password: str
    take_screenshots: bool = True

@router.get("/health")
async def automation_health_check():
    """
    MCP Health check endpoint
    Tests browser initialization and portal accessibility
    """
    try:
        log_operation("HEALTH_CHECK", "Starting automation health check")
        
        health_result = await run_health_check()
        
        if health_result["status"] == "healthy":
            return {
                "status": "healthy",
                "message": "Automation system is operational",
                "details": health_result
            }
        else:
            return {
                "status": "degraded",
                "message": "Some components are not healthy",
                "details": health_result
            }
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/test/login-flow")
async def test_login_flow():
    """
    MCP Test endpoint for login flow
    Tests navigation, form detection, CAPTCHA detection
    """
    try:
        log_operation("TEST_LOGIN_FLOW", "Starting login flow test")
        
        test_result = await run_automation_test()
        
        return {
            "success": test_result["success"],
            "message": "Login flow test completed",
            "test_results": test_result
        }
        
    except Exception as e:
        logger.error(f"Login flow test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

class LoginWithSaveRequest(BaseModel):
    username: str
    password: str
    save_to_env: bool = True
    max_attempts: int = 2

@router.post("/login/auto")
async def auto_login():
    """
    Automatic login using environment credentials with retry logic
    Asks user to login manually after max attempts exceeded
    """
    try:
        log_operation("AUTO_LOGIN", "Starting automatic login with retry logic")
        
        async with PlaywrightEwayAutomation() as automation:
            result = await automation.auto_login()
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "requires_manual_input": result.data.get("requires_manual_input", False) if result.data else False,
                "screenshot_path": result.screenshot_path
            }
            
    except Exception as e:
        logger.error(f"Auto-login API failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto-login failed: {str(e)}")

@router.post("/login/manual")
async def manual_login(request: LoginWithSaveRequest):
    """
    Manual login with credentials provided by user
    Optionally saves credentials to environment for future use
    """
    try:
        log_operation("MANUAL_LOGIN", f"Starting manual login for user: {request.username[:3]}***")
        
        async with PlaywrightEwayAutomation() as automation:
            # Reset login attempts for manual login
            automation.login_attempts = 0
            
            result = await automation.login_with_retry(request.username, request.password)
            
            # Save credentials if requested and login successful
            if result.success and request.save_to_env:
                saved = credentials_manager.save_credentials(request.username, request.password)
                if saved:
                    result.data = result.data or {}
                    result.data["credentials_saved"] = True
                    log_operation("MANUAL_LOGIN", "Credentials saved to environment for future use")
                else:
                    logger.warning("Failed to save credentials to environment")
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "credentials_saved": request.save_to_env and result.success,
                "screenshot_path": result.screenshot_path
            }
            
    except Exception as e:
        logger.error(f"Manual login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Manual login failed: {str(e)}")

@router.get("/credentials/status")
async def credentials_status():
    """
    Check if credentials are available in environment
    """
    try:
        has_credentials = credentials_manager.has_credentials()
        username, _ = credentials_manager.get_credentials()
        
        return {
            "has_credentials": has_credentials,
            "username": username[:3] + "***" if username else None,
            "auto_login_enabled": settings.auto_login,
            "save_on_success": settings.save_credentials_on_success
        }
        
    except Exception as e:
        logger.error(f"Credentials status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.delete("/credentials")
async def clear_credentials():
    """
    Clear saved credentials from environment
    """
    try:
        log_operation("CLEAR_CREDENTIALS", "Clearing saved credentials")
        
        success = credentials_manager.clear_credentials()
        
        if success:
            return {
                "success": True,
                "message": "Credentials cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear credentials")
            
    except Exception as e:
        logger.error(f"Clear credentials failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clear credentials failed: {str(e)}")

@router.post("/test/full-login")
async def test_full_login(request: LoginTestRequest):
    """
    MCP Test endpoint for full login with credentials
    WARNING: Use only in test environment
    """
    try:
        log_operation("TEST_FULL_LOGIN", f"Testing full login for user: {request.username}")
        
        async with PlaywrightEwayAutomation() as automation:
            # Override headless setting for testing if needed
            if not request.take_screenshots:
                automation.test_mode = False
            
            result = await automation.login(request.username, request.password)
            
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "error_details": result.error_details,
                "screenshot_path": result.screenshot_path
            }
            
    except Exception as e:
        logger.error(f"Full login test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login test failed: {str(e)}")

@router.get("/test/browser-capabilities")
async def test_browser_capabilities():
    """
    MCP Test endpoint for browser capabilities
    Tests browser types, viewport, locale settings
    """
    try:
        log_operation("TEST_BROWSER", "Testing browser capabilities")
        
        capabilities = {
            "browsers_available": [],
            "current_config": {
                "browser_type": "chromium",  # From settings
                "headless": True,
                "viewport": {"width": 1366, "height": 768},
                "locale": "en-IN",
                "timezone": "Asia/Kolkata"
            },
            "test_results": {}
        }
        
        # Test different browser types
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        
        try:
            # Test Chromium
            try:
                browser = await playwright.chromium.launch(headless=True)
                await browser.close()
                capabilities["browsers_available"].append("chromium")
                capabilities["test_results"]["chromium"] = "available"
            except:
                capabilities["test_results"]["chromium"] = "unavailable"
            
            # Test Firefox
            try:
                browser = await playwright.firefox.launch(headless=True)
                await browser.close()
                capabilities["browsers_available"].append("firefox")
                capabilities["test_results"]["firefox"] = "available"
            except:
                capabilities["test_results"]["firefox"] = "unavailable"
            
            # Test WebKit
            try:
                browser = await playwright.webkit.launch(headless=True)
                await browser.close()
                capabilities["browsers_available"].append("webkit")
                capabilities["test_results"]["webkit"] = "available"
            except:
                capabilities["test_results"]["webkit"] = "unavailable"
                
        finally:
            await playwright.stop()
        
        return {
            "success": True,
            "message": "Browser capabilities test completed",
            "capabilities": capabilities
        }
        
    except Exception as e:
        logger.error(f"Browser capabilities test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Browser test failed: {str(e)}")

@router.post("/debug/screenshot")
async def take_debug_screenshot(url: str = "https://ewaybillgst.gov.in/Login.aspx"):
    """
    MCP Debug endpoint to take screenshot of any URL
    Useful for debugging portal changes
    """
    try:
        log_operation("DEBUG_SCREENSHOT", f"Taking screenshot of: {url}")
        
        async with PlaywrightEwayAutomation() as automation:
            await automation.page.goto(url)
            await automation.page.wait_for_load_state("networkidle")
            
            screenshot_path = await automation.take_screenshot("debug_manual")
            
            return {
                "success": True,
                "message": "Screenshot captured successfully",
                "screenshot_path": screenshot_path,
                "url": url,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Screenshot capture failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Screenshot failed: {str(e)}")

@router.get("/test/portal-elements")
async def test_portal_elements():
    """
    MCP Test endpoint to analyze portal elements
    Identifies form fields, buttons, and structure changes
    """
    try:
        log_operation("TEST_PORTAL_ELEMENTS", "Analyzing portal elements")
        
        async with PlaywrightEwayAutomation() as automation:
            await automation.page.goto("https://ewaybillgst.gov.in/Login.aspx")
            await automation.page.wait_for_load_state("networkidle")
            
            # Analyze form elements
            elements = {
                "form_fields": {},
                "buttons": {},
                "links": {},
                "images": {},
                "structure": {}
            }
            
            # Find username fields
            username_selectors = [
                "input[name*='username']",
                "input[id*='username']", 
                "input[placeholder*='User']",
                "input[type='text']"
            ]
            
            for selector in username_selectors:
                element = await automation.page.query_selector(selector)
                if element:
                    attrs = await element.evaluate("el => ({ name: el.name, id: el.id, placeholder: el.placeholder, type: el.type })")
                    elements["form_fields"]["username_field"] = {
                        "selector": selector,
                        "attributes": attrs,
                        "found": True
                    }
                    break
            
            # Find password field
            password_element = await automation.page.query_selector("input[type='password']")
            if password_element:
                attrs = await password_element.evaluate("el => ({ name: el.name, id: el.id, placeholder: el.placeholder })")
                elements["form_fields"]["password_field"] = {
                    "selector": "input[type='password']",
                    "attributes": attrs,
                    "found": True
                }
            
            # Find submit buttons
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Login']",
                "button:has-text('Login')"
            ]
            
            for selector in submit_selectors:
                element = await automation.page.query_selector(selector)
                if element:
                    text = await element.text_content() if await element.evaluate("el => el.tagName") == "BUTTON" else await element.get_attribute("value")
                    elements["buttons"]["login_button"] = {
                        "selector": selector,
                        "text": text,
                        "found": True
                    }
                    break
            
            # Check for CAPTCHA
            captcha_present = await automation._check_captcha_present()
            elements["structure"]["captcha_present"] = captcha_present
            
            # Get page title
            title = await automation.page.title()
            elements["structure"]["page_title"] = title
            
            # Get current URL
            elements["structure"]["current_url"] = automation.page.url
            
            # Take screenshot for analysis
            screenshot_path = await automation.take_screenshot("portal_analysis")
            
            return {
                "success": True,
                "message": "Portal elements analyzed successfully",
                "elements": elements,
                "screenshot_path": screenshot_path,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Portal elements analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/status")
async def automation_status():
    """
    MCP Status endpoint providing current automation system status
    """
    try:
        from app.core.config import settings
        
        status = {
            "system_status": "operational",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "browser_type": settings.browser_type,
                "headless": settings.headless,
                "timeout": settings.timeout,
                "slow_mo": settings.slow_mo
            },
            "endpoints": {
                "health_check": "/api/automation/health",
                "login_flow_test": "/api/automation/test/login-flow",
                "full_login_test": "/api/automation/test/full-login",
                "browser_capabilities": "/api/automation/test/browser-capabilities",
                "debug_screenshot": "/api/automation/debug/screenshot",
                "portal_elements": "/api/automation/test/portal-elements"
            },
            "features": {
                "mcp_testing": True,
                "screenshot_capture": True,
                "element_analysis": True,
                "multi_browser_support": True,
                "session_management": True
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
