# 🚀 Get Started - Remote H100 Setup

Your Video Caption Service is configured to use **Qwen3-Omni-30B** on remote H100 cluster. Follow these steps to get started.

---

## Overview

```
Your Mac → SSH Tunnels → Remote H100 Cluster
          (Port 8000, 8080)  (vLLM + Videos)
```

**Setup time:**
- First time: 20-30 minutes (includes remote setup)
- Subsequent uses: 2-3 minutes (tunnels + local services)

---

## Step 1: Remote Server Setup (First Time Only)

### 1.1 Access Remote Server

```bash
ssh naresh@85.234.64.44
```

### 1.2 Create Directories

```bash
mkdir -p ~/datasets/videos
mkdir -p ~/datasets/captions
```

### 1.3 Setup Python Environment

```bash
# Allocate GPU
salloc -p p_naresh --gres=gpu:1 --cpus-per-task=16 --mem=128G --time=24:00:00

# Create venv
python3 -m venv ~/venvs/qwen-vllm
source ~/venvs/qwen-vllm/bin/activate

# Install packages
pip install --upgrade pip
pip install vllm openai transformers accelerate
```

### 1.4 Start vLLM Service

**Create file `~/start-vllm.sbatch`:**

```bash
#!/bin/bash
#SBATCH --job-name=qwen3-vllm
#SBATCH --partition=p_naresh
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=48:00:00
#SBATCH --output=%x-%j.log

source ~/venvs/qwen-vllm/bin/activate
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct \
  --dtype auto \
  --tensor-parallel-size 1 \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0
```

**Submit job:**

```bash
sbatch ~/start-vllm.sbatch
```

**Monitor:** `squeue -u $USER`

### 1.5 Start Video HTTP Server

**Create file `~/start-video-server.sbatch`:**

```bash
#!/bin/bash
#SBATCH --job-name=video-http-server
#SBATCH --partition=p_naresh
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=48:00:00
#SBATCH --output=%x-%j.log

cd ~/datasets/videos
python3 -m http.server 8080
```

**Submit:**

```bash
sbatch ~/start-video-server.sbatch
```

### 1.6 Verify Services

```bash
# Check vLLM
curl http://localhost:8000/v1/models

# Check video server
curl http://localhost:8080/
```

✅ **Remote setup complete!** (See [REMOTE_SETUP.md](REMOTE_SETUP.md) for detailed guide)

---

## Step 2: Upload Videos

From your **local Mac**, upload videos to remote server:

```bash
# Single video
rsync -avz --progress ~/Downloads/my_video.mp4 naresh@85.234.64.44:~/datasets/videos/

# Multiple videos
rsync -avz --progress ~/Movies/videos/ naresh@85.234.64.44:~/datasets/videos/

# From existing backend/videos
rsync -avz --progress ./backend/videos/ naresh@85.234.64.44:~/datasets/videos/
```

**Verify:**

```bash
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/"
```

---

## Step 3: Setup Local Environment

### 3.1 Configure Environment

```bash
cd /path/to/VideoCaptionService

# Copy example config
cp .env.example .env

# View config (already set for remote)
cat .env
```

**.env is pre-configured:**

```env
# Remote Server
REMOTE_HOST=naresh@85.234.64.44
REMOTE_VIDEOS_DIR=~/datasets/videos
REMOTE_CAPTIONS_DIR=~/datasets/captions

# SSH Tunnels
VLLM_API_URL=http://localhost:8000
REMOTE_VIDEO_URL=http://localhost:8080

# Local Ports
BACKEND_PORT=8001
FRONTEND_PORT=3001

# Model
MODEL_NAME=qwen3-omni
```

No changes needed unless you want custom ports.

---

## Step 4: Establish SSH Tunnels

SSH tunnels connect your local machine to remote services.

### Option A: Using Helper Script (Recommended)

In a **new terminal** (keep it open):

```bash
cd /path/to/VideoCaptionService
./scripts/start-tunnels.sh
```

**Output:**

```
========================================
SSH Tunnel Manager
========================================
Remote host: naresh@85.234.64.44
Tunnels:
  - Port 8000 → vLLM API
  - Port 8080 → Video HTTP Server

✓ autossh detected - will use for persistent tunnels
Establishing SSH tunnels...
✓ Tunnels established (background daemon)
✓ vLLM API accessible on port 8000
✓ Video server accessible on port 8080
```

### Option B: Manual

```bash
# Basic tunnel
ssh -N -L 8000:localhost:8000 -L 8080:localhost:8080 naresh@85.234.64.44

# Or with autossh (auto-reconnect)
autossh -M 0 -N -L 8000:localhost:8000 -L 8080:localhost:8080 \
  -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" \
  naresh@85.234.64.44
```

### Verify Tunnels

In another terminal:

```bash
# Test vLLM API
curl http://localhost:8000/v1/models

# Test video server
curl http://localhost:8080/
```

Both should return responses. If not, check remote services.

---

## Step 5: Start Local Services

With tunnels running, start the Docker containers:

```bash
./start.sh
```

**Expected output:**

```
========================================
Video Caption Service - Startup
========================================
Configuration:
  vLLM API Port: 8000 (via SSH tunnel)
  Video Server Port: 8080 (via SSH tunnel)
  Backend Port: 8001
  Frontend Port: 3001

Checking SSH tunnels...
✓ vLLM API tunnel is active (port 8000)
✓ Video server tunnel is active (port 8080)

Starting Docker services...
✓ Docker services started
✓ Backend service is ready

========================================
✓ All Services Started Successfully!
========================================

Access the application:
  Frontend: http://localhost:3001
  Backend API: http://localhost:8011/docs
  Remote vLLM API: http://localhost:8000/docs (via tunnel)

Video files location: Remote server (~/datasets/videos/)
Captions location: ./backend/captions/ (synced from remote)
```

