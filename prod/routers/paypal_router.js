import express from 'express'
const router = express.Router()

router.post('/create-order', async (req, res) => {
    try {
        console.log('📦 PayPal create-order request:', req.body)

        const response = await fetch(`https://api.kingburger.site/api/paypal/create-order`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        })

        const text = await response.text()
        console.log('🔵 PayPal API raw response:', text)

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}: ${text}`)
        }

        const data = JSON.parse(text)
        res.json(data)
    } catch (err) {
        console.error('❌ PayPal create-order error:', err.message)
        res.status(500).json({ error: err.message })
    }
})

router.post('/capture', async (req, res) => {
    try {
        console.log('📦 PayPal capture request:', req.body)

        const response = await fetch(`https://api.kingburger.site/api/paypal/capture`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        })

        const text = await response.text()
        console.log('🔵 PayPal capture raw response:', text)

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}: ${text}`)
        }

        const data = JSON.parse(text)
        res.json(data)
    } catch (err) {
        console.error('❌ PayPal capture error:', err.message)
        res.status(500).json({ error: err.message })
    }
})

router.post('/charge', async (req, res) => {
    try {
        console.log('📦 PayPal charge request:', req.body)

        const response = await fetch(`https://api.kingburger.site/api/paypal/charge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        })

        const text = await response.text()
        console.log('🔵 PayPal charge raw response:', text)

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}: ${text}`)
        }

        const data = JSON.parse(text)
        res.json(data)
    } catch (err) {
        console.error('❌ PayPal charge error:', err.message)
        res.status(500).json({ error: err.message })
    }
})

export default router