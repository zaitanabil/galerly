# Notification Preferences & File Upload Fixes

## Date: 2025-11-17

## Issues Fixed

### 1. ✅ Notification Preferences JavaScript Errors

**Problem:** 
```
TypeError: Cannot set properties of null (setting 'checked')
```

JavaScript was trying to access checkboxes that don't exist in the HTML.

**Solution:**
Updated `/frontend/js/notification-preferences.js` to:
- Use safe checkbox accessors (check if element exists before setting)
- Only use checkboxes that actually exist in HTML:
  - `notify_gallery_shared`
  - `notify_gallery_ready`
  - `notify_selection_reminder`
  - `notify_gallery_expiring`
  - `notify_custom_messages`
  - `notify_client_selected_photos`
  - `notify_client_feedback_received`
- Removed references to non-existent checkboxes:
  - `notify_new_photos_added` (sent manually from gallery)
  - `notify_payment_received` (not implemented)
  - `notify_gallery_viewed` (not implemented)

**Email Notifications Available:**

**Notify Clients When:**
1. ✅ Gallery Shared - When you share a new gallery
2. ✅ Gallery Ready - When their gallery is ready for viewing
3. ✅ Selection Reminders - Remind them to select favorites
4. ✅ Gallery Expiring Soon - When gallery about to expire
5. ✅ Custom Messages - When you send them a message
6. ✅ New Photos Added - Sent manually from gallery page

**Notify Me When:**
1. ✅ Client Selects Photos - When client selects favorites
2. ✅ Client Feedback - When client leaves feedback

### 2. ✅ RAW File Upload Support (DNG, CR2, NEF, etc.)

**Problem:**
File picker wasn't allowing selection of RAW formats like `.dng`

**Solution:**
Updated file input `accept` attribute in:
- `/frontend/gallery.html`
- `/frontend/client-gallery.html`

**Before:**
```html
accept="image/*"
```

**After:**
```html
accept="image/*,.dng,.cr2,.cr3,.nef,.arw,.raf,.orf,.rw2,.pef,.3fr,.heic,.heif"
```

**Now Supports:**
- ✅ Standard: JPEG, PNG, WEBP, GIF
- ✅ Adobe DNG (`.dng`)
- ✅ Canon RAW (`.cr2`, `.cr3`)
- ✅ Nikon RAW (`.nef`)
- ✅ Sony RAW (`.arw`)
- ✅ Fujifilm RAW (`.raf`)
- ✅ Olympus RAW (`.orf`)
- ✅ Panasonic RAW (`.rw2`)
- ✅ Pentax RAW (`.pef`)
- ✅ Hasselblad RAW (`.3fr`)
- ✅ Apple HEIC/HEIF (`.heic`, `.heif`)

### 3. ⚠️  City Search API Error (500)

**Issue:**
```
GET /v1/cities/search?q=Fribourg 500 (Internal Server Error)
```

**Status:** Backend issue - requires investigation
- Code in `/backend/utils/cities.py` looks correct
- Possible causes:
  - DynamoDB table 'galerly-cities' not populated
  - Table doesn't exist
  - Region mismatch
  - Permission issues

**Solution:** Run city import script:
```bash
cd backend
python import_cities_to_dynamodb.py
```

## Files Modified

1. ✅ `/frontend/js/notification-preferences.js` - Fixed null reference errors
2. ✅ `/frontend/gallery.html` - Added RAW file support
3. ✅ `/frontend/client-gallery.html` - Added RAW file support

## Backend Already Supports

All these notification types are already implemented in the backend:

1. **gallery_shared** → `handlers/notification_handler.py::notify_gallery_shared()`
2. **gallery_ready** → `handlers/notification_handler.py::notify_gallery_ready()`
3. **new_photos_added** → `utils/email.py::send_new_photos_added_email()`
4. **selection_reminder** → `handlers/notification_handler.py::notify_selection_reminder()`
5. **gallery_expiring** → `handlers/gallery_expiration_handler.py`
6. **custom_messages** → `handlers/notification_handler.py::notify_custom_message()`
7. **client_selected_photos** → `handlers/notification_handler.py::notify_client_selection()`
8. **client_feedback_received** → `handlers/notification_handler.py::notify_client_feedback()`

## Manual Email Triggers (from Gallery Page)

Photographers can manually send:
- **"Send Email" button** → Sends "new_photos_added" notification to all clients
- **"Remind Clients" button** → Sends selection reminder to all clients

## Testing

1. ✅ Notification preferences page loads without errors
2. ✅ Can save notification preferences
3. ✅ File picker shows RAW files (.dng, .cr2, .nef, etc.)
4. ⚠️  City search needs backend fix (populate cities table)

## Deployment

Frontend changes are ready (just refresh browser).

Backend changes (if any needed for city search):
```bash
cd backend
# Populate cities if needed
python import_cities_to_dynamodb.py

# Deploy Lambda
zip -r galerly-modular.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x "venv/*"
aws lambda update-function-code --function-name galerly-api --zip-file fileb://galerly-modular.zip
```

