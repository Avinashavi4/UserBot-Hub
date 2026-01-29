"""
Vision Analysis Service
Analyze images and PDFs using AI vision models
"""
import base64
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path


class VisionService:
    """Service for AI vision analysis"""
    
    def __init__(self):
        self.gemini_api_key: Optional[str] = None
        self.openai_api_key: Optional[str] = None
    
    def set_gemini_key(self, api_key: str):
        """Set Gemini API key"""
        self.gemini_api_key = api_key
    
    def set_openai_key(self, api_key: str):
        """Set OpenAI API key"""
        self.openai_api_key = api_key
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64"""
        return base64.standard_b64encode(image_bytes).decode("utf-8")
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf"
        }
        return mime_types.get(ext, "image/jpeg")
    
    async def analyze_with_gemini(
        self,
        image_bytes: bytes,
        filename: str,
        prompt: str = "Describe this image in detail.",
        model: str = "gemini-2.0-flash"
    ) -> Dict[str, Any]:
        """
        Analyze image using Gemini Vision
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename
            prompt: Analysis prompt
            model: Gemini model to use
            
        Returns:
            Dict with analysis results
        """
        if not self.gemini_api_key:
            return {
                "success": False,
                "error": "Gemini API key not configured"
            }
        
        try:
            image_b64 = self._encode_image(image_bytes)
            mime_type = self._get_mime_type(filename)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    params={"key": self.gemini_api_key},
                    json={
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": image_b64
                                    }
                                }
                            ]
                        }],
                        "generationConfig": {
                            "temperature": 0.4,
                            "maxOutputTokens": 8192
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "success": True,
                        "analysis": text,
                        "model": model
                    }
                else:
                    error = response.json()
                    return {
                        "success": False,
                        "error": error.get("error", {}).get("message", "Unknown error")
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_with_gpt4(
        self,
        image_bytes: bytes,
        filename: str,
        prompt: str = "Describe this image in detail."
    ) -> Dict[str, Any]:
        """
        Analyze image using GPT-4 Vision
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename
            prompt: Analysis prompt
            
        Returns:
            Dict with analysis results
        """
        if not self.openai_api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }
        
        try:
            image_b64 = self._encode_image(image_bytes)
            mime_type = self._get_mime_type(filename)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{image_b64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 4096
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "analysis": text,
                        "model": "gpt-4o"
                    }
                else:
                    error = response.json()
                    return {
                        "success": False,
                        "error": error.get("error", {}).get("message", "Unknown error")
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_multiple_images(
        self,
        images: List[Dict[str, Any]],
        prompt: str,
        provider: str = "gemini"
    ) -> Dict[str, Any]:
        """
        Analyze multiple images together
        
        Args:
            images: List of dicts with 'bytes' and 'filename' keys
            prompt: Analysis prompt
            provider: 'gemini' or 'openai'
            
        Returns:
            Dict with combined analysis
        """
        if provider == "gemini":
            if not self.gemini_api_key:
                return {"success": False, "error": "Gemini API key not configured"}
            
            try:
                parts = [{"text": prompt}]
                for img in images:
                    parts.append({
                        "inline_data": {
                            "mime_type": self._get_mime_type(img["filename"]),
                            "data": self._encode_image(img["bytes"])
                        }
                    })
                
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                        params={"key": self.gemini_api_key},
                        json={
                            "contents": [{"parts": parts}],
                            "generationConfig": {
                                "temperature": 0.4,
                                "maxOutputTokens": 8192
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return {
                            "success": True,
                            "analysis": text,
                            "image_count": len(images)
                        }
                    else:
                        error = response.json()
                        return {
                            "success": False,
                            "error": error.get("error", {}).get("message", "Unknown error")
                        }
                        
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        else:
            return {"success": False, "error": f"Provider {provider} not supported for multi-image"}
    
    async def extract_text_from_image(
        self,
        image_bytes: bytes,
        filename: str,
        provider: str = "gemini"
    ) -> Dict[str, Any]:
        """
        Extract text (OCR) from image
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename
            provider: 'gemini' or 'openai'
            
        Returns:
            Dict with extracted text
        """
        prompt = """Extract all text visible in this image. 
        Return the text exactly as it appears, preserving formatting where possible.
        If there's no text, respond with 'No text found in image.'"""
        
        if provider == "gemini":
            return await self.analyze_with_gemini(image_bytes, filename, prompt)
        else:
            return await self.analyze_with_gpt4(image_bytes, filename, prompt)


# Global instance
vision_service = VisionService()
