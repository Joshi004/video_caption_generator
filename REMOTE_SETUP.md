# Remote Server Setup Guide

Complete guide for setting up Qwen2-VL-7B vLLM service on the H100 cluster for video captioning.

---

## Overview

This guide sets up everything on **worker-9** (your H100 node) for video captioning.

**What you'll set up:**
- Python virtual environment with vLLM
- vLLM service running Qwen2-VL-7B-Instruct (AI model for video captioning)
- HTTP server to serve videos to vLLM
- Directory structure for videos and captions

**Why these components:**
- **vLLM**: Fast inference server for large language models (serves the AI model)
- **Qwen2-VL-7B-Instruct**: Vision-language AI that generates text captions from videos
- **HTTP Server**: vLLM needs videos accessible via URL (not file paths)
- **Worker-9**: All services run here (simpler, faster, uses your dedicated GPU)

**Models:**
1. **Qwen2-VL-7B-Instruct**: 7B vision-language model via vLLM (fast, reliable)
2. **OmniVinci**: 9B omni-modal model from NVIDIA (vision + audio + text)

**Why these models:**
- ✅ Both have Apache 2.0 license (commercial-friendly)
- ✅ Qwen2-VL works with vLLM (fast inference)
- ✅ OmniVinci adds audio understanding capability
- ✅ Both fit on single H100 GPUs

---

## Prerequisites

- SSH access: `naresh@85.234.64.44`
- Personal partition: `p_naresh` with worker-9
- Python 3.10.12 (confirmed available)
- 8× H100 GPUs (80GB each)

---

## Step 0: Pre-Flight Checks (Optional but Recommended)

### Check if Home Directory is Shared

**Why:** We want to confirm files created on login-1 are visible on worker-9.

```bash
# On login-1
echo "test" > ~/test_shared.txt

# Allocate worker briefly
salloc -p p_naresh --gres=gpu:1 --time=00:02:00
cat ~/test_shared.txt    # Should show "test"
rm ~/test_shared.txt
exit
```

**Result:** If this works, your home directory is shared (common on HPC clusters).

### Check Worker Internet Access

**Why:** vLLM needs to download the model from HuggingFace (~8GB for Qwen2-VL-7B).

```bash
# Allocate worker
salloc -p p_naresh --gres=gpu:1 --time=00:02:00

# Test connectivity
ping -c 3 huggingface.co
curl -I https://huggingface.co

exit
```

**Result:** If successful, worker-9 can download models.

---

## Step 1: Allocate GPU Session

**What:** Request GPU resources from Slurm scheduler for 48 hours.

**Why:** You need 2 GPUs to run both models simultaneously (InternVL2 + OmniVinci).

```bash
salloc -p p_naresh \          # Use your personal partition
       --gres=gpu:2 \          # Request 2 GPUs (for dual model setup)
       --cpus-per-task=16 \    # Request 16 CPU cores
       --mem=128G \            # Request 128GB RAM
       --time=48:00:00         # Reserve for 48 hours
```

**What happens:**
- Slurm finds 2 available GPUs on worker-9
- Your terminal moves to worker-9
- 2 GPUs reserved exclusively for you
- After 48 hours, job ends (can resubmit)

**Verify you're on worker:**
```bash
hostname              # Should show: worker-9
nvidia-smi            # Should show 2 H100 GPUs
```

---

## Step 2: Create Directories

**What:** Create folders for videos and generated captions.

**Why:** Organize files (videos in, captions out).

```bash
# On worker-9 (after salloc)
mkdir -p ~/datasets/videos
mkdir -p ~/datasets/captions

# Verify
ls -la ~/datasets/
```

**Note:** Since home directory is shared, these are visible from login-1 too.

---

## Step 3: Setup Python Environment

**What:** Create isolated Python environment with vLLM and dependencies.

**Why venv needed:**
- vLLM has many dependencies (PyTorch, transformers, etc.)
- Specific versions required (might conflict with system packages)
- Isolated from other users' environments
- Easy to update/rebuild without affecting system

### 3.1 Create Virtual Environment

```bash
# Create venv (one-time)
python3 -m venv ~/venvs/qwen-vllm

# Activate (do this every time you log in)
source ~/venvs/qwen-vllm/bin/activate

# Your prompt changes to show: (qwen-vllm)
```

### 3.2 Install vLLM and Dependencies

