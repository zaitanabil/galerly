#!/bin/bash
# Check status of all services

echo "🔍 Galerly Services Status"
echo "=========================="
echo ""

# Check Docker containers
echo "DOCKER CONTAINERS:"
echo "------------------"
if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep galerly; then
    echo ""
else
    echo "❌ No Docker containers running"
    echo ""
fi

# Check LocalStack
echo "LOCALSTACK:"
echo "-----------"
if curl -s "http://localhost:4566/_localstack/health" > /dev/null 2>&1; then
    echo "✅ LocalStack is running (http://localhost:4566)"
else
    echo "❌ LocalStack is not running"
fi
echo ""

# Check User App Backend
echo "USER APP BACKEND:"
echo "-----------------"
if curl -s "http://localhost:5001/health" > /dev/null 2>&1; then
    echo "✅ Backend is running (http://localhost:5001)"
else
    echo "❌ Backend is not running"
fi
echo ""

# Check User App Frontend
echo "USER APP FRONTEND:"
echo "------------------"
if curl -s "http://localhost:5173" > /dev/null 2>&1; then
    echo "✅ Frontend is running (http://localhost:5173)"
else
    echo "❌ Frontend is not running"
fi
echo ""

# Summary
echo "QUICK LINKS:"
echo "------------"
echo "Frontend:    http://localhost:5173"
echo "Backend API: http://localhost:5001"
echo "LocalStack:  http://localhost:4566"
echo ""

