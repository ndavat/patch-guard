const express = require('express');
const axios = require('axios');
const { validateToken } = require('./auth');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/api/users/:id', async (req, res) => {
    try {
        const userId = req.params.id;
        const response = await axios.get(`https://api.example.com/users/${userId}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/users', async (req, res) => {
    const { name, email } = req.body;

    if (!name || !email) {
        return res.status(400).json({ error: 'Name and email required' });
    }

    try {
        const response = await axios.post('https://api.example.com/users', {
            name,
            email
        });
        res.status(201).json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;
