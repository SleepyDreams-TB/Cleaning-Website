const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();

app.use(express.static('./public'));

app.get('/*', (req, res) => {
    const filePath = path.join(__dirname, 'public', req.path + '.html');

    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
        res.status(404).sendFile(path.join(__dirname, 'public', 'redirects/404.html'));
    }
});

app.listen(3000);