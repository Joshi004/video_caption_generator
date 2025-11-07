
# Qwen3‑Omni 30B on the H100 Cluster — Reference Manual

This guide summarizes everything we discussed so far about using your remote H100 cluster for multimodal video‑caption generation with **Qwen3‑Omni 30B**.

---

## 1. System Overview

### Cluster Basics
- **Login node:** entry point, no GPUs. Use only for lightweight tasks.
- **Worker node:** machines with GPUs (e.g., `worker‑9` → 8× H100 80 GB).
- **Partition:** a queue of nodes with policies. Use your personal partition **`p_naresh`**.
- **Scheduler:** Slurm assigns resources when you request them.

### Key Slurm Commands
| Purpose | Command |
|----------|----------|
| Check partitions | `sinfo -p p_naresh` |
| Interactive GPU session | `salloc -p p_naresh --gres=gpu:1 --cpus-per-task=8 --mem=64G --time=02:00:00` |
| One‑off command | `srun -p p_naresh --gres=gpu:1 nvidia-smi` |
| Submit batch job | `sbatch job.sbatch` |
| Monitor jobs | `squeue -u $USER` |
| Cancel job | `scancel <JOBID>` |

---

## 2. Environment Setup

### Option A – Virtualenv
```bash
python3 -m venv ~/venvs/qwen
source ~/venvs/qwen/bin/activate
pip install --upgrade pip
pip install "git+https://github.com/huggingface/transformers" accelerate qwen-omni-utils -U
pip install flash-attn --no-build-isolation
sudo apt install ffmpeg -y  # if missing
```

### Option B – Container
```bash
srun -p p_naresh --gres=gpu:1 --container-image=nvcr.io/nvidia/pytorch:24.08-py3 bash
```

---

## 3. Running Qwen3‑Omni 30B for Video Captioning

### Simple Python Example
```python
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor
from qwen_omni_utils import process_mm_info

MODEL = "Qwen/Qwen3-Omni-30B-A3B-Instruct"
model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
    MODEL, dtype="auto", device_map="auto", attn_implementation="flash_attention_2"
)
model.disable_talker()
processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL)

conversation = [{
  "role": "user",
  "content": [{"type":"video","video":"sample.mp4"},{"type":"text","text":"Describe this video"}]
}]
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
aud, imgs, vids = process_mm_info(conversation, use_audio_in_video=True)
inputs = processor(text=text, audio=aud, images=imgs, videos=vids, return_tensors="pt", padding=True).to("cuda")
out = model.generate(**inputs).sequences
print(processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

---

## 4. Serving Options

### Option 1 – vLLM API Server

1. **Allocate GPU:**
   ```bash
   salloc -p p_naresh --gres=gpu:1 --time=04:00:00
   ```

2. **Start vLLM (OCI image example):**
   ```bash
   srun -p p_naresh --gres=gpu:1 --container-image=docker.io/vllm/vllm-openai:latest      bash -lc '
       vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct          --dtype auto --tensor-parallel-size 1 --trust-remote-code --port 8000
     '
   ```

3. **Local video server:**
   ```bash
   python -m http.server 8080 --directory ~/datasets/videos &
   ```

4. **Tunnel from laptop & call API:**
   ```bash
   ssh -L 8000:127.0.0.1:8000 naresh@85.234.64.44
   curl http://127.0.0.1:8000/v1/chat/completions      -H "Content-Type: application/json"      -d '{
       "model":"Qwen/Qwen3-Omni-30B-A3B-Instruct",
       "messages":[{
         "role":"user",
         "content":[
           {"type":"text","text":"Describe this video briefly."},
           {"type":"video_url","video_url":{"url":"http://127.0.0.1:8080/sample.mp4"}}
         ]
       }],
       "max_tokens":128
     }'
   ```

### Option 2 – Transformers + FastAPI
If vLLM multimodal gives issues, serve via your own FastAPI app (as shown earlier) using the Transformers API directly.

---

## 5. Resource Planning

| Workload | GPUs | GPU RAM (80 GB each) | System RAM | CPUs |
|-----------|------|----------------------|-------------|------|
| Inference (text only) | 1 H100 | ≤ 80 GB | 64 GB | 16 |
| Longer video + audio | 2 H100 | 160 GB | 128 GB | 32 |
| Training | multi‑GPU (4‑8) |  | 256 GB + | 64 + |

**Tips**
- `model.disable_talker()` saves ~10 GB VRAM (no speech output).  
- Slurm sets `CUDA_VISIBLE_DEVICES`; use GPU 0 inside job.  
- Use BF16/FP16 for lower VRAM usage.  
- If you hit OOM → add `--tensor-parallel-size 2`.

---

## 6. Data Flow Without S3

1. **Store videos** on the **worker** under `~/datasets/videos`.
2. **Serve them locally:** `python -m http.server 8080`.
3. **vLLM fetches via** `http://127.0.0.1:8080/<file>.mp4`.
4. **Laptop** connects to vLLM via SSH tunnel (`localhost:8000`).

---

## 7. Pros & Cons Summary

| Approach | Pros | Cons |
|-----------|------|------|
| **vLLM Server** | Fast, OpenAI‑compatible API, production‑style | Needs URL input for media, multimodal still maturing |
| **Transformers + FastAPI** | Full control, local file access, flexible logic | Manual batching, slower for many requests |
| **Login node** | None (for compute) | No GPUs, not for heavy workloads |

---

## 8. Quick Cheat‑Sheet

| Action | Command |
|--------|----------|
| GPU shell | `salloc -p p_naresh --gres=gpu:1 --cpus-per-task=16 --mem=64G` |
| List jobs | `squeue -u $USER` |
| Cancel job | `scancel <JOBID>` |
| Copy data | `rsync -av ./videos naresh@85.234.64.44:~/datasets/videos/` |
| Start video server | `python -m http.server 8080 --directory ~/datasets/videos` |
| Start vLLM | `vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --port 8000` |
| Test API | `curl http://127.0.0.1:8000/v1/chat/completions ...` |

---

**End of Reference Manual**
