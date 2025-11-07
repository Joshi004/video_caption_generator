#!/bin/bash

# SSH Tunnel Manager for Video Caption Service
# Establishes tunnels to remote vLLM and video server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Configuration
REMOTE_HOST=${REMOTE_HOST:-naresh@85.234.64.44}
QWEN2VL_PORT=${QWEN2VL_PORT:-8000}
OMNIVINCI_PORT=${OMNIVINCI_PORT:-8001}
QWEN3OMNI_PORT=${QWEN3OMNI_PORT:-8002}
VIDEO_PORT=${VIDEO_PORT:-8080}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SSH Tunnel Manager - Multi-Model Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Remote host: $REMOTE_HOST"
echo "Tunnels:"
echo "  - Port $QWEN2VL_PORT → Qwen2-VL-7B API (worker-9:8000)"
echo "  - Port $OMNIVINCI_PORT → OmniVinci API (worker-9:8001)"
echo "  - Port $QWEN3OMNI_PORT → Qwen3-Omni-30B API (worker-9:8002)"
echo "  - Port $VIDEO_PORT → Video HTTP Server (worker-9:8080)"
echo ""
echo "Local services:"
echo "  - Backend API: Port 8011 (Docker)"
echo "  - Frontend: Port 3001 (Docker)"
echo ""

# Check if autossh is available
if command -v autossh &> /dev/null; then
    USE_AUTOSSH=true
    echo -e "${GREEN}✓ autossh detected - will use for persistent tunnels${NC}"
else
    USE_AUTOSSH=false
    echo -e "${YELLOW}⚠ autossh not found - using regular ssh${NC}"
    echo "  Install autossh for automatic reconnection:"
    echo "  brew install autossh (macOS)"
fi

echo ""

# Check if tunnels are already running
TUNNEL_RUNNING=false

if lsof -ti:$QWEN2VL_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port $QWEN2VL_PORT is already in use${NC}"
    TUNNEL_RUNNING=true
fi

if lsof -ti:$OMNIVINCI_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port $OMNIVINCI_PORT is already in use${NC}"
    TUNNEL_RUNNING=true
fi

if lsof -ti:$QWEN3OMNI_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port $QWEN3OMNI_PORT is already in use${NC}"
    TUNNEL_RUNNING=true
fi

if lsof -ti:$VIDEO_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port $VIDEO_PORT is already in use${NC}"
    TUNNEL_RUNNING=true
fi

if [ "$TUNNEL_RUNNING" = true ]; then
    echo ""
    read -p "Ports are in use. Kill existing processes and restart? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing processes on ports $QWEN2VL_PORT, $OMNIVINCI_PORT, $QWEN3OMNI_PORT, and $VIDEO_PORT..."
        lsof -ti:$QWEN2VL_PORT | xargs kill -9 2>/dev/null || true
        lsof -ti:$OMNIVINCI_PORT | xargs kill -9 2>/dev/null || true
        lsof -ti:$QWEN3OMNI_PORT | xargs kill -9 2>/dev/null || true
        lsof -ti:$VIDEO_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "Keeping existing tunnels. Exiting."
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Establishing SSH tunnels...${NC}"
echo ""

if [ "$USE_AUTOSSH" = true ]; then
    # Use autossh for persistent tunnels
    echo "Starting autossh (persistent tunnel with auto-reconnect)..."
    echo ""
    echo "Command:"
    echo "autossh -M 0 -fN -o ExitOnForwardFailure=yes \\"
    echo "  -L $QWEN2VL_PORT:worker-9:8000 \\"
    echo "  -L $OMNIVINCI_PORT:worker-9:8001 \\"
    echo "  -L $VIDEO_PORT:worker-9:8080 \\"
    echo "  $REMOTE_HOST"
    echo ""
    
    autossh -M 0 -fN -o ExitOnForwardFailure=yes \
        -L $QWEN2VL_PORT:worker-9:8000 \
        -L $OMNIVINCI_PORT:worker-9:8001 \
        -L $QWEN3OMNI_PORT:worker-9:8002 \
        -L $VIDEO_PORT:worker-9:8080 \
        $REMOTE_HOST
    
    echo -e "${YELLOW}Note: OmniVinci tunneled to localhost:$OMNIVINCI_PORT (avoiding conflict with backend on 8001)${NC}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Tunnels established (background daemon)${NC}"
    else
        echo -e "${RED}✗ Failed to establish tunnels${NC}"
        exit 1
    fi
