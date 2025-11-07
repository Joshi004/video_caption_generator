#!/bin/bash

# Video Caption Service - Stop Script
# Stops Docker services

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
echo -e "${BLUE}Video Caption Service - Shutdown${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Determine docker-compose command
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Stop Docker services
echo "Stopping Docker services..."
$DOCKER_COMPOSE down

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker services stopped${NC}"
else
    echo -e "${YELLOW}⚠ Error stopping Docker services${NC}"
fi

echo ""
echo -e "${YELLOW}Note:${NC} SSH tunnels to remote server are still active."
echo "To close SSH tunnels, manually kill the ssh process or close the terminal."
echo ""
echo "Remote services (vLLM, video server) remain running on the cluster."
echo "These should be managed directly on the remote server."
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Shutdown Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""


