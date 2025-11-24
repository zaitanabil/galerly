# 🎯 Stripe Webhook Quick Reference

## 📋 Events to Select in Stripe Dashboard

Search for these in the "Find event by name" box and check them:

### Subscriptions (4 events)
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `customer.subscription.trial_will_end`

### Invoices (3 events)
- `invoice.paid`
- `invoice.payment_failed`
- `invoice.payment_action_required`

### Customers (3 events)
- `customer.created`
- `customer.updated`
- `customer.deleted`

### Checkout (2 events)
- `checkout.session.completed`
- `checkout.session.expired`

**Total: 11 events**

---

## 🚀 Quick Start

### 1. Install Stripe CLI (one-time)
```bash
brew install stripe/stripe-cli/stripe
```

### 2. Login to Stripe
```bash
stripe login
```

### 3. Start Webhook Listener
```bash
stripe listen --forward-to http://localhost:5001/v1/billing/webhook
```

**Copy the webhook secret (whsec_...)**

### 4. Add Secret to .env
```bash
echo "STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx" >> backend/.env
```

### 5. Test It
```bash
stripe trigger customer.subscription.created
```

---

## 🧪 Testing Commands

```bash
# Test subscription created
stripe trigger customer.subscription.created

# Test subscription updated
stripe trigger customer.subscription.updated

# Test payment success
stripe trigger invoice.paid

# Test payment failure
stripe trigger invoice.payment_failed

# Test checkout completed
stripe trigger checkout.session.completed
```

---

## 📁 Files Created

- `backend/handlers/stripe_webhook_handler.py` - Webhook processing logic
- Webhook endpoint already exists: `POST /v1/billing/webhook`

---

## 🔧 Production Setup

When deploying to production:

1. In Stripe Dashboard → Webhooks → Create endpoint
2. URL: `https://api.galerly.com/v1/billing/webhook`
3. Select same 11 events
4. Copy production webhook secret
5. Add to AWS Lambda env: `STRIPE_WEBHOOK_SECRET=whsec_prod_xxxxx`

---

## 💡 What Each Event Does

| Event | Action |
|-------|--------|
| `customer.subscription.created` | Sets user's `stripe_subscription_id` and activates subscription |
| `customer.subscription.updated` | Updates user's plan (plus/pro) and subscription status |
| `customer.subscription.deleted` | Downgrades user to free plan |
| `invoice.paid` | Logs successful payment |
| `invoice.payment_failed` | Logs payment failure |
| `checkout.session.completed` | Logs successful checkout |

---

## ⚠️ Environment Variables Required

```bash
# backend/.env
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
STRIPE_PRICE_PLUS=price_xxxxxxxxxxxxx
STRIPE_PRICE_PRO=price_xxxxxxxxxxxxx
```

---

## 🎬 Running Everything

```bash
# Terminal 1 - API
cd backend && python api.py

# Terminal 2 - Stripe Listener
stripe listen --forward-to http://localhost:5001/v1/billing/webhook

# Terminal 3 - Test
stripe trigger customer.subscription.created
```

