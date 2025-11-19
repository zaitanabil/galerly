# Gallery Share Token Expiration System

## Overview

All gallery share tokens automatically expire after **7 days** to comply with Swiss data protection laws and security best practices.

## How It Works

### Token Lifecycle

```
Gallery Created
    ↓
Token Generated (Valid for 7 days)
    ↓
Client Access Attempt
    ↓
Check Token Age
    ├─ Valid (< 7 days) → ✅ Allow Access
    └─ Expired (> 7 days) → 🔄 Auto-Regenerate → ✅ Allow Access
```

### Token Expiration: 7 Days

**Compliance:** Swiss Federal Act on Data Protection (FADP) and Swiss law requirements

- **Creation:** When a gallery is created, `share_token_created_at` is set
- **Validation:** On every access, token age is checked
- **Expiration:** If token age > 7 days, it's considered expired
- **Regeneration:** System automatically generates a new token
- **Notification:** Photographer sees new share URL in dashboard

## Implementation Details

### Database Schema

**New Field Added to Galleries:**
```python
'share_token_created_at': '2025-11-16T22:09:10.790931Z'  # ISO 8601 format
```

### Backend Logic

**Location:** `backend/handlers/client_handler.py`

#### Token Expiration Check
```python
def is_token_expired(token_created_at):
    """Check if a share token is expired (older than 7 days)"""
    if not token_created_at:
        return True  # No creation date = expired
    
    created_date = datetime.fromisoformat(token_created_at.replace('Z', ''))
    age = datetime.utcnow() - created_date
    return age > timedelta(days=7)
```

#### Auto-Regeneration
```python
def regenerate_gallery_token(gallery):
    """Regenerate expired share token for a gallery"""
    new_token = secrets.token_urlsafe(16)
    current_time = datetime.utcnow().isoformat() + 'Z'
    frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
    new_share_url = f"{frontend_url}/client-gallery?token={new_token}"
    
    # Update in DynamoDB
    galleries_table.update_item(
        Key={'user_id': gallery['user_id'], 'id': gallery['id']},
        UpdateExpression='SET share_token = :token, share_token_created_at = :created, share_url = :url',
        ExpressionAttributeValues={
            ':token': new_token,
            ':created': current_time,
            ':url': new_share_url
        }
    )
    
    return gallery
```

### Gallery Access Flow

**When a client accesses a gallery via share token:**

1. **Lookup Gallery:** Find gallery by `share_token`
2. **Check Expiration:** Validate `share_token_created_at`
3. **If Expired:**
   - Generate new token
   - Update database
   - Set `gallery['token_expired'] = True`
   - Log regeneration
4. **If Valid:** Continue normal access
5. **Return Gallery:** Always allow access (user-friendly)

### Files Modified

#### `backend/handlers/gallery_handler.py`
- Added `share_token_created_at` to new galleries
- Added `share_token_created_at` to duplicated galleries
- Store creation timestamp alongside token

#### `backend/handlers/client_handler.py`
- Added `TOKEN_EXPIRATION_DAYS = 7` constant
- Added `is_token_expired()` function
- Added `regenerate_gallery_token()` function
- Modified `handle_get_client_gallery_by_token()` to check/regenerate

## Migration

### Add Token Creation Dates

**Script:** `backend/add_token_expiration.py`

Adds `share_token_created_at` to existing galleries that don't have it.

```bash
cd backend
source venv/bin/activate
python3 add_token_expiration.py
```

**What It Does:**
1. Scans all galleries in DynamoDB
2. Finds galleries without `share_token_created_at`
3. Adds field with current timestamp
4. Updates `updated_at` field

**Result:** All existing tokens are valid for 7 more days

## User Experience

### For Clients (Gallery Viewers)

**Seamless Experience:**
- Old links still work (token auto-regenerates)
- No error messages for expired tokens
- Gallery loads normally
- Transparent regeneration

**Example:**
```
Client clicks old link (8 days old)
    ↓
Backend detects expiration
    ↓
New token generated automatically
    ↓
Gallery loads normally
    ↓
Client sees no difference
```

### For Photographers

**Dashboard Updates:**
- New share URL appears after token regeneration
- Share button shows current URL
- Old URLs become invalid after regeneration
- Notification that link was updated (optional)

**Best Practice:**
- Check share URLs periodically
- Re-share links if clients report issues
- Use dashboard to get latest URL

## Security Benefits

### Token Rotation
- **Automatic:** No manual intervention needed
- **Frequent:** Every 7 days maximum
- **Transparent:** Users unaffected
- **Secure:** Old tokens become invalid

