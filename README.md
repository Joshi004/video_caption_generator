# Video Caption Service

Generate video captions using Qwen3-Omni-30B on remote H100 cluster with a modern web interface.

## 🎯 Features

- 🎥 **Video-to-Text Captioning**: Comprehensive video analysis including visual content, actions, audio, and speech
- 🤖 **Qwen3-Omni-30B**: Powered by Alibaba's advanced multimodal LLM running on H100 GPUs
- 🎨 **Modern UI**: Beautiful React + Material-UI interface
- 🐳 **Docker Ready**: Easy deployment with Docker Compose
- ☁️ **Remote Processing**: Leverage powerful H100 cluster for caption generation
- 🔒 **Secure**: SSH tunnels for encrypted communication with remote server

## 🏗️ Architecture

```
Local Machine (MacBook)
├── Frontend (React+MUI - Port 3001)
├── Backend (FastAPI - Port 8001)
└── SSH Tunnels (localhost:8000, localhost:8080)
        ↓ Encrypted SSH
Remote H100 Cluster (85.234.64.44)
├── vLLM Service (Qwen3-Omni-30B - Port 8000)
├── Video HTTP Server (Port 8080)
├── Videos: ~/datasets/videos/
└── Captions: ~/datasets/captions/
```

## 📋 Prerequisites

### Local Machine
- **Docker & Docker Compose**: For containerized services
- **SSH Access**: To remote server (naresh@85.234.64.44)
- **Network**: Stable internet connection for SSH tunnels

### Remote Server (Already Set Up)
- **H100 GPU Cluster**: With Slurm scheduler
- **Personal Partition**: `p_naresh` with worker-9 node
- **8× H100 GPUs**: 80GB VRAM each

## 🚀 Quick Start

### Step 1: Setup Remote Server

**First time only** - Set up the H100 cluster:

```bash
# See REMOTE_SETUP.md for complete guide
# Summary:
# 1. SSH to server: ssh naresh@85.234.64.44
# 2. Create directories: mkdir -p ~/datasets/{videos,captions}
# 3. Start vLLM service (see REMOTE_SETUP.md)
# 4. Start video HTTP server (see REMOTE_SETUP.md)
```

📖 **Full instructions**: [REMOTE_SETUP.md](REMOTE_SETUP.md)

### Step 2: Upload Videos to Remote

```bash
# Upload videos to remote server
rsync -avz --progress ./my-videos/ naresh@85.234.64.44:~/datasets/videos/
```

### Step 3: Configure Local Environment

```bash
cd VideoCaptionService
cp .env.example .env
# .env is pre-configured for remote setup
```

### Step 4: Establish SSH Tunnels

In a **separate terminal**, run:

```bash
./scripts/start-tunnels.sh
```

This creates tunnels for:
- Port 8000: vLLM API
- Port 8080: Video HTTP server

Keep this terminal open!

### Step 5: Start Local Services

```bash
./start.sh
```

This will:
- ✅ Verify SSH tunnels are active
- ✅ Start backend Docker container
- ✅ Start frontend Docker container

### Step 6: Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8011/docs
- **Remote vLLM**: http://localhost:8000/docs (via tunnel)

### Step 7: Generate Captions

1. Open http://localhost:3001
2. Videos from remote server appear automatically
3. Click "Generate Caption" on any video
4. Processing happens on remote H100 (1-3 minutes)
5. Click "View" to see video with caption

## 📂 Project Structure

```
VideoCaptionService/
├── backend/                    # FastAPI backend (Docker)
│   ├── app/
│   │   ├── routers/            # API endpoints
│   │   ├── services/           # Business logic (vLLM client)
│   │   └── utils/              # Helper functions
│   ├── videos/                 # (Not used - videos on remote)
│   └── captions/               # Generated captions (synced from remote)
│
├── frontend/                   # React frontend (Docker)
│   └── src/
│       ├── components/         # UI components
│       └── services/           # API client
│
├── scripts/                    # Helper scripts
│   ├── start-tunnels.sh        # Establish SSH tunnels
│   └── sync-captions.sh        # Sync captions from remote
│
├── docker-compose.yml          # Docker orchestration
├── start.sh                    # Startup script (checks tunnels)
├── stop.sh                     # Shutdown script
├── REMOTE_SETUP.md             # Remote server setup guide
└── .env.example                # Environment configuration
```

## 🎮 Usage

### Daily Workflow

**1. Start SSH Tunnels** (if not already running):
```bash
./scripts/start-tunnels.sh
```

**2. Start Local Services**:
```bash
./start.sh
```

**3. Use the Application**:
- Open http://localhost:3001
- Generate captions for videos
- All processing happens on remote H100 cluster

**4. Stop Local Services**:
```bash
./stop.sh
```

Note: SSH tunnels and remote services remain running.

### Managing Videos

**Upload videos to remote:**
```bash
rsync -avz my_video.mp4 naresh@85.234.64.44:~/datasets/videos/
```

