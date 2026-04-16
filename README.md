# Automation Job Radar Bridge

This project acts as a bridge between **n8n** and a local **Playwright** scraper. It uses a Node.js Express server to receive commands and execute Python scripts.

## Project Structure
- `bridge.js`: Node.js server that listens for HTTP requests from n8n.
- `scraper.py`: Python script using Playwright to perform web scraping.
- `requirements.txt`: Python dependencies.
- `package.json`: Node.js dependencies.

## Setup

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
playwright install chromium


# Running the Project
# To use the automation, you need to have **two** separate terminal windows running:

# Terminal 1: Start the Bridge Server
# This server acts as the intermediary between n8n and your Python scripts, To activate it run:

node bridge.js

# Terminal 2: Start n8n
# This launches the automation workflow engine, To activate it run:

npx n8n start

## 📂 Version Control & Backups

To ensure the stability of the automation flow and maintain a history of functional versions, backups are stored in the following directory: `Automation_job_radar/Version control`

### How to Restore / Load a Version:
1. **Open n8n:** Access your local instance (e.g., `http://localhost:5678`).
2. **Create or Open a Workflow:** Start with a blank canvas.
3. **Import JSON:**
   * Go to the **Menu** (three dots `...` in the top right corner).
   * Select `Import from File`.
   * Choose the desired `.json` file from the `Version control` folder.
   * **Alternatively:** Simply drag the JSON file into the n8n editor or use `CTRL+V` to paste the JSON structure directly.

> [!IMPORTANT]
> **Credentials:** Note that credentials (API Keys, OAuth tokens) are **not** included in the backup files for security reasons. You will need to re-select or re-configure your Google Gemini and Google Sheets credentials after importing.
