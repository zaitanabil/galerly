# Backend Setup

## Prerequisites
- Python 3.11+
- AWS CLI configured
- boto3 installed

## Initial Setup

```bash
cd backend

# 1. Create tables
python setup_dynamodb.py create

# 2. Import cities
python import_cities_to_dynamodb.py

# 3. Configure AWS
python setup_aws.py all

# 4. Verify
python setup_dynamodb.py list
python manage_indexes.py
```

## Commands

### DynamoDB Management
```bash
python setup_dynamodb.py create    # Create all 5 tables
python setup_dynamodb.py optimize  # Enable PITR, encryption
python setup_dynamodb.py list      # Show table status
python setup_dynamodb.py delete    # ⚠️ Delete all tables
```

### AWS Configuration
```bash
python setup_aws.py api-cors    # Enable API Gateway CORS
python setup_aws.py s3-cors     # Enable S3 CORS
python setup_aws.py all         # Configure all
python setup_aws.py verify      # Verify configs
```

### Index Management
```bash
python manage_indexes.py           # Check indexes
python manage_indexes.py --create  # Create missing indexes
```

## Tables Created

1. **galerly-users** - User accounts
2. **galerly-galleries** - Photo galleries (isolated per user)
3. **galerly-photos** - Photos (linked to galleries)
4. **galerly-sessions** - Auth sessions (24h TTL)
5. **galerly-newsletters** - Newsletter subscribers
6. **galerly-contact** - Support tickets
7. **galerly-cities** - City autocomplete data

## Configuration

Edit in scripts:
- `REGION` - AWS region (default: us-east-1)
- `API_GATEWAY_ID` - API Gateway ID
- `S3_BUCKET_NAME` - S3 bucket name

## Migration from Shell Scripts

Old shell scripts removed:
- ~~create-dynamodb-tables.sh~~ → `setup_dynamodb.py create`
- ~~optimize_dynamodb.sh~~ → `setup_dynamodb.py optimize`
- ~~enable-cors.sh~~ → `setup_aws.py api-cors`
- ~~configure-s3-cors.sh~~ → `setup_aws.py s3-cors`

## Troubleshooting

**Permission denied:**
```bash
chmod +x setup_dynamodb.py setup_aws.py
```

**AWS credentials:**
```bash
aws configure
```

**Table already exists:**
Normal - scripts skip existing resources.

**CORS not working:**
Wait 30-60s for API Gateway deployment propagation.

