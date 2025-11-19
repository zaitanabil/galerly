# API Reference

Base URL: `https://ow085upbvb.execute-api.us-east-1.amazonaws.com/prod/api/v1`

## Authentication

Most endpoints require Bearer token in header:
```
Authorization: Bearer <token>
```

## Endpoints

### Public (No Auth)

#### Authentication
```http
POST /auth/register
Body: { email, password, name, username, role }
Returns: { token, user }

POST /auth/login
Body: { email, password }
Returns: { token, user }
```

#### Photographers
```http
GET /photographers?city=Paris
Returns: [ { id, name, username, city, specialties, bio, portfolio_url } ]

GET /photographers/{id}
Returns: { id, name, username, city, specialties, bio, gallery_count, photo_count }
```

#### Cities
```http
GET /cities/search?q=par
Returns: [ { city_ascii, country, lat, lng, population } ]
```

#### Newsletter
```http
POST /newsletter/subscribe
Body: { email, firstName }
Returns: { message, success }

POST /newsletter/unsubscribe
Body: { email }
Returns: { message, success }
```

#### Contact/Support
```http
POST /contact/submit
Body: { name, email, issueType, message }
Returns: { message, ticket_id, success }
```

### Protected (Auth Required)

#### User
```http
GET /auth/me
Returns: { id, email, name, username, role, subscription, city, bio, specialties }

PUT /profile
Body: { name?, username?, bio?, city?, specialties?, portfolio_url? }
Returns: { message, user }
```

#### Galleries
```http
GET /galleries
Returns: [ { id, name, client_name, photo_count, view_count, created_at } ]

POST /galleries
Body: { name, description, client_name, client_email, privacy, allow_download, allow_comments }
Returns: { message, gallery }

GET /galleries/{id}
Returns: { gallery, photos }

PUT /galleries/{id}
Body: { name?, description?, privacy?, allow_download?, allow_comments? }
Returns: { message, gallery }

DELETE /galleries/{id}
Returns: { message }
```

#### Photos
```http
POST /galleries/{id}/photos
Body: FormData with 'photo' file
Returns: { message, photo }

PUT /photos/{id}
Body: { status?, title?, description? }
Returns: { message, photo }

POST /photos/{id}/comments
Body: { comment }
Returns: { message, photo }
```

#### Client Access
```http
GET /client/galleries
Returns: [ { id, name, photographer_name, photo_count, created_at } ]

GET /client/galleries/{id}
Returns: { gallery, photos, photographer }
```

#### Dashboard
```http
GET /dashboard
Returns: { 
  gallery_count, 
  photo_count, 
  total_views,
  recent_galleries: [],
  recent_photos: []
}
```

## Status Codes

- `200` - Success
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (access denied)
- `404` - Not found
- `500` - Server error

## Rate Limits

- API Gateway: 10,000 req/sec
- Newsletter: Throttled per IP
- Photo upload: 50MB max file size

## Error Response

```json
{
  "error": "Error message",
  "message": "Detailed description"
}
```

## Success Response

```json
{
  "message": "Success message",
  "data": { ... }
}
```