**What each package does:**
- `vllm`: Fast inference server for LLMs
- `transformers`: Hugging Face library (model loading)
- `accelerate`: Multi-GPU support
- `qwen-vl-utils`: Qwen vision utilities (for video processing)

**Option A: Using requirements.txt (Recommended)**

This ensures consistent versions and faster installation.

```bash
# Create requirements.txt
cat > ~/venvs/requirements.txt << 'EOF'
# vLLM and dependencies for Qwen2-VL video captioning
vllm>=0.6.0
transformers>=4.40.0
accelerate>=0.30.0
torch>=2.3.0
qwen-vl-utils
EOF

# Install all packages at once
pip install --upgrade pip
pip install -r ~/venvs/requirements.txt
```

**Option B: Manual installation**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install packages one by one (takes 5-10 minutes)
pip install vllm
pip install transformers
pip install accelerate
pip install qwen-vl-utils
```

**Verify installation:**
```bash
python -c "import vllm; print(vllm.__version__)"
```

**Expected output:** Version number like `0.6.0` or higher.

---

## Step 4: Start HTTP Server for Videos

**What:** Simple Python HTTP server to serve video files.

**Why needed:** vLLM's API uses `video_url` (not file uploads). The model fetches videos from a URL like `http://localhost:8080/video.mp4`.

**Start in background:**

```bash
# Navigate to videos directory
cd ~/datasets/videos

# Start HTTP server in background
nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &

# Verify it's running
curl http://localhost:8080/
# Should show HTML directory listing
```

**What this does:**
- Serves all files in `~/datasets/videos/` via HTTP
- Runs in background (nohup = continues after you log out)
- Logs to `~/video-server.log`
- Accessible at `http://localhost:8080/filename.mp4`

**To stop it later:**
```bash
# Find process ID
lsof -i :8080

# Kill it
kill <PID>
```

---

## Step 5: Start Model Services

**What:** Start two AI model services on different GPUs.

**Why:** 
- Qwen2-VL-7B via vLLM (fast, lightweight)
- OmniVinci via custom service (audio+vision understanding)

### 5.1 Start Qwen2-VL-7B on GPU 0 (vLLM Service)

```bash
# Make sure you allocated 2 GPUs
# salloc -p p_naresh --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=48:00:00

# Activate venv
source ~/venvs/qwen-vllm/bin/activate

# Start Qwen2-VL-7B on GPU 0 (port 8000) - via vLLM
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0
```

**What this does:**
- `CUDA_VISIBLE_DEVICES=0`: Use only GPU 0
- `Qwen/Qwen2-VL-7B-Instruct`: 7B vision-language model (Apache 2.0)
- `--port 8000`: Primary model API endpoint via vLLM
- Downloads ~8GB on first run (3-5 minutes)

**Expected output:**
```
INFO: Loading model Qwen/Qwen2-VL-7B-Instruct
INFO: Model loaded successfully
INFO: Application startup complete.
```

**Keep this terminal running!**

### 5.2 Start OmniVinci on GPU 1 (Custom Service)

**Important:** OmniVinci doesn't work with vLLM yet. We'll use a custom FastAPI service with Transformers.

