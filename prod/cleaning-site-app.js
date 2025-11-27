const express = require('express');
const path = require('path');
const fs = require('fs');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 3000;

// MongoDB connection
const MONGO_URI = process.env.MONGO_URI;
let db;
async function connectDB() {
    if (!db) {
        const client = new MongoClient(MONGO_URI);
        await client.connect();
        db = client.db("cleaning_website"); // your DB name
    }
    return db;
}

// Parse JSON bodies
app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Log all requests
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
});

// ==================== Username/Email availability check ====================
app.post('/users/check_user_avail', async (req, res) => {
    try {
        const { username, email } = req.body;
        if (!username && !email) return res.status(400).json({ error: "Username or email is required" });

        const database = await connectDB();
        const usersCollection = database.collection("usersCleaningSite");

        const user = await usersCollection.findOne({
            $or: [
                username ? { userName: username } : null,
                email ? { email: email } : null
            ].filter(Boolean)
        });

        res.json({ exists: !!user });
    } catch (err) {
        console.error("❌ check_user_avail error:", err);
        res.status(500).json({ error: "Server error" });
    }
});

// ==================== Catch-all route for HTML / 404 ====================
app.get('*', (req, res) => {
    const requestedPath = req.path === '/' ? '/index' : req.path;
    const filePath = path.join(__dirname, 'public', requestedPath + '.html');

    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
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
