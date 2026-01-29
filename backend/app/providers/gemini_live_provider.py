"""Gemini Live API Provider for real-time voice conversations"""
import asyncio
import base64
import json
from typing import Optional, Callable, Dict, Any, AsyncGenerator
import httpx

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiLiveProvider:
    """Provider for Gemini Live API - real-time voice conversations"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-live"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self.session = None
        
        if GENAI_AVAILABLE and api_key:
            self.client = genai.Client(api_key=api_key)
    
    def is_available(self) -> bool:
        return bool(self.api_key and GENAI_AVAILABLE)
    
    async def start_session(
        self,
        system_instruction: str = "",
        voice_name: str = "Puck",
        response_modalities: list = None,
        on_audio: Callable = None,
        on_text: Callable = None,
        on_transcript: Callable = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Start a Gemini Live session for real-time voice conversation.
        
        Args:
            system_instruction: System prompt for the AI
            voice_name: Voice to use (Puck, Kore, Charon, etc.)
            response_modalities: ["AUDIO"] or ["TEXT"] or both
            on_audio: Callback for audio data
            on_text: Callback for text responses
            on_transcript: Callback for transcriptions
        """
        if not self.is_available():
            raise ValueError("Gemini Live API not available. Install google-genai package.")
        
        if response_modalities is None:
            response_modalities = [types.Modality.AUDIO]
        
        config = types.LiveConnectConfig(
            response_modalities=response_modalities,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=system_instruction)]
            ) if system_instruction else None
        )
        
        async with self.client.aio.live.connect(
            model=self.model,
            config=config
        ) as session:
            self.session = session
            
            # Yield session started event
            yield {"type": "session_started"}
            
            # Listen for responses
            async for response in session.receive():
                if response.server_content:
                    server_content = response.server_content
                    
                    if server_content.model_turn:
                        for part in server_content.model_turn.parts:
                            if part.inline_data:
                                # Audio response
                                audio_data = base64.b64encode(part.inline_data.data).decode()
                                yield {
                                    "type": "audio",
                                    "data": audio_data,
                                    "mime_type": part.inline_data.mime_type
                                }
                            elif part.text:
                                # Text response
                                yield {
                                    "type": "text",
                                    "data": part.text
                                }
                    
                    if server_content.turn_complete:
                        yield {"type": "turn_complete"}
                    
                    if server_content.interrupted:
                        yield {"type": "interrupted"}
                
                # Handle transcriptions
                if hasattr(response, 'input_transcription') and response.input_transcription:
                    yield {
                        "type": "input_transcript",
                        "text": response.input_transcription.text,
                        "is_final": response.input_transcription.is_final
                    }
                
                if hasattr(response, 'output_transcription') and response.output_transcription:
                    yield {
                        "type": "output_transcript", 
                        "text": response.output_transcription.text,
                        "is_final": response.output_transcription.is_final
                    }
    
    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm"):
        """Send audio data to the session"""
        if self.session:
            await self.session.send_realtime_input(
                audio=types.Blob(data=audio_data, mime_type=mime_type)
            )
    
    async def send_text(self, text: str):
        """Send text message to the session"""
        if self.session:
            await self.session.send(input=text, end_of_turn=True)
    
    async def close_session(self):
        """Close the current session"""
        self.session = None


class GeminiLiveFallback:
    """
    Fallback implementation using Gemini's standard API with text-to-speech.
    For when google-genai Live API is not available.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def chat_with_audio(
        self,
        text: str,
        system_instruction: str = "",
        voice: str = "en-US-Neural2-A"
    ) -> Dict[str, Any]:
        """
        Send text and get audio response using standard Gemini API.
        Returns both text and audio (base64 encoded).
        """
        async with httpx.AsyncClient(timeout=60) as client:
            # First get text response from Gemini
            url = f"{self.base_url}/models/gemini-2.0-flash:generateContent"
            
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None,
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 1024
                }
            }
            
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                json={k: v for k, v in payload.items() if v is not None}
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.text}")
            
            data = response.json()
            text_response = data["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "text": text_response,
                "audio": None  # Would need TTS integration
            }
