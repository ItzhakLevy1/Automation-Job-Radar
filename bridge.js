const express = require('express');
const { exec } = require('child_process');
const app = express();
const port = 3000;

app.get('/run-scraper', (req, res) => {
    const url = req.query.url || "https://www.google.com";
    
    console.log(`Starting Playwright scan for: ${url}`);
    
    // Executing the python scraper script
    exec(`python scraper.py "${url}"`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Execution Error: ${error.message}`);
            return res.status(500).json({ status: "error", message: error.message });
        }
        
        console.log(`Scan finished successfully`);
        res.json({ 
            status: "success", 
            output: stdout 
        });
    });
});

app.listen(port, () => {
    console.log(`Bridge is running on http://localhost:${port}`);
});