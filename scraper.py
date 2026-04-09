import sys  # Import system-specific parameters and functions for CLI arguments
import io   # Import io for encoding management
from playwright.sync_api import sync_playwright  # Import the synchronous version of Playwright

# Force UTF-8 encoding for standard output to support Hebrew characters in n8n/Node.js
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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

        # Adding a small focus command to ensure the window is active
        # This is helpful when running from background services like n8n
        page.focus("body") 
        
        print(f"Navigating to: {url}")
        
        # 'wait_until="domcontentloaded"' is faster and often more stable for titles
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Small sleep to let the UI catch up
        page.wait_for_timeout(2000)
        
        # --- NEW LOGIC START ---
        
        # Get the visible text from the body of the page
        raw_text = page.inner_text("body")
        
        # Clean up: Split into lines, strip whitespace, and remove empty lines
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        # Define a broad list of keywords to identify potential entry-level job sections
        keywords = [
            'qa', 'automation', 'full stack', 'frontend', 'backend', 'developer', 
            'software', 'engineer', 'junior', 'entry', 'graduate', 'intern',
            'בדיקות', 'פיתוח', 'תוכנה', 'מתכנת', 'אוטומציה', 'בודק', 'ג\'וניור', 
            'ללא ניסיון', 'מתחיל', 'בוגר', 'ידניות'
        ]
        
        relevant_content = []
        
        # Iterate through lines to find matches and grab surrounding context
        for i in range(len(lines)):
            current_line_lower = lines[i].lower()
            if any(word in current_line_lower for word in keywords):
                # Grab 3 lines before and 6 lines after to capture job title and requirements
                start = max(0, i - 5)
                end = min(len(lines), i + 13)
                relevant_content.extend(lines[start:end])
        
        # Remove duplicates while preserving order
        final_text = "\n".join(list(dict.fromkeys(relevant_content)))
        
        # Fallback: If no keywords matched, return the first 200 lines to avoid missing data
        if len(final_text) < 100:
            final_text = "\n".join(lines[:200])

        # --- NEW LOGIC END ---
        
        print(f"Extraction finished. Captured {len(final_text)} characters.")
        
        # Stay for 5 seconds so you can witness the result
        page.wait_for_timeout(5000)
        
        browser.close()
        
        # Return the filtered content instead of just the title
        return final_text

# This line checks if the script is being run directly by the user 
# (e.g., 'python scraper.py') and not imported as a library by another script.
if __name__ == "__main__":
    
    # 'sys.argv' is a list containing all command-line arguments.
    # 'sys.argv[0]' is the script name itself, and 'sys.argv[1]' is the first actual argument.
    # This line sets a default URL (Google) if no argument was provided.
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    
    try:
        # Execute the scanner function with the target URL
        # result_content now holds the filtered job data
        result_content = run_scanner(target_url)
        
        # Print a formatted success message that the Bridge can parse
        # We output the actual text content for n8n to send to Gemini
        print(f"SUCCESS_DATA: {result_content}")
        
    except Exception as e:
        # Catch any errors (timeout, connection, etc.) and print them
        print(f"ERROR: {str(e)}")
        
        # Exit with status code 1 to indicate a failure to the calling process
        sys.exit(1)