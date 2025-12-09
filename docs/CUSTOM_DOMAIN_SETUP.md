# Custom Domain Integration - Environment Variables

This document describes all environment variables required for the custom domain feature with CloudFront and ACM integration.

## Required Environment Variables

### AWS Configuration

```bash
# AWS Region (must be us-east-1 for ACM certificates used with CloudFront)
AWS_REGION=us-east-1

# AWS Credentials (if not using IAM roles)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### CloudFront Configuration

```bash
# Main CloudFront distribution domain (used as origin for custom domains)
CLOUDFRONT_DOMAIN=cdn.galerly.com

# CloudFront endpoint URL (for LocalStack development)
CLOUDFRONT_ENDPOINT_URL=http://localhost:4566
```

### ACM Configuration

```bash
# ACM endpoint URL (for LocalStack development)
ACM_ENDPOINT_URL=http://localhost:4566
```

### DNS Configuration

```bash
# CNAME target for DNS verification (legacy endpoint)
CNAME_TARGET=cdn.galerly.com
```

### DynamoDB Tables

```bash
# Custom domains configuration table
DYNAMODB_TABLE_CUSTOM_DOMAINS=galerly-custom-domains-prod

# For local development
DYNAMODB_TABLE_CUSTOM_DOMAINS=galerly-custom-domains-local
```

### Frontend URLs

```bash
# Frontend URL for generating links
FRONTEND_URL=https://galerly.com

# For local development
FRONTEND_URL=http://localhost:3000
```

## Production Configuration

For production deployment, add these to your AWS Systems Manager Parameter Store or Secrets Manager:

```bash
# Production example
AWS_REGION=us-east-1
CLOUDFRONT_DOMAIN=cdn.galerly.com
CNAME_TARGET=cdn.galerly.com
DYNAMODB_TABLE_CUSTOM_DOMAINS=galerly-custom-domains-prod
FRONTEND_URL=https://galerly.com
```

## Development Configuration

For local development with LocalStack:

```bash
# Development example (.env.local)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
CLOUDFRONT_ENDPOINT_URL=http://localhost:4566
ACM_ENDPOINT_URL=http://localhost:4566
CLOUDFRONT_DOMAIN=d123abc.cloudfront.net
CNAME_TARGET=localhost
DYNAMODB_TABLE_CUSTOM_DOMAINS=galerly-custom-domains-local
FRONTEND_URL=http://localhost:3000
```

## IAM Permissions Required

The Lambda execution role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:GetDistributionConfig",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "acm:RequestCertificate",
        "acm:DescribeCertificate",
        "acm:ListCertificates",
        "acm:DeleteCertificate",
        "acm:AddTagsToCertificate"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/galerly-custom-domains-*",
        "arn:aws:dynamodb:*:*:table/galerly-users-*"
      ]
    }
  ]
}
```

## DynamoDB Table Schema

Create the custom domains table with this schema:

```python
# Table: galerly-custom-domains-prod
{
  "TableName": "galerly-custom-domains-prod",
  "KeySchema": [
    {
      "AttributeName": "user_id",
      "KeyType": "HASH"
    },
    {
      "AttributeName": "domain",
      "KeyType": "RANGE"
    }
  ],
  "AttributeDefinitions": [
    {
      "AttributeName": "user_id",
      "AttributeType": "S"
    },
    {
      "AttributeName": "domain",
      "AttributeType": "S"
    }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

## API Endpoints

The custom domain feature exposes these endpoints:

### Setup Custom Domain
```
POST /v1/portfolio/custom-domain/setup
Authorization: Bearer <token>

Request Body:
{
  "domain": "gallery.yourstudio.com",
  "auto_provision": true
}

