# Current Status & Next Steps

## ✅ What's Working

1. **Backend running** on port 8011
   - `/api/videos` endpoint works ✅
   - Returns 5 videos ✅

2. **Frontend running** on port 3001
   - UI accessible ✅

3. **Code updated** with dual model support
   - Qwen2-VL-7B (port 8000)
   - OmniVinci (port 8001)

---

## ⚠️ What's Not Working

### Issue 1: `/api/videos/available-models` Returns 404

**Cause:** Route order conflict with `/{filename}` path parameter

**Status:** Code is fixed but Docker container not picking it up properly

**Fix:** Need fresh rebuild

### Issue 2: Caption Generation Fails

**Error:**  
```
vLLM service error: Cannot connect to host host.docker.internal:8080
```

**Cause:** vLLM on remote worker-9 trying to fetch video from wrong URL

**Status:** Video URL base changed to `http://127.0.0.1:8080` in code

---

## 🔧 Complete Fix Steps

### Step 1: Create Correct .env File

```bash
cd /Users/nareshjoshi/Documents/TetherWorkspace/VideoCaptionService

# Create .env file
cat > .env << 'EOF'
QWEN2VL_API_URL=http://localhost:8000
OMNIVINCI_API_URL=http://localhost:8001
REMOTE_VIDEO_URL=http://localhost:8080
REMOTE_HOST=naresh@85.234.64.44
REMOTE_VIDEOS_DIR=~/datasets/videos
REMOTE_CAPTIONS_DIR=~/datasets/captions
BACKEND_PORT=8011
FRONTEND_PORT=3001
MAX_VIDEO_SIZE_MB=100
MAX_VIDEO_DURATION_SEC=300
DEFAULT_MODEL=qwen2vl
VIDEOS_DIR=/app/videos
CAPTIONS_DIR=/app/captions
EOF
```

### Step 2: Complete Docker Rebuild

```bash
# Stop everything
docker-compose down

# Remove cached images
docker system prune -f

# Rebuild completely
docker-compose build --no-cache

# Start with environment variable
BACKEND_PORT=8011 docker-compose up -d

# Watch logs
docker logs -f video-caption-backend
```

### Step 3: Verify Services

```bash
# Wait for startup
sleep 20

# Test backend
curl http://localhost:8011/api/videos | jq 'length'
# Should return: 5

# Test models endpoint
curl http://localhost:8011/api/videos/available-models | jq
# Should return both models

# Test frontend
curl http://localhost:3001 | head -5
# Should return HTML
```

---

## Alternative: Simplified Testing

**For now, test caption generation directly** (bypassing model selector):

```bash
# Make sure tunnels are running
./scripts/start-tunnels.sh

# Test caption generation with Qwen2-VL
curl -X POST "http://localhost:8011/api/videos/3.mp4/caption?model=qwen2vl" \
  -H "Content-Type: application/json"
```

**If this works,** the API is functional, just the route needs fixing.

**If this fails with video URL error,** check:
1. Is HTTP server running on worker-9?
2. Does `~/datasets/videos/3.mp4` exist on remote?

---

## Quick Debug Commands

```bash
# 1. Check tunnels
lsof -i :8000  # Qwen2-VL
lsof -i :8001  # OmniVinci
lsof -i :8080  # Videos

# 2. Test tunnels
curl http://localhost:8000/v1/models
curl http://localhost:8001/v1/models

# 3. Check backend container
docker ps | grep backend
docker logs video-caption-backend --tail 50

# 4. Test endpoints
curl http://localhost:8011/api/videos
curl http://localhost:8011/openapi.json | jq '.paths | keys'
```

---

## Expected Final State

```
Remote (worker-9):
├── Qwen2-VL vLLM (port 8000) ✅ Running
├── OmniVinci service (port 8001) - Optional
├── HTTP server (port 8080) ✅ Running
└── Videos in ~/datasets/videos/

SSH Tunnels:
├── localhost:8000 → worker-9:8000 ✅
├── localhost:8001 → worker-9:8001 ✅
└── localhost:8080 → worker-9:8080 ✅

Local:
├── Backend (port 8011) ✅ Running (needs rebuild)
├── Frontend (port 3001) ✅ Running
└── Videos in backend/videos/
```

---

## Next Action

**Create the .env file as shown in Step 1, then rebuild Docker containers!**

This will fix both the models endpoint and the caption generation.



