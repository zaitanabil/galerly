#!/bin/bash
# View logs from all services

echo "📊 Galerly Service Logs"
echo "======================="
echo ""
echo "Choose which logs to view:"
echo ""
echo "1) All Docker services (LocalStack, Backend, Frontend)"
echo "2) User App Backend only"
echo "3) User App Frontend only"
echo "4) Admin App Backend only"
echo "5) Admin App Frontend only"
echo "6) LocalStack only"
echo ""
read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "Showing all Docker service logs (Ctrl+C to exit)..."
        docker-compose -f docker/docker-compose.localstack.yml logs -f
        ;;
    2)
        echo ""
        echo "Showing User App Backend logs (Ctrl+C to exit)..."
        docker-compose -f docker/docker-compose.localstack.yml logs -f backend
        ;;
    3)
        echo ""
        echo "Showing User App Frontend logs (Ctrl+C to exit)..."
        docker-compose -f docker/docker-compose.localstack.yml logs -f frontend
        ;;
    4)
        echo ""
        echo "Showing Admin App Backend logs (Ctrl+C to exit)..."
        tail -f logs/admin-backend.log
        ;;
    5)
        echo ""
        echo "Showing Admin App Frontend logs (Ctrl+C to exit)..."
        tail -f logs/admin-frontend.log
        ;;
    6)
        echo ""
        echo "Showing LocalStack logs (Ctrl+C to exit)..."
        docker logs -f galerly-localstack
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

