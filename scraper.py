import sys
import io
import math
import json
from playwright.sync_api import sync_playwright

# --- CONFIGURATION & ENCODING ---
# Ensure the terminal handles Hebrew characters correctly for automation logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def scroll_to_bottom(page):
    """
    Handles page scrolling and 'Load More' button interaction.
    Specifically optimized for Elbit Systems and MUI-based job boards.
    """
    print("Waiting for page loader...")
    sys.stdout.flush()
    try:
        # Wait for the Hebrew 'Loading Jobs' spinner to disappear
        page.wait_for_selector("text=טוען משרות", state="hidden", timeout=15000)
    except Exception:
        pass

    last_height = page.evaluate("document.body.scrollHeight")
    
    # Loop to scroll and click 'Load More' up to 8 times
    for attempt in range(8): 
        print(f"--- Scroll Attempt {attempt + 1} ---")
        sys.stdout.flush()
        
        # Scroll to the current bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2500) # Slightly longer wait for content to render

        # Look for the 'Load More' button in Hebrew
        load_more_button = page.locator("button").filter(has_text="תוצאות חיפוש נוספות").first
        
        if load_more_button.is_visible():
            print(f"Clicking 'Load More' button...")
            sys.stdout.flush()
            try:
                load_more_button.scroll_into_view_if_needed()
                load_more_button.click(force=True)
                page.wait_for_timeout(2000)
                continue 
            except Exception:
                pass
        
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            # Try one last small scroll just in case
            page.evaluate("window.scrollBy(0, -300)")
            page.wait_for_timeout(500)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            if page.evaluate("document.body.scrollHeight") == last_height:
                break
        last_height = new_height

def process_text(raw_text):
    """
    EXPANDED text processing to ensure no jobs are missed.
    Captures more context around keywords.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    keywords = [
        'qa', 'automation', 'full stack', 'frontend', 'backend', 'developer', 
        'software', 'engineer', 'junior', 'entry', 'graduate', 'intern',
        'בדיקות', 'פיתוח', 'תוכנה', 'מתכנת', 'אוטומציה', 'בודק', 'ג\'וניור', 
        'ללא ניסיון', 'מתחיל', 'בוגר', 'ידניות', 'embedded', 'rt'
    ]
    
    relevant_content = []
    for i in range(len(lines)):
        current_line_lower = lines[i].lower()
        if any(word in current_line_lower for word in keywords):
            # INCREASED CONTEXT: 10 lines above and 30 lines below
            # This ensures the AI sees the full job block even in "messy" HTML
            start = max(0, i - 10)
            end = min(len(lines), i + 30)
            relevant_content.extend(lines[start:end])
            
    # Removing duplicates while preserving order
    seen = set()
    result_lines = []
    for line in relevant_content:
        if line not in seen:
            result_lines.append(line)
            seen.add(line)
            
    result = "\n".join(result_lines)
    
    # Fallback: If filtered result is too small, SQ Link might have a different structure
    # In that case, we return more of the raw text
    if len(result) < 500:
        return "\n".join(lines[:400]) 
    return result

def run_scanner(url, strategy, wait_input):
    with sync_playwright() as p:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--window-size=1920,1080", "--force-device-scale-factor=1"
            ]
        )
        
        context = browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            bypass_csp=True
        )
        
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Navigating to {url}...")
        sys.stdout.flush()
        
        # Use 'networkidle' specifically for SQ Link as it's heavy on JS
        wait_until_mode = "networkidle" if "sqlink" in url.lower() else "domcontentloaded"
        page.goto(url, wait_until=wait_until_mode, timeout=60000)

        # Dynamic wait calculation
        wait_seconds = wait_input if wait_input < 100 else wait_input / 1000
        page.wait_for_timeout(wait_seconds * 1000)

        final_text = ""

        # Force scroll for SQ Link even if strategy is simple
        if strategy == "scroll" or "sqlink" in url.lower():
            scroll_to_bottom(page)
            # Give it a second to stabilize after scrolling
            page.wait_for_timeout(2000)
            raw_text = page.inner_text("body")
            final_text = process_text(raw_text)
            
        elif strategy == "deep":
            # (Deep strategy remains same but with expanded context)
            job_keywords = ['qa', 'automation', 'test', 'software', 'developer', 'בדיקות', 'אוטומציה', 'פיתוח']
            combined_results = []
            elements = page.query_selector_all("a, button, [role='button']")
            valid_links = [el for el in elements if any(kw in (el.inner_text() or "").lower() for kw in job_keywords)]
            
            for i in range(min(len(valid_links), 15)):
                try:
                    current_el = valid_links[i]
                    if not current_el.is_visible(): continue
                    current_el.click()
                    page.wait_for_timeout(3000)
                    combined_results.append(page.inner_text("body"))
                    page.go_back(wait_until="domcontentloaded")
                except Exception:
                    pass
            final_text = process_text("\n".join(combined_results))

        if not final_text or len(final_text) < 150:
            raw_text = page.inner_text("body")
            final_text = process_text(raw_text)

        # Site Name Logic
        url_lower = url.lower()
        site_name = "SQ Link" if "sqlink" in url_lower else "Company"
        if "elbit" in url_lower: site_name = "Elbit Systems"
        elif "tesnet" in url_lower: site_name = "Tesnet"
        elif "peak" in url_lower: site_name = "Peak Innovation"

        header = f"🚩 SITE: {site_name} 🚩"
        browser.close()

        # Chunking for AI
        chunk_size = 8000 # Slightly larger chunks
        if len(final_text) > chunk_size:
            chunks = [final_text[i:i + chunk_size] for i in range(0, len(final_text), chunk_size)]
            return [f"{header} (Part {idx+1}/{len(chunks)})\n{c}" for idx, c in enumerate(chunks)]
        else:
            return [f"{header}\n{final_text}"]

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else ""
    selected_strategy = sys.argv[2].strip().lower() if len(sys.argv) > 2 else "simple"
    try:
        raw_wait = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    except ValueError:
        raw_wait = 5
    
    if not target_url:
        sys.exit(1)

    try:
        output_list = run_scanner(target_url, selected_strategy, raw_wait)
        print(f"SOURCE_URL: {target_url}")
        # Return as JSON array for n8n processing
        print(f"SUCCESS_DATA_JSON: {json.dumps(output_list)}")
        sys.stdout.flush()
    except Exception as e:
        # Catch and report errors to n8n
        print(f"ERROR: {str(e)}")
        sys.stdout.flush()
        sys.exit(1)