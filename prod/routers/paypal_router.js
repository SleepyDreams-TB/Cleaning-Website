import express from 'express'
const router = express.Router()

router.post('/create-order', async (req, res) => {
    const response = await fetch(`https://api.kingburger.site/api/paypal/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
    })
    const data = await response.json()
    res.json(data)
})

router.post('/capture', async (req, res) => {
    const response = await fetch(`https://api.kingburger.site/api/paypal/capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
    })
    const data = await response.json()
    res.json(data)
})

router.post('/charge', async (req, res) => {
    const response = await fetch(`https://api.kingburger.site/api/paypal/charge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
    })
    const data = await response.json()
    res.json(data)
})

export default router