# Dual Model Setup - Complete Guide

Your Video Caption Service now supports **two AI models** running simultaneously on remote H100 cluster!

---

## 🎯 Available Models

### Model 1: InternVL2-26B (Primary - Recommended)

**Parameters:** 26 billion  
**License:** MIT (✅ **Commercial use unlimited**)  
**Port:** 8000  
**GPU:** 0  

**Best for:**
- ✅ Commercial applications
- ✅ Production deployments
- ✅ No legal concerns
- ✅ Fast and reliable
- ✅ High-quality captions

**Command:**
```bash
CUDA_VISIBLE_DEVICES=0 vllm serve OpenGVLab/InternVL2-26B \
  --dtype bfloat16 --max-model-len 8192 --trust-remote-code \
  --port 8000 --host 0.0.0.0
```

### Model 2: OmniVinci/NVLM (Secondary - Testing)

**Parameters:** 72 billion  
**License:** Custom NVIDIA (check for commercial use)  
**Port:** 8001  
**GPU:** 1  

**Best for:**
- Testing and comparison
- Research purposes
- Advanced features

**Command:**
```bash
CUDA_VISIBLE_DEVICES=1 vllm serve nvidia/NVLM-D-72B \
  --dtype bfloat16 --max-model-len 4096 --trust-remote-code \
  --port 8001 --host 0.0.0.0
```

---

## 🏗️ Architecture

```
Remote H100 Cluster (worker-9):
├── GPU 0 → InternVL2-26B (port 8000)
├── GPU 1 → OmniVinci (port 8001)  
├── HTTP Server (port 8080) → Videos
└── Directories:
    ├── ~/datasets/videos/
    └── ~/datasets/captions/

Your Mac:
├── SSH Tunnels:
│   ├── localhost:8000 → worker-9:8000 (InternVL2)
│   ├── localhost:8001 → worker-9:8001 (OmniVinci)
│   └── localhost:8080 → worker-9:8080 (Videos)
├── Backend (port 8001 local)
├── Frontend (port 3001)
└── Browser → Model selector UI
```

---

## 🚀 Quick Start

### On Remote Server (Worker-9)

```bash
# 1. Allocate 2 GPUs
salloc -p p_naresh --gres=gpu:2 --cpus-per-task=16 --mem=128G --time=48:00:00

# 2. Create directories
mkdir -p ~/datasets/{videos,captions}

# 3. Setup venv
python3 -m venv ~/venvs/qwen-vllm
source ~/venvs/qwen-vllm/bin/activate

# 4. Install dependencies with requirements.txt
cat > ~/venvs/requirements.txt << 'EOF'
vllm>=0.6.0
transformers>=4.40.0
accelerate>=0.30.0
torch>=2.3.0
qwen-vl-utils
EOF

pip install --upgrade pip
pip install -r ~/venvs/requirements.txt

# 5. Start HTTP server (background)
cd ~/datasets/videos
nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &

# 6. Start both models using tmux
tmux new -s models

# Terminal 1: InternVL2 on GPU 0
CUDA_VISIBLE_DEVICES=0 vllm serve OpenGVLab/InternVL2-26B \
  --dtype bfloat16 --max-model-len 8192 --trust-remote-code \
  --port 8000 --host 0.0.0.0

# Press Ctrl+B then C to create new window

# Terminal 2: OmniVinci on GPU 1
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=1 vllm serve nvidia/NVLM-D-72B \
  --dtype bfloat16 --max-model-len 4096 --trust-remote-code \
  --port 8001 --host 0.0.0.0

# Press Ctrl+B then D to detach
```

### On Your Mac

```bash
# 1. Upload videos to remote
rsync -avz ./backend/videos/ naresh@85.234.64.44:~/datasets/videos/

# 2. Establish SSH tunnels
./scripts/start-tunnels.sh
# This creates tunnels to ports 8000, 8001, and 8080

# 3. Start local services
./start.sh

# 4. Open browser
open http://localhost:3001
```

---

## 🎨 How to Use in the UI

### 1. Open Application
Navigate to http://localhost:3001

### 2. Generate Caption
Click "Generate Caption" on any video

### 3. Select Model
A dialog appears with two options:
- **InternVL2-26B** (Default) - MIT license, commercial-safe
- **OmniVinci** (Experimental) - Advanced features

### 4. Processing
Selected model processes the video on H100 GPU

### 5. View Results
Caption appears with model name badge

### 6. Compare Models
Generate captions with both models to compare quality!

---

## 📊 Model Comparison

| Feature | InternVL2-26B | OmniVinci/NVLM |
|---------|---------------|----------------|
| Parameters | 26B | 72B |
| License | MIT (fully open) | Custom NVIDIA |
| Commercial Use | ✅ Yes, unlimited | ⚠️ Check license |
| Speed | Fast (~1-2 min) | Slower (~2-4 min) |
| Quality | Excellent | Very high |
| GPU Memory | ~52GB | ~76GB |
| Recommended For | Production | Testing/Research |

---

## 🔧 Configuration Files

### .env.example
```env
# InternVL2-26B (Primary)
INTERNVL2_API_URL=http://localhost:8000

# OmniVinci (Secondary)
OMNIVINCI_API_URL=http://localhost:8001

# Video Server
REMOTE_VIDEO_URL=http://localhost:8080

# Default model
DEFAULT_MODEL=internvl2
```

### Caption File Naming
```
video.mp4_internvl2.json    # Caption from InternVL2
video.mp4_omnivinci.json    # Caption from OmniVinci
```

