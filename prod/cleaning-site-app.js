const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files normally
app.use(express.static(path.join(__dirname, 'public')));

// Log all incoming requests for debugging
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
});

// Catch-all route to serve HTML files or 404
app.get('*', (req, res) => {
    // Map '/' to '/index'
    const requestedPath = req.path === '/' ? '/index' : req.path;

    // Build full file path
    const filePath = path.join(__dirname, 'public', requestedPath + '.html');

    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
        // Fallback 404 page
        const fallbackPath = path.join(__dirname, 'public', 'redirects', '404.html');
        if (fs.existsSync(fallbackPath)) {
            res.status(404).sendFile(fallbackPath);
        } else {
            res.status(404).send('404 Not Found');
        }
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
