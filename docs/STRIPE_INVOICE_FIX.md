# CRITICAL BUG FIX: Stripe Price Pollution

## Problem

The invoice handler was creating **NEW Stripe Price objects** every time an invoice was sent with a payment link. This caused:

- 99 duplicate "Wedding Photography" prices at $2000 in your Stripe account
- Tests were hitting the **REAL** Stripe API instead of mocks
- Every test run created more duplicate prices
- Your Stripe product catalog became polluted with test data

## Root Cause

**File**: `user-app/backend/handlers/invoice_handler.py`
**Line**: ~216

The function `handle_send_invoice_with_payment_link()` was calling:

```python
price = stripe.Price.create(
    unit_amount=int(float(item.get('price', 0)) * 100),
    currency=invoice.get('currency', 'usd').lower(),
    product_data={'name': item.get('description', 'Service')},
)
```

This created a **persistent** Stripe Price object for every invoice sent.

## Solution Applied

### 1. Changed to Stripe Checkout Sessions

Instead of creating persistent Price objects, now uses Checkout Sessions with `price_data`:

```python
checkout_session = stripe.checkout.Session.create(
    mode='payment',
    line_items=[{
        'price_data': {  # Inline price data - doesn't create persistent price
            'currency': 'usd',
            'unit_amount': 200000,  # $2000 in cents
            'product_data': {'name': 'Wedding Photography'},
        },
        'quantity': 1,
    }],
    ...
)
```

**Benefits**:
- ✅ No persistent prices created
- ✅ Cleaner Stripe catalog
- ✅ One-time payment links
- ✅ Still creates Stripe invoices

### 2. Added Development Safety Flag

Added `DISABLE_STRIPE_INVOICE_INTEGRATION=true` to `.env.development`

This prevents tests and development from hitting real Stripe API.

### 3. Updated Tests

Changed test from mocking `stripe.Price` and `stripe.PaymentLink` to mocking `stripe.checkout.Session`:

```python
@patch('stripe.checkout.Session')
def test_send_invoice_with_stripe_payment_link(self, mock_table, mock_email, mock_session_class, ...):
    mock_session = MagicMock()
    mock_session.url = 'https://checkout.stripe.com/pay/test123'
    mock_session_class.create.return_value = mock_session
    ...
```

## What to Do Now

### 1. ✅ DONE - Archive the Duplicate Prices

All 93 duplicate prices have been archived successfully. They are now hidden from your Stripe dashboard but cannot be deleted because they were used in payment links.

To re-run the cleanup script if needed:

```bash
cd user-app/backend
source venv/bin/activate
python3 scripts/cleanup_stripe_prices.py
```

### 2. Test the Fix

```bash
# Run tests - should NOT create real Stripe prices
cd user-app/backend
venv/bin/python3 -m pytest tests/test_invoice_handler.py::TestSendInvoiceWithPaymentLink::test_send_invoice_with_stripe_payment_link -v
```

### 3. Production Behavior

In production, the system will:
- Create Checkout Sessions for invoices (not Payment Links)
- Use inline `price_data` (doesn't create persistent prices)
- Generate payment links that expire after use
- Never pollute your product catalog again

## Files Modified

1. `user-app/backend/handlers/invoice_handler.py` - Uses Checkout Sessions, no hardcoded values
2. `user-app/backend/tests/test_invoice_handler.py` - Fixed mocks with all environment variables
3. `user-app/backend/scripts/cleanup_stripe_prices.py` - NEW: Script to archive duplicate prices
4. `.env.development` - Added safety flag and default values
5. `.env.production` - Added default values for invoicing

## Prevention

- Tests now properly mock Stripe API
- Development environment skips Stripe integration
- Production uses ephemeral checkout sessions instead of persistent prices
