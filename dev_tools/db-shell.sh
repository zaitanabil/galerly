#!/bin/bash
# Database shell - Interactive DynamoDB and S3 explorer

echo "🗄️  Galerly Database Shell"
echo "========================="
echo ""

export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"

echo "Choose an operation:"
echo ""
echo "1) List all DynamoDB tables"
echo "2) Scan a DynamoDB table"
echo "3) List all S3 buckets"
echo "4) List objects in S3 bucket"
echo "5) Count items in all tables"
echo "6) Interactive AWS CLI"
echo ""
read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "DynamoDB Tables:"
        echo "----------------"
        aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb list-tables | jq -r '.TableNames[]'
        ;;
    2)
        echo ""
        echo "Available tables:"
        aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb list-tables | jq -r '.TableNames[]'
        echo ""
        read -p "Enter table name: " table_name
        echo ""
        echo "Scanning $table_name..."
        aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb scan --table-name "$table_name" | jq '.Items | length' | xargs echo "Items found:"
        aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb scan --table-name "$table_name" | jq '.Items[] | keys'
        ;;
    3)
        echo ""
        echo "S3 Buckets:"
        echo "-----------"
        aws --endpoint-url=$AWS_ENDPOINT_URL s3 ls
        ;;
    4)
        echo ""
        echo "Available buckets:"
        aws --endpoint-url=$AWS_ENDPOINT_URL s3 ls
        echo ""
        read -p "Enter bucket name: " bucket_name
        echo ""
        echo "Objects in $bucket_name:"
        aws --endpoint-url=$AWS_ENDPOINT_URL s3 ls s3://$bucket_name --recursive
        ;;
    5)
        echo ""
        echo "Counting items in all tables..."
        echo "-------------------------------"
        for table in $(aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb list-tables | jq -r '.TableNames[]'); do
            count=$(aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb scan --table-name "$table" --select COUNT | jq '.Count')
            echo "$table: $count items"
        done
        ;;
    6)
        echo ""
        echo "Interactive AWS CLI (type 'exit' to quit)"
        echo "Example: dynamodb list-tables"
        echo ""
        while true; do
            read -p "aws > " cmd
            if [ "$cmd" = "exit" ]; then
                break
            fi
            aws --endpoint-url=$AWS_ENDPOINT_URL $cmd
        done
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""

