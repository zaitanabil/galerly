#!/bin/bash
# View logs from all services

echo "📊 Galerly Service Logs"
echo "======================="
echo ""
echo "Choose which logs to view:"
echo ""
echo "1) All Docker services (LocalStack, Backend, Frontend)"
echo "2) Backend only"
echo "3) Frontend only"
echo "4) LocalStack only"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Showing all Docker service logs (Ctrl+C to exit)..."
        docker-compose -f docker/docker-compose.localstack.yml logs -f
        ;;
    2)
        echo ""
        echo "Showing Backend logs (Ctrl+C to exit)..."
        docker-compose -f docker/docker-compose.localstack.yml logs -f backend
        ;;
    3)
        echo ""
        echo "Showing Frontend logs (Ctrl+C to exit)..."
        docker-compose -f docker/docker-compose.localstack.yml logs -f frontend
        ;;
    4)
        echo ""
        echo "Showing LocalStack logs (Ctrl+C to exit)..."
        docker logs -f galerly-localstack
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

