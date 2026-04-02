// Import the Express framework to create our web server
const express = require('express');

// Import 'exec' from child_process to run shell commands (like running Python)
const { exec } = require('child_process');

// Initialize the Express application
const app = express();

// Define the port where the server will listen for requests
const port = 3000;

/**
 * Endpoint: GET /run-scraper
 * This route triggers the Playwright scraper script.
 * Usage: http://localhost:3000/run-scraper?url=https://example.com
 */
app.get('/run-scraper', (req, res) => {
    
    // Extract the 'url' parameter from the request query string. 
    // Defaults to Google if no URL is provided.
    const url = req.query.url || "https://www.google.com";
    
    // Log the start of the process to the terminal for debugging
    console.log(`Starting Playwright scan for: ${url}`);
    
    /**
     * exec: Runs the Python script as a separate system process.
     * Arguments:
     * - error: Contains details if the command fails to run.
     * - stdout: Standard Output (anything the Python script 'print'ed).
     * - stderr: Standard Error (any warnings or non-fatal errors from Python).
     */
    exec(`python scraper.py "${url}"`, (error, stdout, stderr) => {
        
        // Handle critical execution errors (e.g., Python not installed or file missing)
        if (error) {
            console.error(`Execution Error: ${error.message}`);
            
            // Send a 500 Internal Server Error response back to n8n
            return res.status(500).json({ 
                status: "error", 
                message: error.message 
            });
        }
        
        // Log a success message to the bridge terminal
        console.log(`Scan finished successfully`);
        
        // Send the final result back to n8n as a JSON object
        res.json({ 
            status: "success", 
            output: stdout // This contains the 'SUCCESS_DATA' from our Python script
        });
    });
});

// Start the server and listen for incoming HTTP connections
app.listen(port, () => {
    console.log(`Bridge is running on http://localhost:${port}`);
});