"""
Image Generation Service
Generate images using various AI models
"""
import base64
import httpx
from typing import Dict, Any, Optional


class ImageGenerationService:
    """Service for AI image generation"""
    
    def __init__(self):
        self.openai_api_key: Optional[str] = None
    
    def set_api_key(self, api_key: str):
        """Set OpenAI API key for DALL-E"""
        self.openai_api_key = api_key
    
    async def generate_dalle(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3
        
        Args:
            prompt: Image description
            size: Image size (1024x1024, 1792x1024, or 1024x1792)
            quality: standard or hd
            n: Number of images
            
        Returns:
            Dict with generated image data
        """
        if not self.openai_api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": n,
                        "size": size,
                        "quality": quality,
                        "response_format": "url"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    images = []
                    for img in data.get("data", []):
                        images.append({
                            "url": img.get("url"),
                            "revised_prompt": img.get("revised_prompt", prompt)
                        })
                    
                    return {
                        "success": True,
                        "images": images,
                        "prompt": prompt
                    }
                else:
                    error_data = response.json()
                    return {
                        "success": False,
                        "error": error_data.get("error", {}).get("message", "Unknown error")
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_with_bytez(
        self,
        prompt: str,
        api_key: str,
        model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    ) -> Dict[str, Any]:
        """
        Generate image using Bytez API (Stable Diffusion)
        
        Args:
            prompt: Image description
            api_key: Bytez API key
            model: Model to use
            
        Returns:
            Dict with generated image data
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"https://api.bytez.com/model/{model}/infer",
                    headers={
                        "Authorization": f"Key {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "num_inference_steps": 30
                    }
                )
                
                if response.status_code == 200:
                    # Response is image bytes
                    image_data = base64.b64encode(response.content).decode('utf-8')
                    return {
                        "success": True,
                        "images": [{
                            "base64": image_data,
                            "format": "png"
                        }],
                        "prompt": prompt,
                        "model": model
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
image_service = ImageGenerationService()
