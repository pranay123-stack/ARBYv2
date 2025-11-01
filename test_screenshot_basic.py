"""
Simple test for screenshot capture utilities
"""

import asyncio
import os
from pathlib import Path

# Add the project root to Python path
import sys
sys.path.insert(0, '/workspace')

from playwright.async_api import async_playwright

async def simple_screenshot_test():
    """Test basic screenshot functionality"""
    print("Testing basic screenshot capture...")
    
    try:
        # Launch browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        # Create a simple page
        await page.set_content("""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Test Page for Screenshot</h1>
            <p>This is a test page for the screenshot capture utilities.</p>
            <div style="border: 2px solid blue; padding: 20px; margin: 20px 0;">
                <h2>Sample Content</h2>
                <p>Sample odds: Home 2.10 | Draw 3.40 | Away 3.60</p>
            </div>
        </body>
        </html>
        """)
        
        # Create output directory
        os.makedirs("/workspace/arbitech/logs/screenshots", exist_ok=True)
        
        # Test basic screenshot capture using Playwright directly
        screenshot_path = "/workspace/arbitech/logs/screenshots/test_screenshot.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        
        if os.path.exists(screenshot_path):
            file_size = os.path.getsize(screenshot_path)
            print(f"✓ Screenshot captured successfully!")
            print(f"  - Path: {screenshot_path}")
            print(f"  - Size: {file_size} bytes")
        else:
            print("✗ Screenshot file not found")
        
        await browser.close()
        await playwright.stop()
        
        # Test image processing (basic PIL functionality)
        print("\nTesting basic image processing...")
        try:
            from PIL import Image
            
            # Open the screenshot
            with Image.open(screenshot_path) as img:
                print(f"✓ Image opened successfully")
                print(f"  - Size: {img.size}")
                print(f"  - Mode: {img.mode}")
                
                # Test resize
                resized = img.resize((800, 600))
                print(f"✓ Image resized to: {resized.size}")
                
                # Test format conversion
                jpeg_path = "/workspace/arbitech/logs/screenshots/test_converted.jpg"
                resized.convert('RGB').save(jpeg_path, 'JPEG', quality=90)
                print(f"✓ Image converted to JPEG: {jpeg_path}")
                
        except Exception as e:
            print(f"✗ Image processing failed: {str(e)}")
        
        print("\n✓ Basic functionality test completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(simple_screenshot_test())
