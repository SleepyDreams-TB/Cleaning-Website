const express = require('express');
const path = require('path');
const fs = require('fs');
const { MongoClient } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 3000;

import express from "express";
import bodyParser from "body-parser";
import Mailjet from "node-mailjet";

// MongoDB connection
const MONGO_URI = process.env.MONGO_URI;
let db;

async function connectDB() {
    if (!db) {
        const client = new MongoClient(MONGO_URI);
        await client.connect();
        db = client.db("kingburgerstore_db");
    }
    return db;
}

// ==================== Middleware ====================
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Log all requests
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
});

// ==================== Static Files ====================
// Serve static files from public folder (CSS, JS, images, etc.)
app.use(express.static(path.join(__dirname, 'public')));

// ==================== API Routes ====================

//mailer via mailjet API
const mailjet = require('node-mailjet').connect(
    process.env.MJ_APIKEY_PUBLIC,
    process.env.MJ_APIKEY_PRIVATE
)
app.post("/mail/contact", async (req, res) => {
    try {
        const name = req.body.name?.trim();
        const email = req.body.email?.trim();
        const message = req.body.message?.trim();

        if (!name || !email || !message) {
            return res.status(400).send("All fields are required.");
        }

        const request = mailjet.post("send", { version: "v3.1" }).request({
            Messages: [
                {
                    From: {
                        Email: email,
                        Name: name,
                    },
                    To: [
                        {
                            Email: "tiaanburger1112@gmail.com",
                            Name: "Tiaan Burger",
                        },
                    ],
                    Subject: `New Inquiry from ${name}`,
                    TextPart: `Name: ${name}\nEmail: ${email}\nMessage:\n${message}`,
                },
            ],
        });

        await request;
        res.status(200).send("Thank you! Your message has been sent.");
    } catch (err) {
        console.error("Mailjet error:", err);
        res.status(500).send("Oops! Something went wrong. Please try again.");
    }
});

// Catch non-POST requests
app.all("/mail/contact", (req, res) => {
    res.status(403).send("There was a problem with your submission.");
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

// Catch non-POST requests
app.all("/mail/contact", (req, res) => {
    res.status(403).send("There was a problem with your submission.");
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

// Username/Email availability check
app.post('/users/check_user_avail', async (req, res) => {
    try {
        const { username, email } = req.body;
        if (!username && !email) {
            return res.status(400).json({ error: "Username or email is required" });
        }

        const database = await connectDB();
        const usersCollection = database.collection("store_users");

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

// ==================== Health Check ====================
app.get('/health', (req, res) => {
    res.json({ status: 'Server is running' });
});

// ==================== Catch-all Route for HTML Pages / 404 ====================
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
            res.status(404).json({ error: '404 Not Found' });
        }
    }
});

// ==================== Error Handling ====================
app.use((err, req, res, next) => {
    console.error('❌ Server error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

// ==================== Start Server ====================
app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
});