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
        page.wait_for_timeout(2000) 

        # Look for the 'Load More' button in Hebrew
        load_more_button = page.locator("button").filter(has_text="תוצאות חיפוש נוספות").first
        
        if load_more_button.is_visible():
            print(f"Clicking 'Load More' button...")
            sys.stdout.flush()
            try:
                load_more_button.scroll_into_view_if_needed()
                load_more_button.click(force=True)
                page.wait_for_timeout(1500)
                continue 
            except Exception:
                pass
        
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def process_text(raw_text):
    """
    Filters raw page text to keep only relevant tech job information.
    Reduces the payload size for the AI by removing non-tech noise.
    """
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
            # Capture context: 5 lines above and 13 lines below
            start = max(0, i - 5)
            end = min(len(lines), i + 13)
            relevant_content.extend(lines[start:end])
            
    result = "\n".join(list(dict.fromkeys(relevant_content)))
    return result if len(result) > 100 else "\n".join(lines[:200])

def run_scanner(url, strategy):
    """
    Main execution logic for scanning a job board.
    Detects site type, runs strategy, and splits output into chunks.
    """
    # Force 'scroll' strategy for Elbit Systems
    if "elbit" in url.lower():
        strategy = "scroll"

    with sync_playwright() as p:
        print("!!!!!!!!!!!!!!!! SCRAPER INITIALIZED !!!!!!!!!!!!!!!!")
        sys.stdout.flush()
        
        browser = p.chromium.launch(
            headless=False, 
            args=["--window-size=1920,1080", "--force-device-scale-factor=1"]
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        print(f"Opening URL: {url} | Strategy: {strategy}")
        sys.stdout.flush()
        
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        final_text = ""

        if strategy == "scroll":
            scroll_to_bottom(page)
            raw_text = page.inner_text("body")
            final_text = process_text(raw_text)
            
        elif strategy == "deep":
            job_keywords = ['qa', 'automation', 'test', 'software', 'developer', 'בדיקות', 'אוטומציה', 'פיתוח']
            action_keywords = ['apply', 'details', 'view', 'לפרטים', 'הגש', 'צפייה']
            combined_results = []
            
            elements = page.query_selector_all("a, button, [role='button']")
            valid_links = [el for el in elements if any(kw in (el.inner_text() or "").lower() for kw in job_keywords + action_keywords)]
            
            for i in range(min(len(valid_links), 15)):
                try:
                    current_el = valid_links[i]
                    if not current_el.is_visible(): continue
                    job_title_context = current_el.inner_text().strip()
                    current_el.click()
                    page.wait_for_timeout(3000)
                    job_description = page.inner_text("body")
                    combined_results.append(f"--- JOB START ---\nContext: {job_title_context}\nContent: {job_description}\n--- JOB END ---\n")
                    page.go_back(wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                except Exception:
                    if page.url != url: page.goto(url)
            final_text = "\n".join(combined_results)

        # Fallback for empty results
        if not final_text or len(final_text) < 100:
            raw_text = page.inner_text("body")
            final_text = process_text(raw_text)

        # --- SITE NAME IDENTIFICATION (ROBUST VERSION) ---
        url_lower = url.lower()
        if "elbit" in url_lower:
            site_name = "Elbit Systems"
        elif "tesnet" in url_lower:
            site_name = "Tesnet"
        elif "peak" in url_lower:
            site_name = "Peak Innovation"
        else:
            # Fallback: Extract from domain (e.g., https://site.com -> Site)
            site_name = url.split("//")[-1].split(".")[0].capitalize()

        # The clean header YOU want
        header = f"🚩 SITE: {site_name} 🚩"
        browser.close()

        # --- CHUNKING LOGIC ---
        chunk_size = 7000
        if len(final_text) > chunk_size:
            num_chunks = math.ceil(len(final_text) / chunk_size)
            chunks = [final_text[i:i + chunk_size] for i in range(0, len(final_text), chunk_size)]
            return [f"{header} (Part {idx+1}/{len(chunks)})\n{c}" for idx, c in enumerate(chunks)]
        else:
            return [f"{header}\n{final_text}"]

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else ""
    selected_strategy = sys.argv[2].strip().lower() if len(sys.argv) > 2 else "simple"
    
    if not target_url:
        sys.exit(1)

    try:
        output_list = run_scanner(target_url, selected_strategy)
        print(f"SOURCE_URL: {target_url}")
        # Return as JSON array for n8n processing
        print(f"SUCCESS_DATA_JSON: {json.dumps(output_list)}")
        sys.stdout.flush()
        
    except Exception as e:
        # Catch and report errors to n8n
        print(f"ERROR: {str(e)}")
        sys.stdout.flush()
        sys.exit(1)