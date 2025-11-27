import express from "express";
import path from "path";
import multer from "multer";
import fs from "fs";

const app = express();
app.use("/images", express.static(path.join(process.cwd(), "images")));
app.use("/test", express.static(path.join(process.cwd(), "html")));
const PORT = process.env.PORT || 3000;

// GitHub repo details
const token = process.env.GITHUB_TOKEN;
const repo = "Cleaning-Website";
const branch = "media-file-server";

app.listen(PORT, () => {
  console.log(`Server is running on Port: ${PORT}`);
});

// Multer configuration for file uploads: Size limit 5MB, only images
const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: 5 * 1024 * 1024 }, // 5 MB
  fileFilter: (req, file, cb) => {
    // Allowed MIME types
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true); // accept file
    } else {
      cb(new Error('Invalid file type. Only JPG, PNG, GIF allowed.'));
    }
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    res.status(400).send(`Upload error: ${err.message}`);
  } else if (err) {
    res.status(400).send(`Error: ${err.message}`);
  } else {
    next();
  }
});

app.options('/upload', (req, res) => {
  // Respond to preflight requests
  const allowedOrigins = ['https://kingburger.site', 'https://media.kingburger.site'];
  const origin = req.headers.origin;
  if (allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }
  res.setHeader('Access-Control-Allow-Methods', 'POST');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.sendStatus(200);
});

app.post('/upload', upload.single('file'), async (req, res) => {
  const origin = req.headers.origin;
  if (!origin || origin !== 'https://kingburger.site') {
    return res.status(403).send('Forbidden: Invalid origin');
  }

  if (!req.file) return res.status(400).send('No file uploaded');

  const fileData = fs.readFileSync(req.file.path);
  const base64File = fileData.toString('base64');

  const imagesPath = `images/${req.file.originalname}`;
  const url = `https://api.github.com/repos/SleepyDreams-TB/Cleaning-Website/contents/${imagesPath}`;

  const body = {
    message: `Add image ${req.file.originalname}`,
    content: base64File,
    branch: branch
  };

  try {
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        Authorization: `token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (response.ok) {
      res.send(`File uploaded to GitHub: ${data.content.download_url}`);
    } else {
      res.status(500).send(`GitHub upload failed: ${data.message}`);
    }
  } catch (error) {
    res.status(500).send(`Error uploading to GitHub: ${error.message}`);
  } finally {
    fs.unlinkSync(req.file.path); // remove temporary file
  }
});
