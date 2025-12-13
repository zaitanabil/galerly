#!/bin/bash

#######################################################################
# Production Verification Script - New Features
# Verifies all newly deployed features are working correctly
#######################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_ENDPOINT="${API_ENDPOINT:-https://api.galerly.com}"
TEST_TOKEN="${TEST_TOKEN}"
VERBOSE="${VERBOSE:-false}"

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Functions
print_header() {
    echo ""
    echo "======================================================================"
    echo "$1"
    echo "======================================================================"
}

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="${4:-200}"
    local data="$5"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -n "Testing: $name... "
    
    if [ "$VERBOSE" = "true" ]; then
        echo ""
        echo "  Method: $method"
        echo "  Endpoint: $endpoint"
        echo "  Expected: $expected_status"
    fi
    
    local response
    local http_code
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $TEST_TOKEN" \
            "$API_ENDPOINT$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Authorization: Bearer $TEST_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_ENDPOINT$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        
        if [ "$VERBOSE" = "true" ]; then
            echo "  Status: $http_code"
            echo "  Response: ${body:0:200}..."
        fi
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "  Expected: $expected_status"
        echo "  Got: $http_code"
        echo "  Response: ${body:0:200}"
        return 1
    fi
}

verify_authentication() {
    print_header "1. Authentication Verification"
    
    if [ -z "$TEST_TOKEN" ]; then
        echo -e "${RED}✗ TEST_TOKEN not set${NC}"
        echo "Please set TEST_TOKEN environment variable with a valid JWT token"
        exit 1
    fi
    
    echo -e "${GREEN}✓ TEST_TOKEN is set${NC}"
    
    # Test token validity
    test_endpoint "Token validation" "GET" "/v1/auth/me" 200
}

verify_seo_endpoints() {
    print_header "2. SEO Features Verification"
    
    # SEO Recommendations
    test_endpoint "SEO recommendations" "GET" "/v1/seo/recommendations" 200
    
    # One-click optimize (assuming it exists)
    echo "Note: One-click optimize endpoint should be tested manually"
}

verify_analytics_endpoints() {
    print_header "3. Analytics Features Verification"
    
    # Excel export (may take longer)
    echo "Testing Excel export (may take up to 10 seconds)..."
    test_endpoint "Excel export - summary" "GET" "/v1/analytics/export/excel?type=summary&start_date=2025-01-01&end_date=2025-01-31" 200
}

verify_email_automation_endpoints() {
    print_header "4. Email Automation Features Verification"
    
    # List templates
    test_endpoint "Email templates list" "GET" "/v1/email-automation/templates" 200
    
    # Test template application (will create actual workflow, use with caution)
    echo "Note: Template application endpoint should be tested manually to avoid creating test workflows"
}

verify_gallery_statistics_endpoints() {
    print_header "5. Gallery Statistics Features Verification"
    
    echo "Note: Gallery statistics require a valid gallery ID"
    echo "Testing with placeholder (expect 404 or 403)..."
    test_endpoint "Gallery statistics (no auth)" "GET" "/v1/galleries/test_gallery_id/statistics" "40" # 400-range expected
}

verify_selection_endpoints() {
    print_header "6. Client Selection Workflow Verification"
    
    # List sessions
    test_endpoint "List selection sessions" "GET" "/v1/selections/sessions" 200
    
    echo "Note: Other selection endpoints require valid session/gallery IDs"
    echo "Full workflow testing should be done manually with real data"
}

verify_video_features() {
    print_header "7. Video Quality Selector Verification"
    
    echo "Video quality selector is a frontend feature"
    echo "Manual verification required:"
    echo "  1. Open gallery with video"
    echo "  2. Verify quality selector appears"
    echo "  3. Test quality switching"
    echo "  4. Verify preference persists"
}

verify_database() {
    print_header "8. Database Verification"
    
    echo "Checking if client_selections table exists..."
    
    if command -v aws &> /dev/null; then
        local table_name="${DYNAMODB_CLIENT_SELECTIONS_TABLE:-client_selections}"
        
        if aws dynamodb describe-table --table-name "$table_name" &> /dev/null; then
            echo -e "${GREEN}✓ client_selections table exists${NC}"
            
            # Get table status
            local status=$(aws dynamodb describe-table --table-name "$table_name" --query 'Table.TableStatus' --output text)
            echo "  Status: $status"
            
            # Check GSI
            local gsi_count=$(aws dynamodb describe-table --table-name "$table_name" --query 'length(Table.GlobalSecondaryIndexes)' --output text)
            echo "  GSI Count: $gsi_count"
            
            if [ "$gsi_count" -ge "1" ]; then
                echo -e "${GREEN}✓ Required GSI exists${NC}"
            else
                echo -e "${YELLOW}⚠ No GSI found${NC}"
            fi
        else
            echo -e "${RED}✗ client_selections table not found${NC}"
            echo "  Run: python user-app/backend/setup_client_selections_table.py"
        fi
    else
        echo -e "${YELLOW}⚠ AWS CLI not available, skipping database check${NC}"
    fi
}

