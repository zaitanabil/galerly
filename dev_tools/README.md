# Galerly Development Tools

Essential development scripts for running and managing Galerly locally.

## 🚀 Quick Start

```bash
# Start everything (User App + Admin App + LocalStack)
./dev_tools/start-all.sh

# Stop everything
./dev_tools/stop-all.sh

# Check status of all services
./dev_tools/check-status.sh
```

## 📋 Available Scripts

### Main Scripts

#### `start-all.sh`
**Start complete development environment**
- Starts LocalStack (S3, DynamoDB, SES)
- Starts User App (frontend + backend in Docker)
- Starts Admin App (frontend + backend locally)

**Usage:**
```bash
./dev_tools/start-all.sh
```

**What it does:**
1. Validates environment configuration
2. Starts LocalStack container
3. Sets up AWS resources (S3 buckets, DynamoDB tables)
4. Starts user app backend (Docker)
5. Starts user app frontend (Docker)
6. Starts admin app backend (local Python)
7. Starts admin app frontend (local Node.js)

**Services:**
- User Frontend: http://localhost:5173
- User Backend: http://localhost:5001
- Admin Frontend: http://localhost:3001
- Admin Backend: http://localhost:5002
- LocalStack: http://localhost:4566

---

#### `stop-all.sh`
**Stop all services**

**Usage:**
```bash
./dev_tools/stop-all.sh
```

**What it does:**
1. Stops Docker containers
2. Kills admin app processes
3. Cleans up ports 5002 and 3001

---

#### `check-status.sh`
**Check status of all running services**

**Usage:**
```bash
./dev_tools/check-status.sh
```

**Shows:**
- Docker containers status
- LocalStack health
- User app status (frontend + backend)
- Admin app status (frontend + backend)
- Quick links to all services

---

### Development Scripts

#### `dev-rebuild.sh`
**Complete rebuild of all services**

Useful when:
- Docker images are outdated
- Need fresh start with no cache
- After major code changes

**Usage:**
```bash
./dev_tools/dev-rebuild.sh
```

**What it does:**
1. Stops all services
2. Removes Docker images
3. Cleans build artifacts
4. Rebuilds and restarts everything

---

#### `restart-backend.sh`
**Quick restart user app backend only**

**Usage:**
```bash
./dev_tools/restart-backend.sh
```

**Use when:** Making Python backend code changes

---

#### `restart-frontend.sh`
**Quick restart user app frontend only**

**Usage:**
```bash
./dev_tools/restart-frontend.sh
```

**Use when:** Frontend not hot-reloading properly

---

#### `restart-admin-backend.sh`
**Quick restart admin app backend only**

**Usage:**
```bash
./dev_tools/restart-admin-backend.sh
```

**Use when:** Making admin backend code changes

---

#### `restart-admin-frontend.sh`
**Quick restart admin app frontend only**

**Usage:**
```bash
./dev_tools/restart-admin-frontend.sh
```

**Use when:** Admin frontend not hot-reloading properly

---

### Utility Scripts

#### `view-logs.sh`
**Interactive log viewer**

**Usage:**
```bash
./dev_tools/view-logs.sh
```

**Options:**
1. All Docker services
2. User backend only
3. User frontend only
4. Admin backend only
5. Admin frontend only
6. LocalStack only

---

#### `run-tests.sh`
**Run all tests**

**Usage:**
```bash
./dev_tools/run-tests.sh
```

**Runs:**
- User app frontend tests (Vitest)
- User app backend tests (pytest, if installed)

**Current Status:**
- ✅ 39 frontend tests passing
- ✅ 37 backend test files ready

---

#### `db-shell.sh`
**Interactive database explorer**

**Usage:**
```bash
./dev_tools/db-shell.sh
```

**Features:**
1. List all DynamoDB tables
2. Scan a table
3. List all S3 buckets
4. List objects in bucket
5. Count items in all tables
6. Interactive AWS CLI

**Example commands:**
```bash
# List tables
aws --endpoint-url=http://localhost:4566 dynamodb list-tables

# Scan users table
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name galerly-users-local

# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls
```

---

#### `reset-localstack.sh`
**Reset LocalStack data**

⚠️  **Destructive operation!** Deletes all data in LocalStack.

**Usage:**
```bash
./dev_tools/reset-localstack.sh
```

**What it deletes:**
- All S3 buckets and objects
- All DynamoDB tables
- All LocalStack resources