**Download the service script** (I've created this for you):

The `omnivinci_service.py` file is in your project root. Copy it to the remote server:

```bash
# From your Mac
scp omnivinci_service.py naresh@85.234.64.44:~/omnivinci_service.py
```

**Or create it manually on worker-9:**

```bash
# Create the service file (see omnivinci_service.py in project)
# Or download from project repo
```

**Install OmniVinci requirements:**

```bash
source ~/venvs/qwen-vllm/bin/activate

# Install OmniVinci following official instructions
pip install --upgrade pip
pip install torch torchvision torchaudio
pip install transformers accelerate
pip install fastapi uvicorn httpx
```

**Start OmniVinci service:**

```bash
# Activate venv
source ~/venvs/qwen-vllm/bin/activate

# Run on GPU 1, port 8001
CUDA_VISIBLE_DEVICES=1 python ~/omnivinci_service.py
```

**Alternative - Using tmux to manage both:**

```bash
# Start tmux session
tmux new -s models

# Window 1: Qwen2-VL via vLLM (GPU 0)
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 --max-model-len 8192 --trust-remote-code --port 8000 --host 0.0.0.0

# Create new window: Ctrl+B then C
tmux new-window

# Window 2: OmniVinci via Transformers (GPU 1)
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=1 python ~/omnivinci_service.py

# Detach from tmux: Ctrl+B then D
# Reattach later: tmux attach -t models
```

### 5.3 Alternative: Run Both as Batch Jobs

**When to use:** If you want models to run after you log out.

**Create file: `~/start-dual-models.sbatch`**

```bash
#!/bin/bash
#SBATCH --job-name=dual-models
#SBATCH --partition=p_naresh
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=48:00:00
#SBATCH --output=dual-models-%j.log
#SBATCH --error=dual-models-%j.err

source ~/venvs/qwen-vllm/bin/activate

# Start Qwen2-VL via vLLM on GPU 0 in background
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 --max-model-len 8192 --trust-remote-code \
  --port 8000 --host 0.0.0.0 &

# Wait for first model to initialize
sleep 30

# Start OmniVinci via Transformers on GPU 1 in background
CUDA_VISIBLE_DEVICES=1 python ~/omnivinci_service.py &

# Wait for both processes
wait
```

**Submit:**
```bash
sbatch ~/start-dual-models.sbatch
```

**Monitor:**
```bash
squeue -u $USER
tail -f dual-models-*.log
```

---

## Step 6: Upload Videos

**What:** Transfer video files from your Mac to the remote server.

**Why:** Videos must be on the server where vLLM can access them via HTTP.

From your **Mac terminal** (NOT on the server):

```bash
# Single video
rsync -avz --progress ~/Downloads/video.mp4 naresh@85.234.64.44:~/datasets/videos/
rsync -avz --progress /Users/nareshjoshi/Documents/TetherWorkspace/VideoCaptionService/backend/videos/Bill-gates-thankyou.mp4 naresh@85.234.64.44:~/datasets/videos/

# Multiple videos from a folder
rsync -avz --progress ~/Movies/my-videos/ naresh@85.234.64.44:~/datasets/videos/
rsync -avz --progress /Users/nareshjoshi/Documents/TetherWorkspace/VideoCaptionService/backend/videos/ naresh@85.234.64.44:~/datasets/videos/

# If you have videos in backend/videos locally
rsync -avz --progress ./backend/videos/ naresh@85.234.64.44:~/datasets/videos/
```

**What rsync flags mean:**
- `-a`: Archive mode (preserves permissions, timestamps)
- `-v`: Verbose (shows progress)
- `-z`: Compress during transfer (faster over network)
- `--progress`: Show file-by-file progress

**Verify upload:**

```bash
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/"
```

---

## Step 7: Verify Everything Works

**What:** Test that all components are running correctly.

### 7.1 Check Both Model Services are Running

```bash
# From worker-9

# Check Qwen2-VL (port 8000)
curl http://localhost:8000/v1/models

# Check OmniVinci (port 8001)
curl http://localhost:8001/v1/models
```

**Expected output:**

**Qwen2-VL (port 8000):**
```json
{
  "object": "list",
  "data": [{
    "id": "Qwen/Qwen2-VL-7B-Instruct",
    "object": "model",
    "owned_by": "qwen"
  }]
}
```

**OmniVinci (port 8001):**
```json
{
  "object": "list",
  "data": [{
    "id": "nvidia/omnivinci",
    "object": "model",
    "owned_by": "nvidia"
  }]
}
```

### 7.2 Check Video Server is Running

```bash
curl http://localhost:8080/
```

**Expected output:** HTML directory listing of videos

### 7.3 Test End-to-End Caption Generation

**Test Qwen2-VL (port 8000):**

```bash
# Replace "your-video.mp4" with actual filename
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this video in detail."},
        {"type": "video_url", "video_url": {"url": "http://127.0.0.1:8080/your-video.mp4"}}
      ]
    }],
    "max_tokens": 256
  }'
```

**Test OmniVinci (port 8001):**

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/omnivinci",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this video and its audio in detail."},
        {"type": "video_url", "video_url": {"url": "http://127.0.0.1:8080/your-video.mp4"}}
      ]
    }],
    "max_tokens": 512
  }'
