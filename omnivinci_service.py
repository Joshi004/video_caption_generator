#!/usr/bin/env python3
"""
OmniVinci FastAPI Service
Runs OmniVinci model using Transformers (vLLM doesn't support it yet)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
import uvicorn
import httpx
import tempfile
import os
from transformers import AutoProcessor, AutoModel, AutoConfig

app = FastAPI(title="OmniVinci Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model and processor
model = None
processor = None
model_name = "nvidia/omnivinci"

class ChatMessage(BaseModel):
    role: str
    content: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    id: str
    object: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@app.on_event("startup")
async def load_model():
    """Load OmniVinci model on startup"""
    global model, processor
    
    print(f"Loading model: {model_name}")
    
    try:
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        
        model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        
        # Configure for video processing
        model.config.load_audio_in_video = True
        processor.config.load_audio_in_video = True
        model.config.num_video_frames = 128
        processor.config.num_video_frames = 128
        model.config.audio_chunk_length = "max_3600"
        processor.config.audio_chunk_length = "max_3600"
        
        print(f"Model loaded successfully on {model.device}")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "model_name": model_name
    }

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    return {
        "object": "list",
        "data": [
            {
                "id": model_name,
                "object": "model",
                "owned_by": "nvidia",
                "permission": []
            }
        ]
    }

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Generate caption for video (OpenAI-compatible API)"""
    
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Extract content from first message
        message = request.messages[0]
        text_content = ""
        video_url = None
        
        for item in message.content:
            if item.get("type") == "text":
                text_content = item.get("text", "")
            elif item.get("type") == "video_url":
                video_url = item.get("video_url", {}).get("url")
        
        if not video_url:
            raise HTTPException(status_code=400, detail="No video_url provided")
        
        # Download video from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(response.content)
                video_path = tmp.name
        
        try:
            # Prepare conversation for OmniVinci
            conversation = [{
                "role": "user",
                "content": [
                    {"type": "video", "video": video_path},
                    {"type": "text", "text": text_content}
                ]
            }]
            
            # Process with OmniVinci
            text = processor.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
            inputs = processor([text])
            
            # Generate
            with torch.no_grad():
                output_ids = model.generate(
                    input_ids=inputs.input_ids,
                    media=getattr(inputs, 'media', None),
                    media_config=getattr(inputs, 'media_config', None),
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            
            # Decode output
            caption = processor.tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
            
            # Clean up temp file
            os.unlink(video_path)
            
            # Return OpenAI-compatible response
            return ChatResponse(
                id="chat-" + str(hash(caption))[:16],
                object="chat.completion",
                model=model_name,
                choices=[
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": caption
                        },
                        "finish_reason": "stop"
                    }
                ],
                usage={
                    "prompt_tokens": 0,
                    "completion_tokens": len(caption.split()),
                    "total_tokens": len(caption.split())
                }
            )
            
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(video_path):
                os.unlink(video_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)




