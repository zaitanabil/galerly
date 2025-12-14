#!/bin/bash
# Verify GitHub Actions environment configuration

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)

if [ -z "$REPO" ]; then
    REPO="zaitanabil/galerly"
fi

echo "Repository: $REPO"
echo ""

SECRET_COUNT=$(gh secret list --repo "$REPO" | wc -l | xargs)
VAR_COUNT=$(gh variable list --repo "$REPO" | wc -l | xargs)

echo "Secrets: $SECRET_COUNT"
echo "Variables: $VAR_COUNT"
echo "Total: $((SECRET_COUNT + VAR_COUNT))"
echo ""

echo "Secrets configured:"
gh secret list --repo "$REPO" | awk '{print "  - " $1}'
echo ""

echo "Sample variables (first 20):"
gh variable list --repo "$REPO" | head -20 | awk '{print "  - " $1 " = " $2}'
echo ""

if [ "$SECRET_COUNT" -eq 7 ] || [ "$SECRET_COUNT" -eq 8 ]; then
    if [ "$VAR_COUNT" -ge 118 ]; then
        echo "✓ All environment variables configured"
        exit 0
    fi
fi

echo "⚠ Configuration incomplete"
exit 1
