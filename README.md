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