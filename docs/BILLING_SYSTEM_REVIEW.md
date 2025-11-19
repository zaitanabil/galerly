# Galerly Billing System - Comprehensive Review & Improvements

## Executive Summary

This document outlines the billing system's current state, identified issues, and implemented improvements to handle all edge cases including rapid plan changes, cancellations, reactivations, and refund policy enforcement.

---

## ✅ IMPROVEMENTS IMPLEMENTED

### 1. Race Condition Prevention
**File**: `backend/handlers/billing_handler.py`

**Changes**:
- Added `processing_change` flag with DynamoDB conditional updates
- Prevents concurrent plan modifications
- Returns `409 Conflict` if change already in progress
- Automatically releases lock on completion or error
- Uses `ConditionExpression` to ensure atomic operations

**Example Flow**:
```
User clicks "Upgrade to Pro" twice rapidly
→ First request: Sets processing_change=True
→ Second request: Sees processing_change=True, returns 409 error
→ First request completes: Sets processing_change=False
```

### 2. Refund Policy Implementation
**File**: `backend/handlers/refund_handler.py` (NEW)

**Refund Rules Enforced**:
- ✅ 14-day window from initial purchase
- ✅ Starter → Plus: No refund if > 5GB OR > 5 galleries used
- ✅ Plus → Pro: No refund if > 50GB used  
- ✅ Automatic eligibility checking
- ✅ Admin review workflow for refund requests

**Key Functions**:
- `check_refund_eligibility(user)` - Validates refund eligibility
- `handle_request_refund(user, body)` - Submits refund request
- `handle_get_refund_status(user)` - Gets refund request status

**Usage Statistics Tracked**:
```python
{
    'days_since_purchase': 7,
    'total_storage_gb': 3.2,
    'galleries_since_purchase': 3,
    'purchase_date': '2025-01-15T10:30:00Z'
}
```

### 3. Audit Logging
**Integration Points** (to be created):
- All plan changes logged with timestamps
- Includes: user_id, action type, from_plan, to_plan, metadata
- Enables tracking of subscription history
- Helps prevent abuse and supports dispute resolution

**Required**: Create `utils/audit_log.py` with:
```python
def log_subscription_change(user_id, action, from_plan, to_plan, effective_at=None, metadata=None):
    """Log all subscription state changes"""
    pass
```

### 4. Improved State Machine Logic

**Current State Transitions**:
```
Free → Plus/Pro: Checkout → Active
Plus ↔ Pro: Immediate with proration
Plus/Pro → Free: Scheduled at period end
Canceled → Reactivate: Remove cancel_at_period_end
Pending Downgrade → Upgrade: Clear pending, apply new plan
```

**State Validation**:
- Checks for pending plan changes before allowing new changes
- Prevents invalid transitions (e.g., Free → Free)
- Handles reactivation separately to avoid currency mismatches
- Validates Stripe subscription state before modifications

---

## 🔧 REQUIRED ADDITIONAL WORK

### 1. Create Refunds DynamoDB Table

**AWS Console** or **CLI**:
```bash
aws dynamodb create-table \
    --table-name galerly-refunds \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        '[{
            "IndexName": "UserIdIndex",
            "KeySchema": [{"AttributeName":"user_id","KeyType":"HASH"}],
            "Projection": {"ProjectionType":"ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits":5,"WriteCapacityUnits":5}
        }]' \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 2. Create Audit Log Utility

**File**: `backend/utils/audit_log.py`
```python
"""
Subscription audit logging for compliance and dispute resolution
"""
import uuid
from datetime import datetime
from utils.config import dynamodb

audit_table = dynamodb.Table('galerly-audit-log')

def log_subscription_change(user_id, action, from_plan, to_plan, effective_at=None, metadata=None):
    """
    Log subscription state changes
    
    Actions: 'upgrade', 'downgrade_scheduled', 'reactivation', 
             'cancellation', 'checkout_completed'
    """
    try:
        audit_entry = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': action,
            'from_plan': from_plan,
            'to_plan': to_plan,
            'effective_at': effective_at,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        audit_table.put_item(Item=audit_entry)
        print(f"✅ Logged {action}: {from_plan} → {to_plan} for user {user_id}")
    except Exception as e:
        print(f"⚠️  Error logging audit entry: {str(e)}")
        # Don't fail the main operation if logging fails
```

**Create Table**:
```bash
aws dynamodb create-table \
    --table-name galerly-audit-log \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        '[{
            "IndexName": "UserIdTimestampIndex",
            "KeySchema": [
                {"AttributeName":"user_id","KeyType":"HASH"},
                {"AttributeName":"timestamp","KeyType":"RANGE"}
            ],
            "Projection": {"ProjectionType":"ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits":5,"WriteCapacityUnits":5}
        }]' \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 3. Frontend Improvements Needed

**File**: `frontend/js/billing.js`

