# Galerly Docker Architecture

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Host Machine (macOS)                             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Docker Network: galerly-local                    │ │
│  │                         (Bridge Network)                            │ │
│  │                                                                     │ │
│  │  ┌──────────────────┐   ┌─────────────────┐   ┌────────────────┐ │ │
│  │  │   LocalStack     │   │   Backend       │   │   Frontend     │ │ │
│  │  │   Container      │   │   Container     │   │   Container    │ │ │
│  │  │                  │   │                 │   │                │ │ │
│  │  │  - S3            │◄──┤  Python 3.11    │◄──┤  Node 18       │ │ │
│  │  │  - DynamoDB      │   │  Flask API      │   │  React + Vite  │ │ │
│  │  │  - SES           │   │  boto3          │   │  TypeScript    │ │ │
│  │  │                  │   │                 │   │                │ │ │
│  │  │  Port: 4566      │   │  Port: 5001     │   │  Port: 5173    │ │ │
│  │  │                  │   │                 │   │                │ │ │
│  │  └──────────────────┘   └─────────────────┘   └────────────────┘ │ │
│  │         │                        │                      │         │ │
│  └─────────┼────────────────────────┼──────────────────────┼─────────┘ │
│            │                        │                      │           │
│            │                        │                      │           │
│         localhost:4566          localhost:5001        localhost:5173  │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Persistent Storage                           │   │
│  │                                                                 │   │
│  │  localstack_data/                                              │   │
│  │  ├── s3/                    # S3 bucket data                   │   │
│  │  ├── dynamodb/              # DynamoDB tables                  │   │
│  │  └── recorded_api_calls/    # API call recordings            │   │
│  │                                                                 │   │
│  │  backend/                   # Backend code (volume mount)      │   │
│  │  frontend/                  # Frontend code (volume mount)     │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Request Flow
```
Browser (localhost:5173)
    │
    ├──► Frontend Container (React/Vite)
    │         │
    │         ├──► API Request to http://localhost:5001
    │         │         │
    │         │         └──► Backend Container (Flask)
    │         │                   │
    │         │                   ├──► AWS SDK (boto3)
    │         │                   │         │
    │         │                   │         └──► LocalStack Container
    │         │                   │                   │
    │         │                   │                   ├──► S3 Operations
    │         │                   │                   ├──► DynamoDB Queries
    │         │                   │                   └──► SES Email
    │         │                   │
    │         │                   └──► Response
    │         │
    │         └──► Render UI
    │
    └──► Direct S3 Access (for renditions)
              │
              └──► LocalStack:4566
```

### 2. Container-to-Container Communication
```
Frontend Container
    │
    ├──► Uses host network (localhost:5001)
    │    for API calls from browser
    │
Backend Container
    │
    ├──► Uses Docker network (localstack:4566)
    │    for AWS service calls
    │
LocalStack Container
    │
    └──► Listens on all networks (4566)
```

## Volume Mounts

### Backend Container
```
Host: backend/
  │
  ├──► Container: /app
  │
  └──► Hot Reload: Flask auto-reloads on file changes
```

### Frontend Container
```
Host: frontend/
  │
  ├──► Container: /app
  │
  └──► Hot Reload: Vite HMR updates on file changes
       (node_modules excluded via anonymous volume)
```

### LocalStack Container
```
Host: localstack_data/
  │
  ├──► Container: /var/lib/localstack
  │
  └──► Persistence: Data survives container restarts
```

## Network Configuration

### Docker Network: galerly-local
- **Type**: Bridge
- **Driver**: bridge
- **Subnet**: Auto-assigned by Docker
- **Gateway**: Auto-assigned by Docker

### Container DNS
- Containers can resolve each other by name:
  - `localstack` → LocalStack container
  - `backend` → Backend container
  - `frontend` → Frontend container

### Port Mapping
```
Container Name         Internal Port    External Port    Purpose
─────────────────────────────────────────────────────────────────
galerly-localstack     4566            → 4566            AWS APIs
galerly-backend-local  5001            → 5001            Flask API
galerly-frontend-      5173            → 5173            Vite Dev
  local                                                  Server
```

