# Testing Guide - Video Caption Service

This guide will help you test the Video Caption Service end-to-end.

## Prerequisites Checklist

Before testing, ensure you have:

- [ ] Docker and Docker Compose installed
- [ ] NVIDIA GPU with 16GB+ VRAM
- [ ] Python 3.10+ installed
- [ ] At least 20GB free disk space
- [ ] 10GB+ free RAM

## Step-by-Step Testing

### Step 1: Setup Environment

```bash
cd /Users/nareshjoshi/Documents/TetherWorkspace/VideoCaptionService

# Create .env file if not exists
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Edit .env to set your MODEL_PATH
# Default: MODEL_PATH=/Users/nareshjoshi/models/omnivinci
```

### Step 2: Make Scripts Executable

```bash
chmod +x start.sh stop.sh
chmod +x omnivinci-service/start_omnivinci.sh
chmod +x omnivinci-service/stop_omnivinci.sh
```

### Step 3: Prepare Test Video

Place a test video in the backend/videos directory:

```bash
# Example: Copy a sample video
cp /path/to/your/test_video.mp4 backend/videos/

# Or download a sample video
# curl -o backend/videos/sample.mp4 https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4
```

**Note**: Ensure video meets constraints:
- Size: < 100MB
- Duration: < 5 minutes
- Format: .mp4, .mov, .avi, .mkv, or .webm

### Step 4: Start All Services

```bash
./start.sh
```

**What happens:**
1. Checks if OmniVinci service is running
2. If not, creates virtual environment
3. Downloads OmniVinci model (first time only, ~10GB)
4. Starts model inference service
5. Builds Docker containers
6. Starts backend and frontend services

**Expected output:**
```
========================================
✓ All Services Started Successfully!
========================================

Access the application:

  Frontend: http://localhost:3001
  Backend API: http://localhost:8011/docs
  Model Service: http://localhost:8501/docs
```

**Time estimates:**
- First run (with model download): 15-30 minutes
- Subsequent runs: 2-5 minutes

### Step 5: Verify Services

Open your browser and check:

1. **Frontend** - http://localhost:3001
   - Should show the Video Caption Service UI
   - Should display your test video in the grid

2. **Backend API** - http://localhost:8011/docs
   - Should show FastAPI Swagger documentation
   - Try the GET /api/videos endpoint

3. **Model Service** - http://localhost:8501/docs
   - Should show model service API docs
   - Try GET /health endpoint

**Command line verification:**

```bash
# Check all services
curl http://localhost:3001
curl http://localhost:8001/health
curl http://localhost:8501/health

# List videos via API
curl http://localhost:8001/api/videos | jq

# Check Docker containers
docker-compose ps
```

### Step 6: Generate Caption

1. Open http://localhost:3001 in your browser
2. Find your test video in the grid
3. Click "Generate Caption" button
4. Wait for processing (1-3 minutes depending on video length)
5. Caption generation progress shown in dialog

**What's happening:**
- Frontend sends request to Backend
- Backend validates video constraints
- Backend forwards video to Model Service
- OmniVinci processes video (128 frames + audio)
- Caption returned and saved as JSON
- UI updates automatically

**Monitor progress:**

```bash
# Watch backend logs
docker-compose logs -f backend

# Watch model service logs
tail -f omnivinci-service/omnivinci-service.log
```

### Step 7: View Caption

Once generated:

1. Video card shows "Captioned" badge (green)
2. Preview of caption text appears in card
3. Click "View" button
4. Modal opens showing:
   - Video player (left)
   - Full caption text (right)
   - Model name badge (OMNIVINCI)
   - Regenerate button

**Verify caption file:**

```bash
# Check captions directory
ls -la backend/captions/

# View caption JSON
cat backend/captions/test_video.mp4_omnivinci.json | jq
```

**Expected JSON format:**
```json
{
  "filename": "test_video.mp4",
  "caption": "The video features...",
  "generated_at": "2025-11-03T10:30:00Z",
  "processing_time_seconds": 12.4,
  "model_name": "omnivinci",
  "model_version": "nvidia/omnivinci"
}
```

### Step 8: Test Regeneration

1. With caption viewer open, click "Regenerate"
2. Or from grid, click "Regenerate" button
3. New caption replaces old one
4. File timestamp updates

### Step 9: Test Filtering

Use filter buttons to test:
- "All" - Shows all videos
- "Captioned" - Shows only videos with captions
- "Not Captioned" - Shows videos without captions

### Step 10: Stop Services