Both captions can coexist for the same video!

---

## 🧪 Testing Both Models

### From Worker-9:

```bash
# Test InternVL2
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "OpenGVLab/InternVL2-26B",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this video."},
        {"type": "video_url", "video_url": {"url": "http://127.0.0.1:8080/test.mp4"}}
      ]
    }],
    "max_tokens": 256
  }'

# Test OmniVinci
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/NVLM-D-72B",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this video."},
        {"type": "video_url", "video_url": {"url": "http://127.0.0.1:8080/test.mp4"}}
      ]
    }],
    "max_tokens": 256
  }'
```

### From Your Mac (via tunnels):

```bash
# Test both APIs
curl http://localhost:8000/v1/models  # InternVL2
curl http://localhost:8001/v1/models  # OmniVinci
```

---

## 📈 Resource Usage

```bash
# Check both GPUs on worker-9
nvidia-smi

# Expected output:
# GPU 0: InternVL2-26B using ~52GB
# GPU 1: OmniVinci using ~76GB
# Total: ~128GB / 160GB available (2× H100 80GB)
```

**You still have 6 more GPUs available!** Could run even more model instances if needed.

---

## 🛠️ Managing Services

### Start Both Models

```bash
# Using tmux (recommended)
tmux new -s models

# Window 1: InternVL2
CUDA_VISIBLE_DEVICES=0 vllm serve OpenGVLab/InternVL2-26B \
  --dtype bfloat16 --port 8000 --host 0.0.0.0 --trust-remote-code

# Ctrl+B, C (new window)

# Window 2: OmniVinci
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=1 vllm serve nvidia/NVLM-D-72B \
  --dtype bfloat16 --port 8001 --host 0.0.0.0 --trust-remote-code

# Ctrl+B, D (detach)
```

### Monitor Services

```bash
# List tmux sessions
tmux ls

# Reattach to session
tmux attach -t models

# Navigate between windows
# Ctrl+B, N (next window)
# Ctrl+B, P (previous window)
# Ctrl+B, 0 (window 0)
# Ctrl+B, 1 (window 1)
```

### Stop Services

```bash
# Reattach to tmux
tmux attach -t models

# In each window: Ctrl+C to stop vLLM

# Kill entire session
tmux kill-session -t models
```

---

## 🔍 Troubleshooting

### One Model Works, Other Doesn't

```bash
# Check both ports
curl http://localhost:8000/v1/models  # InternVL2
curl http://localhost:8001/v1/models  # OmniVinci

# Check GPU memory
nvidia-smi

# Check processes
ps aux | grep vllm
```

### Model Selection Not Showing in UI

```bash
# Check backend models endpoint
curl http://localhost:8001/api/videos/models

# Expected output:
{
  "models": {
    "internvl2": {...},
    "omnivinci": {...}
  },
  "default": "internvl2"
}
```

### Only Want to Use One Model

Just start the one you want and skip the other! The UI will only show available models.

---

## 💡 Pro Tips

### Tip 1: Start with InternVL2 Only

For commercial projects, you may only need InternVL2:

```bash
# Allocate just 1 GPU
salloc -p p_naresh --gres=gpu:1 --cpus-per-task=8 --mem=64G

# Start only InternVL2
CUDA_VISIBLE_DEVICES=0 vllm serve OpenGVLab/InternVL2-26B \
  --dtype bfloat16 --port 8000 --host 0.0.0.0 --trust-remote-code

# Tunnel only port 8000
ssh -N -L 8000:worker-9:8000 -L 8080:worker-9:8080 naresh@85.234.64.44
```

### Tip 2: Compare Caption Quality

Generate captions with both models for the same video and compare!

### Tip 3: Use More GPUs

You have 8 H100 GPUs! Can run up to 8 model instances simultaneously:

```bash
# Allocate all 8 GPUs
salloc -p p_naresh --gres=gpu:8

# Run multiple InternVL2 instances for parallel processing
CUDA_VISIBLE_DEVICES=0 vllm serve ... --port 8000
CUDA_VISIBLE_DEVICES=1 vllm serve ... --port 8010
CUDA_VISIBLE_DEVICES=2 vllm serve ... --port 8020
# etc.
```

---

## 📝 Caption File Structure

Each model creates its own caption file:

```bash
backend/captions/
├── myvideo.mp4_internvl2.json    # InternVL2's caption
└── myvideo.mp4_omnivinci.json    # OmniVinci's caption
```

**Format:**
```json
{
  "filename": "myvideo.mp4",
  "caption": "The video shows...",
  "generated_at": "2025-11-05T20:30:00Z",
  "processing_time_seconds": 45.2,
  "model_name": "internvl2",
  "model_version": "OpenGVLab/InternVL2-26B"
}
```

---

## 🎯 Recommended Workflow

### For Commercial Projects:
1. Use **InternVL2-26B** exclusively (MIT license)
2. Start only this model on remote
3. Faster, legally safe, excellent quality

### For Testing/Research:
1. Run both models
2. Compare caption quality
3. Choose best model for your use case
4. Then deploy with chosen model only

---

## 📚 Documentation References

- **REMOTE_SETUP.md** - Complete remote setup (updated for dual models)
- **GET_STARTED.md** - Quick start guide
- **README.md** - Main documentation
- **Commands.md** - Your cluster commands reference

---

**Dual model setup complete! You can now use both InternVL2-26B and OmniVinci!** 🎉




