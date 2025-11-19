# Stripe Integration Setup - COMPLETE ✅

## Configuration Status

✅ **Stripe Keys Configured**
- Secret Key: Added to `.env`
- Publishable Key: Added to `frontend/js/config.js`
- Webhook Secret: Added to `.env`

✅ **Price IDs Configured**
- Professional Plan: `price_1ST5MkC1Mw54p58QmFXSuYSu`
- Business Plan: `price_1ST5NCC1Mw54p58QfHpicHPf`

✅ **Webhook Endpoint Configured**
- URL: `https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod/api/v1/billing/webhook`
- Events: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.paid`

## Security Features Implemented

✅ **Webhook Signature Verification**
- All webhook requests are verified using Stripe's signature
- Invalid signatures are rejected with 400 error
- Prevents unauthorized webhook calls

## Next Steps

### 1. Test the Integration

**Test Checkout Flow:**
1. Login to dashboard
2. Go to `/billing.html`
3. Click "Upgrade to Professional" or "Upgrade to Business"
4. Complete Stripe checkout (use test card: `4242 4242 4242 4242`)
5. Verify subscription is activated

**Test Webhook:**
1. In Stripe Dashboard, go to Webhooks
2. Click on your webhook endpoint
3. Click "Send test webhook"
4. Select event: `checkout.session.completed`
5. Verify webhook is received and processed

### 2. Monitor Webhook Delivery

- Check Stripe Dashboard > Webhooks for delivery status
- Check CloudWatch logs for Lambda execution logs
- Verify subscriptions are being created in DynamoDB

### 3. Production Checklist

Before going live:
- [ ] Switch to Stripe Live keys (replace test keys)
- [ ] Update Price IDs to live price IDs
- [ ] Verify webhook endpoint is accessible
- [ ] Test with real payment method
- [ ] Monitor first few transactions
- [ ] Set up webhook retry alerts in Stripe

## Environment Variables Required

Make sure these are set in your Lambda environment:

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_PRICE_PROFESSIONAL=price_...
STRIPE_PRICE_BUSINESS=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=https://galerly.app
```

## Dependencies

Install Stripe package:
```bash
pip install stripe>=7.0.0
```

Add to Lambda deployment package or use Lambda Layers.

## Testing Cards

**Success:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits

**Decline:**
- Card: `4000 0000 0000 0002`

## Troubleshooting

**Webhook not received:**
- Check API Gateway CORS settings
- Verify endpoint URL is correct
- Check Lambda logs for errors

**Signature verification fails:**
- Verify `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
- Ensure raw body is passed correctly (not parsed JSON)

**Subscription not activating:**
- Check webhook logs for errors
- Verify `user_id` is in checkout session metadata
- Check DynamoDB tables exist

---

**Status:** Ready for testing! 🚀