**Use when:**
- Need fresh database
- Testing from scratch
- Development data is corrupted

---

#### `backup-localstack-s3.sh`
**Backup LocalStack S3 data**

**Usage:**
```bash
./dev_tools/backup-localstack-s3.sh
```

**Creates backup of:**
- All S3 buckets
- All objects in buckets

**Backup location:** `./local/backups/s3-backup-YYYY-MM-DD-HHMMSS/`

---

#### `restore-localstack-s3.sh`
**Restore LocalStack S3 data**

**Usage:**
```bash
./dev_tools/restore-localstack-s3.sh
```

**Prompts for backup directory to restore**

---

## 🔧 Common Workflows

### Daily Development

```bash
# Morning - Start everything
./dev_tools/start-all.sh

# Check if everything is running
./dev_tools/check-status.sh

# View logs while developing
./dev_tools/view-logs.sh

# Evening - Stop everything
./dev_tools/stop-all.sh
```

### After Backend Code Changes

```bash
# Quick restart
./dev_tools/restart-backend.sh

# Or restart admin backend
./dev_tools/restart-admin-backend.sh
```

### After Frontend Code Changes

Usually hot-reload works, but if not:
```bash
./dev_tools/restart-frontend.sh
# or
./dev_tools/restart-admin-frontend.sh
```

### Testing

```bash
# Run all tests
./dev_tools/run-tests.sh

# Or manually
cd user-app/frontend && npm test
cd user-app/backend && pytest
```

### Database Operations

```bash
# Explore database
./dev_tools/db-shell.sh

# Backup before major changes
./dev_tools/backup-localstack-s3.sh

# Reset if needed
./dev_tools/reset-localstack.sh
```

### Complete Rebuild

```bash
# When things are broken
./dev_tools/dev-rebuild.sh
```

---

## 📁 Project Structure

```
galerly.com/
├── user-app/
│   ├── backend/          # User API (Docker, Port 5001)
│   └── frontend/         # User UI (Docker, Port 5173)
├── admin-app/
│   ├── backend/          # Admin API (Local, Port 5002)
│   └── frontend/         # Admin UI (Local, Port 3001)
├── docker/
│   └── docker-compose.localstack.yml
├── dev_tools/            # This directory
└── logs/                 # Admin app logs
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check status
./dev_tools/check-status.sh

# View logs
./dev_tools/view-logs.sh

# Try rebuild
./dev_tools/dev-rebuild.sh
```

### Port Already in Use

```bash
# Check what's using the port
lsof -ti:5001  # User backend
lsof -ti:5173  # User frontend
lsof -ti:5002  # Admin backend
lsof -ti:3001  # Admin frontend

# Kill process
kill -9 $(lsof -ti:5002)
```

### LocalStack Not Responding

```bash
# Reset LocalStack
./dev_tools/reset-localstack.sh

# Or restart Docker
docker-compose -f docker/docker-compose.localstack.yml restart localstack
```

### Docker Issues

```bash
# Stop all containers
docker-compose -f docker/docker-compose.localstack.yml down

# Remove old images
docker rmi galerly-backend-local galerly-frontend-local

# Rebuild
./dev_tools/dev-rebuild.sh
```

---

## 📝 Environment Files

Make sure these files exist before starting:

### User App
- `user-app/backend/.env.local` (copy from `.env.local.template`)
- `user-app/frontend/.env` (auto-created by start-all.sh)

### Admin App
- `admin-app/backend/.env` (auto-created by start-all.sh)

---

## 🎯 Development Tips

1. **Use `check-status.sh` often** - Quick way to see what's running
2. **Keep logs open** - Run `view-logs.sh` in a separate terminal
3. **Backup before experiments** - Use `backup-localstack-s3.sh`
4. **Reset when stuck** - `reset-localstack.sh` solves many issues
5. **Test frequently** - Run `run-tests.sh` before committing

---

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| User Frontend | 5173 | http://localhost:5173 |
| User Backend | 5001 | http://localhost:5001 |
| Admin Frontend | 3001 | http://localhost:3001 |
| Admin Backend | 5002 | http://localhost:5002 |
| LocalStack | 4566 | http://localhost:4566 |

---

## 🔐 Default Credentials

**LocalStack AWS:**
- Access Key: `test`
- Secret Key: `test`
- Region: `us-east-1`
- Endpoint: `http://localhost:4566`

---

**Need help?** Check the logs with `./dev_tools/view-logs.sh`