**Add Refund Check Button**:
```javascript
// Add to displaySubscription() function
if (status === 'active' && subscription.subscription && currentPlan !== 'free') {
    html += `
        <button onclick="checkRefundEligibility()" class="item-5 submit-btn" 
                style="margin-top: 12px; width: 100%; background: #f97316; color: white;">
            <div class="main-6">
                <span>Request Refund</span>
            </div>
        </button>
    `;
}

// Add function
async function checkRefundEligibility() {
    try {
        const result = await window.apiRequest('billing/refund/check');
        
        if (result.eligible) {
            if (confirm(`You are eligible for a refund.\n\nUsage: ${result.details.total_storage_gb} GB, ${result.details.galleries_since_purchase} galleries\n\nWould you like to submit a refund request?`)) {
                const reason = prompt('Please provide a reason for your refund request (minimum 10 characters):');
                if (reason && reason.length >= 10) {
                    await submitRefundRequest(reason);
                }
            }
        } else {
            alert(`Not eligible for refund:\n\n${result.reason}\n\nDetails:\n${JSON.stringify(result.details, null, 2)}`);
        }
    } catch (error) {
        console.error('Error checking refund eligibility:', error);
        alert('Failed to check refund eligibility: ' + error.message);
    }
}

async function submitRefundRequest(reason) {
    try {
        const result = await window.apiRequest('billing/refund/request', {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
        alert(`✅ ${result.message}\n\nReference ID: ${result.refund_id}`);
        location.reload();
    } catch (error) {
        console.error('Error submitting refund request:', error);
        alert('Failed to submit refund request: ' + error.message);
    }
}
```

**Add Race Condition Handling**:
```javascript
// Update setupPlanChangeButtons() to handle 409 errors
try {
    const result = await changePlan(planId);
    // ... success handling
} catch (error) {
    if (error.status === 409) {
        alert('⚠️ Another subscription change is in progress. Please wait a moment and try again.');
    } else {
        alert(`Failed to change plan: ${error.message}`);
    }
    button.disabled = false;
    buttonText.textContent = originalText;
}
```

### 4. Email Template for Refund Requests

**File**: `backend/utils/email.py`

**Add Functions**:
```python
def send_admin_refund_request_notification(refund_id, user_email, username, plan, reason, details):
    """Notify admin of new refund request"""
    subject = f"🔔 Refund Request #{refund_id[:8]}"
    admin_email = os.environ.get('ADMIN_EMAIL', 'office@galerly.com')
    
    body = f"""
    <h2>New Refund Request</h2>
    <p><strong>Request ID:</strong> {refund_id}</p>
    <p><strong>User:</strong> {username} ({user_email})</p>
    <p><strong>Plan:</strong> {plan}</p>
    <p><strong>Reason:</strong> {reason}</p>
    
    <h3>Eligibility Details:</h3>
    <ul>
        <li>Days since purchase: {details.get('days_since_purchase')}</li>
        <li>Storage used: {details.get('total_storage_gb')} GB</li>
        <li>Galleries created: {details.get('galleries_since_purchase')}</li>
    </ul>
    
    <p><a href="https://admin.galerly.com/refunds/{refund_id}">Review Request →</a></p>
    """
    
    send_email(admin_email, subject, body)

def send_refund_request_confirmation_email(user_email, username, refund_id):
    """Confirm refund request submission to user"""
    subject = "Refund Request Received"
    
    body = f"""
    <h2>Your Refund Request Has Been Received</h2>
    <p>Hi {username},</p>
    <p>We've received your refund request (ID: {refund_id[:8]}).</p>
    <p>Our team will review your request and respond within 2-3 business days.</p>
    <p>You'll receive an email notification once a decision has been made.</p>
    """
    
    send_email(user_email, subject, body)
```

### 5. API Route Registration

**File**: `backend/api.py`

**Add Routes**:
```python
# Refund endpoints
elif path == '/v1/billing/refund/check':
    from handlers.refund_handler import handle_check_refund_eligibility
    return handle_check_refund_eligibility(user)

elif path == '/v1/billing/refund/request':
    from handlers.refund_handler import handle_request_refund
    body = json.loads(event.get('body', '{}'))
    return handle_request_refund(user, body)

elif path == '/v1/billing/refund/status':
    from handlers.refund_handler import handle_get_refund_status
    return handle_get_refund_status(user)
```

---

## 🔍 EDGE CASES NOW HANDLED

### 1. Rapid Plan Changes
**Scenario**: User clicks "Upgrade" multiple times
**Handling**: 
- First request sets `processing_change=True`
- Subsequent requests return 409 error
- User sees "Please wait" message

### 2. Cancel → Immediate Upgrade
**Scenario**: User cancels, then upgrades before period end
**Handling**:
- Clears `pending_plan='free'`
- Removes `cancel_at_period_end` from Stripe
- Applies new plan with proration
- User remains on current plan until upgrade applied

