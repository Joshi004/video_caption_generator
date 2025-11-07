# Quick Reference - Dual Model Video Caption Service

**One-page cheat sheet** for running dual models on H100 cluster.

---

## 🚀 Remote Setup (One-Time)

```bash
# 1. SSH to server
ssh naresh@85.234.64.44

# 2. Allocate 2 GPUs (48 hours)
salloc -p p_naresh --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=48:00:00

# 3. Create directories
mkdir -p ~/datasets/{videos,captions}

# 4. Create venv and requirements
python3 -m venv ~/venvs/qwen-vllm
source ~/venvs/qwen-vllm/bin/activate

cat > ~/venvs/requirements.txt << 'EOF'
vllm>=0.6.0
transformers>=4.40.0
accelerate>=0.30.0
torch>=2.3.0
qwen-vl-utils
EOF

pip install --upgrade pip && pip install -r ~/venvs/requirements.txt

# 5. Start HTTP server (background)
cd ~/datasets/videos && nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &

# 6. Start models with tmux
tmux new -s models

# Window 1: InternVL2-26B (GPU 0, port 8000)
CUDA_VISIBLE_DEVICES=0 vllm serve OpenGVLab/InternVL2-26B \
  --dtype bfloat16 --max-model-len 8192 --trust-remote-code --port 8000 --host 0.0.0.0

# Press Ctrl+B then C (new window)

# Window 2: OmniVinci (GPU 1, port 8001)
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=1 vllm serve nvidia/NVLM-D-72B \
  --dtype bfloat16 --max-model-len 4096 --trust-remote-code --port 8001 --host 0.0.0.0

# Press Ctrl+B then D (detach)
```

---

## 💻 Local Usage (Daily)

```bash
# Terminal 1: Start SSH tunnels (keep open)
cd /path/to/VideoCaptionService
./scripts/start-tunnels.sh

# Terminal 2: Start Docker services
./start.sh

# Browser: Open application
open http://localhost:3001
```

---

## 🔍 Verification Commands

```bash
# From worker-9
curl http://localhost:8000/v1/models  # InternVL2
curl http://localhost:8001/v1/models  # OmniVinci
curl http://localhost:8080/           # Videos

# From Mac (via tunnels)
curl http://localhost:8000/v1/models
curl http://localhost:8001/v1/models
curl http://localhost:8080/

# Check GPUs
nvidia-smi  # Should show both GPUs in use
```

---

## 📤 Upload Videos

```bash
# From Mac
rsync -avz ./backend/videos/ naresh@85.234.64.44:~/datasets/videos/
```

---

## 🔄 Sync Captions

```bash
# From Mac
./scripts/sync-captions.sh
```

---

## 🛑 Shutdown

```bash
# Mac: Stop Docker
./stop.sh

# Mac: Stop tunnels
lsof -ti:8000 | xargs kill
lsof -ti:8001 | xargs kill
lsof -ti:8080 | xargs kill

# Remote: Stop models (reattach to tmux first)
tmux attach -t models
# Ctrl+C in each window
tmux kill-session -t models

# Remote: Exit allocation
exit
```

---

## 🎯 Model Comparison

| Feature | InternVL2-26B | OmniVinci |
|---------|---------------|-----------|
| **Size** | 26B params | 72B params |
| **License** | MIT ✅ | Custom ⚠️ |
| **Commercial** | Yes, unlimited | Check license |
| **Speed** | Fast (1-2 min) | Slower (2-4 min) |
| **Port** | 8000 | 8001 |
| **GPU** | 0 | 1 |
| **Use For** | Production | Testing |

---

## 📝 Key URLs

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3001 |
| **Backend API** | http://localhost:8011/docs |
| **InternVL2 API** | http://localhost:8000/docs |
| **OmniVinci API** | http://localhost:8001/docs |

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Tunnels fail | `./scripts/start-tunnels.sh` |
| Models not responding | Check `tmux attach -t models` |
| GPU memory error | Use `nvidia-smi` to check usage |
| Port in use | `lsof -ti:PORT \| xargs kill` |
| Videos don't load | Verify `curl http://localhost:8080/` |

---

## 📚 Full Documentation

- **REMOTE_SETUP.md** - Complete setup guide
- **DUAL_MODEL_SETUP.md** - Model usage details
- **GET_STARTED.md** - Quick start
- **Commands.md** - Cluster commands

---

**Everything ready! Read REMOTE_SETUP.md to begin.** 🎉


