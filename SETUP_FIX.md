# Setup Fix - Complete Working Configuration

## Summary of Issues Found:

1. ✅ Port conflict: Fixed by moving backend to 8011, OmniVinci on 8001
2. ✅ Indentation error: Fixed in model_client.py
3. ✅ Route order: Fixed - /available-models before /{filename}
4. ⚠️ .env file: Needs manual creation

---

## Step 1: Create .env File (CRITICAL!)

**Run this command:**

```bash
cd /Users/nareshjoshi/Documents/TetherWorkspace/VideoCaptionService

cat > .env << 'EOF'
# Remote Services (via SSH tunnels)
QWEN2VL_API_URL=http://localhost:8000
OMNIVINCI_API_URL=http://localhost:8001
REMOTE_VIDEO_URL=http://localhost:8080

# Remote Server
REMOTE_HOST=naresh@85.234.64.44
REMOTE_VIDEOS_DIR=~/datasets/videos
REMOTE_CAPTIONS_DIR=~/datasets/captions

# Local Ports
BACKEND_PORT=8011
FRONTEND_PORT=3001

# Video Constraints  
MAX_VIDEO_SIZE_MB=100
MAX_VIDEO_DURATION_SEC=300

# Model
DEFAULT_MODEL=qwen2vl

# Internal Docker Paths
VIDEOS_DIR=/app/videos
CAPTIONS_DIR=/app/captions
EOF

# Verify
cat .env
```

---

## Step 2: Restart Everything

```bash
cd /Users/nareshjoshi/Documents/TetherWorkspace/VideoCaptionService

# 1. Stop containers
docker-compose down

# 2. Rebuild with no cache
docker-compose build --no-cache

# 3. Start with explicit port
BACKEND_PORT=8011 docker-compose up -d

# 4. Wait and test
sleep 15
curl http://localhost:8011/api/videos | jq 'length'
curl http://localhost:8011/api/videos/available-models | jq
```

---

## Step 3: Test Model Selection

```bash
# Should return both models
curl http://localhost:8011/api/videos/available-models

# Expected output:
{
  "models": {
    "qwen2vl": {
      "name": "Qwen/Qwen2-VL-7B-Instruct",
      "display_name": "Qwen2-VL-7B",
      "short_name": "qwen2vl",
      "url": "http://localhost:8000"
    },
    "omnivinci": {
      "name": "nvidia/omnivinci",
      "display_name": "OmniVinci",
      "short_name": "omnivinci",
      "url": "http://localhost:8001"
    }
  },
  "default": "qwen2vl"
}
```

---

## Step 4: Test Caption Generation

```bash
# Make sure SSH tunnels are active
lsof -i :8000  # Should show ssh process
lsof -i :8001  # Should show ssh process

# Test simple caption
curl "http://localhost:8011/api/videos/3.mp4/caption?model=qwen2vl&regenerate=false" -X POST | jq
```

---

## Step 5: Open Frontend

```bash
open http://localhost:3001
```

**In the UI:**
1. Click "Generate Caption" on a video
2. Model selector dialog should appear with both models
3. Select Qwen2-VL-7B or OmniVinci
4. Caption generates on remote H100

---

## Current Port Configuration

| Service | Port |  Location |
|---------|------|-----------|
| Qwen2-VL API | 8000 | Remote (tunneled) |
| OmniVinci API | 8001 | Remote (tunneled) |
| Backend API | 8011 | Local (Docker) |
| Frontend | 3001 | Local (Docker) |
| Video Server | 8080 | Remote (tunneled) |

---

## If Still Having Issues

### Issue: Models not showing in UI

```bash
# Check backend models endpoint
curl http://localhost:8011/api/videos/available-models

# Check frontend console (browser DevTools)
# Look for errors calling /api/videos/available-models
```

### Issue: Caption generation fails

```bash
# Check if tunnels are active
lsof -i :8000
lsof -i :8001

# Check if vLLM is running on remote
ssh naresh@85.234.64.44
ssh worker-9
tmux attach -t models
# See if vLLM process is running in window 0

# Test tunnel connectivity
curl http://localhost:8000/v1/models
curl http://localhost:8001/v1/models
```

### Issue: Video not found by vLLM

```bash
# Make sure video exists on remote
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/3.mp4"

# Make sure HTTP server is running on worker-9
ssh naresh@85.234.64.44
ssh worker-9
ps aux | grep "http.server"

# If not running:
cd ~/datasets/videos
nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &
```

---

## Complete Working Flow

```
1. Remote worker-9:
   - Qwen2-VL vLLM running on port 8000
   - OmniVinci service on port 8001 (or skip if not needed)
   - HTTP server on port 8080 serving ~/datasets/videos/

2. SSH Tunnels:
   ssh -fN -o ExitOnForwardFailure=yes \
     -L 8000:worker-9:8000 \
     -L 8001:worker-9:8001 \
     -L 8080:worker-9:8080 \
     naresh@85.234.64.44

3. Local services:
   - Backend on port 8011 (Docker)
   - Frontend on port 3001 (Docker)

4. Browser:
   http://localhost:3001
```

---

**Start with creating the .env file, then follow the steps above!**



