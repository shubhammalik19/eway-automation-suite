#!/usr/bin/env python3
"""
Simple E-way Bill Login System
Direct login with auto-fill functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.automation.eway_automation import PlaywrightEwayAutomation
from app.core.session_manager import get_session_manager
from app.core.config import settings
from app.core.logging import logger


class SimpleEwayLogin:
    """
    Simple E-way Bill Login System
    Direct login with page reload and auto-fill
    """
    
    def __init__(self):
        self.automation = PlaywrightEwayAutomation()
        self.session_manager = get_session_manager()
        logger.info("Simple E-way login system initialized")
    
    async def login_with_autofill(self) -> dict:
        """
        Direct login: open page, reload once, auto-fill credentials
        """
        print("🚀 Starting E-way Bill Login")
        print("=" * 30)
        print("🔄 Opening login page...")
        print("🔄 Will reload page once")
        print("🔄 Will auto-fill username and password")
        print()
        
        # Use the automation module with auto-fill enabled (always headful for manual login)
        result = await self.automation.login_with_autofill(headless=False)
        
        if result["success"]:
            print("✅ Login successful!")
            print(f"📋 Session ID: {result['session_id']}")
        else:
            print("❌ Login failed")
            print(f"🔍 Reason: {result['message']}")
        
        return result
    
    async def close(self):
        """Clean shutdown"""
        await self.automation.close_browser()


async def main():
    """Main function - direct login only"""
    system = SimpleEwayLogin()
    
    print("\n🎯 E-way Bill Auto Login")
    print("=" * 25)
    print("🔄 Starting automatic login process...")
    print()
    
    try:
        result = await system.login_with_autofill()
        if result["success"]:
            print("✅ Login process completed successfully!")
            if result.get("browser_closed", False):
                print("📴 Browser closed automatically (production mode)")
            else:
                print("🌐 Browser will remain open for debugging")
        else:
            print("❌ Login process failed")
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        # Browser close is handled by the automation module based on debug mode
        pass


if __name__ == "__main__":
    asyncio.run(main())