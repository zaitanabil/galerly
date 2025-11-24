#!/bin/bash

# Galerly Automated Test Runner
# Runs all tests in Docker with detailed reporting

set -e

echo "================================================"
echo "    GALERLY AUTOMATED TEST SUITE               "
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create test results directory
mkdir -p test-results

echo -e "${BLUE}📦 Building test containers...${NC}"
docker-compose -f docker/docker-compose.test.yml build --quiet

echo ""
echo "================================================"
echo "       BACKEND TESTS (500+ tests)              "
echo "================================================"
echo ""

if docker-compose -f docker/docker-compose.test.yml run --rm backend-tests; then
    echo -e "${GREEN}✅ Backend tests: PASSED${NC}"
    BACKEND_STATUS=0
else
    echo -e "${RED}❌ Backend tests: FAILED${NC}"
    BACKEND_STATUS=1
fi

echo ""
echo "================================================"
echo "       INTEGRATION TESTS (20 workflows)        "
echo "================================================"
echo ""

if docker-compose -f docker/docker-compose.test.yml run --rm integration-tests; then
    echo -e "${GREEN}✅ Integration tests: PASSED${NC}"
    INTEGRATION_STATUS=0
else
    echo -e "${RED}❌ Integration tests: FAILED${NC}"
    INTEGRATION_STATUS=1
fi

echo ""
echo "================================================"
echo "       TEST RESULTS SUMMARY                     "
echo "================================================"
echo ""

# Count test files
BACKEND_TEST_FILES=$(find backend/tests -name "test_*.py" | wc -l | tr -d ' ')
echo "📊 Test files executed: ${BACKEND_TEST_FILES}"
echo ""

if [ $BACKEND_STATUS -eq 0 ] && [ $INTEGRATION_STATUS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ ALL TESTS PASSED (500+ tests)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📈 Coverage report:${NC} file://$(pwd)/backend/htmlcov/index.html"
    echo -e "${BLUE}📄 Test results:${NC} $(pwd)/test-results/"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Backend:     $([ $BACKEND_STATUS -eq 0 ] && echo -e '${GREEN}PASSED${NC}' || echo -e '${RED}FAILED${NC}')"
    echo "Integration: $([ $INTEGRATION_STATUS -eq 0 ] && echo -e '${GREEN}PASSED${NC}' || echo -e '${RED}FAILED${NC}')"
    echo ""
    exit 1
fi
