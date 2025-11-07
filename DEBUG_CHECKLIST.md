# Debug Checklist - Connection Reset Error

## Error: `curl: (56) Recv failure: Connection reset by peer`

This means the vLLM service crashed or closed the connection during processing.

---

## Step 1: Check if Tunnel is Still Active

```bash
# From your Mac
lsof -i :8000
lsof -i :8001
lsof -i :8080

# Should show ssh processes for each port
```

**If nothing shows:** Restart tunnels
```bash
./scripts/start-tunnels.sh
```

---

## Step 2: Check if vLLM is Still Running

```bash
# SSH to worker-9
ssh naresh@85.234.64.44
ssh worker-9

# Check if vLLM process is running
ps aux | grep vllm

# Check GPU memory
nvidia-smi

# Try accessing locally
curl http://localhost:8000/v1/models
```

**If vLLM crashed:** Check tmux logs
```bash
# Reattach to tmux session
tmux attach -t models

# You'll see the crash logs in window 0 (Qwen2-VL)
# Press Ctrl+B, 0 to go to window 0
# Press Ctrl+B, 1 to go to window 1 (OmniVinci)
```

---

## Step 3: Common Causes & Solutions

### Cause 1: Video Too Large

**Problem:** Video file might be too big to process

**Check video size:**
```bash
# From Mac
ls -lh backend/videos/3.mp4

# From remote
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/3.mp4"
```

**Solution:** Try with smaller video first
```bash
# Test with a small video
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{
      "role":"user",
      "content":[
        {"type":"text","text":"Briefly describe this video."},
        {"type":"video_url","video_url":{"url":"http://127.0.0.1:8080/3.mp4"}}
      ]
    }],
    "max_tokens": 128
  }'
```

### Cause 2: Video URL Not Accessible

**Problem:** vLLM on worker-9 can't reach `http://127.0.0.1:8080/3.mp4`

**Check on worker-9:**
```bash
# SSH to worker-9
ssh naresh@85.234.64.44
ssh worker-9

# Test video server
curl -I http://localhost:8080/3.mp4

# Should return 200 OK
```

**If video server not running:**
```bash
cd ~/datasets/videos
nohup python3 -m http.server 8080 > ~/video-server.log 2>&1 &
```

### Cause 3: Out of Memory (OOM)

**Problem:** GPU ran out of memory processing the video

**Check GPU memory:**
```bash
# On worker-9
nvidia-smi

# Look at GPU 0 memory usage
# If showing 80000+ MiB / 81559 MiB → OOM likely
```

**Solutions:**
```bash
# Option A: Reduce max_model_len
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 4096 \  # Reduced from 8192
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0

# Option B: Lower GPU memory utilization
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \  # Default is 0.9
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0
```

### Cause 4: Request Timeout

**Problem:** Your prompt is very long, vLLM might have timed out

**Your prompt:**
```
"Describe this video in details desucss every thing that is happening on the screen 
and also discuss what people are saying and any words or text shown on the screen, 
Try to get the complete story and whats the meaning"
```

**Solution:** Use shorter prompt first
```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{
      "role":"user",
      "content":[
        {"type":"text","text":"Describe this video."},
        {"type":"video_url","video_url":{"url":"http://127.0.0.1:8080/3.mp4"}}
      ]
    }],
    "max_tokens": 256
  }'
```

### Cause 5: vLLM Crashed During Processing

**Check tmux logs:**
```bash
# Reattach to see crash logs
tmux attach -t models
```

**Restart vLLM:**
```bash
# In tmux window 0 (Ctrl+B, 0)
# If crashed, restart:
source ~/venvs/qwen-vllm/bin/activate
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0
```

---

## Step 4: Test with Simple Request First

```bash
# Test 1: Text-only (no video)
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{"role":"user","content":[{"type":"text","text":"Hello"}]}],
    "max_tokens": 10
  }'

# If this works, vLLM is fine

# Test 2: Simple video caption
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{
      "role":"user",
      "content":[
        {"type":"text","text":"What is in this video?"},
        {"type":"video_url","video_url":{"url":"http://127.0.0.1:8080/3.mp4"}}
      ]
    }],
    "max_tokens": 50
  }'

# If this works, start increasing complexity
```

---

## Step 5: Most Likely Solution

Based on your detailed prompt, I suspect **video processing caused OOM or timeout**.

**Try this:**

```bash
# 1. Check if video exists on remote
ssh naresh@85.234.64.44 "ls -lh ~/datasets/videos/3.mp4"

# 2. Restart vLLM with more conservative settings
# On worker-9, in tmux:
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.80 \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0

# 3. Test with shorter prompt
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{
      "role":"user",
      "content":[
        {"type":"text","text":"Describe this video in detail."},
        {"type":"video_url","video_url":{"url":"http://127.0.0.1:8080/3.mp4"}}
      ]
    }],
    "max_tokens": 512
  }'
```

---

## Quick Fix Commands

```bash
# From Mac - Kill and restart tunnel
lsof -ti:8000 | xargs kill
./scripts/start-tunnels.sh

# SSH to remote and check services
ssh naresh@85.234.64.44
ssh worker-9
tmux attach -t models
```

---

**Start with Step 1-3, then let me know what you find!**




