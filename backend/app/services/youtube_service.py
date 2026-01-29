"""
YouTube Service
Extract transcripts and chat with YouTube videos
"""
from typing import Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import re


class YouTubeService:
    """Service for YouTube video analysis"""
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'(?:youtube\.com\/shorts\/)([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def get_transcript(
        self, 
        video_url: str,
        languages: list = ['en', 'en-US', 'hi']
    ) -> Dict[str, Any]:
        """
        Get transcript from a YouTube video
        
        Args:
            video_url: YouTube video URL
            languages: Preferred languages for transcript
            
        Returns:
            Dict with transcript and metadata
        """
        video_id = self.extract_video_id(video_url)
        
        if not video_id:
            return {
                "success": False,
                "error": "Invalid YouTube URL",
                "video_id": None
            }
        
        try:
            # Try to get transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try manual transcripts first, then auto-generated
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except:
                    continue
            
            if not transcript:
                # Get any available transcript
                transcript = transcript_list.find_generated_transcript(languages)
            
            if not transcript:
                # Last resort: get first available
                for t in transcript_list:
                    transcript = t
                    break
            
            if transcript:
                transcript_data = transcript.fetch()
                
                # Combine transcript text
                full_text = " ".join([entry['text'] for entry in transcript_data])
                
                # Create timestamped segments
                segments = []
                for entry in transcript_data:
                    segments.append({
                        "text": entry['text'],
                        "start": entry['start'],
                        "duration": entry.get('duration', 0)
                    })
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "language": transcript.language,
                    "full_text": full_text,
                    "segments": segments,
                    "word_count": len(full_text.split())
                }
            else:
                return {
                    "success": False,
                    "error": "No transcript available for this video",
                    "video_id": video_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id
            }
    
    async def summarize_for_context(
        self, 
        video_url: str,
        max_length: int = 4000
    ) -> Dict[str, Any]:
        """
        Get video transcript formatted for AI context
        
        Args:
            video_url: YouTube video URL
            max_length: Maximum context length
            
        Returns:
            Dict with context-ready transcript
        """
        result = await self.get_transcript(video_url)
        
        if not result["success"]:
            return result
        
        full_text = result["full_text"]
        
        # Truncate if needed
        if len(full_text) > max_length:
            full_text = full_text[:max_length] + "... [transcript truncated]"
        
        return {
            "success": True,
            "video_id": result["video_id"],
            "context": full_text,
            "language": result["language"],
            "word_count": result["word_count"]
        }


# Global instance
youtube_service = YouTubeService()
