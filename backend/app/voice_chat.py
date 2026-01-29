"""Voice Chat WebSocket Handler for real-time audio conversations"""
import asyncio
import base64
import json
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import httpx


@dataclass
class VoiceChatConfig:
    """Configuration for voice chat session"""
    system_instruction: str = ""
    language: str = "English"
    from_language: str = "English"
    mode: str = "teacher"  # teacher or immersive
    mission: Optional[Dict] = None
    voice_name: str = "Puck"
    enable_transcription: bool = True


class VoiceChatHandler:
    """
    Handles voice chat sessions using text-based AI with TTS/STT.
    Falls back to this when Gemini Live API is not available.
    """
    
    def __init__(self, providers: dict, groq_api_key: str = None):
        self.providers = providers
        self.groq_api_key = groq_api_key
        self.active_sessions: Dict[str, Dict] = {}
    
    async def create_session(self, session_id: str, config: VoiceChatConfig) -> Dict:
        """Create a new voice chat session"""
        
        # Build system instruction based on mission and mode
        system_instruction = self._build_system_instruction(config)
        
        self.active_sessions[session_id] = {
            "config": config,
            "system_instruction": system_instruction,
            "conversation_history": [],
            "audio_queue": asyncio.Queue(),
            "active": True
        }
        
        return {
            "type": "session_created",
            "session_id": session_id,
            "config": {
                "language": config.language,
                "mode": config.mode,
                "mission": config.mission["title"] if config.mission else None
            }
        }
    
    def _build_system_instruction(self, config: VoiceChatConfig) -> str:
        """Build system instruction based on mode and mission"""
        
        if not config.mission:
            return config.system_instruction or "You are a helpful language learning assistant."
        
        mission = config.mission
        language = config.language
        from_language = config.from_language
        
        if config.mode == "teacher":
            return f"""ROLEPLAY INSTRUCTION:
You are acting as **{mission.get('persona', 'a native speaker')}**, helping someone learn {language}.
The user is a language learner (native speaker of {from_language}) trying to: "{mission.get('title')}" ({mission.get('situation')}).

TEACHING GUIDELINES:
1. Be encouraging and patient. This is a learning experience.
2. When the user makes mistakes, gently correct them and explain the grammar/vocabulary in {from_language}.
3. Provide translations when asked or when the user seems stuck.
4. If the user uses {from_language}, respond in {from_language} first with guidance, then demonstrate in {language}.
5. Use simple, clear {language} appropriate for a learner.

MISSION OBJECTIVES:
{chr(10).join(f"- {obj}" for obj in mission.get('objectives', []))}

When objectives are complete, congratulate the user and provide 3 learning tips."""

        else:  # immersive mode
            return f"""ROLEPLAY INSTRUCTION:
You are acting as **{mission.get('persona', 'a native speaker')}**, a native speaker of {language}.
The user is a language learner trying to: "{mission.get('title')}" ({mission.get('situation')}).
Your goal is to play your role naturally. Do not act as an AI assistant. Act as the person.

INTERACTION GUIDELINES:
1. ONLY speak in {language}. Do not use {from_language} at all.
2. If the user speaks {from_language}, look confused and ask them (in {language}) to speak {language}.
3. Be helpful but strict about language practice.
4. Speak naturally as a native speaker would in this situation.
5. Keep responses conversational and realistic.

MISSION OBJECTIVES for the user to achieve:
{chr(10).join(f"- {obj}" for obj in mission.get('objectives', []))}

When objectives are complete, congratulate them enthusiastically in {language}."""
    
    async def process_audio_message(
        self, 
        session_id: str, 
        audio_data: str,  # Base64 encoded
        mime_type: str = "audio/webm"
    ):
        """
        Process incoming audio from user.
        Uses speech-to-text, then AI response, then text-to-speech.
        Yields multiple messages as async generator.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            yield {"type": "error", "message": "Session not found"}
            return
        
        try:
            # 1. Speech-to-text (using Groq Whisper if available)
            transcript = await self._speech_to_text(audio_data, mime_type)
            
            # Send transcript to client
            yield {
                "type": "input_transcript",
                "text": transcript,
                "is_final": True
            }
            
            # 2. Get AI response
            response_text = await self._get_ai_response(session, transcript)
            
            # Send text response
            yield {
                "type": "text",
                "data": response_text
            }
            
            # Send output transcript
            yield {
                "type": "output_transcript",
                "text": response_text,
                "is_final": True
            }
            
            # 3. Text-to-speech (if TTS available)
            # For now, we'll just return text - TTS can be added via browser Web Speech API
            
            yield {"type": "turn_complete"}
            
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    async def process_text_message(self, session_id: str, text: str) -> Dict:
        """Process text message from user"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"type": "error", "message": "Session not found"}
        
        try:
            response_text = await self._get_ai_response(session, text)
            
            return {
                "type": "text",
                "data": response_text
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def _speech_to_text(self, audio_data: str, mime_type: str) -> str:
        """Convert speech to text using Groq Whisper API"""
        if not self.groq_api_key:
            raise ValueError("Speech-to-text requires Groq API key")
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Groq Whisper API
            files = {
                'file': ('audio.webm', audio_bytes, mime_type),
                'model': (None, 'whisper-large-v3'),
            }
            
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.groq_api_key}"},
                files=files
            )
            
            if response.status_code != 200:
                raise Exception(f"Whisper API error: {response.text}")
            
            return response.json().get("text", "")
    
    async def _get_ai_response(self, session: Dict, user_message: str) -> str:
        """Get AI response using best available provider"""
        from app.providers.base import Message
        
        # Add to conversation history
        session["conversation_history"].append({
            "role": "user",
            "content": user_message
        })
        
        # Build messages
        messages = [Message(role="system", content=session["system_instruction"])]
        for msg in session["conversation_history"][-10:]:  # Keep last 10 exchanges
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        # Try providers in order: groq (fastest), deepseek, openrouter
        provider_order = ["groq", "deepseek", "openrouter", "gemini"]
        
        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if provider and provider.is_available():
                try:
                    response = await provider.chat(messages)
                    
                    # Add to history
                    session["conversation_history"].append({
                        "role": "assistant",
                        "content": response.content
                    })
                    
                    return response.content
                except Exception as e:
                    print(f"Provider {provider_name} failed: {e}")
                    continue
        
        raise ValueError("No AI providers available")
    
    def end_session(self, session_id: str):
        """End a voice chat session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["active"] = False
            del self.active_sessions[session_id]
            return {"type": "session_ended", "session_id": session_id}
        return {"type": "error", "message": "Session not found"}