else
    # Use regular ssh (manual mode)
    echo "Starting ssh tunnels in background..."
    echo ""
    echo "Command:"
    echo "ssh -fN -o ExitOnForwardFailure=yes \\"
    echo "  -L $QWEN2VL_PORT:worker-9:8000 \\"
    echo "  -L $OMNIVINCI_PORT:worker-9:8001 \\"
    echo "  -L $VIDEO_PORT:worker-9:8080 \\"
    echo "  $REMOTE_HOST"
    echo ""
    
    ssh -fN -o ExitOnForwardFailure=yes \
        -L $QWEN2VL_PORT:worker-9:8000 \
        -L $OMNIVINCI_PORT:worker-9:8001 \
        -L $QWEN3OMNI_PORT:worker-9:8002 \
        -L $VIDEO_PORT:worker-9:8080 \
        $REMOTE_HOST
    
    echo -e "${YELLOW}Note: OmniVinci tunneled to localhost:$OMNIVINCI_PORT (avoiding conflict with backend on 8001)${NC}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Tunnels established (background process)${NC}"
    else
        echo -e "${RED}✗ Failed to establish tunnels${NC}"
        exit 1
    fi
fi

echo ""
echo "Waiting for tunnels to initialize..."
sleep 3

# Verify tunnels
echo ""
echo "Verifying tunnels..."

# Test Qwen2-VL tunnel
if curl -s --max-time 5 http://localhost:$QWEN2VL_PORT/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qwen2-VL API accessible on port $QWEN2VL_PORT${NC}"
else
    echo -e "${YELLOW}⚠ Qwen2-VL API not responding on port $QWEN2VL_PORT${NC}"
    echo "  Make sure Qwen2-VL vLLM is running on remote server (GPU 0, port 8000)"
fi

# Test OmniVinci tunnel
if curl -s --max-time 5 http://localhost:$OMNIVINCI_PORT/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OmniVinci API accessible on port $OMNIVINCI_PORT${NC}"
else
    echo -e "${YELLOW}⚠ OmniVinci API not responding on port $OMNIVINCI_PORT${NC}"
    echo "  Make sure OmniVinci service is running on remote server (GPU 1, port 8001)"
fi

# Test Qwen3-Omni tunnel
if curl -s --max-time 5 http://localhost:$QWEN3OMNI_PORT/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qwen3-Omni API accessible on port $QWEN3OMNI_PORT${NC}"
else
    echo -e "${YELLOW}⚠ Qwen3-Omni API not responding on port $QWEN3OMNI_PORT${NC}"
    echo "  Make sure Qwen3-Omni service is running (port 8002)"
fi

# Test video server tunnel (optional)
if curl -s --max-time 5 http://localhost:$VIDEO_PORT/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Video server accessible on port $VIDEO_PORT (optional)${NC}"
else
    echo -e "${YELLOW}⚠ Video server not responding on port $VIDEO_PORT${NC}"
    echo "  This is optional - videos also served from local backend/videos/"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Tunnel Setup Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Tunnels are running in the background."
echo ""
echo "To stop tunnels:"
echo "  lsof -ti:$QWEN2VL_PORT | xargs kill"
echo "  lsof -ti:$OMNIVINCI_PORT | xargs kill"
echo "  lsof -ti:$QWEN3OMNI_PORT | xargs kill"
echo "  lsof -ti:$VIDEO_PORT | xargs kill"
echo ""
echo "Or simply close this terminal."
echo ""
echo "Video locations:"
echo "  - Local: backend/videos/ (for frontend playback)"
echo "  - Remote: ~/datasets/videos/ (for AI processing)"
echo ""
echo "Now you can run:"
echo "  ./start.sh"
echo ""

