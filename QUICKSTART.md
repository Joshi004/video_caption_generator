# Quick Start Guide

Get up and running in 5 minutes!

## 📦 What You'll Need

- Docker Desktop installed and running
- NVIDIA GPU with 16GB+ VRAM
- 20GB free disk space
- Python 3.10+ installed

## 🚀 3-Step Setup

### 1️⃣ Configure

```bash
cd VideoCaptionService

# Create your .env file
cp .env.example .env

# Edit .env - set your model path
# Default: MODEL_PATH=/Users/nareshjoshi/models/omnivinci
```

### 2️⃣ Add a Video

```bash
# Place any video file in backend/videos/
cp ~/Movies/my_video.mp4 backend/videos/

# Requirements:
# - Size: < 100MB
# - Duration: < 5 minutes
# - Format: .mp4, .mov, .avi, .mkv, .webm
```

### 3️⃣ Start Everything

```bash
# Make scripts executable
chmod +x start.sh stop.sh

# Start all services
./start.sh

# ⏳ Wait 2-5 minutes (first run may take longer for model download)
```

## 🎉 You're Ready!

Open your browser to: **http://localhost:3001**

You should see:
- ✅ Your video in a grid
- ✅ "Generate Caption" button
- ✅ Beautiful Material-UI interface

## 🎬 Generate Your First Caption

1. Click **"Generate Caption"** on your video
2. Wait 1-3 minutes (processing with OmniVinci)
3. Click **"View"** to see video + caption

## 🛑 Stop Services

```bash
./stop.sh

# Choose 'N' to keep model service running (faster restart)
# Choose 'Y' to stop everything
```

## 🔍 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3001 | Main UI |
| **Backend API** | http://localhost:8011/docs | REST API |
| **Model Service** | http://localhost:8501/docs | OmniVinci |

## 🆘 Troubleshooting

### Services won't start?

```bash
# Check if ports are in use
lsof -i :3001
lsof -i :8001
lsof -i :8501

# Check Docker is running
docker ps

# Check GPU
nvidia-smi
```

### Can't see videos?

```bash
# Check video directory
ls -la backend/videos/

# Check file size
du -h backend/videos/*.mp4

# Should be < 100MB per file
```

### Caption generation fails?

```bash
# Check model service logs
tail -f omnivinci-service/omnivinci-service.log

# Check backend logs
docker-compose logs backend

# Verify model service is healthy
curl http://localhost:8501/health
```

## 📚 Next Steps

- Read [README.md](README.md) for detailed documentation
- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing
- Check backend/captions/ folder for generated JSON files

## 💡 Tips

- **First run?** Model download takes 10-15 minutes
- **Testing?** Use short videos (< 1 min) for faster results
- **Multiple videos?** All videos in backend/videos/ appear automatically
- **Regenerate?** Click "Regenerate" to create new captions
- **Keep model running?** Say 'N' when stopping - faster next startup

## 🎯 Common Ports

If default ports conflict, edit `.env`:

```env
MODEL_SERVICE_PORT=8501  # Change to 8502, 8503, etc.
BACKEND_PORT=8001        # Change to 8002, 8003, etc.
FRONTEND_PORT=3001       # Change to 3002, 3003, etc.
```

---

**That's it! Enjoy your Video Caption Service! 🚀**