## Environment Variables

### LocalStack Container
```yaml
Environment:
  - AWS_ENDPOINT_URL=http://localstack:4566  # Internal
  - AWS_REGION=us-east-1
  - Services enabled: s3,dynamodb,ses,lambda
  
Exposed:
  - http://localhost:4566  # External access
```

### Backend Container
```yaml
Environment (from .env.local):
  - AWS_ENDPOINT_URL=http://localstack:4566  # Container network
  - AWS_REGION=us-east-1
  - JWT_SECRET=***
  - DYNAMODB_TABLE_USERS=galerly-users-local
  - S3_PHOTOS_BUCKET=galerly-photos-local
  - PORT=5001
  - FLASK_HOST=0.0.0.0
  
Exposed:
  - http://localhost:5001  # External access
```

### Frontend Container
```yaml
Environment:
  - VITE_BACKEND_HOST=localhost       # Browser connects
  - VITE_BACKEND_PORT=5001             # to host network
  - VITE_BACKEND_PROTOCOL=http
  - VITE_LOCALSTACK_HOST=localhost
  - VITE_LOCALSTACK_PORT=4566
  
Exposed:
  - http://localhost:5173  # External access
```

## Build Process

### 1. Backend Build
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["python", "api.py"]
```

### 2. Frontend Build
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

## Startup Sequence

```
1. Start LocalStack Container
   ├──► Wait for health check (/_localstack/health)
   └──► ✅ Ready

2. Setup AWS Resources
   ├──► Create S3 buckets
   ├──► Create DynamoDB tables
   └──► ✅ Resources ready

3. Build Backend Container
   ├──► Install Python dependencies
   ├──► Copy application code
   └──► ✅ Backend built

4. Start Backend Container
   ├──► Load .env.local
   ├──► Start Flask server
   ├──► Wait for health check (/health)
   └──► ✅ Backend ready

5. Build Frontend Container
   ├──► Install Node dependencies
   ├──► Copy application code
   └──► ✅ Frontend built

6. Start Frontend Container
   ├──► Start Vite dev server
   ├──► Wait for server ready
   └──► ✅ Frontend ready

7. ✅ All Services Running
   └──► Show live logs
```

## Health Checks

### LocalStack
```bash
curl http://localhost:4566/_localstack/health
```

### Backend
```bash
curl http://localhost:5001/health
```

### Frontend
```bash
curl http://localhost:5173
```

## Resource Requirements

### Minimum
- **Docker**: 4GB RAM, 2 CPU cores
- **Disk**: 10GB free space

### Recommended
- **Docker**: 8GB RAM, 4 CPU cores
- **Disk**: 20GB free space

## Security Considerations

### Local Development Only
- No TLS/HTTPS required
- Simplified authentication
- Debug mode enabled
- All ports exposed to localhost

### Production Differences
- TLS/HTTPS required
- Strict CORS policies
- Debug mode disabled
- Only necessary ports exposed
- Secrets managed externally

## Troubleshooting Flow

```
Container Issue?
    │
    ├──► Container not running?
    │    └──► Check: docker ps -a
    │         └──► View logs: docker logs <container>
    │
    ├──► Port conflict?
    │    └──► Check: lsof -i :<port>
    │         └──► Stop conflicting service
    │
    ├──► Build failed?
    │    └──► Rebuild: docker-compose build --no-cache
    │
    ├──► Network issue?
    │    └──► Check: docker network inspect galerly-local
    │
    └──► Volume issue?
         └──► Remove: docker-compose down -v
              └──► Restart: ./scripts/start-localstack.sh
```

## Performance Tips

### 1. Docker Resources
- Allocate more RAM to Docker Desktop
- Enable VirtioFS for faster file sync

### 2. Build Optimization
- Use `.dockerignore` to exclude unnecessary files
- Layer caching for faster rebuilds

### 3. Volume Performance
- Named volumes for node_modules (faster than bind mounts)
- Polling-based file watching for Docker

### 4. Development Workflow
- Keep containers running between code changes
- Use hot reload instead of rebuilding
- Only rebuild when dependencies change