```

**What this does:**

**Qwen2-VL (vLLM):**
1. Receives request
2. Fetches video from HTTP server
3. Processes video frames (visual analysis only)
4. Generates text caption
5. Returns JSON response

**OmniVinci (Custom service):**
1. Receives request
2. Downloads video from HTTP server
3. Processes video frames + audio track
4. Generates comprehensive description (vision + audio)
5. Returns JSON response

**Expected output:**
```json
{
  "id": "cmpl-...",
  "object": "chat.completion",
  "model": "Qwen/Qwen2-VL-7B-Instruct",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "The video shows a person walking down a street..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 45,
    "total_tokens": 195
  }
}
```

**If this works, your setup is complete!** ✅

**Key Differences:**
- **Qwen2-VL**: Fast (vLLM optimized), vision-only analysis
- **OmniVinci**: Slower (Transformers), includes audio understanding from [NVlabs/OmniVinci](https://github.com/NVlabs/OmniVinci)

---

## Step 8: Setup SSH Tunnels (From Your Mac)

**What:** Create encrypted connections from your Mac to the services on worker-9.

**Why:** Services run on worker-9 (port 8000, 8080), but you need to access them from your Mac. SSH tunnels forward these ports to your local machine.

**How it works:**
```
Your Mac          SSH Tunnel          Server
localhost:8000  ←→ Encrypted SSH ←→  worker-9:8000 (vLLM)
localhost:8080  ←→ Encrypted SSH ←→  worker-9:8080 (videos)
```

### 8.1 Check Port Accessibility (From login-1)

First, verify login-1 can reach worker-9 ports:

```bash
# SSH to login-1
ssh naresh@85.234.64.44

# Test vLLM port
curl http://worker-9:8000/v1/models

# Test video server port
curl http://worker-9:8080/
```

**If both work:** Use Method 2 below (multi-hop)  
**If they fail:** Ports might only be accessible from worker-9 itself

### 8.2 Establish Tunnels (From Your Mac)

Open **new terminal on your Mac** and run:

```bash
# Tunnel for AI model APIs and video server
ssh -fN -o ExitOnForwardFailure=yes \
  -L 8000:worker-9:8000 \
  -L 8001:worker-9:8001 \
  -L 8080:worker-9:8080 \
  naresh@85.234.64.44
```

**What each part means:**
- `-f`: Run in background (forks to background after auth)
- `-N`: Don't execute commands (just tunnel)
- `-o ExitOnForwardFailure=yes`: Exit if port forwarding fails
- `-L 8000:worker-9:8000`: Qwen2-VL API
- `-L 8001:worker-9:8001`: OmniVinci API
- `-L 8080:worker-9:8080`: Video HTTP server (optional - videos also local)

**Note:** Frontend streams videos from local `backend/videos/`. Port 8080 tunnel is optional backup.

### 8.3 Or Use the Helper Script

Easier option - use the provided script:

```bash
cd /path/to/VideoCaptionService
./scripts/start-tunnels.sh
```

This handles everything automatically including auto-reconnect.

### 8.4 Verify Tunnels Work (From Your Mac)

```bash
# Test Qwen2-VL API (required)
curl http://localhost:8000/v1/models

# Test OmniVinci API (required)
curl http://localhost:8001/v1/models

# Test video server (optional)
curl http://localhost:8080/
```

**If model APIs work, tunnels are active!** ✅

---

## Step 9: Start Local Services (From Your Mac)

Now that tunnels are active, start your local Docker containers:

```bash
cd /path/to/VideoCaptionService

# Start local services
./start.sh
```

This starts:
- Backend (FastAPI) on port 8001
- Frontend (React) on port 3001

**Open browser:**
```
http://localhost:3001
```

You should see your videos and can generate captions!

---

## Summary: What's Running Where

```
Worker-9 (Remote H100):
├── Qwen2-VL-7B vLLM (GPU 0, port 8000) → Fast vision model
├── OmniVinci Service (GPU 1, port 8001) → Vision+Audio model
├── HTTP Server (port 8080) → Serves videos to LOCAL AI models
└── Videos: ~/datasets/videos/ (for AI processing)

Your Mac:
├── SSH Tunnels:
│   ├── Port 8000 → Qwen2-VL API
│   ├── Port 8001 → OmniVinci API
│   └── Port 8080 → Video HTTP Server
├── Backend (port 8011 local) → API + model selection
├── Frontend (port 3001) → Web UI + video player
├── Videos: backend/videos/ (for frontend playback)
└── Browser → http://localhost:3001
```

**Data Flow:**
- **For playback:** Frontend → Local backend/videos/ (fast, no network)
- **For AI processing:** AI models → Remote ~/datasets/videos/ via HTTP server

**Licenses:**
- Qwen2-VL-7B: Apache 2.0 (commercial-friendly, <100M MAU clause)
- OmniVinci: Apache 2.0 ([source](https://github.com/NVlabs/OmniVinci))

---

## Monitoring and Management

### Check If Services Are Running

```bash
# Check Slurm allocation
squeue -u $USER
# Should show your salloc session