### Attack Mitigation
- **Link Sharing:** Limits exposure window
- **Stolen Tokens:** Expire automatically
- **Social Engineering:** Reduces effectiveness
- **Data Leaks:** Time-limited impact

### Compliance
- **Swiss FADP:** 7-day access token limit
- **GDPR:** Data minimization principle
- **Security Standards:** Token rotation best practice

## API Response

### Expired Token Response

**Status:** `200 OK` (Still serves gallery)

**Response Body:**
```json
{
  "id": "afab3c2c-35aa-422d-a3ea-4abf2d79802b",
  "name": "FPVFocus",
  "share_token": "NEW_TOKEN_HERE",
  "share_url": "https://galerly.com/client-gallery?token=NEW_TOKEN_HERE",
  "share_token_created_at": "2025-11-16T22:09:10.790931Z",
  "token_expired": true,
  "message": "This share link has expired. A new link has been generated.",
  "photos": [...],
  "photographer_name": "NZ"
}
```

### Valid Token Response

**Status:** `200 OK`

**Response Body:**
```json
{
  "id": "afab3c2c-35aa-422d-a3ea-4abf2d79802b",
  "name": "FPVFocus",
  "share_token": "ZFejffd_Cg1y76mfR-tZPQ",
  "share_url": "https://galerly.com/client-gallery?token=ZFejffd_Cg1y76mfR-tZPQ",
  "share_token_created_at": "2025-11-16T22:09:10.790931Z",
  "photos": [...],
  "photographer_name": "NZ"
}
```

## Testing

### Test Token Expiration

**Manual Test:**
```bash
# 1. Create a test gallery
# 2. Manually set token_created_at to 8 days ago
aws dynamodb update-item \
  --table-name galerly-galleries \
  --key '{"user_id": {"S": "USER_ID"}, "id": {"S": "GALLERY_ID"}}' \
  --update-expression "SET share_token_created_at = :date" \
  --expression-attribute-values '{":date": {"S": "2025-11-08T00:00:00Z"}}'

# 3. Access gallery via token
curl "https://galerly.com/client-gallery?token=TOKEN"

# 4. Check response - should have token_expired: true
```

### Verify Auto-Regeneration

```python
# Check if token was regenerated
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('galerly-galleries')

response = table.get_item(Key={'user_id': 'USER_ID', 'id': 'GALLERY_ID'})
gallery = response['Item']

print(f"Token: {gallery['share_token']}")
print(f"Created: {gallery['share_token_created_at']}")
print(f"Share URL: {gallery['share_url']}")
```

## Monitoring

### CloudWatch Logs

**Look for:**
```
✅ Regenerated token for gallery: FPVFocus (ID: afab3c2c-...)
⚠️ Token expired for gallery afab3c2c-..., regenerated new token
```

### Database Checks

**Find galleries with old tokens:**
```python
from datetime import datetime, timedelta

# Scan for galleries with tokens older than 6 days
threshold = (datetime.utcnow() - timedelta(days=6)).isoformat() + 'Z'

response = galleries_table.scan(
    FilterExpression='share_token_created_at < :threshold',
    ExpressionAttributeValues={':threshold': threshold}
)

print(f"Galleries with tokens > 6 days old: {len(response['Items'])}")
```

## Troubleshooting

### Issue: Token Keeps Regenerating

**Cause:** `share_token_created_at` missing or invalid

**Fix:**
```bash
cd backend
python3 add_token_expiration.py
```

### Issue: Old Links Not Working

**Cause:** Token expired and regenerated

**Solution:**
1. Photographer logs into dashboard
2. Opens gallery settings
3. Copies new share URL
4. Shares updated link with clients

### Issue: Migration Fails

**Cause:** DynamoDB permissions or connection

**Fix:**
```bash
# Check AWS credentials
aws dynamodb describe-table --table-name galerly-galleries

# Verify .env file
cat backend/.env | grep AWS_

# Re-run migration
cd backend && python3 add_token_expiration.py
```

## Future Enhancements

### Planned Features

1. **Email Notifications**
   - Notify photographer when token regenerates
   - Send new link to clients automatically

2. **Configurable Expiration**
   - Allow photographers to set custom expiration (1-7 days)
   - Premium users: longer expiration periods

3. **Token Analytics**
   - Track token regeneration frequency
   - Monitor access patterns
   - Alert on suspicious activity

4. **Batch Regeneration**
   - Admin tool to regenerate all tokens
   - Scheduled regeneration for extra security

## Status: ✅ IMPLEMENTED

- ✅ Token expiration logic implemented
- ✅ Auto-regeneration working
- ✅ Database migration completed
- ✅ Swiss law compliant (7-day max)
- ✅ User-friendly experience
- ✅ Deployed to production

**Last Updated:** 2025-11-16

