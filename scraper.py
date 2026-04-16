import sys  # Import system-specific parameters and functions for CLI arguments
import io   # Import io for encoding management
from playwright.sync_api import sync_playwright  # Import the synchronous version of Playwright

# Force UTF-8 encoding for standard output to support Hebrew characters in n8n/Node.js
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Define a function to run the web scanner using Playwright
# Now accepts 'strategy' to decide between a surface scan or a deep click-through scan
def run_scanner(url, strategy):
    # 'with' ensures resources like the browser are properly closed after use
    with sync_playwright() as p:
        
        # We manually set the window size to a standard Full HD resolution
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
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        page = context.new_page()
        
        # Bring the page to the front and ensure it has focus
        page.bring_to_front()

        # Adding a small focus command to ensure the window is active
        page.focus("body") 
        
        print(f"Navigating to: {url} with strategy: {strategy}")
        
        # Navigate to the target URL
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Small sleep to let the UI catch up
        page.wait_for_timeout(3000)

        # --- STRATEGY BRANCHING START ---
        
        final_text = ""

        if strategy == "deep":
            # Keywords to identify relevant job links or buttons for clicking
            job_keywords = ['qa', 'automation', 'test', 'software', 'developer', 'בדיקות', 'אוטומציה', 'פיתוח']
            action_keywords = ['apply', 'details', 'view', 'לפרטים', 'הגש', 'צפייה']

            combined_results = []

            # Find all potential entry points (links or buttons)
            elements = page.query_selector_all("a, button, [role='button']")
            
            valid_links = []
            for el in elements:
                text = (el.inner_text() or "").lower()
                # If the element contains job or action keywords, we consider it a candidate
                if any(kw in text for kw in job_keywords + action_keywords):
                    valid_links.append(el)

            print(f"Found {len(valid_links)} potential job elements. Starting deep scan...")

            # Limit the scan to the first 15 items to prevent timeouts and excessive resource use
            for i in range(min(len(valid_links), 15)): 
                try:
                    # Re-fetch elements briefly if needed, but here we use the original list
                    current_el = valid_links[i]
                    
                    if not current_el.is_visible():
                        continue

                    job_title_context = current_el.inner_text().strip()
                    print(f"Deep Scanning: {job_title_context}")

                    # Perform the click to enter the job page
                    current_el.click()
                    page.wait_for_timeout(3000) # Wait for the description page to load
                    
                    # Capture the full text of the job description page
                    job_description = page.inner_text("body")
                    combined_results.append(f"--- JOB START ---\nContext: {job_title_context}\nContent: {job_description}\n--- JOB END ---\n")
                    
                    # Navigate back to the main list to continue the loop
                    page.go_back(wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)

                except Exception as e:
                    print(f"Skipping element {i} due to error: {str(e)}")
                    # Ensure we are back on the main URL if a click led us astray
                    if page.url != url:
                        page.goto(url)

            final_text = "\n".join(combined_results)
        
        # Fallback or "Simple" strategy: Just grab the text from the main page
        if strategy == "simple" or not final_text:
            print("Executing simple surface scan...")
            raw_text = page.inner_text("body")
            
            # Use your original logic to filter keywords on the main page
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            keywords = [
                'qa', 'automation', 'full stack', 'frontend', 'backend', 'developer', 
                'software', 'engineer', 'junior', 'entry', 'graduate', 'intern',
                'בדיקות', 'פיתוח', 'תוכנה', 'מתכנת', 'אוטומציה', 'בודק', 'ג\'וניור', 
                'ללא ניסיון', 'מתחיל', 'בוגר', 'ידניות'
            ]
            
            relevant_content = []
            for i in range(len(lines)):
                current_line_lower = lines[i].lower()
                if any(word in current_line_lower for word in keywords):
                    start = max(0, i - 5)
                    end = min(len(lines), i + 13)
                    relevant_content.extend(lines[start:end])
            
            final_text = "\n".join(list(dict.fromkeys(relevant_content)))
            
            # Final fallback if keyword filtering was too aggressive
            if len(final_text) < 100:
                final_text = "\n".join(lines[:200])

        # --- STRATEGY BRANCHING END ---

        print(f"Extraction finished. Captured {len(final_text)} characters.")
        
        # Stay for a few seconds to ensure logs are captured
        page.wait_for_timeout(3000)
        
        browser.close()
        
        return final_text

# Main execution block
if __name__ == "__main__":
    
    # sys.argv[1] is the URL
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"

    # sys.argv[2] is the Strategy (simple or deep) passed from n8n
    # Defaults to 'simple' if the second argument is missing
    strategy = sys.argv[2] if len(sys.argv) > 2 else "simple"
    
    try:
        # Execute the scanner function with both URL and Strategy
        result_content = run_scanner(target_url, strategy)
        
        # Print the success marker followed by the data
        # We limit to 50k characters to keep the n8n buffer manageable
        print(f"SOURCE_URL: {target_url}")
        print(f"SUCCESS_DATA: {result_content[:50000]}") 
        
    except Exception as e:
        # Catch and report errors to n8n
        print(f"ERROR: {str(e)}")
        sys.exit(1)