# Check vLLM process
ps aux | grep vllm

# Check HTTP server process
ps aux | grep "http.server"
```

### View Logs

```bash
# vLLM logs (if running in terminal, you'll see output there)
# If using sbatch:
tail -f vllm-*.log

# Video server logs
tail -f ~/video-server.log
```

### Monitor GPU Usage

```bash
# On worker-9
nvidia-smi

# Watch in real-time (updates every second)
watch -n 1 nvidia-smi

# You should see vLLM using GPU memory when model is loaded
```

### Stop Services

```bash
# Stop vLLM (if running interactively)
Ctrl+C

# Stop HTTP server
lsof -i :8080      # Get PID
kill <PID>

# Cancel Slurm allocation (stops everything)
exit                # If using salloc
scancel <JOBID>     # If using sbatch
```

---

## Troubleshooting

### vLLM Won't Start

**Symptom:** Error when running `vllm serve` command.

**Checks:**
```bash
# 1. Is GPU available?
nvidia-smi

# 2. Is venv activated?
which python    # Should show ~/venvs/qwen-vllm/bin/python

# 3. Is vLLM installed?
pip show vllm

# 4. Enough disk space for model download?
df -h ~         # Need ~60GB free
```

**Solution - Check resources:**
```bash
# Qwen2-VL-7B should work fine on 1 GPU, but if issues persist:

# 1. Check if model downloaded completely
ls -lh ~/.cache/huggingface/hub/

# 2. Try with more memory
salloc -p p_naresh --gres=gpu:1 --cpus-per-task=16 --mem=128G
```

### Model Download is Slow/Fails

**Symptom:** Download hangs or errors out.

**Checks:**
```bash
# Test internet
ping huggingface.co

# Check disk space
df -h ~

# Check cache directory
ls -lh ~/.cache/huggingface/
```

**Solution - Manual download:**
```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2-VL-7B-Instruct
```

### Port Already in Use

**Symptom:** "Address already in use" error.

**Find and kill process:**
```bash
# Find process on port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Same for port 8080
lsof -i :8080
kill -9 <PID>
```

### SSH Tunnel Disconnects

**Symptom:** Connection drops, tunnels stop working.

**Solution - Use autossh (on Mac):**
```bash
brew install autossh
./scripts/start-tunnels.sh  # Auto-uses autossh
```

**Or add keepalive to SSH:**
```bash
ssh -N -L 8000:worker-9:8000 -L 8080:worker-9:8080 \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  naresh@85.234.64.44
```

### Video Not Found by vLLM

**Symptom:** vLLM can't access video file.

**Checks:**
```bash
# 1. Does video exist?
ls -lh ~/datasets/videos/your-video.mp4

# 2. Is HTTP server running?
curl http://localhost:8080/

# 3. Can you access the video?
curl -I http://localhost:8080/your-video.mp4

