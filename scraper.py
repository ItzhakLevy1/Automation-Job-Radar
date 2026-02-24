import sys  # Import system-specific parameters and functions for CLI arguments
from playwright.sync_api import sync_playwright  # Import the synchronous version of Playwright

# Define a function to run the web scanner using Playwright
def run_scanner(url):
    # 'with' ensures resources like the browser are properly closed after use
    with sync_playwright() as p:
        
         # We manually set the window size to a standard Full HD resolution
        # This is more reliable than '--start-maximized'
        browser = p.chromium.launch(
            headless=False, 
            slow_mo=1000,
            args=[
                "--window-size=1920,1080",
                "--window-position=0,0",
                "--force-device-scale-factor=1" # Ensures no weird zooming
            ]
        )
        
        # Explicitly setting the viewport to match the window size
        # This forces the website to occupy the entire window space
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        page = context.new_page()
        
        # Bring the page to the front and ensure it has focus
        page.bring_to_front()
        
        print(f"Navigating to: {url}")
        
        # 'wait_until="domcontentloaded"' is faster and often more stable for titles
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Small sleep to let the UI catch up
        page.wait_for_timeout(2000)
        
        title = page.title()
        print(f"Page title found: {title}")
        
        # Stay for 5 seconds so you can witness the result
        page.wait_for_timeout(5000)
        
        browser.close()
        return title

# This line checks if the script is being run directly by the user 
# (e.g., 'python scraper.py') and not imported as a library by another script.
if __name__ == "__main__":
    
    # 'sys.argv' is a list containing all command-line arguments.
    # 'sys.argv[0]' is the script name itself, and 'sys.argv[1]' is the first actual argument.
    # This line sets a default URL (Google) if no argument was provided.
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    
    try:
        # Execute the scanner function with the target URL
        result_title = run_scanner(target_url)
        
        # Print a formatted success message that the Bridge can parse
        print(f"SUCCESS_DATA: {result_title}")
        
    except Exception as e:
        # Catch any errors (timeout, connection, etc.) and print them
        print(f"ERROR: {str(e)}")
        
        # Exit with status code 1 to indicate a failure to the calling process
        sys.exit(1)