const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static('./public'));

app.get('/*', (req, res) => {
    const filePath = path.join(__dirname, 'public', req.path + '.html');

    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
        res.status(404).sendFile(path.join(__dirname, 'public', 'redirects/404.html'));
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});