# 4. Check permissions
ls -l ~/datasets/videos/
```

**Fix permissions if needed:**
```bash
chmod 644 ~/datasets/videos/*.mp4
```

### Caption Generation Takes Too Long

**Symptom:** Processing one video takes >3 minutes.

**Reasons:**
- Large video file (>100MB)
- Long video (>5 min)
- Many frames to process
- First-time model loading

**Solutions:**
```bash
# 1. Reduce max_tokens in API request
"max_tokens": 128    # Shorter captions = faster

# 2. Check GPU isn't shared
nvidia-smi    # Should show only your process

# 3. Verify video server is fast
curl -w "@-" -o /dev/null http://localhost:8080/your-video.mp4 <<< "time_total: %{time_total}s"
```

**Note:** Qwen2-VL-7B is much faster than 30B models (~2-3x speedup).

---

## Performance Tuning

### Qwen2-VL-7B is Already Optimized!

**Good news:** The 7B model is:
- ✅ Fast inference (~30-60 seconds per video)
- ✅ Fits on 1 GPU with plenty of room
- ✅ Lower memory requirements (only ~16GB VRAM)

### For Processing Multiple Videos Simultaneously

You could run multiple vLLM instances on different GPUs:

```bash
# GPU 0: vLLM instance 1 (port 8000)
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct --port 8000 --host 0.0.0.0

# GPU 1: vLLM instance 2 (port 8001) - in another terminal/job
CUDA_VISIBLE_DEVICES=1 vllm serve Qwen/Qwen2-VL-7B-Instruct --port 8001 --host 0.0.0.0
```

**Benefits:**
- Process 2 videos simultaneously (2x throughput)
- Each gets dedicated GPU
- You have 8 GPUs available!

### For Very Long Videos

```bash
# Increase max_model_len if needed
vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --max-model-len 16384 \  # Double the default
  --dtype auto --trust-remote-code --port 8000 --host 0.0.0.0
```

### Optimize Video Uploads

```bash
# Faster rsync (less verbose, more compression)
rsync -az ~/videos/ naresh@85.234.64.44:~/datasets/videos/

# Parallel rsync for multiple files
parallel -j 4 rsync -az {} naresh@85.234.64.44:~/datasets/videos/ ::: *.mp4
```

---

## Maintenance

### Update vLLM

```bash
source ~/venvs/qwen-vllm/bin/activate
pip install --upgrade vllm
```

### Clear Old Captions

```bash
# Archive captions older than 30 days
find ~/datasets/captions -name "*.json" -mtime +30 -exec mv {} ~/datasets/captions/archive/ \;
```

### Backup Captions

```bash
# From local machine
rsync -avz naresh@85.234.64.44:~/datasets/captions/ ./caption-backups/
```

---

## Quick Reference

### Setup (One-Time) - Dual Model Configuration

```bash
# 1. Allocate 2 GPUs for dual model setup
salloc -p p_naresh --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=48:00:00

# 2. Create directories
mkdir -p ~/datasets/{videos,captions}

# 3. Setup venv with requirements.txt
python3 -m venv ~/venvs/qwen-vllm
source ~/venvs/qwen-vllm/bin/activate

# Create requirements.txt
cat > ~/venvs/requirements.txt << 'EOF'
# vLLM for Qwen2-VL-7B
vllm>=0.6.0

# Transformers and dependencies for both models
transformers>=4.40.0
accelerate>=0.30.0
torch>=2.3.0

# Qwen utilities
qwen-vl-utils

# FastAPI for OmniVinci service
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
EOF

# Install all packages
pip install --upgrade pip
pip install -r ~/venvs/requirements.txt

# 4. Start HTTP server (background)
cd ~/datasets/videos && nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &

# 5. Copy OmniVinci service script
# From your Mac, copy omnivinci_service.py to remote:
# scp omnivinci_service.py naresh@85.234.64.44:~/

# 6. Start both models using tmux
tmux new -s models

# Window 1: Qwen2-VL via vLLM on GPU 0
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 --max-model-len 8192 --trust-remote-code --port 8000 --host 0.0.0.0

# In new tmux window (Ctrl+B then C):
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=1 python ~/omnivinci_service.py

# Detach: Ctrl+B then D
```

### Daily Usage
```bash
# From Mac: Establish tunnels
./scripts/start-tunnels.sh

# From Mac: Start local services  
./start.sh

# Open browser
open http://localhost:3001
```

### Common Commands
| Task | Command |
|------|---------|
| Check GPU status | `nvidia-smi` |
| Check jobs | `squeue -u $USER` |
| Upload video | `rsync -avz video.mp4 naresh@85.234.64.44:~/datasets/videos/` |
| Test vLLM | `curl http://localhost:8000/v1/models` |
| Test video server | `curl http://localhost:8080/` |
| View logs | `tail -f ~/video-server.log` |
| Stop services | `Ctrl+C` (vLLM), `kill <PID>` (HTTP server) |

---

## Resource Allocation Guide

| Workload | GPUs | Memory | CPUs | Time |
|----------|------|--------|------|------|
| Testing (Qwen2-VL-7B) | 1 H100 | 32G | 4 | 2:00:00 |
| Production (Qwen2-VL-7B) | 1 H100 | 64G | 8 | 48:00:00 |
| Long videos | 1 H100 | 64G | 8 | 48:00:00 |
| Batch processing (parallel) | 4 H100 | 256G | 32 | 72:00:00 |

---

## Security Notes

- Services bind to `0.0.0.0` but are only accessible within cluster
- SSH tunnel provides secure access from your Mac
- No authentication needed (cluster network is isolated)
- For production, consider adding API keys

---

## Support

If you encounter issues:

1. Check logs: `tail -f *.log`
2. Verify GPU status: `nvidia-smi`
3. Check Slurm status: `squeue -u $USER`
4. Review this guide's troubleshooting section

---

**You're now ready to use the remote H100 cluster for video captioning!**

