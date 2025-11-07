import httpx
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path


# Model configuration
AVAILABLE_MODELS = {
    "qwen2vl": {
        "name": "Qwen/Qwen2-VL-7B-Instruct",
        "url": os.getenv("QWEN2VL_API_URL", "http://localhost:8000"),
        "display_name": "Qwen2-VL-7B",
        "short_name": "qwen2vl"
    },
    "omnivinci": {
        "name": "nvidia/omnivinci",
        "url": os.getenv("OMNIVINCI_API_URL", "http://localhost:8001"),
        "display_name": "OmniVinci",
        "short_name": "omnivinci"
    },
    "qwen3omni": {
        "name": "/home/naresh/models/qwen3-omni-30b",
        "url": os.getenv("QWEN3OMNI_API_URL", "http://localhost:8002"),
        "display_name": "Qwen3-Omni-30B",
        "short_name": "qwen3omni"
    }
}


class VLLMClient:
    """HTTP client for communicating with remote vLLM service via OpenAI-compatible API"""
    
    def __init__(self, model_key: str = "qwen2vl", video_url_base: str = None):
        """
        Initialize vLLM client for a specific model
        
        Args:
            model_key: Key from AVAILABLE_MODELS ('qwen2vl' or 'omnivinci')
            video_url_base: Base URL for video HTTP server
        """
        if model_key not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}")
        
        self.model_config = AVAILABLE_MODELS[model_key]
        self.vllm_url = self.model_config["url"]
        self.model_name = self.model_config["name"]
        self.model_key = model_key
        
        # Video URL base - use localhost:8080 for remote vLLM to access video HTTP server on worker-9
        # Not host.docker.internal - that's only for backend to access Mac's tunneled services
        self.video_url_base = "http://127.0.0.1:8080"
        self.timeout = 300.0  # 5 minutes timeout for video processing
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if vLLM service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.vllm_url}/v1/models")
                response.raise_for_status()
                models_data = response.json()
                return {
                    "status": "healthy",
                    "model_loaded": True,
                    "models": models_data.get("data", [])
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.vllm_url}/v1/models")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Failed to get model info: {str(e)}")
    
    async def generate_caption(
        self,
        video_filename: str,
        prompt: str = None
    ) -> Dict[str, Any]:
        """
        Generate caption for video using model-specific API
        
        Args:
            video_filename: Name of the video file (accessible via remote HTTP server)
            prompt: Optional custom prompt
        
        Returns:
            Dictionary with caption and metadata
        """
        # Construct video URL for model to access
        video_url = f"{self.video_url_base}/{video_filename}"
        
        # Default prompt if none provided
        if not prompt:
            prompt = "Describe this video in detail, including what you see, hear, and any actions taking place."
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # OmniVinci uses custom /infer/video endpoint with form data
                if self.model_key == "omnivinci":
                    response = await client.post(
                        f"{self.vllm_url}/infer/video",
                        data={"url": video_url, "prompt": prompt}
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    processing_time = time.time() - start_time
                    
                    # Extract caption from OmniVinci response
                    caption = result.get("response", result.get("caption", ""))
                    
                    return {
                        "caption": caption,
                        "processing_time": processing_time,
                        "model": self.model_name,
                        "tokens_used": {}
                    }
                
                # Other models use vLLM OpenAI-compatible API
                else:
                    request_payload = {
                        "model": self.model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "video_url", "video_url": {"url": video_url}}
                                ]
                            }
                        ],
                        "max_tokens": 512,
                        "temperature": 0.7
                    }
                    
                    response = await client.post(
                        f"{self.vllm_url}/v1/chat/completions",
                        json=request_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    processing_time = time.time() - start_time
                    
                    # Extract caption from OpenAI response format
                    caption = result["choices"][0]["message"]["content"]
                    
                    return {
                        "caption": caption,
                        "processing_time": processing_time,
                        "model": self.model_name,
                        "tokens_used": result.get("usage", {})
                    }
        
        except httpx.TimeoutException:
            raise Exception("Model service request timed out (>5 minutes)")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise Exception(f"vLLM service error: {e.response.status_code} - {error_detail}")
        except Exception as e:
            raise Exception(f"Failed to generate caption: {str(e)}")


def get_available_models() -> Dict[str, Any]:
    """Get list of available models"""
    return {
        key: {
            "name": config["name"],
            "display_name": config["display_name"],
            "short_name": config["short_name"],
            "url": config["url"]
        }
        for key, config in AVAILABLE_MODELS.items()
    }


# Alias for backward compatibility
ModelServiceClient = VLLMClient


