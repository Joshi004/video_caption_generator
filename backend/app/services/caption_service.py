import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .model_client import ModelServiceClient


class CaptionService:
    """Service for managing video captions"""
    
    def __init__(
        self,
        videos_dir: str = "/app/videos",
        captions_dir: str = "/app/captions",
        model_name: str = "qwen2vl"
    ):
        self.videos_dir = Path(videos_dir)
        self.captions_dir = Path(captions_dir)
        self.model_name = model_name
        self.model_client = ModelServiceClient()
        
        # Ensure directories exist
        self.captions_dir.mkdir(parents=True, exist_ok=True)
    
    def get_caption_path(self, video_filename: str) -> Path:
        """
        Get the caption file path for a video
        Format: {video_filename}_{model_name}.json
        """
        return self.captions_dir / f"{video_filename}_{self.model_name}.json"
    
    def caption_exists(self, video_filename: str) -> bool:
        """Check if caption exists for a video"""
        caption_path = self.get_caption_path(video_filename)
        return caption_path.exists()
    
    def load_caption(self, video_filename: str) -> Optional[Dict[str, Any]]:
        """Load caption data from JSON file"""
        caption_path = self.get_caption_path(video_filename)
        
        if not caption_path.exists():
            return None
        
        try:
            with open(caption_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading caption: {str(e)}")
            return None
    
    def load_all_captions(self, video_filename: str) -> list[Dict[str, Any]]:
        """
        Load captions from all available models for a video
        
        Returns:
            List of caption data dictionaries, one per model that has generated a caption
        """
        from .model_client import AVAILABLE_MODELS
        
        all_captions = []
        
        for model_key, model_config in AVAILABLE_MODELS.items():
            # Construct caption path for this model
            caption_path = self.captions_dir / f"{video_filename}_{model_key}.json"
            
            if caption_path.exists():
                try:
                    with open(caption_path, 'r', encoding='utf-8') as f:
                        caption_data = json.load(f)
                        # Add model key to the data
                        caption_data['model_key'] = model_key
                        caption_data['model_display_name'] = model_config['display_name']
                        all_captions.append(caption_data)
                except Exception as e:
                    print(f"Error loading caption for {model_key}: {str(e)}")
        
        return all_captions
    
    def save_caption(
        self,
        video_filename: str,
        caption: str,
        processing_time: float,
        prompt: str = None,
        model_version: str = "Qwen/Qwen2-VL-7B-Instruct"  # Updated by model_key at generation time
    ) -> Dict[str, Any]:
        """
        Save caption data to JSON file
        
        Args:
            video_filename: Name of the video file
            caption: Generated caption text
            processing_time: Time taken to generate caption
            prompt: Prompt used to generate the caption
            model_version: Version identifier of the model
        
        Returns:
            Caption data dictionary
        """
        caption_data = {
            "filename": video_filename,
            "caption": caption,
            "prompt": prompt,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "processing_time_seconds": processing_time,
            "model_name": self.model_name,
            "model_version": model_version
        }
        
        caption_path = self.get_caption_path(video_filename)
        
        try:
            with open(caption_path, 'w', encoding='utf-8') as f:
                json.dump(caption_data, f, indent=2, ensure_ascii=False)
            
            print(f"Caption saved: {caption_path}")
            return caption_data
        
        except Exception as e:
            raise Exception(f"Failed to save caption: {str(e)}")
    
    def delete_caption(self, video_filename: str) -> bool:
        """Delete caption file"""
        caption_path = self.get_caption_path(video_filename)
        
        if caption_path.exists():
            try:
                caption_path.unlink()
                print(f"Caption deleted: {caption_path}")
                return True
            except Exception as e:
                print(f"Error deleting caption: {str(e)}")
                return False
        
        return False
    
    async def generate_caption(
        self,
        video_filename: str,
        prompt: Optional[str] = None,
        model_key: str = "qwen2vl",
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate caption for a video
        
        Args:
            video_filename: Name of the video file
            prompt: Optional custom prompt
            model_key: Model to use (qwen2vl or omnivinci)
            regenerate: If True, regenerate even if caption exists
        
        Returns:
            Caption data dictionary
        """
        # Update model name for this request
        self.model_name = model_key
        
        # Check if caption already exists for this model
        if not regenerate and self.caption_exists(video_filename):
            existing_caption = self.load_caption(video_filename)
            if existing_caption:
                return existing_caption
        
        # Note: Videos are stored remotely, no local path check needed
        # The video filename is passed to the model client which constructs the remote URL
        
        # Create model client for selected model
        from .model_client import VLLMClient
        model_client = VLLMClient(model_key=model_key)
        
        # Generate caption using vLLM service
        result = await model_client.generate_caption(
            video_filename,
            prompt=prompt
        )
        
        # Save caption with prompt
        caption_data = self.save_caption(
            video_filename=video_filename,
            caption=result["caption"],
            processing_time=result["processing_time"],
            prompt=prompt
        )
        
        return caption_data


