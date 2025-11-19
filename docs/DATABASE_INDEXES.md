# Galerly - Complete Database Index Reference

## 📊 All Tables & Indexes

### 1. **galerly-users**
**Purpose:** User account management

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `email` (HASH) | Login, user lookup by email |
| **GSI: UserIdIndex** | `id` (HASH) | Query user by UUID |

**Access Patterns:**
- ✅ Get user by email (login)
- ✅ Get user by ID (from session)

---

### 2. **galerly-galleries**
**Purpose:** Gallery management with user isolation

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `user_id` (HASH) + `id` (RANGE) | User's galleries - automatic isolation |
| **GSI: ClientEmailIndex** | `client_email` (HASH) | Client gallery access |
| **GSI: ShareTokenIndex** | `share_token` (HASH) | Public gallery viewing via share link |
| **GSI: GalleryIdIndex** | `id` (HASH) | Gallery lookup by ID |

**Access Patterns:**
- ✅ List all galleries for a user: `query(user_id=X)`
- ✅ Get specific gallery: `get_item(user_id=X, id=Y)`
- ✅ Client galleries: `query(ClientEmailIndex, client_email=X)`
- ✅ Find gallery by share token: `query(ShareTokenIndex, share_token=Z)`
- ✅ Get gallery by ID: `query(GalleryIdIndex, id=X)`

**Security:** `user_id` as partition key = **complete data isolation per user**

---

### 3. **galerly-photos**
**Purpose:** Photo storage and management

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `id` (HASH) | Direct photo lookup |
| **GSI: GalleryIdIndex** | `gallery_id` (HASH) | List all photos in a gallery |
| **GSI: UserIdIndex** | `user_id` (HASH) | Security checks, list user's photos |

**Access Patterns:**
- ✅ Get photo by ID: `get_item(id=X)`
- ✅ List photos in gallery: `query(GalleryIdIndex, gallery_id=X)`
- ✅ List all user's photos: `query(UserIdIndex, user_id=X)`
- ✅ Verify photo ownership: `get_item(id=X)` → check `user_id`

**Security:** Every photo has `user_id` field for ownership verification

---

### 4. **galerly-sessions**
**Purpose:** User session management

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `token` (HASH) | Fast session validation |
| **GSI: UserIdIndex** | `user_id` (HASH) | List/revoke all user sessions |

**Access Patterns:**
- ✅ Validate session: `get_item(token=X)`
- ✅ List user sessions: `query(UserIdIndex, user_id=X)`
- ✅ Revoke all user sessions: Query by `user_id` → delete items

**Security:** Sessions are cryptographically random tokens, tied to specific users

---

### 5. **galerly-cities**
**Purpose:** City autocomplete database (public data)

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `city_ascii` (HASH) + `country` (RANGE) | Unique city identification |
| **GSI: country-population-index** | `country` (HASH) + `population` (RANGE) | Query cities by country, sorted by size |

**Access Patterns:**
- ✅ Get specific city: `get_item(city_ascii=X, country=Y)`
- ✅ List cities in country: `query(country-population-index, country=X)`
- ✅ Search cities: **In-memory cache** (loaded on Lambda cold start)

**Performance:** 45K+ cities loaded into Lambda memory for instant search (10-50ms)

---

### 6. **galerly-newsletters**
**Purpose:** Newsletter subscribers

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `email` (HASH) | Subscriber management |
| **GSI: SubscribedAtIndex** | `subscribed_at` (HASH) | Analytics queries |

**Access Patterns:**
- ✅ Check subscription: `get_item(email=X)`
- ✅ Subscribe/unsubscribe: `put_item/update_item`
- ✅ Analytics by date: `query(SubscribedAtIndex, subscribed_at=X)`

**Security:** Public endpoint - rate limited in API Gateway

---

### 7. **galerly-contact**
**Purpose:** Support tickets / contact form submissions

| Index Type | Keys | Use Case |
|------------|------|----------|
| **Primary Key** | `id` (HASH) | Unique ticket ID |
| **GSI: CreatedAtIndex** | `created_at` (HASH) | List tickets by date |
| **GSI: StatusIndex** | `status` (HASH) | Filter by status (new/in_progress/resolved) |

**Access Patterns:**
- ✅ Get ticket: `get_item(id=X)`
- ✅ Submit ticket: `put_item`
- ✅ List by date: `query(CreatedAtIndex, created_at=X)`
- ✅ Filter by status: `query(StatusIndex, status='new')`

**Security:** Public submission - admin-only reads

---

## 🎯 Index Strategy

### Primary Keys
- **HASH only:** Single-attribute lookup (e.g., `email`, `id`)
- **HASH + RANGE:** Hierarchical data (e.g., `user_id` + `gallery_id`)

### Global Secondary Indexes (GSI)
- **Alternate access patterns** (query by different attributes)
- **No extra cost** with PAY_PER_REQUEST billing
- **Eventually consistent** reads (acceptable for our use case)

---

## ⚡ Performance Characteristics

| Query Type | Latency | Cost |
|------------|---------|------|
| Primary key get | ~5-10ms | $0.25 per million |
| Primary key query | ~10-20ms | $0.25 per million |
| GSI query | ~15-30ms | $0.25 per million |
| Table scan | ~100ms-seconds | **Expensive - avoid!** |

---

## 🔐 Security Through Indexes

### User Data Isolation Methods:

1. **Partition Key Isolation** (galerly-galleries)
   - `user_id` as partition key
   - Users can ONLY query their own partition
   - **Impossible to access other users' data**

2. **Ownership Verification** (galerly-photos)
   - `user_id` field on every photo
   - Check ownership before updates/deletes
   - UserIdIndex for bulk operations

3. **Session Binding** (galerly-sessions)
   - Tokens tied to specific users
   - UserIdIndex for session management
   - Revoke all user sessions on logout

---

## 📝 Maintenance Commands

### Check All Indexes
```bash
cd backend
python manage_indexes.py
```

### Create Missing Indexes
```bash
python manage_indexes.py --create
```

### List Tables
```bash
python setup_dynamodb.py list
```

### Check Index Status (AWS CLI)
```bash
aws dynamodb describe-table --table-name galerly-photos \
  --query 'Table.GlobalSecondaryIndexes[*].[IndexName,IndexStatus]' \
  --region us-east-1
```

---

## ✅ Index Checklist

- [x] **galerly-users:** UserIdIndex
- [x] **galerly-galleries:** ClientEmailIndex, ShareTokenIndex, GalleryIdIndex
- [x] **galerly-photos:** GalleryIdIndex, UserIdIndex
- [x] **galerly-sessions:** UserIdIndex
- [x] **galerly-cities:** country-population-index
- [x] **galerly-newsletters:** SubscribedAtIndex
- [x] **galerly-contact:** CreatedAtIndex, StatusIndex

**Total: 12 indexes across 7 tables**

