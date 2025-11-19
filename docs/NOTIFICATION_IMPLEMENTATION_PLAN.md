# Notification System Implementation Status

## ✅ COMPLETED

### 1. New Photos Added (via Send Email Button)
- **Frontend**: `sendBatchEmailNotification()` in `gallery-loader.js`
- **Backend**: `handle_send_batch_notification()` in `photo_handler.py`
- **Endpoint**: `POST /v1/galleries/{id}/photos/notify-clients`
- **Status**: ✅ Working

---

## 🚧 TO IMPLEMENT

### 2. Gallery Shared
**When**: Gallery is first created/shared with clients
**Where to implement**: `backend/handlers/gallery_handler.py` - `handle_create_gallery()`
**Logic**:
```python
# After gallery creation, send notification to all client emails
for client_email in client_emails:
    notify_gallery_shared(
        gallery_id=new_gallery['id'],
        client_email=client_email,
        client_name=client_name,  # Extract from email if needed
        photographer_name=user['full_name'],
        gallery_url=f"{frontend_url}/client-gallery?token={share_token}",
        description=gallery_description
    )
```

### 3. Gallery Ready
**When**: Photos are added and gallery is ready for viewing
**Where to implement**: `backend/handlers/photo_handler.py` - `handle_confirm_upload()`
**Logic**: Send notification when FIRST photo is uploaded to an empty gallery
```python
# After photo upload confirmed
if previous_photo_count == 0 and new_photo_count == 1:
    # Gallery is now ready - send notification
    for client_email in client_emails:
        notify_gallery_ready(
            user_id=user['id'],
            gallery_id=gallery_id,
            client_email=client_email,
            client_name=client_name,
            photographer_name=user['full_name'],
            gallery_url=gallery_url,
            message='Your gallery is ready for viewing!'
        )
```

### 4. Selection Reminders
**When**: Photographer manually triggers
**Where to implement**: Frontend button + Backend endpoint
**Frontend**: Add button to `gallery.html` (similar to Send Email button)
**Backend**: Endpoint already exists!
- `handle_send_selection_reminder()` in `notification_handler.py`
- Endpoint: `POST /v1/notifications/send-selection-reminder`
  - Body: `{ "gallery_id": "xxx" }`

### 5. Gallery Expiring Soon
**When**: X days before expiry (scheduled job)
**Where to implement**: `backend/handlers/scheduled_handler.py` - create new function
**Logic**:
```python
def check_expiring_galleries():
    """Check for galleries expiring in next 7 days and send notifications"""
    # Scan galleries table for galleries with expiry_date in next 7 days
    # For each gallery:
    #   - Calculate days_remaining
    #   - If days_remaining <= 7 and not already notified:
    #       - Send notification to all client_emails
    #       - Mark as notified in gallery metadata
```
**Note**: Requires AWS EventBridge/Lambda scheduled rule (daily)

### 6. Custom Messages (Comment on Photo)
**When**: Photographer adds comment to a photo
**Where to implement**: `backend/handlers/photo_handler.py` - create `handle_add_comment()`
**Frontend**: Comment feature in photo modal (currently only allows client comments)
**Logic**:
```python
# When photographer adds comment to photo
notify_custom_message(
    user_id=user['id'],
    client_email=client_email,
    client_name=client_name,
    photographer_name=user['full_name'],
    subject=f"New message about {photo_title}",
    title="Your photographer left a message",
    message=comment_text,
    button_text="View Photo",
    button_url=f"{frontend_url}/client-gallery?token={token}&photo={photo_id}"
)
```

### 7. Client Selects Photos (Photographer Notification)
**When**: Client favorites/approves a photo
**Where to implement**: `backend/handlers/client_favorites_handler.py` - `handle_add_to_favorites()`
**Logic**:
```python
# After client adds photo to favorites
# Get photographer details
photographer = users_table.get_item(Key={'id': gallery['user_id']})['Item']

notify_client_selected_photos(
    photographer_id=photographer['id'],
    photographer_email=photographer['email'],
    photographer_name=photographer['full_name'],
    client_name=client_name,
    gallery_name=gallery['name'],
    gallery_url=f"{frontend_url}/gallery?id={gallery_id}",
    selection_count=1  # or total count if batch
)
```

### 8. Client Feedback (Photographer Notification)
**When**: Client leaves a comment on a photo
**Where to implement**: `backend/handlers/photo_handler.py` - `handle_add_comment()` (for client comments)
**Logic**:
```python
# After client adds comment
# Get photographer details
photographer = users_table.get_item(Key={'id': gallery['user_id']})['Item']

notify_client_feedback(
    photographer_id=photographer['id'],
    photographer_email=photographer['email'],
    photographer_name=photographer['full_name'],
    client_name=client_name,
    gallery_name=gallery['name'],
    gallery_url=f"{frontend_url}/gallery?id={gallery_id}&photo={photo_id}",
    rating=None,  # No rating system yet
    feedback=comment_text
)
```

---

## 📋 IMPLEMENTATION PRIORITY

1. **Gallery Shared** - High Priority (core user flow)
2. **Client Selects Photos** - High Priority (photographer value)
3. **Client Feedback** - High Priority (photographer value)
4. **Gallery Ready** - Medium Priority (nice to have)
5. **Selection Reminders** - Medium Priority (frontend button needed)
6. **Custom Messages** - Low Priority (requires comment feature for photographers)
7. **Gallery Expiring Soon** - Low Priority (requires scheduled job setup)

---

## 📝 NOTES

- All notification functions already exist in `notification_handler.py`
- All email templates already exist in `email_templates_branded.py`
- Just need to add the trigger calls in the right places
- Need to check notification preferences before sending (using `should_send_notification()`)


