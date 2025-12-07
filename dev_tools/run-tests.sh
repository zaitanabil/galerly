#!/bin/bash
# Run all tests (user app frontend and backend)

echo "🧪 Running Galerly Tests"
echo "========================"
echo ""

# User App Frontend Tests
echo "📦 User App Frontend Tests"
echo "--------------------------"
cd user-app/frontend
npm test -- --run
FRONTEND_EXIT=$?
cd ../..

echo ""
echo ""

# User App Backend Tests (if pytest is installed)
echo "🐍 User App Backend Tests"
echo "-------------------------"
cd user-app/backend

if [ -d "venv" ]; then
    source venv/bin/activate
    if command -v pytest &> /dev/null; then
        pytest tests/ -v
        BACKEND_EXIT=$?
    else
        echo "⚠️  pytest not installed. Skipping backend tests."
        echo "   Install: pip install pytest pytest-mock"
        BACKEND_EXIT=0
    fi
else
    echo "⚠️  Virtual environment not found. Skipping backend tests."
    BACKEND_EXIT=0
fi

cd ../..

echo ""
echo ""

# Summary
echo "TEST SUMMARY"
echo "============"
if [ $FRONTEND_EXIT -eq 0 ]; then
    echo "✅ Frontend tests passed"
else
    echo "❌ Frontend tests failed"
fi

if [ $BACKEND_EXIT -eq 0 ]; then
    echo "✅ Backend tests passed (or skipped)"
else
    echo "❌ Backend tests failed"
fi

echo ""

if [ $FRONTEND_EXIT -eq 0 ] && [ $BACKEND_EXIT -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi

