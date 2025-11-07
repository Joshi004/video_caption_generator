Here’s a complete all-in-one cheat sheet with every command you’ll regularly use on your H100 Slurm cluster — including login, job inspection, worker access, monitoring, tunneling, serving files, and running models.

You can safely copy this into a Markdown file (Cluster_Quick_Reference.md) for future use.

⸻

🧭 Cluster Quick Reference — H100 + Slurm + vLLM

⸻

## Login & Basic Info

# Login to cluster
ssh naresh@85.234.64.44

# Check available partitions and nodes
sinfo -s
sinfo -p p_naresh

# View node and GPU details
scontrol show node worker-9 | egrep "NodeName=|State=|Gres=|RealMemory="

# Check your running or queued jobs
squeue -u $USER


⸻

💻 Launching & Managing Jobs

# Start an interactive session with 1 GPU
salloc -p p_naresh --gres=gpu:1 --time=02:00:00 --mem=128G

# Run a one-off GPU command
srun -p p_naresh --gres=gpu:1 --time=00:05:00 nvidia-smi

# Cancel a running job
scancel <JOBID>

# View all running worker nodes for your jobs
squeue -u $USER -o "%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R"
# (shows jobID, partition, name, user, state, time, nodes, nodelist)


⸻

🧠 Monitoring System Resources

# CPU & memory usage
htop

# GPU utilization
nvidia-smi

# Disk space
df -h

# Memory usage
free -h

# Running vLLM or HTTP processes
ps aux | grep vllm
ps aux | grep http.server


⸻

🚀 Running Models (vLLM)

# Start model server on worker
vllm serve Qwen/Qwen2-VL-7B-Instruct \
  --dtype auto \
  --max-model-len 8192 \
  --trust-remote-code \
  --port 8000 --host 0.0.0.0

# Check health
curl -s http://127.0.0.1:8000/health && echo


⸻

🧵 SSH Tunneling (Local <-> Remote)

Forward ports (on your laptop)

# Basic tunnel (blocking terminal)
ssh -L 8000:localhost:8000 naresh@85.234.64.44

# Tunnel both vLLM and video HTTP ports
ssh -L 8000:localhost:8000 -L 8080:localhost:8080 naresh@85.234.64.44

# Run tunnel in background
ssh -fN -o ExitOnForwardFailure=yes \
  -L 8000:worker-9:8000 \
  -L 8080:worker-9:8080 \
  naresh@85.234.64.44

If 8000 is in use

# Use alternate ports
ssh -fN -L 9000:localhost:8000 -L 9090:localhost:8080 naresh@85.234.64.44

Then access:
	•	vLLM → http://127.0.0.1:9000
	•	Videos → http://127.0.0.1:9090

Kill existing tunnels

lsof -i :8000
kill <PID>
pkill -f "ssh -fN -L"


⸻

🎥 Hosting Video Files

# Go to your video directory
cd ~/datasets/videos

# Start HTTP server (foreground)
python3 -m http.server 8080

# Run server in background
nohup python3 -m http.server 8080 > server.log 2>&1 &
# or
tmux new -s videoserver
python3 -m http.server 8080

# Verify
curl -I http://127.0.0.1:8080/

Stop server

pkill -f "http.server"
tmux kill-session -t videoserver


⸻

🧩 Making API Requests (from your laptop)

Text-only

curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2-VL-7B-Instruct",
    "messages": [{"role": "user", "content": [{"type":"text","text":"Say hello"}]}]
  }'

Video captioning

curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"Qwen/Qwen2-VL-7B-Instruct",
    "messages":[{
      "role":"user",
      "content":[
        {"type":"text","text":"Give a one-line caption for this video."},
        {"type":"video_url","video_url":{"url":"http://127.0.0.1:8080/Bill-gates-thankyou.mp4"}}
      ]
    }],
    "max_tokens":64
  }' | jq -r '.choices[0].message.content'


⸻

🔍 Debugging and Logs

# List current jobs
squeue -u $USER

# Get job details
scontrol show job <JOBID>

# View Slurm output logs (if job script used)
cat slurm-<JOBID>.out

# Tail live log (during training/inference)
tail -f slurm-<JOBID>.out


⸻

🧹 Cleanup

# Stop model server
pkill -f vllm

# Stop background HTTP server
pkill -f "http.server"

# Exit interactive session
exit


⸻

🧠 Tips

Task	Command
Reconnect to existing job	squeue -u $USER → note NODELIST → srun --jobid=<JOBID> --pty bash
List all running workers	squeue -u $USER -o "%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R"
Get GPU utilization	watch -n 2 nvidia-smi
Check remaining job time	`scontrol show job 
Quickly free all background servers	pkill -f "http.server"; pkill -f vllm


⸻

Would you like me to generate this as a downloadable Markdown file (Cluster_Quick_Reference.md) so you can keep it in your local repo or home directory on the cluster?