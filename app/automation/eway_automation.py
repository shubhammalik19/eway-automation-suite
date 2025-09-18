"""
Playwright-based E-way Bill Automation System
Using Model Context Protocol (MCP) for testing and development
"""

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import asyncio
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import re
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger, log_automation_step
from app.core.credentials import credentials_manager


@dataclass
class EwayBillData:
    """Data structure for E-way Bill information"""
    ewb_number: str
    valid_until: Optional[str] = None
    from_place: Optional[str] = None
    to_place: Optional[str] = None
    document_no: Optional[str] = None
    vehicle_number: Optional[str] = None
    kilometers: Optional[float] = None
    status: str = "pending"


@dataclass
class AutomationResult:
    """Result of automation operation"""
    success: bool
    message: str
    data: Optional[Dict] = None
    error_details: Optional[str] = None
    screenshot_path: Optional[str] = None


class PlaywrightEwayAutomation:
    """
    Main Playwright automation class for E-way Bill operations
    Implements MCP (Model Context Protocol) for consistent testing
    """
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.session_cookies = None
        self.login_url = settings.login_url
        
        # Login attempt tracking
        self.login_attempts = 0
        self.max_login_attempts = 2
        
        # MCP Testing Configuration
        self.test_mode = settings.debug
        self.screenshots_dir = Path("./data/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Playwright automation initialized in MCP mode")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_browser()

    async def start_browser(self, headless: bool = None) -> bool:
        """
        Start Playwright browser with MCP configuration
        Args:
            headless: Override headless mode. If None, uses DEBUG setting (headless when DEBUG=False)
        Returns: True if successful, False otherwise
        """
        try:
            log_automation_step("BROWSER_START", "Initializing Playwright browser")
            
            self.playwright = await async_playwright().start()
            
            # Determine headless mode based on DEBUG setting if not explicitly provided
            if headless is None:
                use_headless = not settings.debug  # headless when DEBUG=False, headful when DEBUG=True
            else:
                use_headless = headless
            
            logger.info(f"🖥️  Browser mode: {'headless' if use_headless else 'headful'} (DEBUG={settings.debug})")
            
            # Browser configuration for testing
            browser_config = {
                "headless": use_headless,
                "slow_mo": settings.slow_mo if not use_headless else 0,  # No slow_mo in headless
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            }
            
            # Launch browser based on configuration
            if settings.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(**browser_config)
            elif settings.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_config)
            else:
                self.browser = await self.playwright.webkit.launch(**browser_config)
            
            # Create context with Indian locale and viewport
            context_config = {
                "viewport": {"width": 1366, "height": 768},
                "locale": "en-IN",
                "timezone_id": "Asia/Kolkata",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # Load existing session cookies if available
            if self.session_cookies:
                context_config["storage_state"] = {"cookies": self.session_cookies}
            
            self.context = await self.browser.new_context(**context_config)
            
            # Enable request interception for debugging
            if self.test_mode:
                await self.context.route("**/*", self._log_requests)
            
            self.page = await self.context.new_page()
            
            # Set default timeouts
            self.page.set_default_timeout(settings.timeout)
            
            log_automation_step("BROWSER_START", "Browser started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            return False

    async def _log_requests(self, route, request):
        """Log HTTP requests for debugging (MCP testing mode)"""
        if self.test_mode:
            logger.debug(f"Request: {request.method} {request.url}")
        await route.continue_()

    async def close_browser(self):
        """Close browser and cleanup resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            log_automation_step("BROWSER_CLOSE", "Browser closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

    async def take_screenshot(self, name: str = None) -> str:
        """Take screenshot for debugging/testing"""
        if not self.page:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name or 'screenshot'}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        
        await self.page.screenshot(path=str(filepath), full_page=True)
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)

    async def auto_login(self) -> AutomationResult:
        """
        LEGAL COMPLIANCE: Auto-login functionality REMOVED
        Redirects to manual login system for legal compliance
        """
        logger.warning("Auto-login functionality has been REMOVED for legal compliance")
        log_automation_step("LEGAL_COMPLIANCE", "Auto-login disabled - redirecting to manual login")
        
        return AutomationResult(
            success=False,
            message="Auto-login disabled for legal compliance. Use manual login system instead.",
            data={
                "legal_compliance": True,
                "auto_login_disabled": True,
                "manual_login_required": True,
                "instructions": "Use: python manual_login_system.py manual-login"
            }
        )
    
    async def login_with_retry(self, username: str = None, password: str = None) -> AutomationResult:
        """
        LEGAL COMPLIANCE: Automated login with retry REMOVED
        Redirects to manual login system for legal compliance
        """
        logger.warning("Automated login with retry has been REMOVED for legal compliance")
        log_automation_step("LEGAL_COMPLIANCE", "Login retry disabled - manual login required")
        
        return AutomationResult(
            success=False,
            message="Automated login disabled for legal compliance. Use manual login system instead.",
            data={
                "legal_compliance": True,
                "automated_retry_disabled": True,
                "manual_login_required": True,
                "max_attempts_exceeded": True,
                "requires_manual_input": True,
                "action_required": "Use: python manual_login_system.py manual-login"
            }
        )

    async def login(self, username: str = None, password: str = None) -> AutomationResult:
        """
        LEGAL COMPLIANCE: Automated login functionality REMOVED
        Redirects to manual login system for legal compliance
        """
        logger.warning("Automated login functionality has been REMOVED for legal compliance")
        log_automation_step("LEGAL_COMPLIANCE", "Automated login disabled - manual entry required")
        
        return AutomationResult(
            success=False,
            message="Automated login disabled for legal compliance. User must login manually.",
            data={
                "legal_compliance": True,
                "automated_login_disabled": True,
                "manual_login_required": True,
                "action_required": "Use manual login system: python manual_login_system.py manual-login"
            }
        )

    async def _check_captcha_present(self) -> bool:
        """Check if CAPTCHA is present on the page"""
        captcha_selectors = [
            "#imgcaptcha",  # Specific E-way portal CAPTCHA
            "img[src='Captcha.aspx']",
            "img[src*='Captcha.aspx']",
            "img[src*='captcha']",
            "img[src*='Captcha']",
            "img[alt*='captcha']",
            "img[alt*='Captcha']",
            "#captcha",
            ".captcha"
        ]
        
        for selector in captcha_selectors:
            element = await self.page.query_selector(selector)
            if element:
                return True
        
        return False

    async def get_captcha_image(self) -> dict:
        """Get CAPTCHA image as base64 encoded string"""
        try:
            # Navigate to login page first
            await self.page.goto("https://ewaybillgst.gov.in/Login.aspx")
            await self.page.wait_for_load_state("networkidle")
            
            # Find CAPTCHA image with priority selectors
            captcha_selectors = [
                "#imgcaptcha",  # Primary E-way portal selector
                "img[src='Captcha.aspx']",
                "img[src*='Captcha.aspx']",
                "img[src*='captcha']",
                "img[src*='Captcha']",
                "img[alt*='captcha']",
                "img[alt*='Captcha']",
                "#captcha",
                ".captcha"
            ]
            
            captcha_element = None
            for selector in captcha_selectors:
                captcha_element = await self.page.query_selector(selector)
                if captcha_element:
                    logger.info(f"Found CAPTCHA with selector: {selector}")
                    break
            
            if not captcha_element:
                return {
                    "success": False,
                    "message": "No CAPTCHA found on the page"
                }
            
            # Wait a bit for the CAPTCHA to fully load
            await self.page.wait_for_timeout(1000)
            
            # Get CAPTCHA image as base64
            captcha_image = await captcha_element.screenshot()
            import base64
            captcha_base64 = base64.b64encode(captcha_image).decode('utf-8')
            
            return {
                "success": True,
                "captcha_image": captcha_base64,
                "message": "CAPTCHA image retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to get CAPTCHA image: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get CAPTCHA image: {str(e)}"
            }

    async def login_with_captcha(self, username: str, password: str, captcha_text: str = None) -> dict:
        """Login with CAPTCHA support - following the working Selenium pattern"""
        try:
            # Navigate to login page
            await self.page.goto("https://ewaybillgst.gov.in/Login.aspx")
            await self.page.wait_for_load_state("networkidle")
            log_automation_step("LOGIN_START", "Navigated to login page")

            # FIRST ATTEMPT: Fill credentials (like Selenium does first)
            credentials_filled = await self._fill_login_credentials(username, password)
            if not credentials_filled:
                return {
                    "success": False,
                    "captcha_required": False,
                    "message": "Could not fill login credentials"
                }

            # Check if CAPTCHA is present
            captcha_present = await self._check_captcha_present()
            log_automation_step("CAPTCHA_CHECK", f"CAPTCHA present: {captcha_present}")

            if captcha_present and not captcha_text:
                # Return CAPTCHA image for user input
                captcha_result = await self.get_captcha_image()
                return {
                    "success": False,
                    "captcha_required": True,
                    "captcha_image": captcha_result.get("captcha_image"),
                    "message": "Please enter CAPTCHA to continue"
                }

            # CRITICAL: Following Selenium pattern - refresh page to reset CSRF token
            if captcha_present and captcha_text:
                log_automation_step("CSRF_RESET", "🔄 Refreshing page to reset CSRF token (like working Selenium)")

                await self.page.reload()
                await self.page.wait_for_load_state("networkidle")
                await self.page.wait_for_timeout(2000)  # 2 second wait like Selenium

                # SECOND ATTEMPT: Re-fill credentials after refresh (like Selenium)
                log_automation_step("REFILL_CREDS", "Re-filling credentials after page refresh")
                credentials_filled = await self._fill_login_credentials(username, password)
                if not credentials_filled:
                    return {
                        "success": False,
                        "captcha_required": False,
                        "message": "Could not re-fill credentials after refresh"
                    }

                # Fill CAPTCHA after refresh - wait for DOM to be ready
                log_automation_step("CAPTCHA_WAIT", "Waiting for page to be fully loaded after refresh")
                
                # Wait for the login form to be ready (important after refresh)
                try:
                    await self.page.wait_for_selector("form", timeout=10000)
                    await self.page.wait_for_load_state("domcontentloaded")
                    await self.page.wait_for_timeout(2000)  # Additional 2 seconds for any dynamic content
                except Exception as e:
                    log_automation_step("CAPTCHA_ERROR", f"Error waiting for page to load: {str(e)}")
                
                captcha_selectors = [
                    "input[name='txtCaptcha']", 
                    "#txtCaptcha",
                    "input[type='text'][name='txtCaptcha']",
                    "input[id='txtCaptcha']"
                ]
                captcha_filled = False

                # First, debug what CAPTCHA fields are available after refresh
                log_automation_step("CAPTCHA_DEBUG", "Searching for CAPTCHA input after page refresh")
                all_inputs = await self.page.query_selector_all("input")
                for i, input_elem in enumerate(all_inputs):
                    try:
                        input_name = await input_elem.get_attribute("name") or ""
                        input_id = await input_elem.get_attribute("id") or ""
                        input_type = await input_elem.get_attribute("type") or ""
                        if "captcha" in input_name.lower() or "captcha" in input_id.lower():
                            log_automation_step("CAPTCHA_DEBUG", f"Found potential CAPTCHA field: name='{input_name}', id='{input_id}', type='{input_type}'")
                    except:
                        pass

                # Try each selector with explicit wait
                for selector in captcha_selectors:
                    try:
                        # First, wait for the element to exist
                        await self.page.wait_for_selector(selector, timeout=5000)
                        captcha_input = await self.page.query_selector(selector)
                        
                        if captcha_input:
                            # Check if element is visible and enabled
                            is_visible = await captcha_input.is_visible()
                            is_enabled = await captcha_input.is_enabled()
                            
                            if not is_visible:
                                log_automation_step("CAPTCHA_DEBUG", f"CAPTCHA field {selector} found but not visible")
                                continue
                                
                            if not is_enabled:
                                log_automation_step("CAPTCHA_DEBUG", f"CAPTCHA field {selector} found but not enabled")
                                continue
                            
                            await captcha_input.click()
                            await captcha_input.select_all()
                            await captcha_input.type(captcha_text.lower())
                            captcha_filled = True
                            log_automation_step("CAPTCHA_FILL", f"CAPTCHA filled with {selector} (lowercase)")
                            break
                        else:
                            log_automation_step("CAPTCHA_DEBUG", f"Selector {selector} found by wait but not by query")
                    except Exception as e:
                        log_automation_step("CAPTCHA_DEBUG", f"Wait for {selector} failed: {str(e)}")
                        continue

                if not captcha_filled:
                    log_automation_step("CAPTCHA_ERROR", "Could not find any CAPTCHA input field after refresh")
                    # Return CAPTCHA required instead of failing completely
                    captcha_result = await self.get_captcha_image()
                    return {
                        "success": False,
                        "captcha_required": True,
                        "captcha_image": captcha_result.get("captcha_image"),
                        "message": "CAPTCHA field not found after page refresh. Please try again."
                    }

            # Debug form state
            await self._debug_form_inputs()

            # CRITICAL DIFFERENCE: Selenium doesn't click submit! It waits for auto-login!
            log_automation_step("WAIT_AUTO_LOGIN", "🚨 NOT clicking submit - waiting for auto-login like Selenium")

            # Wait for URL change (indicating login attempt completion)
            login_url = 'https://ewaybillgst.gov.in/Login.aspx'
            current_url = self.page.url
            max_wait_seconds = 30
            wait_seconds = 0

            while current_url == login_url and wait_seconds < max_wait_seconds:
                await self.page.wait_for_timeout(1000)  # Wait 1 second
                current_url = self.page.url
                wait_seconds += 1

                if wait_seconds % 5 == 0:  # Log every 5 seconds
                    log_automation_step("AUTO_LOGIN_WAIT", f"Waiting for auto-login... {wait_seconds}/{max_wait_seconds}s")

            log_automation_step("URL_CHANGE", f"URL changed from {login_url} to {current_url}")

            # Check if we're still on login page (indicates failure)
            if current_url == login_url:
                log_automation_step("LOGIN_TIMEOUT", "Still on login page after timeout")
                # Get fresh CAPTCHA for retry
                captcha_result = await self.get_captcha_image()
                return {
                    "success": False,
                    "captcha_required": True,
                    "captcha_image": captcha_result.get("captcha_image"),
                    "message": "Login timeout. Please try again with correct CAPTCHA."
                }

            # Verify login success
            login_success = await self._verify_login_success()
            log_automation_step("LOGIN_VERIFY", f"Login verification result: {login_success}")

            if login_success:
                log_automation_step("LOGIN_SUCCESS", "✅ Login successful!")
                return {
                    "success": True,
                    "message": "Login successful",
                    "session_data": {
                        "url": self.page.url,
                        "cookies": await self.page.context.cookies()
                    }
                }
            else:
                log_automation_step("LOGIN_FAILED", "Login verification failed")

                # Check for error messages
                error_selectors = [
                    ".error",
                    ".alert-danger", 
                    "[id*='error']",
                    "[class*='error']",
                    ".validation-summary-errors",
                    ".field-validation-error",
                    "[id*='ErrorMessage']",
                    "[id*='lblError']",
                    "[id*='Error']",
                    ".text-danger",
                    ".alert",
                    "span[style*='color:red']",
                    "span[style*='color:#red']",
                    ".red",
                    "[class*='validation']",
                    "div[style*='color:red']"
                ]

                error_message = "Login failed"
                for selector in error_selectors:
                    try:
                        error_elements = await self.page.query_selector_all(selector)
                        log_automation_step("LOGIN_DEBUG", f"Found {len(error_elements)} elements for selector: {selector}")
                        for i, error_element in enumerate(error_elements):
                            try:
                                text = await error_element.text_content()
                                inner_html = await error_element.inner_html()
                                is_visible = await error_element.is_visible()
                                log_automation_step("LOGIN_DEBUG", f"Element {i}: visible={is_visible}, text='{text}', html='{inner_html[:100]}'")

                                if text and text.strip() and is_visible:
                                    error_message = text.strip()
                                    log_automation_step("LOGIN_DEBUG", f"Found error message: {error_message}")
                                    break
                            except Exception as e:
                                log_automation_step("LOGIN_DEBUG", f"Error processing element {i}: {str(e)}")

                        if error_message != "Login failed":
                            break
                    except Exception as e:
                        log_automation_step("LOGIN_DEBUG", f"Error checking selector {selector}: {str(e)}")
                        continue

                # Check if CAPTCHA is still present
                captcha_still_present = await self._check_captcha_present()
                log_automation_step("LOGIN_DEBUG", f"CAPTCHA still present after login attempt: {captcha_still_present}")

                # If CAPTCHA is still present, it might be wrong
                if captcha_present and captcha_still_present:
                    captcha_result = await self.get_captcha_image()
                    log_automation_step("LOGIN_DEBUG", "Returning CAPTCHA required response due to failed login")
                    return {
                        "success": False,
                        "captcha_required": True,
                        "captcha_image": captcha_result.get("captcha_image"),
                        "message": f"{error_message}. Please try again with correct CAPTCHA."
                    }

                return {
                    "success": False,
                    "message": error_message
                }

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {
                "success": False,
                "message": f"Login error: {str(e)}"
            }

    async def _fill_login_credentials(self, username: str, password: str):
        """Helper method to fill username and password fields"""
        try:
            # Fill username - Updated selectors based on actual E-way portal form structure
            username_selectors = [
                "input[name='txt_username']",  # Actual E-way portal field name
                "#txt_username",
                "input[type='text']",
                "input[name='txtUsername']", 
                "#txtUsername",
                "input[name='username']",
                "#username"
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    username_input = await self.page.query_selector(selector)
                    if username_input:
                        await username_input.fill(username)
                        username_filled = True
                        log_automation_step("CREDENTIALS", f"Username filled with selector: {selector}")
                        break
                except:
                    continue
            
            if not username_filled:
                log_automation_step("CREDENTIALS_ERROR", "Failed to fill username field")
                return False
            
            # Fill password - Updated selectors based on actual E-way portal form structure
            password_selectors = [
                "input[name='txt_password']",  # Actual E-way portal field name  
                "#txt_password",
                "input[type='password']",
                "input[name='txtPassword']",
                "#txtPassword", 
                "input[name='password']",
                "#password"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = await self.page.query_selector(selector)
                    if password_input:
                        await password_input.fill(password)
                        password_filled = True
                        log_automation_step("CREDENTIALS", f"Password filled with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_filled:
                log_automation_step("CREDENTIALS_ERROR", "Failed to fill password field")
                
            return password_filled
            
        except Exception as e:
            log_automation_step("CREDENTIALS_ERROR", f"Error filling credentials: {str(e)}")
            return False

    async def _debug_form_inputs(self):
        """Debug method to log all form inputs and their values"""
        try:
            log_automation_step("FORM_DEBUG", "Analyzing form inputs before submission")
            
            # Get all form inputs
            inputs = await self.page.query_selector_all("input")
            
            for i, input_element in enumerate(inputs):
                try:
                    input_type = await input_element.get_attribute("type") or "text"
                    input_name = await input_element.get_attribute("name") or ""
                    input_id = await input_element.get_attribute("id") or ""
                    input_value = await input_element.get_attribute("value") or ""
                    
                    # Mask sensitive data
                    display_value = input_value
                    if input_type == "password":
                        display_value = "*" * len(input_value) if input_value else ""
                    elif "captcha" in input_name.lower():
                        display_value = f"[{len(input_value)} chars]" if input_value else ""
                    
                    log_automation_step("FORM_DEBUG", f"Input {i}: type='{input_type}', name='{input_name}', id='{input_id}', value='{display_value}'")
                    
                except Exception as e:
                    log_automation_step("FORM_DEBUG", f"Error analyzing input {i}: {str(e)}")
            
            # Check for hidden inputs that might be required
            hidden_inputs = await self.page.query_selector_all("input[type='hidden']")
            log_automation_step("FORM_DEBUG", f"Found {len(hidden_inputs)} hidden inputs")
            
            for i, hidden_input in enumerate(hidden_inputs):
                try:
                    hidden_name = await hidden_input.get_attribute("name") or ""
                    hidden_value = await hidden_input.get_attribute("value") or ""
                    log_automation_step("FORM_DEBUG", f"Hidden {i}: name='{hidden_name}', value='{hidden_value[:50]}...'")
                except Exception as e:
                    log_automation_step("FORM_DEBUG", f"Error analyzing hidden input {i}: {str(e)}")
                    
        except Exception as e:
            log_automation_step("FORM_DEBUG", f"Form debug error: {str(e)}")

    async def _debug_page_content(self, context: str = ""):
        """Debug method to log page content for troubleshooting"""
        try:
            current_url = self.page.url
            page_title = await self.page.title()
            
            log_automation_step("DEBUG_PAGE", f"{context} - URL: {current_url}")
            log_automation_step("DEBUG_PAGE", f"{context} - Title: {page_title}")
            
            # Check for common elements that might indicate login state
            debug_selectors = [
                "form",
                "input[type='password']",
                "[href*='logout']",
                "[href*='dashboard']",
                ".error",
                ".alert",
                "h1",
                "h2",
                ".navbar",
                ".menu"
            ]
            
            for selector in debug_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        element_count = len(elements)
                        first_element = elements[0]
                        element_text = ""
                        try:
                            element_text = await first_element.text_content()
                            element_text = element_text[:100] if element_text else ""
                        except:
                            pass
                        
                        log_automation_step("DEBUG_PAGE", f"{context} - Found {element_count} '{selector}' elements. First: {element_text}")
                except Exception as e:
                    log_automation_step("DEBUG_PAGE", f"{context} - Error checking '{selector}': {str(e)}")
            
        except Exception as e:
            log_automation_step("DEBUG_PAGE", f"{context} - Debug page content error: {str(e)}")

    async def _verify_login_success(self) -> bool:
        """Verify if login was successful"""
        current_url = self.page.url
        log_automation_step("LOGIN_VERIFY", f"Verifying login success - Current URL: {current_url}")
        
        # Check URL patterns that indicate successful login
        success_patterns = [
            "dashboard",
            "home",
            "main",
            "index",
            "menu"
        ]
        
        # Check if redirected away from login page
        if self.login_url not in current_url:
            log_automation_step("LOGIN_VERIFY", f"URL changed from login page: {self.login_url}")
            for pattern in success_patterns:
                if pattern in current_url.lower():
                    log_automation_step("LOGIN_VERIFY", f"Found success pattern '{pattern}' in URL")
                    return True
            log_automation_step("LOGIN_VERIFY", "No success patterns found in URL")
        else:
            log_automation_step("LOGIN_VERIFY", "Still on login page")
        
        # Check for elements that indicate successful login
        success_elements = [
            "text=/Welcome/i",
            "text=/Dashboard/i",
            "text=/Logout/i",
            "text=/Sign Out/i",
            "[href*='logout']",
            "[href*='signout']"
        ]
        
        for selector in success_elements:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    element_text = await element.text_content() if hasattr(element, 'text_content') else ""
                    log_automation_step("LOGIN_VERIFY", f"Found success element with selector '{selector}': {element_text}")
                    return True
            except Exception as e:
                log_automation_step("LOGIN_VERIFY", f"Error checking selector '{selector}': {str(e)}")
        
        log_automation_step("LOGIN_VERIFY", "No success elements found - login likely failed")
        return False

    async def _get_error_message(self) -> str:
        """Extract error message from the page"""
        error_selectors = [
            ".error",
            ".alert-danger",
            ".text-danger",
            "[class*='error']",
            "[id*='error']",
            "text=/Invalid|Error|Failed/i"
        ]
        
        for selector in error_selectors:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                if text and text.strip():
                    return text.strip()
        
        return "Unknown error occurred"

    async def test_login_flow(self) -> Dict[str, Any]:
        """
        MCP Test method to verify login flow
        Returns detailed test results for development
        """
        test_results = {
            "test_name": "login_flow_test",
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "success": False,
            "screenshots": []
        }
        
        try:
            # Test browser initialization
            test_results["steps"].append({
                "step": "browser_init",
                "status": "success" if await self.start_browser() else "failed"
            })
            
            # Test navigation to login page
            await self.page.goto(self.login_url)
            test_results["steps"].append({
                "step": "navigate_to_login",
                "status": "success",
                "url": self.page.url
            })
            
            screenshot = await self.take_screenshot("test_login_page")
            test_results["screenshots"].append(screenshot)
            
            # Test form element detection
            username_field = await self.page.query_selector("input[name*='username'], input[id*='username']")
            password_field = await self.page.query_selector("input[type='password']")
            
            test_results["steps"].append({
                "step": "form_elements_detected",
                "status": "success" if (username_field and password_field) else "failed",
                "username_field": bool(username_field),
                "password_field": bool(password_field)
            })
            
            # Test CAPTCHA detection
            captcha_present = await self._check_captcha_present()
            test_results["steps"].append({
                "step": "captcha_detection",
                "status": "success",
                "captcha_present": captcha_present
            })
            
            test_results["success"] = True
            
        except Exception as e:
            test_results["error"] = str(e)
            test_results["success"] = False
            
        finally:
            await self.close_browser()
            
        return test_results

    async def manual_login(self, headless: bool = False) -> Dict[str, Any]:
        """
        UPDATED: Use integrated session manager for manual login
        Compatible with the manual login system for legal compliance
        """
        try:
            logger.info("Starting integrated manual login process...")
            log_automation_step("MANUAL_LOGIN", "Using integrated session manager")
            
            # Import the session manager from our app
            from app.core.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            # Start browser for manual login (always headful for user interaction)
            if not headless:
                # Start browser in visible mode for manual interaction
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    slow_mo=500,
                    args=[
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security'
                    ]
                )
                self.context = await self.browser.new_context(
                    viewport={"width": 1366, "height": 768},
                    locale="en-IN",
                    timezone_id="Asia/Kolkata"
                )
                self.page = await self.context.new_page()
                self.page.set_default_timeout(30000)
            else:
                # Use existing browser setup for headless mode
                await self.start_browser(headless=True)
            
            # Navigate to E-way login page
            await self.page.goto("https://ewaybillgst.gov.in/Login.aspx", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)
            
            # CRITICAL: Reload page once for CSRF token refresh (required for login)
            logger.info("🔄 Reloading page for CSRF token refresh...")
            await self.page.reload()
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            
            logger.info("✅ Login page ready. Please login manually in the browser...")
            
            # Wait for user to login manually
            login_success = await self._wait_for_manual_login()
            
            if login_success:
                # Create session using our session manager
                session_info = await session_manager.create_session(
                    page=self.page,
                    login_method="integrated_manual"
                )
                
                # Take success screenshot
                screenshot_path = await self.take_screenshot("integrated_login_success")
                
                logger.info("🎉 Integrated manual login successful!")
                log_automation_step("MANUAL_LOGIN", f"Session created: {session_info.session_id}")
                
                # Check if we should close browser based on debug mode
                from app.core.config import settings
                if not settings.debug:
                    logger.info("📴 Production mode: Closing browser after successful login")
                    await self.close_browser()
                else:
                    logger.info("🐛 Debug mode: Keeping browser open for debugging")
                
                return {
                    "success": True,
                    "message": "Integrated manual login successful",
                    "session_id": session_info.session_id,
                    "expires_at": session_info.expires_at.isoformat(),
                    "screenshot": screenshot_path,
                    "browser_closed": not settings.debug
                }
            else:
                return {
                    "success": False,
                    "message": "Manual login was not completed or timed out"
                }
                
        except Exception as e:
            logger.error(f"Integrated manual login failed: {str(e)}")
            return {
                "success": False,
                "message": f"Integrated manual login error: {str(e)}"
            }
        finally:
            # Only close browser if not in debug mode
            from app.core.config import settings
            if settings.debug:
                logger.info("🐛 Debug mode: Browser will remain open for debugging")
            else:
                logger.info("📴 Production mode: Closing browser automatically")
                try:
                    await self.close_browser()
                except Exception as e:
                    logger.warning(f"Error closing browser: {str(e)}")

    async def _wait_for_manual_login(self, timeout: int = 300) -> bool:
        """
        Wait for user to complete manual login (5 minute timeout)
        """
        logger.info("Waiting for manual login completion...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if we're on dashboard or any logged-in page
                current_url = self.page.url
                
                # Check for login success indicators
                if any(indicator in current_url.lower() for indicator in [
                    "dashboard", "home", "main", "index"
                ]) and "login" not in current_url.lower():
                    logger.info("Manual login detected - user appears to be logged in!")
                    return True
                
                # Check for specific logged-in elements
                logged_in_indicators = [
                    "text=Dashboard",
                    "text=Logout",
                    "text=Welcome",
                    "[title*='Logout']",
                    "[alt*='Logout']"
                ]
                
                for indicator in logged_in_indicators:
                    try:
                        element = await self.page.query_selector(indicator)
                        if element and await element.is_visible():
                            logger.info(f"Login success detected via element: {indicator}")
                            return True
                    except:
                        continue
                
                # Wait 2 seconds before checking again
                await self.page.wait_for_timeout(2000)
                
            except Exception as e:
                logger.error(f"Error while waiting for login: {str(e)}")
                await self.page.wait_for_timeout(2000)
        
        logger.warning("Manual login timeout - user did not complete login in time")
        return False

    async def login_with_autofill(self, headless: bool = False) -> Dict[str, Any]:
        """
        Login with auto-fill: open page, reload once, auto-fill credentials from env
        """
        try:
            logger.info("Starting login with auto-fill...")
            log_automation_step("AUTOFILL_LOGIN", "Opening login page with auto-fill enabled")
            
            # Get credentials from environment
            import os
            from dotenv import load_dotenv
            
            # Load .env file
            load_dotenv()
            
            username = os.getenv('USER_NAME', '')
            password = os.getenv('PASSWORD', '')
            
            if not username or not password:
                return {
                    "success": False,
                    "message": "Username or password not found in environment variables USER_NAME and PASSWORD"
                }
            
            # Import the session manager from our app
            from app.core.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            # Start browser for auto-fill login (always headful for manual interaction)
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Always headful for login - user needs to see CAPTCHA
                slow_mo=500,
                args=[
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-IN",
                timezone_id="Asia/Kolkata"
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(30000)
            
            # Navigate to login page
            logger.info("🌐 Navigating to E-way Bill portal...")
            
            # Navigate to E-way login page
            logger.info("🌐 Opening E-way Bill login page...")
            await self.page.goto("https://ewaybillgst.gov.in/Login.aspx", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)
            
            # CRITICAL: Reload page once for CSRF token refresh
            logger.info("🔄 Reloading page for CSRF token refresh...")
            await self.page.reload()
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Auto-fill username and password
            logger.info("✍️  Auto-filling username and password...")
            log_automation_step("AUTOFILL", "Filling username from environment")
            
            # Find and fill username field
            username_selectors = [
                'input[name="txtUserName"]',
                'input[id*="UserName"]',
                'input[type="text"]',
                'input[placeholder*="User"]'
            ]
            
            for selector in username_selectors:
                try:
                    username_field = await self.page.query_selector(selector)
                    if username_field:
                        await username_field.fill(username)
                        logger.info(f"✅ Username filled using selector: {selector}")
                        break
                except:
                    continue
            
            # Wait a bit
            await self.page.wait_for_timeout(1000)
            
            log_automation_step("AUTOFILL", "Filling password from environment")
            
            # Find and fill password field
            password_selectors = [
                'input[name="txtPassword"]',
                'input[id*="Password"]',
                'input[type="password"]'
            ]
            
            for selector in password_selectors:
                try:
                    password_field = await self.page.query_selector(selector)
                    if password_field:
                        await password_field.fill(password)
                        logger.info(f"✅ Password filled using selector: {selector}")
                        break
                except:
                    continue
            
            # Wait for user to handle CAPTCHA and submit
            logger.info("🔒 Please solve CAPTCHA and click login button manually...")
            logger.info("⏳ Waiting for login completion...")
            
            # Wait for user to complete login (solve CAPTCHA and submit)
            login_success = await self._wait_for_manual_login(timeout=300)
            
            if login_success:
                # Create session using our session manager
                session_info = await session_manager.create_session(
                    page=self.page,
                    login_method="autofill_login"
                )
                
                # Take success screenshot
                screenshot_path = await self.take_screenshot("autofill_login_success")
                
                logger.info("🎉 Auto-fill login successful!")
                log_automation_step("AUTOFILL_LOGIN", f"Session created: {session_info.session_id}")
                
                # Check if we should close browser based on debug mode
                from app.core.config import settings
                if not settings.debug:
                    logger.info("📴 Production mode: Closing browser after successful login")
                    await self.close_browser()
                else:
                    logger.info("🐛 Debug mode: Keeping browser open for debugging")
                
                return {
                    "success": True,
                    "message": "Auto-fill login successful",
                    "session_id": session_info.session_id,
                    "expires_at": session_info.expires_at.isoformat(),
                    "screenshot": screenshot_path,
                    "browser_closed": not settings.debug
                }
            else:
                return {
                    "success": False,
                    "message": "Login was not completed or timed out"
                }
                
        except Exception as e:
            logger.error(f"Auto-fill login failed: {str(e)}")
            return {
                "success": False,
                "message": f"Auto-fill login error: {str(e)}"
            }
        finally:
            # Only close browser if not in debug mode
            from app.core.config import settings
            if settings.debug:
                logger.info("🐛 Debug mode: Browser will remain open for testing")
            else:
                logger.info("📴 Production mode: Closing browser automatically")
                try:
                    await self.close_browser()
                except Exception as e:
                    logger.warning(f"Error closing browser: {str(e)}")

    async def _save_session(self) -> Dict[str, Any]:
        """
        Save current browser session for future use
        """
        try:
            # Get session storage and cookies
            cookies = await self.context.cookies()
            local_storage = await self.page.evaluate("""() => {
                const storage = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    storage[key] = localStorage.getItem(key);
                }
                return storage;
            }""")
            
            session_data = {
                "session_id": f"manual_session_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "expires": (datetime.now() + timedelta(hours=8)).isoformat(),  # 8 hour session
                "cookies": cookies,
                "local_storage": local_storage,
                "url": self.page.url,
                "user_agent": await self.page.evaluate("navigator.userAgent")
            }
            
            # Save to file
            session_file = Path("data/sessions") / f"{session_data['session_id']}.json"
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"Session saved: {session_file}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            return {"error": str(e)}

    async def load_saved_session(self, session_id: str = None) -> Dict[str, Any]:
        """
        UPDATED: Load session using integrated session manager
        Compatible with manual login system sessions
        """
        try:
            # Import the session manager from our app
            from app.core.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            # Get session info
            if session_id:
                session_info = session_manager.load_session(session_id)
            else:
                session_info = session_manager.get_latest_session()
            
            if not session_info:
                return {"success": False, "message": "No session found"}
            
            if session_info.is_expired():
                return {"success": False, "message": "Session has expired"}
            
            # Start browser and restore session
            await self.start_browser()
            
            # Restore session using session manager
            success = await session_manager.restore_session(session_info, self.page)
            
            if success:
                # Validate session
                is_valid = await session_manager.validate_session(self.page)
                
                if is_valid:
                    self.is_logged_in = True
                    logger.info(f"Integrated session {session_info.session_id} loaded successfully")
                    return {
                        "success": True,
                        "session_id": session_info.session_id,
                        "message": "Session loaded and validated successfully",
                        "expires_at": session_info.expires_at.isoformat()
                    }
                else:
                    return {"success": False, "message": "Session validation failed"}
            else:
                return {"success": False, "message": "Session restore failed"}
                
        except Exception as e:
            logger.error(f"Failed to load integrated session: {str(e)}")
            return {"success": False, "message": f"Session load error: {str(e)}"}

    async def list_saved_sessions(self) -> Dict[str, Any]:
        """
        UPDATED: List sessions using integrated session manager  
        Compatible with manual login system sessions
        """
        try:
            # Import the session manager from our app
            from app.core.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            # Get all sessions
            sessions = session_manager.list_sessions()
            
            session_list = []
            for session in sessions:
                session_list.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "is_expired": session.is_expired(),
                    "time_remaining": session.time_remaining() if not session.is_expired() else "Expired",
                    "login_method": session.login_method
                })
            
            return {
                "success": True,
                "sessions": session_list,
                "total": len(session_list)
            }
            
        except Exception as e:
            logger.error(f"Failed to list integrated sessions: {str(e)}")
            return {"success": False, "message": f"Error listing sessions: {str(e)}"}

    def get_session_manager_status(self) -> Dict[str, Any]:
        """
        Get status of integrated session manager
        """
        try:
            from app.core.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            sessions = session_manager.list_sessions()
            active_sessions = [s for s in sessions if not s.is_expired()]
            
            return {
                "success": True,
                "total_sessions": len(sessions),
                "active_sessions": len(active_sessions),
                "latest_session": sessions[0].session_id if sessions else None,
                "integration_active": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Session manager error: {str(e)}",
                "integration_active": False
            }

    async def list_saved_sessions(self) -> Dict[str, Any]:
        """
        List all available saved sessions
        """
        try:
            sessions_dir = Path("data/sessions")
            if not sessions_dir.exists():
                return {"success": True, "sessions": []}
            
            sessions = []
            for session_file in sessions_dir.glob("manual_session_*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    expires = datetime.fromisoformat(session_data["expires"])
                    is_expired = datetime.now() > expires
                    
                    sessions.append({
                        "session_id": session_data["session_id"],
                        "created": session_data["timestamp"],
                        "expires": session_data["expires"],
                        "expired": is_expired,
                        "size": session_file.stat().st_size
                    })
                except:
                    continue
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x["created"], reverse=True)
            
            return {"success": True, "sessions": sessions}
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
            return {"success": False, "message": f"Error listing sessions: {str(e)}"}

    async def health_check(self) -> Dict[str, Any]:
        """MCP Health check for the automation system"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        try:
            # Check browser initialization
            browser_ok = await self.start_browser()
            health_status["components"]["browser"] = "healthy" if browser_ok else "unhealthy"
            
            # Check portal accessibility
            if browser_ok:
                await self.page.goto(self.login_url, timeout=10000)
                portal_accessible = self.page.url == self.login_url
                health_status["components"]["portal"] = "healthy" if portal_accessible else "unhealthy"
            else:
                health_status["components"]["portal"] = "unknown"
            
            # Check screenshot capability
            try:
                screenshot_path = await self.take_screenshot("health_check")
                health_status["components"]["screenshots"] = "healthy"
                health_status["test_screenshot"] = screenshot_path
            except:
                health_status["components"]["screenshots"] = "unhealthy"
            
            # Overall status
            all_healthy = all(status == "healthy" for status in health_status["components"].values())
            health_status["status"] = "healthy" if all_healthy else "degraded"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        finally:
            await self.close_browser()
        
        return health_status
    
    # Extension System Integration
    def get_extensions(self):
        """
        Get extension system integrated with current automation instance
        """
        from app.automation.eway_extensions import EwayExtensions
        return EwayExtensions(self)
    
    async def extend_single_eway_bill(self, ewb_number: str, new_destination: str, 
                                    transport_mode: str = "Road", 
                                    vehicle_number: str = "") -> AutomationResult:
        """
        Extend single E-way bill using integrated extension system
        """
        extensions = self.get_extensions()
        return await extensions.extend_single_bill(
            ewb_number=ewb_number,
            new_destination=new_destination,
            transport_mode=transport_mode,
            vehicle_number=vehicle_number
        )
    
    async def extend_from_csv_file(self, csv_file_path: str) -> AutomationResult:
        """
        Extend multiple E-way bills from CSV file
        """
        extensions = self.get_extensions()
        return await extensions.extend_from_csv(csv_file_path)
    
    async def auto_extend_expiring_bills(self, days_threshold: int = 1, 
                                       default_destination: str = None) -> AutomationResult:
        """
        Auto-extend expiring E-way bills
        """
        extensions = self.get_extensions()
        return await extensions.auto_extend_expiring(
            days_threshold=days_threshold,
            default_destination=default_destination
        )


# Utility functions for MCP testing
async def run_automation_test():
    """Quick test function for MCP verification"""
    async with PlaywrightEwayAutomation() as automation:
        result = await automation.test_login_flow()
        return result

async def run_health_check():
    """Health check function for monitoring"""
    automation = PlaywrightEwayAutomation()
    return await automation.health_check()