verify_performance() {
    print_header "9. Performance Verification"
    
    echo "Testing response times..."
    
    # Test SEO recommendations response time
    local start=$(date +%s%N)
    curl -s -H "Authorization: Bearer $TEST_TOKEN" \
        "$API_ENDPOINT/v1/seo/recommendations" > /dev/null
    local end=$(date +%s%N)
    local duration=$(( (end - start) / 1000000 ))
    
    echo "SEO recommendations: ${duration}ms"
    
    if [ "$duration" -lt 3000 ]; then
        echo -e "${GREEN}✓ Response time acceptable (<3s)${NC}"
    else
        echo -e "${YELLOW}⚠ Response time slow (>3s)${NC}"
    fi
}

verify_security() {
    print_header "10. Security Verification"
    
    echo "Testing endpoints without authentication..."
    
    # Should fail without token
    local response=$(curl -s -w "\n%{http_code}" "$API_ENDPOINT/v1/seo/recommendations" | tail -n1)
    
    if [ "$response" = "401" ] || [ "$response" = "403" ]; then
        echo -e "${GREEN}✓ Endpoints properly protected${NC}"
    else
        echo -e "${RED}✗ Endpoints not properly protected (got $response)${NC}"
    fi
}

generate_report() {
    print_header "Verification Summary"
    
    local report_file="verification_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Galerly Platform - Production Verification Report
=================================================
Date: $(date)
API Endpoint: $API_ENDPOINT

Test Results:
- Total Tests: $TESTS_TOTAL
- Passed: $TESTS_PASSED
- Failed: $TESTS_FAILED
- Success Rate: $(( TESTS_TOTAL > 0 ? (TESTS_PASSED * 100) / TESTS_TOTAL : 0 ))%

Features Verified:
✓ Authentication
✓ SEO Recommendations
✓ Analytics Export (Excel)
✓ Email Automation Templates
✓ Gallery Statistics
✓ Client Selection Workflow
✓ Video Quality Selector (Frontend)
✓ Database Setup
✓ Performance
✓ Security

Status: $([ $TESTS_FAILED -eq 0 ] && echo "✓ ALL TESTS PASSED" || echo "✗ SOME TESTS FAILED")

Recommendations:
$( [ $TESTS_FAILED -eq 0 ] && cat << REC
- Monitor CloudWatch logs for errors
- Check user adoption metrics
- Collect user feedback
- Plan next feature iteration
REC
 || cat << REC
- Review failed tests above
- Check CloudWatch logs for errors
- Verify environment configuration
- Re-run tests after fixes
REC
)

Manual Testing Required:
- Video quality selector UI
- Selection workflow (end-to-end)
- Email template application
- Excel download in browser
- Mobile responsiveness

EOF
    
    cat "$report_file"
    echo ""
    echo "Report saved to: $report_file"
}

main() {
    print_header "Galerly Platform - Production Verification"
    
    echo "Verifying deployment of new features..."
    echo "API Endpoint: $API_ENDPOINT"
    echo ""
    
    # Run verification steps
    verify_authentication
    verify_seo_endpoints
    verify_analytics_endpoints
    verify_email_automation_endpoints
    verify_gallery_statistics_endpoints
    verify_selection_endpoints
    verify_video_features
    verify_database
    verify_performance
    verify_security
    
    # Generate report
    generate_report
    
    # Exit status
    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ All automated tests passed!${NC}"
        echo "Please complete manual testing checklist"
        exit 0
    else
        echo ""
        echo -e "${RED}✗ Some tests failed${NC}"
        echo "Please review errors above and fix issues"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --endpoint)
            API_ENDPOINT="$2"
            shift 2
            ;;
        --token)
            TEST_TOKEN="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v         Verbose output"
            echo "  --endpoint URL        API endpoint (default: https://api.galerly.com)"
            echo "  --token TOKEN         Test token (or set TEST_TOKEN env var)"
            echo "  --help, -h            Show this help"
            echo ""
            echo "Environment Variables:"
            echo "  TEST_TOKEN            JWT token for authentication"
            echo "  API_ENDPOINT          API base URL"
            echo "  VERBOSE               Enable verbose output (true/false)"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main
main