**Sync captions to local:**
```bash
./scripts/sync-captions.sh
```

**View captions:**
```bash
ls backend/captions/
cat backend/captions/my_video.mp4_qwen3-omni.json
```

**Caption format:**
```json
{
  "filename": "my_video.mp4",
  "caption": "The video shows...",
  "generated_at": "2025-11-05T10:30:00Z",
  "processing_time_seconds": 45.2,
  "model_name": "qwen3-omni",
  "model_version": "Qwen/Qwen3-Omni-30B-A3B-Instruct"
}
```

## 🔧 Configuration

### Environment Variables

Edit `.env`:

```env
# Remote Server
REMOTE_HOST=naresh@85.234.64.44
REMOTE_VIDEOS_DIR=~/datasets/videos
REMOTE_CAPTIONS_DIR=~/datasets/captions

# SSH Tunnel Ports
VLLM_API_URL=http://localhost:8000
REMOTE_VIDEO_URL=http://localhost:8080

# Local Ports
BACKEND_PORT=8011
FRONTEND_PORT=3001

# Video Constraints
MAX_VIDEO_SIZE_MB=100           # Max file size
MAX_VIDEO_DURATION_SEC=300      # Max duration (5 min)

# Model
MODEL_NAME=qwen3-omni
```

## 🐛 Troubleshooting

### SSH Tunnels Not Working

```bash
# Check tunnel status
lsof -i :8000
lsof -i :8080

# Test vLLM connectivity
curl http://localhost:8000/v1/models

# Test video server
curl http://localhost:8080/

# Restart tunnels
lsof -ti:8000 | xargs kill
lsof -ti:8080 | xargs kill
./scripts/start-tunnels.sh
```

### Docker Services Won't Start

```bash
# Check container logs
docker-compose logs -f

# Check port conflicts
lsof -i :8001
lsof -i :3001

# Rebuild containers
docker-compose down
docker-compose up --build
```

### Caption Generation Fails

Check:
1. ✅ SSH tunnels active: `./scripts/start-tunnels.sh`
2. ✅ Remote vLLM running: `curl http://localhost:8000/v1/models`
3. ✅ Video exists on remote: `ssh naresh@85.234.64.44 "ls ~/datasets/videos/"`
4. ✅ Video server running: `curl http://localhost:8080/`
5. ✅ Video size < 100MB, duration < 5 min

### Remote Service Issues

```bash
# SSH to remote server
ssh naresh@85.234.64.44

# Check vLLM status
squeue -u $USER

# View vLLM logs
tail -f qwen3-vllm-*.log

# Restart vLLM (see REMOTE_SETUP.md)
```

## 📊 Performance

- **Caption Generation**: 1-3 minutes per video (depends on length)
- **Network Latency**: 2-5 seconds for video streaming via tunnel
- **Remote Resources**:
  - vLLM Service: 1× H100 (80GB VRAM) + 128GB RAM
  - Processing: ~45s for 1-min video, ~2-3min for 5-min video
- **Local Resources**:
  - Backend Container: ~1GB RAM
  - Frontend Container: ~512MB RAM
  - SSH Tunnels: Minimal CPU/RAM

## 🔒 Security Notes

- All communication with remote server uses encrypted SSH tunnels
- vLLM service only accessible via localhost (tunneled)
- Remote cluster network is isolated
- For production:
  - Use VPN or WireGuard instead of SSH tunnels
  - Add API authentication
  - Implement rate limiting

## 📝 API Documentation

Once running, visit:
- **Backend API**: http://localhost:8011/docs
- **vLLM API**: http://localhost:8000/docs (via tunnel)

Key endpoints:
- `GET /api/videos` - List all videos (from remote)
- `POST /api/videos/{filename}/caption` - Generate caption (via vLLM)
- `GET /api/videos/{filename}/caption` - Get existing caption
- `GET /api/videos/{filename}/stream` - Stream video (from remote)

## 🤝 Contributing

This is a prototype service. Improvements welcome!

## 📄 License

See LICENSE file.

## 🙏 Credits

- **Qwen3-Omni Model**: Alibaba Cloud / Qwen Team
- **Model**: https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct
- **vLLM**: UC Berkeley
- **H100 Cluster**: Remote GPU infrastructure

## 📞 Support

For issues:
1. Check SSH tunnels: `./scripts/start-tunnels.sh`
2. Check local logs: `docker-compose logs -f`
3. Check remote services: See [REMOTE_SETUP.md](REMOTE_SETUP.md)
4. Verify connectivity: `curl http://localhost:8000/v1/models`

## 📚 Additional Documentation

- **[REMOTE_SETUP.md](REMOTE_SETUP.md)** - Complete remote server setup guide
- **[Qwen3_Omni_30B_Cluster_Reference.md](Qwen3_Omni_30B_Cluster_Reference.md)** - Cluster usage reference

---

**Happy Captioning! 🎬**


