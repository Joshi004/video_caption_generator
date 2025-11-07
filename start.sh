#!/bin/bash

# Video Caption Service - Startup Script
# Starts Docker services (requires SSH tunnels to be established separately)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Video Caption Service - Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment variables
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating .env from .env.example..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo "Please review and update .env with your settings."
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        echo "Please create .env file manually with required settings."
        exit 1
    fi
fi

# Load variables
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)

# Use defaults if not set
QWEN2VL_PORT=${QWEN2VL_PORT:-8000}
OMNIVINCI_PORT=${OMNIVINCI_PORT:-8001}
BACKEND_PORT=${BACKEND_PORT:-8011}
FRONTEND_PORT=${FRONTEND_PORT:-3001}

echo "Configuration:"
echo "  Qwen2-VL API Port: $QWEN2VL_PORT (via SSH tunnel)"
echo "  OmniVinci API Port: $OMNIVINCI_PORT (via SSH tunnel)"
echo "  Backend API Port: $BACKEND_PORT (local Docker)"
echo "  Frontend Port: $FRONTEND_PORT (local Docker)"
echo ""

# Check if SSH tunnels are established
echo "Checking SSH tunnels to remote AI models..."

# Check Qwen2-VL tunnel
if curl -s --max-time 5 http://localhost:$QWEN2VL_PORT/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qwen2-VL API tunnel is active (port $QWEN2VL_PORT)${NC}"
else
    echo -e "${YELLOW}⚠ Qwen2-VL API tunnel not detected (port $QWEN2VL_PORT)${NC}"
    echo -e "${YELLOW}  Caption generation with Qwen2-VL will not work${NC}"
fi

# Check OmniVinci tunnel
if curl -s --max-time 5 http://localhost:$OMNIVINCI_PORT/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OmniVinci API tunnel is active (port $OMNIVINCI_PORT)${NC}"
else
    echo -e "${YELLOW}⚠ OmniVinci API tunnel not detected (port $OMNIVINCI_PORT)${NC}"
    echo -e "${YELLOW}  Caption generation with OmniVinci will not work${NC}"
fi

# Check Qwen3-Omni tunnel/service
QWEN3OMNI_PORT=${QWEN3OMNI_PORT:-8002}
if curl -s --max-time 5 http://localhost:$QWEN3OMNI_PORT/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qwen3-Omni API is active (port $QWEN3OMNI_PORT)${NC}"
else
    echo -e "${YELLOW}⚠ Qwen3-Omni API not detected (port $QWEN3OMNI_PORT)${NC}"
    echo -e "${YELLOW}  Caption generation with Qwen3-Omni will not work${NC}"
fi

echo ""
echo -e "${BLUE}Tip:${NC} To establish tunnels, run in a separate terminal:"
echo -e "${BLUE}  ./scripts/start-tunnels.sh${NC}"
echo ""

echo ""
echo "Starting Docker services..."
echo ""

# Make sure docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not found${NC}"
        echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    # Try using docker compose (new syntax)
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Stop existing containers if any
echo "Stopping any existing containers..."
$DOCKER_COMPOSE down > /dev/null 2>&1 || true

# Start Docker services
echo "Building and starting containers..."
echo -e "${YELLOW}Note:${NC} Using cached layers. For complete rebuild, use: ./hard-restart.sh"
$DOCKER_COMPOSE up --build -d

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start Docker services${NC}"
    exit 1
fi

echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check backend health
echo "Checking backend service..."
BACKEND_READY=false
for i in {1..10}; do
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        BACKEND_READY=true
        echo -e "${GREEN}✓ Backend service is ready${NC}"
        break
    fi
    sleep 2
done

if [ "$BACKEND_READY" = false ]; then
    echo -e "${YELLOW}⚠ Backend service not responding${NC}"
    echo "Check logs: docker-compose logs backend"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access the application:"
echo ""
echo -e "  ${BLUE}Frontend:${NC} http://localhost:$FRONTEND_PORT"
echo -e "  ${BLUE}Backend API:${NC} http://localhost:$BACKEND_PORT/docs"
echo -e "  ${BLUE}Qwen2-VL API:${NC} http://localhost:$QWEN2VL_PORT/docs (tunneled)"
echo -e "  ${BLUE}OmniVinci API:${NC} http://localhost:$OMNIVINCI_PORT/docs (tunneled)"
echo ""
echo "Video files:"
echo "  - Local (for playback): ./backend/videos/"
echo "  - Remote (for AI processing): ~/datasets/videos/ on server"
echo ""
echo "Captions location: ./backend/captions/ (synced from remote)"
echo ""
echo "To sync captions from remote:"
echo "  ./scripts/sync-captions.sh"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop all services:"
echo "  ./stop.sh"
echo ""
echo -e "${GREEN}========================================${NC}"


