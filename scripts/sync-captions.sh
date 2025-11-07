#!/bin/bash

# Caption Sync Script
# Synchronizes captions from remote server to local machine

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
REMOTE_CAPTIONS_DIR=${REMOTE_CAPTIONS_DIR:-~/datasets/captions}
LOCAL_CAPTIONS_DIR="$PROJECT_DIR/backend/captions"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Caption Synchronization${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Remote: $REMOTE_HOST:$REMOTE_CAPTIONS_DIR"
echo "Local:  $LOCAL_CAPTIONS_DIR"
echo ""

# Check if local directory exists
if [ ! -d "$LOCAL_CAPTIONS_DIR" ]; then
    echo -e "${YELLOW}⚠ Local captions directory not found${NC}"
    echo "Creating: $LOCAL_CAPTIONS_DIR"
    mkdir -p "$LOCAL_CAPTIONS_DIR"
fi

# Sync captions from remote to local
echo "Syncing captions..."
echo ""

rsync -avz --progress \
    "$REMOTE_HOST:$REMOTE_CAPTIONS_DIR/" \
    "$LOCAL_CAPTIONS_DIR/"

RSYNC_EXIT=$?

echo ""

if [ $RSYNC_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Captions synced successfully${NC}"
    
    # Count caption files
    CAPTION_COUNT=$(find "$LOCAL_CAPTIONS_DIR" -name "*.json" -type f | wc -l | tr -d ' ')
    echo ""
    echo "Total caption files: $CAPTION_COUNT"
    
    if [ $CAPTION_COUNT -gt 0 ]; then
        echo ""
        echo "Recent captions:"
        ls -lht "$LOCAL_CAPTIONS_DIR"/*.json 2>/dev/null | head -5
    fi
else
    echo -e "${RED}✗ Sync failed${NC}"
    echo "Check connection to remote server"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Sync Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""




