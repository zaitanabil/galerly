#!/bin/bash

# CloudWatch Log Groups Cleanup
# Deletes old log groups to reduce costs

echo "🔍 Analyzing CloudWatch Log Groups..."
echo ""

# List all log groups with size
aws logs describe-log-groups --query 'logGroups[*].[logGroupName,storedBytes]' --output table

echo ""
echo "💡 RECOMMENDATIONS:"
echo "   • Keep: /aws/lambda/galerly-api (needed for debugging)"
echo "   • Delete: Old/unused log groups"
echo "   • Set retention: 7 days for Lambda logs"
echo ""
echo "🗑️  To delete a log group:"
echo "   aws logs delete-log-group --log-group-name <NAME>"
echo ""
echo "⏰ To set retention (auto-delete after 7 days):"
echo "   aws logs put-retention-policy --log-group-name /aws/lambda/galerly-api --retention-in-days 7"
