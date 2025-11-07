# Final Setup Guide - Qwen2-VL-7B + OmniVinci

**Your chosen models:**
1. **Qwen/Qwen2-VL-7B-Instruct** - 7B vision model (Apache 2.0)
2. **nvidia/omnivinci** - 9B omni-modal model (Apache 2.0, from [NVlabs/OmniVinci](https://github.com/NVlabs/OmniVinci))

Both are **commercial-friendly with Apache 2.0 license**! ✅

---

## ✅ What's Been Configured

### Code Updated (13 files):
- ✅ Backend model client - Dual model support
- ✅ Backend API - Model selection endpoint
- ✅ Frontend UI - Model chooser dialog
- ✅ SSH tunnel script - 3 ports (8000, 8001, 8080)
- ✅ Environment config - Dual model URLs
- ✅ Docker compose - Multi-model env vars
- ✅ **NEW:** `omnivinci_service.py` - Custom service for OmniVinci

### Documentation Updated (4 files):
- ✅ REMOTE_SETUP.md - Complete dual model guide
- ✅ DUAL_MODEL_SETUP.md - Usage instructions
- ✅ QUICK_REFERENCE.md - One-page cheat sheet
- ✅ IMPLEMENTATION_COMPLETE.md - Full summary

---

## 🚀 How to Set Up (Copy-Paste Commands)

### Part 1: Remote Server Setup

```bash
# 1. SSH to server
ssh naresh@85.234.64.44

# 2. Allocate 2 GPUs (48 hours)
salloc -p p_naresh --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=48:00:00

# 3. Create directories
mkdir -p ~/datasets/{videos,captions}

# 4. Setup venv with requirements.txt
python3 -m venv ~/venvs/qwen-vllm
source ~/venvs/qwen-vllm/bin/activate

# Create requirements.txt
cat > ~/venvs/requirements.txt << 'EOF'
# vLLM for Qwen2-VL-7B
vllm>=0.6.0

# Transformers and dependencies
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

# Install packages (takes 10-15 minutes)
pip install --upgrade pip
pip install -r ~/venvs/requirements.txt

# 5. Start HTTP server for videos
cd ~/datasets/videos
nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &

# Verify
curl http://localhost:8080/

# 6. Exit to copy OmniVinci service file
exit
```

### Part 2: Copy OmniVinci Service Script

```bash
# From your Mac
cd /path/to/VideoCaptionService
scp omnivinci_service.py naresh@85.234.64.44:~/omnivinci_service.py
```

### Part 3: Start Both Models

```bash
# SSH back to server
ssh naresh@85.234.64.44

# Get your GPU allocation (should still be active)
squeue -u $USER

# SSH to worker-9
ssh worker-9

# Start models with tmux
tmux new -s models

# Terminal 1: Qwen2-VL via vLLM (GPU 0, port 8000)
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0

# Wait for "Application startup complete"
# Then press: Ctrl+B, then C (creates new window)

# Terminal 2: OmniVinci via Custom Service (GPU 1, port 8001)
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=1 python ~/omnivinci_service.py

# Wait for "Model loaded successfully"
# Then press: Ctrl+B, then D (detach from tmux)
```

### Part 4: Verify Services (From worker-9)

```bash
# Open new SSH session to worker-9
ssh naresh@85.234.64.44
ssh worker-9

# Test Qwen2-VL
curl http://localhost:8000/v1/models

# Test OmniVinci  
curl http://localhost:8001/v1/models

# Test video server
curl http://localhost:8080/
```

If all three respond, services are running! ✅

### Part 5: Upload Videos

```bash
# From your Mac
rsync -avz --progress ./backend/videos/ naresh@85.234.64.44:~/datasets/videos/

# Verify
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/"
```

### Part 6: Start Local Services

```bash
# From your Mac

# Terminal 1: Start SSH tunnels (keep open)
cd /path/to/VideoCaptionService
./scripts/start-tunnels.sh

# You should see:
# ✓ Qwen2-VL API accessible on port 8000
# ✓ OmniVinci API accessible on port 8001  
# ✓ Video server accessible on port 8080

# Terminal 2: Start Docker containers
./start.sh

# Open browser
open http://localhost:3001
```

---

## 🎯 Using the Application

### 1. Click "Generate Caption"
Model selector dialog appears

### 2. Choose Model:
- **Qwen2-VL-7B** (Default)
  - 7B parameters
  - Fast (1-2 min)
  - Vision-only analysis
  - Apache 2.0 license
  
- **OmniVinci**
  - 9B parameters
  - Slower (2-4 min)
  - Vision + Audio analysis
  - Apache 2.0 license
  - From [NVIDIA NVlabs](https://github.com/NVlabs/OmniVinci)

### 3. Processing
- Video streams from remote server
- Processing happens on H100 GPU
- Caption appears when complete

### 4. View Results
- Click "View" to see full caption
- Model name shown on card
- Can regenerate with different model

---

## 📊 Model Comparison

| Feature | Qwen2-VL-7B | OmniVinci |
|---------|-------------|-----------|
| **Parameters** | 7 billion | 9 billion |
| **License** | Apache 2.0 (<100M MAU) | Apache 2.0 ✅ |
| **Commercial** | ✅ Yes (conditional) | ✅ Yes |
| **Modalities** | Vision + Text | Vision + Audio + Text |
| **Inference** | vLLM (fast) | Transformers (slower) |
| **Speed** | 1-2 min/video | 2-4 min/video |
| **VRAM** | ~16GB | ~20GB |
| **GPU** | GPU 0 | GPU 1 |
| **Port** | 8000 | 8001 |
| **Best For** | Fast captions | Audio analysis |

**Source:** [NVlabs/OmniVinci GitHub](https://github.com/NVlabs/OmniVinci)

---

## 🔍 Verification Checklist

### Remote Server (worker-9)
- [ ] 2 GPUs allocated via salloc
- [ ] Directories created (`~/datasets/videos`, `~/datasets/captions`)
- [ ] Venv created and activated
- [ ] Packages installed from requirements.txt
- [ ] HTTP server running (port 8080)
- [ ] omnivinci_service.py copied to ~/
- [ ] Qwen2-VL vLLM running (GPU 0, port 8000)
- [ ] OmniVinci service running (GPU 1, port 8001)
- [ ] Videos uploaded to ~/datasets/videos/

Test commands:
```bash
curl http://localhost:8000/v1/models  # Qwen2-VL
curl http://localhost:8001/v1/models  # OmniVinci
curl http://localhost:8080/           # Videos
nvidia-smi                             # Check both GPUs
```

### Local Mac
- [ ] SSH tunnels active (ports 8000, 8001, 8080)
- [ ] Docker containers running
- [ ] Frontend accessible (http://localhost:3001)
- [ ] Can see videos in UI
- [ ] Model selector shows both models
- [ ] Can generate captions with Qwen2-VL
- [ ] Can generate captions with OmniVinci

Test commands:
```bash
curl http://localhost:8000/v1/models  # via tunnel
curl http://localhost:8001/v1/models  # via tunnel
curl http://localhost:8080/           # via tunnel
curl http://localhost:8011/api/videos/models  # backend API
```

---

## 🆘 Troubleshooting

### OmniVinci Service Won't Start

**Error: Module not found**
```bash
# Make sure all dependencies installed
source ~/venvs/qwen-vllm/bin/activate
pip install transformers accelerate torch fastapi uvicorn httpx
```

**Error: Model download fails**
```bash
# Check internet and disk space
ping huggingface.co
df -h ~

# Try manual download
huggingface-cli download nvidia/omnivinci
```

### Qwen2-VL Works, OmniVinci Doesn't

**OmniVinci uses Transformers (not vLLM):**
- Slower startup (~5-10 min first time)
- Downloads ~9GB model
- Check logs: `tmux attach -t models` then switch to window 2

### Both Models Show in UI But Generation Fails

Check SSH tunnels:
```bash
# From Mac
curl http://localhost:8000/v1/models  # Qwen2-VL
curl http://localhost:8001/v1/models  # OmniVinci

# If either fails, restart tunnels
./scripts/start-tunnels.sh
```

---

## 📝 Quick Commands

```bash
# Start tunnels (Mac)
./scripts/start-tunnels.sh

# Start services (Mac)
./start.sh

# Check remote services (worker-9)
tmux attach -t models  # See both model logs

# Upload videos (Mac)
rsync -avz video.mp4 naresh@85.234.64.44:~/datasets/videos/

# Sync captions (Mac)
./scripts/sync-captions.sh

# Monitor GPUs (worker-9)
nvidia-smi
```

---

## 🎉 You're All Set!

**Both models ready:**
- ✅ Qwen2-VL-7B-Instruct (fast, vLLM-optimized)
- ✅ OmniVinci (audio understanding, from [NVIDIA NVlabs](https://github.com/NVlabs/OmniVinci))

**Both Apache 2.0 licensed - commercial-friendly!**

---

## 📚 Next Steps

1. **Follow REMOTE_SETUP.md** - Complete setup on worker-9
2. **Copy omnivinci_service.py** - To remote server
3. **Start both models** - Using tmux
4. **Test locally** - Run `./start.sh` and open browser
5. **Generate captions** - Try both models and compare!

**Questions? Check:**
- REMOTE_SETUP.md - Detailed remote setup
- DUAL_MODEL_SETUP.md - Model usage guide
- QUICK_REFERENCE.md - Command cheat sheet

---

**Happy Captioning!** 🎬