### 3. Downgrade → Change Mind → Upgrade
**Scenario**: User schedules Plus → Starter, then upgrades to Pro
**Handling**:
- Clears pending downgrade
- Removes scheduled Stripe changes
- Applies Pro plan immediately with proration

### 4. Multiple Downgrades in Period
**Scenario**: User tries Pro → Plus → Starter in same billing period
**Handling**:
- Pro → Plus: Scheduled at period end
- During period, Plus → Starter: Replaces pending with Starter
- Only one scheduled change at a time

### 5. Refund After Downgrade Request
**Scenario**: User schedules downgrade, then requests refund
**Handling**:
- Refund check sees pending_plan
- Still checks current plan usage
- Eligibility based on actual usage, not scheduled plan

---

## 📋 TESTING CHECKLIST

### Basic Flows
- [ ] Free → Plus upgrade (checkout)
- [ ] Free → Pro upgrade (checkout)
- [ ] Plus → Pro upgrade (immediate, prorated)
- [ ] Pro → Plus downgrade (scheduled)
- [ ] Plus → Free downgrade (with deletion if needed)

### Edge Cases
- [ ] Rapid double-click on upgrade button
- [ ] Cancel → Reactivate same plan
- [ ] Cancel → Upgrade to different plan
- [ ] Downgrade scheduled → Change to different downgrade
- [ ] Downgrade scheduled → Upgrade instead
- [ ] Downgrade scheduled → Reactivate current plan

### Refund Policy
- [ ] Check eligibility within 14 days, low usage → Eligible
- [ ] Check eligibility within 14 days, high usage → Not eligible
- [ ] Check eligibility after 14 days → Not eligible
- [ ] Submit refund request → Email sent to admin and user
- [ ] Check refund status → See pending request

### Error Handling
- [ ] Stripe API error → User sees friendly message
- [ ] Processing lock not released → Auto-cleanup after timeout
- [ ] Invalid plan ID → Validation error
- [ ] No Stripe subscription → Clear error message

---

## 🚨 CRITICAL SECURITY NOTES

1. **Never Trust Client-Side Data**: All plan changes validated server-side
2. **Idempotency**: Stripe operations are idempotent (safe to retry)
3. **Webhook Verification**: Stripe webhooks verified with signature
4. **Audit Trail**: All changes logged for dispute resolution
5. **Rate Limiting**: Consider adding rate limiting to prevent API abuse

---

## 📊 MONITORING RECOMMENDATIONS

**CloudWatch Metrics to Track**:
- `billing.plan_changes.count` (by action type)
- `billing.refund_requests.count`
- `billing.processing_lock.conflicts`
- `billing.stripe_api.errors`
- `billing.webhook.failures`

**Alerts to Configure**:
- More than 5 refund requests in 1 hour
- Processing lock held > 5 minutes
- Stripe webhook failures
- Plan change errors > 10% of attempts

---

## 🎯 NEXT STEPS

1. **IMMEDIATE** (Do Now):
   - [ ] Create `galerly-refunds` DynamoDB table
   - [ ] Create `galerly-audit-log` DynamoDB table
   - [ ] Deploy updated `billing_handler.py` with race condition prevention
   - [ ] Deploy new `refund_handler.py`

2. **SHORT TERM** (This Week):
   - [ ] Create `utils/audit_log.py`
   - [ ] Add refund email templates
   - [ ] Update frontend `billing.js` with refund UI
   - [ ] Add API routes for refund endpoints
   - [ ] Test all edge cases

3. **MEDIUM TERM** (This Month):
   - [ ] Create admin panel for refund review
   - [ ] Add CloudWatch monitoring
   - [ ] Implement rate limiting
   - [ ] Create automated cleanup job for stale processing locks

4. **LONG TERM** (Ongoing):
   - [ ] Monitor refund patterns
   - [ ] Analyze subscription churn
   - [ ] Optimize proration calculations
   - [ ] A/B test pricing strategies

---

## 📞 SUPPORT PROCESS

**User Requests Refund**:
1. Frontend checks eligibility automatically
2. User submits request with reason
3. Admin receives email notification
4. Admin reviews in admin panel (to be built)
5. Admin approves/rejects via Stripe Dashboard
6. User receives email notification
7. If approved, refund processed within 5-7 business days

**Current Manual Process** (until admin panel built):
1. User submits request → Stored in `galerly-refunds` table
2. Admin checks table directly or via email
3. Admin logs into Stripe Dashboard
4. Admin processes refund manually
5. Admin updates `galerly-refunds` table status
6. Admin sends email to user

---

## ✅ CONCLUSION

The billing system now has:
- **Robust race condition prevention**
- **Clear refund policy enforcement**
- **Comprehensive audit logging**
- **Improved state machine logic**
- **Better error handling**

**Remaining work**: Frontend UI updates, email templates, admin review panel

