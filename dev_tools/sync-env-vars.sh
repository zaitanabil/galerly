#!/bin/bash
# Sync environment variables from .env.production to GitHub and AWS Lambda
# This ensures all variables are always up-to-date

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=== Environment Variables Sync ==="
echo ""

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env.production not found${NC}"
    exit 1
fi

# Read AWS region from env or use default
AWS_REGION="${AWS_REGION:-eu-central-1}"
LAMBDA_FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-galerly-api}"

echo "Reading variables from: $ENV_FILE"
echo "AWS Region: $AWS_REGION"
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo ""

# Arrays to store variables and secrets
declare -A VARIABLES
declare -A SECRETS

# Secret keys (sensitive data)
SECRET_KEYS=(
    "JWT_SECRET"
    "STRIPE_SECRET_KEY"
    "STRIPE_WEBHOOK_SECRET"
    "STRIPE_PUBLISHABLE_KEY"
    "SMTP_PASSWORD"
)

# Read .env.production and categorize
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove quotes from value
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    
    # Check if it's a secret
    is_secret=false
    for secret_key in "${SECRET_KEYS[@]}"; do
        if [[ "$key" == "$secret_key" ]]; then
            is_secret=true
            break
        fi
    done
    
    if [ "$is_secret" = true ]; then
        SECRETS["$key"]="$value"
    else
        VARIABLES["$key"]="$value"
    fi
done < "$ENV_FILE"

echo -e "${YELLOW}Found ${#VARIABLES[@]} variables and ${#SECRETS[@]} secrets${NC}"
echo ""

# Update GitHub Variables
if command -v gh &> /dev/null; then
    echo -e "${GREEN}Updating GitHub Variables...${NC}"
    for key in "${!VARIABLES[@]}"; do
        echo "  - $key"
        gh variable set "$key" --body "${VARIABLES[$key]}" 2>/dev/null || echo "    (failed, may need repo permissions)"
    done
    echo ""
    
    echo -e "${GREEN}Updating GitHub Secrets...${NC}"
    for key in "${!SECRETS[@]}"; do
        echo "  - $key"
        gh secret set "$key" --body "${SECRETS[$key]}" 2>/dev/null || echo "    (failed, may need repo permissions)"
    done
    echo ""
else
    echo -e "${YELLOW}gh CLI not found, skipping GitHub sync${NC}"
    echo ""
fi

# Update AWS Lambda Environment Variables
if command -v aws &> /dev/null; then
    echo -e "${GREEN}Building Lambda environment JSON...${NC}"
    
    # Lambda-relevant prefixes (exclude frontend VITE_*, LIFECYCLE_*, CDN_*, etc.)
    LAMBDA_PREFIXES=("DYNAMODB_TABLE_" "S3_" "STRIPE_" "SMTP_" "JWT_" "FROM_" "API_" "FRONTEND_URL" "ENVIRONMENT" "DEBUG" "AWS_REGION" "DEFAULT_INVOICE" "DEFAULT_ITEM" "PRESIGNED_URL_EXPIRY")
    
    # Start JSON
    json='{"Variables":{'
    first=true
    
    # Add filtered variables (excluding AWS_REGION which is reserved)
    for key in "${!VARIABLES[@]}"; do
        # Skip AWS reserved variables
        if [ "$key" = "AWS_REGION" ] || [ "$key" = "AWS_ACCESS_KEY_ID" ] || [ "$key" = "AWS_SECRET_ACCESS_KEY" ]; then
            continue
        fi
        
        # Check if key matches Lambda-relevant prefixes
        include=false
        for prefix in "${LAMBDA_PREFIXES[@]}"; do
            if [[ "$key" == "$prefix"* ]] || [[ "$key" == "$prefix" ]]; then
                include=true
                break
            fi
        done
        
        if [ "$include" = true ]; then
            if [ "$first" = true ]; then
                first=false
            else
                json+=','
            fi
            # Escape quotes in value
            escaped_value="${VARIABLES[$key]//\"/\\\"}"
            json+="\"$key\":\"$escaped_value\""
        fi
    done
    
    # Add secrets
    for key in "${!SECRETS[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            json+=','
        fi
        # Escape quotes in value
        escaped_value="${SECRETS[$key]//\"/\\\"}"
        json+="\"$key\":\"$escaped_value\""
    done
    
    json+='}}'
    
    # Save to temp file
    TMP_JSON="/tmp/lambda-env-$$.json"
    echo "$json" > "$TMP_JSON"
    
    echo "Updating Lambda function: $LAMBDA_FUNCTION_NAME"
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_FUNCTION_NAME" \
        --region "$AWS_REGION" \
        --environment "file://$TMP_JSON" \
        --query 'FunctionName' \
        --output text 2>&1 && echo -e "${GREEN}✅ Lambda updated${NC}" || echo -e "${RED}Failed to update Lambda${NC}"
    
    # Cleanup
    rm -f "$TMP_JSON"
    echo ""
else
    echo -e "${YELLOW}AWS CLI not found, skipping Lambda sync${NC}"
    echo ""
fi

echo -e "${GREEN}=== Sync Complete ===${NC}"
echo ""
echo "Summary:"
echo "  Variables synced: ${#VARIABLES[@]}"
echo "  Secrets synced: ${#SECRETS[@]}"
echo ""