```bash
./stop.sh
```

When prompted:
- Choose 'N' to keep model service running (faster restart)
- Choose 'Y' to stop everything (clean shutdown)

## Troubleshooting Tests

### Test 1: Check Port Conflicts

```bash
# Check if ports are available
lsof -i :8501  # Model service
lsof -i :8001  # Backend
lsof -i :3001  # Frontend

# If ports in use, either:
# 1. Kill the process
# 2. Change ports in .env
```

### Test 2: Verify GPU Access

```bash
# Check GPU availability
nvidia-smi

# Check CUDA version
python -c "import torch; print(torch.cuda.is_available())"

# Check from model service venv
cd omnivinci-service
source venv/bin/activate
python -c "import torch; print(torch.cuda.is_available())"
deactivate
```

### Test 3: Check Model Download

```bash
# Verify model exists
ls -lh $MODEL_PATH

# Should show files like:
# config.json
# model.safetensors
# preprocessor_config.json
# etc.
```

### Test 4: Backend Can Reach Model Service

```bash
# From inside backend container
docker-compose exec backend curl http://host.docker.internal:8501/health
```

### Test 5: Video Validation

```bash
# Test oversized video
dd if=/dev/zero of=backend/videos/large.mp4 bs=1M count=150
# Should get 413 error

# Test long video
# Should get error if > 5 minutes

# Check video properties
ffprobe backend/videos/test_video.mp4
```

## Performance Benchmarks

Track these metrics during testing:

| Metric | Expected Value |
|--------|----------------|
| Model startup time | 2-5 minutes |
| Caption generation (1 min video) | 1-2 minutes |
| Caption generation (5 min video) | 3-5 minutes |
| Memory (model service) | ~18GB VRAM + 10GB RAM |
| Memory (backend container) | ~1GB RAM |
| Memory (frontend container) | ~512MB RAM |

## Success Criteria

Your test is successful if:

- [x] All services start without errors
- [x] Frontend loads and shows videos
- [x] Caption generation completes successfully
- [x] Caption appears in UI and as JSON file
- [x] Video player works in viewer modal
- [x] Filter buttons work correctly
- [x] Services stop cleanly

## Common Issues and Solutions

### Issue: Model download fails

**Solution:**
```bash
# Manual download
pip install huggingface-hub
huggingface-cli download nvidia/omnivinci --local-dir ~/models/omnivinci
```

### Issue: Out of memory

**Solutions:**
- Close other GPU applications
- Reduce video length
- Check GPU memory: `nvidia-smi`

### Issue: Caption generation timeout

**Solutions:**
- Video too long (> 5 min)
- Increase timeout in backend config
- Check model service logs

### Issue: Frontend can't reach backend

**Solutions:**
- Check CORS settings
- Verify backend port in .env
- Check docker network: `docker network inspect videocaptionservice_video-caption-network`

## Advanced Testing

### Test API Directly

```bash
# Generate caption via API
curl -X POST "http://localhost:8001/api/videos/test_video.mp4/caption" \
  -H "accept: application/json"

# Get caption
curl "http://localhost:8001/api/videos/test_video.mp4/caption" | jq

# Delete caption
curl -X DELETE "http://localhost:8001/api/videos/test_video.mp4/caption"

# Stream video
curl "http://localhost:8001/api/videos/test_video.mp4/stream" > downloaded.mp4
```

### Load Testing

```bash
# Generate captions for multiple videos in parallel
for video in backend/videos/*.mp4; do
    filename=$(basename "$video")
    curl -X POST "http://localhost:8001/api/videos/$filename/caption" &
done
wait
```

### Log Analysis

```bash
# Backend logs
docker-compose logs backend | grep ERROR

# Model service logs  
grep ERROR omnivinci-service/omnivinci-service.log

# Container resource usage
docker stats
```

## Cleanup After Testing

```bash
# Remove all generated captions
rm backend/captions/*.json

# Remove test videos
rm backend/videos/*.mp4

# Stop and remove containers
./stop.sh
docker-compose down -v

# Remove model service venv (optional)
rm -rf omnivinci-service/venv/
```

## Next Steps

After successful testing:

1. **Production Setup**: Update CORS, add authentication
2. **Performance Tuning**: Adjust timeouts, memory limits
3. **Monitoring**: Add logging, metrics, alerts
4. **Scaling**: Add Redis for job queue, multiple workers
5. **Model Expansion**: Support other models beyond OmniVinci

---

**Happy Testing! 🧪**