Response:
{
  "success": true,
  "domain": "gallery.yourstudio.com",
  "certificate_arn": "arn:aws:acm:us-east-1:...",
  "distribution_id": "E123ABC456DEF",
  "distribution_domain": "d123abc456def.cloudfront.net",
  "validation_records": [
    {
      "name": "_abc123.gallery.yourstudio.com",
      "type": "CNAME",
      "value": "_xyz789.acm-validations.aws"
    }
  ],
  "status": "pending_validation",
  "next_steps": [...]
}
```

### Check Domain Status
```
GET /v1/portfolio/custom-domain/status?domain=gallery.yourstudio.com
Authorization: Bearer <token>

Response:
{
  "domain": "gallery.yourstudio.com",
  "overall_status": "pending|active|not_configured",
  "ready": false,
  "certificate": {
    "arn": "arn:aws:acm:...",
    "status": "PENDING_VALIDATION|ISSUED",
    "issued": false,
    "validation_records": [...]
  },
  "distribution": {
    "id": "E123ABC456DEF",
    "domain": "d123abc456def.cloudfront.net",
    "status": "InProgress|Deployed",
    "deployed": false
  },
  "dns_propagation": {
    "propagated": false,
    "percentage": 45.5,
    "ready": false,
    "servers_propagated": 3,
    "servers_checked": 7
  }
}
```

### Refresh Certificate Status
```
POST /v1/portfolio/custom-domain/refresh
Authorization: Bearer <token>

Request Body:
{
  "domain": "gallery.yourstudio.com"
}

Response:
{
  "success": true,
  "domain": "gallery.yourstudio.com",
  "status": "active|pending_validation",
  "certificate_status": "ISSUED|PENDING_VALIDATION",
  "message": "Domain is now active with SSL certificate!"
}
```

## Troubleshooting

### Certificate Stuck in PENDING_VALIDATION
- Verify DNS records are added correctly
- Wait 10-30 minutes for DNS propagation
- Check with DNS propagation checker
- Try refreshing certificate status

### CloudFront Distribution Not Deploying
- Check IAM permissions
- Verify certificate is in us-east-1 region
- Check CloudWatch logs for errors
- Distribution deployment can take 15-30 minutes

### DNS Not Propagating
- Some DNS servers update faster than others
- Full global propagation can take 24-48 hours
- 80%+ propagation is usually sufficient
- Use the DNS propagation checker endpoint

## Monitoring

Monitor these CloudWatch metrics:

```
- CloudFront: Requests, ErrorRate, 4xxErrorRate, 5xxErrorRate
- ACM: DaysToExpiry (set alarm for < 30 days)
- Lambda: Duration, Errors, Throttles
```

## Cost Estimates

Approximate monthly costs per custom domain:

```
- CloudFront Distribution: $0 (free tier) + $0.085/GB data transfer
- ACM Certificate: $0 (free with CloudFront)
- Route 53 Hosted Zone: Not required (users use their own DNS)
- DynamoDB: ~$0.01/month (on-demand pricing)

Total: ~$0.01-$5/month depending on traffic
```

## Security Considerations

1. **SSL/TLS**: Automatic with ACM, using TLS 1.2+
2. **Certificate Renewal**: ACM auto-renews DNS-validated certificates
3. **Domain Ownership**: Verified via DNS CNAME records
4. **Access Control**: Plan-based (Plus, Pro, Ultimate only)
5. **Rate Limiting**: Implement on setup endpoint to prevent abuse

## Limitations

1. **Subdomains Only**: Root domains (example.com) not supported, only subdomains (gallery.example.com)
2. **Region Restriction**: ACM certificates must be in us-east-1 for CloudFront
3. **Validation Method**: DNS validation only (email validation not supported)
4. **Deployment Time**: Initial setup takes 30-45 minutes
5. **DNS Propagation**: Can take up to 48 hours globally

## Support

For issues with custom domain setup:
1. Check CloudWatch logs in Lambda function
2. Verify all environment variables are set
3. Check IAM permissions
4. Review DynamoDB table access
5. Contact AWS support for CloudFront/ACM issues
