#!/bin/bash
# Validate that all required environment variables are set in GitHub Actions
# Used in CI/CD pipeline to prevent deployment with missing configuration

set -e

MISSING=()
ERRORS=()

# Secrets
REQUIRED_SECRETS=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "JWT_SECRET"
    "SMTP_PASSWORD"
    "STRIPE_SECRET_KEY"
    "STRIPE_WEBHOOK_SECRET"
    "STRIPE_PUBLISHABLE_KEY"
)

# Variables (sample of critical ones)
REQUIRED_VARS=(
    "AWS_REGION"
    "ENVIRONMENT"
    "FRONTEND_URL"
    "API_BASE_URL"
    "S3_BUCKET"
    "S3_PHOTOS_BUCKET"
    "S3_RENDITIONS_BUCKET"
    "DYNAMODB_TABLE_USERS"
    "DYNAMODB_TABLE_GALLERIES"
    "DYNAMODB_TABLE_PHOTOS"
    "LAMBDA_FUNCTION_NAME"
    "CLOUDFRONT_DISTRIBUTION_ID"
)

# Check secrets
for secret in "${REQUIRED_SECRETS[@]}"; do
    if [ -z "${!secret}" ]; then
        MISSING+=("$secret")
    fi
done

# Check variables
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING+=("$var")
    fi
done

# Production-specific validation
if [ "$ENVIRONMENT" = "production" ]; then
    # Check Stripe is not in test mode
    if [[ "$STRIPE_SECRET_KEY" == sk_test_* ]]; then
        ERRORS+=("STRIPE_SECRET_KEY is in test mode (production requires live key)")
    fi
    
    # Check HTTPS is used
    if [[ "$FRONTEND_URL" != https://* ]]; then
        ERRORS+=("FRONTEND_URL must use HTTPS in production")
    fi
fi

# Report results
if [ ${#MISSING[@]} -gt 0 ]; then
    exit 1
fi

if [ ${#ERRORS[@]} -gt 0 ]; then
    exit 1
fi

exit 0
