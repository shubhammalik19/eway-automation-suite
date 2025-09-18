#!/usr/bin/env python3
"""
E-way Bill Manual Login System - LEGAL COMPLIANCE VERSION
NO AUTOMATION - User must manually enter everything
Only shows credentials from environment for reference
"""

import asyncio
import sys
import time
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.core.session_manager import EwaySessionManager, get_session_manager
from app.core.logging import logger, log_automation_step
from playwright.async_api import async_playwright


class ManualOnlyLoginSystem:
    """
    Manual-Only E-way Bill Login System - LEGAL COMPLIANCE
    NO AUTOMATION - Only opens browser, user does everything manually
    Shows environment credentials for reference only
    """
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.playwright = None
        self.browser = None
        self.page = None
    
    def get_credentials_from_env(self):
        """
        Get credentials from environment variables for display reference only
        Does NOT auto-fill - only shows for user convenience
        """
        username = os.getenv('EWAY_USERNAME', '')
        password = os.getenv('EWAY_PASSWORD', '')
        
        return username, password
    
    async def check_login_page(self):
        """
        Verify eWayBill login page is accessible
        """
        print("🔍 Checking eWayBill login page accessibility...")
        
        try:
            await self._start_browser(headless=True)
            
            # Navigate to login page
            await self.page.goto("https://ewaybillgst.gov.in/Login.aspx", 
                                wait_until="networkidle", timeout=30000)
            
            # Take screenshot
            screenshot_path = await self._take_screenshot("login_page_check")
            
            # Get basic page info
            title = await self.page.title()
            url = self.page.url
            
            # Check if we can find the login form
            form_elements = await self._analyze_login_form()
            
            print(f"✅ Login page accessible")
            print(f"📄 Title: {title}")
            print(f"🔗 URL: {url}")
            print(f"📝 Username field: {'✅' if form_elements['username'] else '❌'}")
            print(f"🔐 Password field: {'✅' if form_elements['password'] else '❌'}")
            print(f"🖼️ CAPTCHA present: {'✅' if form_elements['captcha'] else '❌'}")
            print(f"📸 Screenshot: {screenshot_path}")
            
            return {
                "success": True,
                "title": title,
                "url": url,
                "form_complete": all([form_elements['username'], form_elements['password']]),
                "captcha_present": form_elements['captcha'],
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            print(f"❌ Login page check failed: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            await self._close_browser()
    
    async def _analyze_login_form(self):
        """Analyze login form elements"""
        try:
            # Look for username field
            username_field = await self.page.query_selector(
                "input[name='txt_username'], input[type='text']:not([type='hidden']):not([name*='captcha'])"
            )
            
            # Look for password field  
            password_field = await self.page.query_selector("input[type='password']")
            
            # Look for CAPTCHA
            captcha_image = await self.page.query_selector(
                "img[src*='Captcha'], img[src*='captcha'], #imgcaptcha"
            )
            
            return {
                "username": bool(username_field),
                "password": bool(password_field),
                "captcha": bool(captcha_image)
            }
            
        except Exception as e:
            logger.error(f"Form analysis error: {str(e)}")
            return {"username": False, "password": False, "captcha": False}
    
    async def start_manual_login(self):
        """
        Open browser for COMPLETELY manual login - LEGAL COMPLIANCE
        NO AUTOMATION - user must manually enter everything
        Only shows environment credentials for reference
        """
        print("🚀 Starting Completely Manual Login Process")
        print("=" * 50)
        print("⚖️  LEGAL COMPLIANCE: NO AUTOMATION")
        print("📌 Browser will open to login page")
        print("👤 You MUST manually type username")
        print("🔐 You MUST manually type password")
        print("🔒 You MUST manually solve CAPTCHA")
        print("🖱️  You MUST manually click Login button")
        print("⏱️  System only detects successful completion")
        print("💾 Session saved for future headless use")
        print()
        
        # Get credentials from environment for user reference ONLY
        username, password = self.get_credentials_from_env()
        
        if username:
            print("📋 Environment Credential Reference:")
            print(f"   Username: {username}")
            print(f"   Password: {'*' * len(password) if password else 'Not set'}")
            print("   ⚠️  You must manually type these into browser")
            print()
        else:
            print("💡 Optional: Set environment variables for reference:")
            print("   export EWAY_USERNAME='your_username'")
            print("   export EWAY_PASSWORD='your_password'")
            print()
        
        try:
            # Start browser in visible mode
            await self._start_browser(headless=False)
            
            # Navigate to login page
            print("🌐 Opening eWayBill login page...")
            await self.page.goto("https://ewaybillgst.gov.in/Login.aspx", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)  # Wait 2 seconds
            
            # Take initial screenshot
            await self._take_screenshot("manual_login_start")
            
            # CRITICAL: Reload page once to refresh CSRF token
            print("🔄 Reloading page once for CSRF token refresh...")
            await self.page.reload()
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)  # Wait for page to be ready
            
            await self._take_screenshot("login_page_ready")
            
            print("✅ Login page is ready")
            print("👆 Please complete ALL steps manually in the browser:")
            print("   1. Manually type username")
            print("   2. Manually type password") 
            print("   3. Manually solve CAPTCHA")
            print("   4. Manually click Login button")
            print()
            print("🔍 System monitoring for successful login...")
            
            # Wait for manual login completion
            login_success = await self._wait_for_manual_login()
            
            if login_success:
                print("🎉 Manual login successful!")
                
                # Create and save session
                session_info = await self.session_manager.create_session(
                    page=self.page,
                    login_method="completely_manual"
                )
                
                # Take success screenshot
                success_screenshot = await self._take_screenshot("login_success")
                
                print(f"💾 Session saved successfully!")
                print(f"   📋 Session ID: {session_info.session_id}")
                print(f"   ⏰ Valid until: {session_info.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   ⏳ Duration: {session_info.time_remaining()}")
                print(f"   📸 Screenshot: {success_screenshot}")
                
                # Keep browser open for a moment so user can see success
                print("✅ Login completed! Browser will close in 5 seconds...")
                await asyncio.sleep(5)
                
                return {
                    "success": True,
                    "session_id": session_info.session_id,
                    "expires_at": session_info.expires_at.isoformat(),
                    "screenshot": success_screenshot
                }
                
            else:
                print("❌ Manual login was not completed or timed out")
                print("💡 Please try again - you have 5 minutes to complete login")
                
                return {
                    "success": False,
                    "message": "Login not completed within timeout period"
                }
                
        except Exception as e:
            print(f"❌ Manual login failed: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            await self._close_browser()
    
    async def _wait_for_manual_login(self, timeout: int = 300) -> bool:
        """
        Wait for user to complete manual login
        Detects success by URL changes and page elements
        """
        start_time = time.time()
        initial_url = self.page.url
        
        print(f"⏳ Waiting for manual login (timeout: {timeout//60} minutes)")
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.page.url
                
                # Method 1: Check if URL changed from login page
                if current_url != initial_url and "login" not in current_url.lower():
                    print(f"🔗 URL changed: {current_url}")
                    await asyncio.sleep(3)  # Wait for page to stabilize
                    return True
                
                # Method 2: Look for logout/dashboard elements
                success_indicators = [
                    "text=/logout/i", 
                    "text=/sign out/i",
                    "text=/dashboard/i",
                    "[href*='logout']",
                    "text=/welcome/i",
                    "text=/home/i"
                ]
                
                for indicator in success_indicators:
                    try:
                        element = await self.page.query_selector(indicator)
                        if element and await element.is_visible():
                            print(f"✅ Success indicator found: {indicator}")
                            return True
                    except:
                        continue
                
                # Method 3: Check page title changes
                current_title = await self.page.title()
                if current_title and "login" not in current_title.lower():
                    if current_title not in ["Login | E-WayBill System", "E-WayBill System"]:
                        print(f"📄 Title changed: {current_title}")
                        return True
                
                # Show progress every 30 seconds
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0 and elapsed > 0:
                    remaining = timeout - elapsed
                    print(f"⏳ Still waiting... ({remaining//60}m {remaining%60}s remaining)")
                
                # Wait before next check
                await self.page.wait_for_timeout(2000)
                
            except Exception as e:
                logger.warning(f"Login detection error: {str(e)}")
                await asyncio.sleep(2)
        
        print("⏰ Manual login timeout reached")
        return False
    
    async def test_saved_session(self, session_id: str = None):
        """
        Test a saved session by loading it
        """
        print(f"🧪 Testing saved session: {session_id or 'latest'}")
        
        try:
            # Get session
            if session_id:
                session_info = self.session_manager.load_session(session_id)
            else:
                session_info = self.session_manager.get_latest_session()
            
            if not session_info:
                print("❌ No session found to test")
                return {"success": False, "message": "No session found"}
            
            if session_info.is_expired():
                print(f"❌ Session {session_info.session_id} has expired")
                return {"success": False, "message": "Session expired"}
            
            print(f"📋 Session Details:")
            print(f"   ID: {session_info.session_id}")
            print(f"   Created: {session_info.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Expires: {session_info.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Time left: {session_info.time_remaining()}")
            
            # Start browser and restore session
            await self._start_browser(headless=False)
            
            print("🔄 Restoring session...")
            success = await self.session_manager.restore_session(session_info, self.page)
            
            if success:
                # Validate session
                is_valid = await self.session_manager.validate_session(self.page)
                
                if is_valid:
                    print("✅ Session restored and validated!")
                    
                    # Take screenshot
                    screenshot = await self._take_screenshot("session_test")
                    
                    # Get current info
                    current_url = self.page.url
                    current_title = await self.page.title()
                    
                    print(f"🌐 Current URL: {current_url}")
                    print(f"📄 Current title: {current_title}")
                    print(f"📸 Screenshot: {screenshot}")
                    
                    # Keep browser open for user to see
                    print("✅ Session test successful! Browser will close in 10 seconds...")
                    await asyncio.sleep(10)
                    
                    return {
                        "success": True,
                        "session_id": session_info.session_id,
                        "current_url": current_url,
                        "screenshot": screenshot
                    }
                else:
                    print("❌ Session validation failed - session may have expired")
                    return {"success": False, "message": "Session validation failed"}
            else:
                print("❌ Failed to restore session")
                return {"success": False, "message": "Session restore failed"}
                
        except Exception as e:
            print(f"❌ Session test failed: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            await self._close_browser()
    
    def list_sessions(self):
        """List all saved sessions"""
        print("📋 Saved Sessions")
        print("=" * 40)
        
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print("No saved sessions found.")
            print("💡 Use 'manual-login' command to create your first session")
            return []
        
        for i, session in enumerate(sessions, 1):
            status = "🟢 ACTIVE" if not session.is_expired() else "🔴 EXPIRED"
            
            print(f"{i}. {status} {session.session_id}")
            print(f"   Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Expires: {session.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if not session.is_expired():
                print(f"   Time left: {session.time_remaining()}")
            
            if session.user_info:
                if 'display_name' in session.user_info:
                    print(f"   User: {session.user_info['display_name']}")
            
            print()
        
        return sessions
    
    def cleanup_sessions(self):
        """Remove expired sessions"""
        print("🧹 Cleaning up expired sessions...")
        
        cleaned = self.session_manager.cleanup_expired_sessions()
        
        if cleaned > 0:
            print(f"✅ Removed {cleaned} expired sessions")
        else:
            print("✅ No expired sessions to remove")
        
        return cleaned
    
    async def _start_browser(self, headless: bool = False):
        """Start browser with optimal settings"""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            slow_mo=500 if not headless else 0,
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-dev-shm-usage'
            ]
        )
        
        self.page = await self.browser.new_page()
        
        # Set timeout
        self.page.set_default_timeout(30000)
        
        # Set viewport for non-headless
        if not headless:
            await self.page.set_viewport_size({"width": 1366, "height": 768})
    
    async def _close_browser(self):
        """Clean browser shutdown"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Browser cleanup error: {str(e)}")
    
    async def _take_screenshot(self, name: str) -> str:
        """Take screenshot with timestamp"""
        if not self.page:
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        
        screenshots_dir = Path("data/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = screenshots_dir / filename
        
        await self.page.screenshot(path=str(filepath), full_page=True)
        return str(filepath)


async def main():
    """Main function with command handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Completely Manual E-way Bill Login System - Legal Compliance")
    parser.add_argument("command", 
                       choices=["check", "manual-login", "test-session", "list", "cleanup", "interactive"],
                       help="Command to execute")
    parser.add_argument("--session-id", help="Specific session ID for testing")
    
    args = parser.parse_args()
    
    system = ManualOnlyLoginSystem()
    
    try:
        if args.command == "check":
            result = await system.check_login_page()
            if not result["success"]:
                print("Login page check failed - please check your internet connection")
                
        elif args.command == "manual-login":
            result = await system.start_manual_login()
            if result["success"]:
                print(f"\n🎉 Success! Session ID: {result['session_id']}")
            else:
                print(f"\n❌ Failed: {result.get('message', 'Unknown error')}")
                
        elif args.command == "test-session":
            result = await system.test_saved_session(args.session_id)
            if result["success"]:
                print("\n✅ Session test successful!")
            else:
                print(f"\n❌ Session test failed: {result.get('message', 'Unknown error')}")
                
        elif args.command == "list":
            system.list_sessions()
            
        elif args.command == "cleanup":
            system.cleanup_sessions()
            
        elif args.command == "interactive":
            await interactive_mode(system)
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


async def interactive_mode(system):
    """Interactive menu-driven mode"""
    print("\n🎯 Completely Manual E-way Bill Login System")
    print("=" * 50)
    print("⚖️  LEGAL COMPLIANCE: NO AUTOMATION")
    print("👤 You must manually enter ALL credentials in browser")
    print("📋 Environment variables shown for reference only")
    print()
    
    while True:
        print("\n📋 Available Commands:")
        print("1. Check login page")
        print("2. Start manual login")
        print("3. Test saved session")
        print("4. List sessions")
        print("5. Cleanup expired sessions")
        print("6. Exit")
        
        choice = input("\n👆 Enter choice (1-6): ").strip()
        
        try:
            if choice == "1":
                await system.check_login_page()
                
            elif choice == "2":
                print("\n🔐 Completely Manual Login - Legal Compliance")
                print("⚖️  NO AUTOMATION - You must manually enter everything")
                print("📋 Environment credentials shown for reference only")
                print()
                
                result = await system.start_manual_login()
                if result["success"]:
                    print(f"\n🎉 Login successful! Session: {result['session_id']}")
                    
                    # Ask about testing
                    test_now = input("\n🧪 Test this session now? (y/n): ").lower().strip()
                    if test_now == 'y':
                        await system.test_saved_session(result['session_id'])
                
            elif choice == "3":
                sessions = system.list_sessions()
                if sessions:
                    print("\nEnter session number to test (or Enter for latest):")
                    session_choice = input("👆 Choice: ").strip()
                    
                    if session_choice.isdigit():
                        session_num = int(session_choice) - 1
                        if 0 <= session_num < len(sessions):
                            session_id = sessions[session_num].session_id
                            await system.test_saved_session(session_id)
                        else:
                            print("❌ Invalid session number")
                    else:
                        await system.test_saved_session()
                        
            elif choice == "4":
                system.list_sessions()
                
            elif choice == "5":
                system.cleanup_sessions()
                
            elif choice == "6":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())