---

## Step 6: Use the Application

### 6.1 Open Web Interface

```bash
open http://localhost:3001
# Or navigate in browser to http://localhost:3001
```

### 6.2 Generate Captions

1. **Videos appear** in grid (loaded from remote server)
2. **Click "Generate Caption"** on any video
3. **Wait** for processing (1-3 minutes)
   - Video is streamed from remote
   - Processing happens on H100 GPU
   - Caption is generated by Qwen3-Omni-30B
4. **Caption appears** with "Captioned (QWEN3-OMNI)" badge
5. **Click "View"** to see video with full caption

### 6.3 View API Docs

- **Backend**: http://localhost:8011/docs
- **vLLM**: http://localhost:8000/docs

---

## Step 7: Sync Captions (Optional)

Captions are stored on remote server. To copy them locally:

```bash
./scripts/sync-captions.sh
```

**Output:**

```
========================================
Caption Synchronization
========================================
Remote: naresh@85.234.64.44:~/datasets/captions
Local:  /path/to/backend/captions

Syncing captions...
receiving file list ... done
video1.mp4_qwen3-omni.json
video2.mp4_qwen3-omni.json

✓ Captions synced successfully
Total caption files: 2
```

---

## Stopping Services

### Stop Local Containers

```bash
./stop.sh
```

**Note:** This only stops Docker containers. SSH tunnels and remote services remain running.

### Stop SSH Tunnels

```bash
# Find and kill tunnel processes
lsof -ti:8000 | xargs kill
lsof -ti:8080 | xargs kill

# Or just close the terminal running tunnels
```

### Stop Remote Services

```bash
# SSH to remote
ssh naresh@85.234.64.44

# Check jobs
squeue -u $USER

# Cancel job
scancel <JOBID>
```

---

## Daily Usage

After initial setup, your daily workflow is:

```bash
# 1. Ensure remote services are running (check once)
ssh naresh@85.234.64.44 "squeue -u \$USER"

# 2. Start tunnels (keep terminal open)
./scripts/start-tunnels.sh

# 3. Start local services
./start.sh

# 4. Use the app
open http://localhost:3001

# 5. When done, stop local services
./stop.sh
```

---

## Troubleshooting

### Tunnels Won't Connect

```bash
# Check remote services
ssh naresh@85.234.64.44
squeue -u $USER  # Should show vLLM and video-server jobs

# Check logs
tail -f qwen3-vllm-*.log
tail -f video-http-server-*.log
```

### Videos Don't Appear

```bash
# Verify videos on remote
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/"

# Test video server via tunnel
curl http://localhost:8080/
```

### Caption Generation Fails

```bash
# Check all components
curl http://localhost:8000/v1/models  # vLLM
curl http://localhost:8080/           # Video server
curl http://localhost:8001/health     # Backend
```

### Need Help?

- **Full remote setup**: See [REMOTE_SETUP.md](REMOTE_SETUP.md)
- **Architecture details**: See [README.md](README.md)
- **Cluster reference**: See [Qwen3_Omni_30B_Cluster_Reference.md](Qwen3_Omni_30B_Cluster_Reference.md)

---

## Performance Expectations

| Metric | Value |
|--------|-------|
| Remote model startup | 3-5 minutes (first time: 10-15 min for download) |
| Caption generation (1 min video) | 1-2 minutes |
| Caption generation (5 min video) | 3-5 minutes |
| Video streaming latency | 2-5 seconds initial buffering |
| SSH tunnel overhead | Minimal |

---

## Tips

### Tip 1: Keep Tunnels Running

Use `autossh` (installed via Homebrew) for persistent tunnels:

```bash
brew install autossh
./scripts/start-tunnels.sh  # Automatically uses autossh if available
```

### Tip 2: Batch Upload Videos

```bash
# Upload entire directory
rsync -avz --progress ~/Movies/project-videos/ naresh@85.234.64.44:~/datasets/videos/
```

### Tip 3: Monitor Remote GPU

```bash
# SSH to worker node
ssh naresh@85.234.64.44
squeue -u $USER  # Get job ID
ssh worker-9      # If accessible
nvidia-smi        # View GPU usage
```

### Tip 4: Background Tunnel

```bash
# Run tunnel in background with nohup
nohup ./scripts/start-tunnels.sh > /dev/null 2>&1 &
```

---

## What's Next?

You're all set! Now you can:

- ✅ Generate captions for your videos using H100 cluster
- ✅ Leverage Qwen3-Omni-30B's multimodal capabilities
- ✅ Process videos without needing local GPU
- ✅ Scale up by requesting more GPUs on remote cluster

**Happy Captioning! 🎬**

---

## Quick Reference

| Task | Command |
|------|---------|
| Start tunnels | `./scripts/start-tunnels.sh` |
| Start services | `./start.sh` |
| Stop services | `./stop.sh` |
| Upload video | `rsync -avz video.mp4 naresh@85.234.64.44:~/datasets/videos/` |
| Sync captions | `./scripts/sync-captions.sh` |
| Check remote | `ssh naresh@85.234.64.44 "squeue -u \$USER"` |
| Test vLLM | `curl http://localhost:8000/v1/models` |
| Open UI | `open http://localhost:3001` |
