"""ClawdBot Hub - Multi-Model AI Gateway"""
from fastapi import FastAPI, HTTPException, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import uuid
import asyncio

from app.config import settings, PROVIDERS
from app.router import QueryRouter
from app.providers import (
    ClaudeProvider,
    OpenAIProvider,
    GeminiProvider,
    HuggingFaceProvider,
    PerplexityProvider,
    BytezProvider,
    OpenRouterProvider,
    GroqProvider,
    CerebrasProvider,
    DeepSeekProvider
)
from app.providers.base import Message
from app.voice_chat import VoiceChatHandler, VoiceChatConfig

# Import tools for advanced features
from app.tools.web_search import WebSearchTool, DuckDuckGoSearch
from app.tools.code_executor import CodeExecutor
from app.tools.rag_system import RAGSystem

# Initialize tools
web_search = WebSearchTool()
ddg_search = DuckDuckGoSearch()
code_executor = CodeExecutor()
rag_system = RAGSystem(storage_path="data/rag")

# Initialize FastAPI app
app = FastAPI(
    title="UserBot Hub",
    description="Multi-Model AI Gateway - Routes to the best AI for your query",
    version="1.0.0"
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize providers
providers = {
    "claude": ClaudeProvider(settings.anthropic_api_key),
    "openai": OpenAIProvider(settings.openai_api_key),
    "gemini": GeminiProvider(settings.google_api_key),
    "huggingface": HuggingFaceProvider(settings.huggingface_api_key),
    "perplexity": PerplexityProvider(settings.perplexity_api_key),
    "bytez": BytezProvider(settings.bytez_api_key),
    "openrouter": OpenRouterProvider(settings.openrouter_api_key),
    "groq": GroqProvider(settings.groq_api_key),
    "cerebras": CerebrasProvider(settings.cerebras_api_key),
    "deepseek": DeepSeekProvider(settings.deepseek_api_key),
}

# Get available providers (those with valid API keys)
available_providers = [name for name, provider in providers.items() if provider.is_available()]

# Initialize router
query_router = QueryRouter(available_providers)

# Initialize voice chat handler
voice_chat_handler = VoiceChatHandler(providers, settings.groq_api_key)

# Load missions data
import os
missions_file = os.path.join(os.path.dirname(__file__), 'data', 'missions.json')
with open(missions_file, 'r', encoding='utf-8') as f:
    MISSIONS_DATA = json.load(f)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []
    preferred_provider: Optional[str] = None
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    category: str
    routing_explanation: str
    tokens_used: Optional[int] = None


class ProviderStatus(BaseModel):
    name: str
    available: bool
    models: List[str]
    strengths: List[str]


# API Endpoints
@app.get("/")
async def root():
    """Health check and API info"""
    return {
        "name": "UserBot Hub",
        "status": "running",
        "available_providers": available_providers,
        "version": "1.0.0"
    }


@api_router.get("/providers", response_model=List[ProviderStatus])
async def list_providers():
    """List all configured providers and their status"""
    result = []
    for name, info in PROVIDERS.items():
        result.append(ProviderStatus(
            name=info["name"],
            available=name in available_providers,
            models=info["models"],
            strengths=info["strengths"]
        ))
    return result


@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to ClawdBot Hub
    
    The system automatically routes to the best AI model based on your query,
    or you can specify a preferred provider.
    """
    if not available_providers:
        raise HTTPException(
            status_code=503,
            detail="No AI providers configured. Please add API keys to .env file."
        )
    
    try:
        # Route the query
        provider_name, model, category = query_router.route(
            request.message, 
            request.preferred_provider
        )
        
        # Build messages list
        messages = []
        for msg in request.conversation_history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        messages.append(Message(role="user", content=request.message))
        
        # Get provider and send request
        provider = providers[provider_name]
        print(f"Routing to {provider_name} with model {model}")
        response = await provider.chat(messages, model)
        
        # Get routing explanation
        explanation = query_router.get_routing_explanation(
            request.message, provider_name, category
        )
        
        return ChatResponse(
            response=response.content,
            provider=provider_name,
            model=model,
            category=category,
            routing_explanation=explanation,
            tokens_used=response.tokens_used
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream a response from ClawdBot Hub
    
    Returns a Server-Sent Events stream with the AI response.
    """
    if not available_providers:
        raise HTTPException(
            status_code=503,
            detail="No AI providers configured."
        )
    
    try:
        # Route the query
        provider_name, model, category = query_router.route(
            request.message,
            request.preferred_provider
        )
        
        # Build messages
        messages = []
        for msg in request.conversation_history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        messages.append(Message(role="user", content=request.message))
        
        provider = providers[provider_name]
        
        async def generate():
            # Send metadata first
            metadata = {
                "provider": provider_name,
                "model": model,
                "category": category
            }
            yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"
            
            # Stream content
            async for chunk in provider.stream_chat(messages, model):
                yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/models/{provider}")
async def get_provider_models(provider: str):
    """Get available models for a specific provider"""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    
    return {
        "provider": provider,
        "models": PROVIDERS[provider]["models"],
        "available": provider in available_providers
    }


# ============== LANGUAGE LEARNING ENDPOINTS ==============

@api_router.get("/missions")
async def get_missions():
    """Get all available language learning missions"""
    return MISSIONS_DATA["missions"]


@api_router.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    """Get a specific mission by ID"""
    for mission in MISSIONS_DATA["missions"]:
        if mission["id"] == mission_id:
            return mission
    raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found")


@api_router.get("/languages")
async def get_languages():
    """Get supported languages for learning"""
    return MISSIONS_DATA["languages"]


@api_router.get("/learning-modes")
async def get_learning_modes():
    """Get available learning modes (Teacher/Immersive)"""
    return MISSIONS_DATA["modes"]


# ============== VOICE CHAT ENDPOINTS ==============

class VoiceSessionRequest(BaseModel):
    """Request to start a voice chat session"""
    mission_id: Optional[str] = None
    language: str = "Spanish"
    from_language: str = "English"
    mode: str = "teacher"  # teacher or immersive
    custom_instruction: Optional[str] = None


class VoiceSessionResponse(BaseModel):
    session_id: str
    mission: Optional[dict] = None
    language: str
    mode: str


@api_router.post("/voice/session", response_model=VoiceSessionResponse)
async def create_voice_session(request: VoiceSessionRequest):
    """Create a new voice chat session for language learning"""
    session_id = str(uuid.uuid4())
    
    # Get mission if specified
    mission = None
    if request.mission_id:
        for m in MISSIONS_DATA["missions"]:
            if m["id"] == request.mission_id:
                mission = m
                break
    
    config = VoiceChatConfig(
        system_instruction=request.custom_instruction or "",
        language=request.language,
        from_language=request.from_language,
        mode=request.mode,
        mission=mission
    )
    
    await voice_chat_handler.create_session(session_id, config)
    
    return VoiceSessionResponse(
        session_id=session_id,
        mission=mission,
        language=request.language,
        mode=request.mode
    )


@api_router.delete("/voice/session/{session_id}")
async def end_voice_session(session_id: str):
    """End a voice chat session"""
    result = voice_chat_handler.end_session(session_id)
    if result.get("type") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


class TextMessageRequest(BaseModel):
    text: str


@api_router.post("/voice/session/{session_id}/text")
async def send_voice_text(session_id: str, request: TextMessageRequest):
    """Send a text message in a voice chat session (for testing/fallback)"""
    result = await voice_chat_handler.process_text_message(session_id, request.text)
    if result.get("type") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# WebSocket for real-time voice chat
@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice chat.
    
    Client sends:
    - {"type": "audio", "data": "<base64_audio>", "mime_type": "audio/webm"}
    - {"type": "text", "data": "<text_message>"}
    - {"type": "end"}
    
    Server sends:
    - {"type": "input_transcript", "text": "...", "is_final": true/false}
    - {"type": "output_transcript", "text": "...", "is_final": true/false}
    - {"type": "text", "data": "AI response text"}
    - {"type": "turn_complete"}
    - {"type": "error", "message": "..."}
    """
    await websocket.accept()
    
    # Verify session exists
    if session_id not in voice_chat_handler.active_sessions:
        await websocket.send_json({"type": "error", "message": "Session not found. Create a session first via POST /api/voice/session"})
        await websocket.close()
        return
    
    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})
        
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "audio":
                # Process audio message
                audio_data = data.get("data")
                mime_type = data.get("mime_type", "audio/webm")
                
                async for response in voice_chat_handler.process_audio_message(
                    session_id, audio_data, mime_type
                ):
                    await websocket.send_json(response)
                    
            elif msg_type == "text":
                # Process text message
                text = data.get("data")
                result = await voice_chat_handler.process_text_message(session_id, text)
                await websocket.send_json(result)
                await websocket.send_json({"type": "turn_complete"})
                
            elif msg_type == "end":
                voice_chat_handler.end_session(session_id)
                await websocket.send_json({"type": "session_ended"})
                break
                
    except WebSocketDisconnect:
        voice_chat_handler.end_session(session_id)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# Include API router
app.include_router(api_router)


# ========== NEW TOOL ENDPOINTS ==========

# Web Search
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

@api_router.post("/search")
async def web_search_endpoint(request: SearchRequest):
    """Search the web using DuckDuckGo (no API key needed)"""
    try:
        results = await web_search.search(request.query, request.max_results)
        return {
            "success": True,
            "query": request.query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/search/instant")
async def instant_answer(query: str):
    """Get instant answer from DuckDuckGo"""
    result = await ddg_search.instant_answer(query)
    return result


# Code Execution
class CodeRequest(BaseModel):
    code: str
    variables: Optional[dict] = None

class CalculateRequest(BaseModel):
    expression: str

@api_router.post("/execute")
async def execute_code(request: CodeRequest):
    """Execute Python code safely for data analysis"""
    result = code_executor.execute(request.code, request.variables)
    return result

@api_router.post("/calculate")
async def calculate(request: CalculateRequest):
    """Evaluate a mathematical expression"""
    result = code_executor.calculate(request.expression)
    return result


# RAG System
class DocumentRequest(BaseModel):
    content: str
    metadata: Optional[dict] = None

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

@api_router.post("/rag/add")
async def add_document(request: DocumentRequest):
    """Add a document to the knowledge base"""
    try:
        doc_ids = rag_system.add_text(request.content, request.metadata)
        return {
            "success": True,
            "doc_ids": doc_ids,
            "chunks_added": len(doc_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/rag/query")
async def query_rag(request: QueryRequest):
    """Query the knowledge base"""
    try:
        result = rag_system.query(request.question, request.top_k)
        return {
            "success": True,
            "question": request.question,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/rag/stats")
async def rag_stats():
    """Get RAG system statistics"""
    return rag_system.get_stats()

@api_router.delete("/rag/clear")
async def clear_rag():
    """Clear all documents from knowledge base"""
    rag_system.clear()
    return {"success": True, "message": "Knowledge base cleared"}


# ========== NEW AI HUB SERVICES ==========
from fastapi import UploadFile, File, Form
from app.services.rag_service import rag_service
from app.services.web_search_service import web_search_service
from app.services.youtube_service import youtube_service
from app.services.image_service import image_service
from app.services.vision_service import vision_service
from app.services.memory_service import memory_service

# Configure services with API keys
image_service.set_api_key(settings.openai_api_key)
vision_service.set_gemini_key(settings.google_api_key)
vision_service.set_openai_key(settings.openai_api_key)


# ========== DOCUMENT CHAT (RAG) ENDPOINTS ==========

@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: Optional[str] = Form("default")
):
    """Upload a document for RAG (PDF, TXT, MD)"""
    try:
        content = await file.read()
        result = rag_service.add_document(content, file.filename, collection)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DocumentQueryRequest(BaseModel):
    query: str
    collection: Optional[str] = "default"
    top_k: Optional[int] = 5


@api_router.post("/documents/query")
async def query_documents(request: DocumentQueryRequest):
    """Query uploaded documents"""
    try:
        result = rag_service.query(request.query, request.collection, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/documents/list")
async def list_documents(collection: str = "default"):
    """List all documents in a collection"""
    return rag_service.list_documents(collection)


@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, collection: str = "default"):
    """Delete a specific document"""
    result = rag_service.delete_document(doc_id, collection)
    if result["success"]:
        return result
    raise HTTPException(status_code=404, detail=result.get("error", "Document not found"))


@api_router.delete("/documents/clear/{collection}")
async def clear_documents(collection: str = "default"):
    """Clear all documents from a collection"""
    return rag_service.clear_all(collection)


# ========== WEB SEARCH ENDPOINTS ==========

class WebSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    region: Optional[str] = "wt-wt"


@api_router.post("/web/search")
async def search_web(request: WebSearchRequest):
    """Search the web using DuckDuckGo"""
    try:
        result = await web_search_service.search(
            request.query, 
            request.max_results, 
            request.region
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/web/news")
async def search_news(request: WebSearchRequest):
    """Search news articles"""
    try:
        result = await web_search_service.news_search(
            request.query,
            request.max_results,
            request.region
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== YOUTUBE ENDPOINTS ==========

class YouTubeRequest(BaseModel):
    url: str


@api_router.post("/youtube/transcript")
async def get_youtube_transcript(request: YouTubeRequest):
    """Get transcript from a YouTube video"""
    try:
        video_id = youtube_service.extract_video_id(request.url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        result = youtube_service.get_transcript(video_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class YouTubeChatRequest(BaseModel):
    url: str
    question: str
    preferred_provider: Optional[str] = None


@api_router.post("/youtube/chat")
async def chat_with_youtube(request: YouTubeChatRequest):
    """Chat about a YouTube video"""
    try:
        video_id = youtube_service.extract_video_id(request.url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        transcript_result = youtube_service.get_transcript(video_id)
        if not transcript_result.get("success"):
            return transcript_result
        
        # Get summarized context
        context = youtube_service.summarize_for_context(
            transcript_result["transcript"], 
            max_chars=8000
        )
        
        prompt = f"""Based on this YouTube video transcript, answer the question.

VIDEO: {transcript_result.get('title', 'Unknown')}

TRANSCRIPT:
{context}

QUESTION: {request.question}

Provide a helpful, accurate answer based on the video content."""
        
        # Route to AI
        provider_name, model, _ = query_router.route(prompt, request.preferred_provider)
        provider = providers[provider_name]
        messages = [Message(role="user", content=prompt)]
        response = await provider.chat(messages, model)
        
        return {
            "success": True,
            "video_id": video_id,
            "title": transcript_result.get("title"),
            "question": request.question,
            "answer": response.content,
            "provider": provider_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== IMAGE GENERATION ENDPOINTS ==========

class ImageGenerateRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"


@api_router.post("/image/generate")
async def generate_image(request: ImageGenerateRequest):
    """Generate an image using DALL-E 3"""
    try:
        result = await image_service.generate_dalle(
            request.prompt,
            request.size,
            request.quality
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== VISION ANALYSIS ENDPOINTS ==========

@api_router.post("/vision/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail."),
    provider: str = Form("gemini")
):
    """Analyze an image using AI vision"""
    try:
        content = await file.read()
        
        if provider == "gemini":
            result = await vision_service.analyze_with_gemini(
                content, file.filename, prompt
            )
        else:
            result = await vision_service.analyze_with_gpt4(
                content, file.filename, prompt
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/vision/ocr")
async def extract_text_from_image(
    file: UploadFile = File(...),
    provider: str = Form("gemini")
):
    """Extract text from an image (OCR)"""
    try:
        content = await file.read()
        result = await vision_service.extract_text_from_image(
            content, file.filename, provider
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== CONVERSATION MEMORY ENDPOINTS ==========

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"


class MessageAddRequest(BaseModel):
    role: str
    content: str
    metadata: Optional[dict] = None


@api_router.post("/memory/conversations")
async def create_conversation(request: ConversationCreateRequest):
    """Create a new conversation"""
    conv_id = memory_service.create_conversation(request.title)
    return {"success": True, "conversation_id": conv_id}


@api_router.get("/memory/conversations")
async def list_conversations():
    """List all conversations"""
    return memory_service.list_conversations()


@api_router.get("/memory/conversations/{conv_id}")
async def get_conversation(conv_id: str, limit: int = 50):
    """Get messages from a conversation"""
    messages = memory_service.get_messages(conv_id, limit)
    return {"conversation_id": conv_id, "messages": messages}


@api_router.post("/memory/conversations/{conv_id}/messages")
async def add_message(conv_id: str, request: MessageAddRequest):
    """Add a message to a conversation"""
    message = memory_service.add_message(
        conv_id, request.role, request.content, request.metadata
    )
    return {"success": True, "message": message}


@api_router.delete("/memory/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation"""
    result = memory_service.delete_conversation(conv_id)
    if result:
        return {"success": True}
    raise HTTPException(status_code=404, detail="Conversation not found")


@api_router.get("/memory/search")
async def search_memory(query: str, limit: int = 10):
    """Search across all conversations"""
    results = memory_service.search_conversations(query, limit)
    return {"query": query, "results": results}


# Research Agent - Combines search + LLM
class ResearchRequest(BaseModel):
    topic: str
    depth: Optional[str] = "basic"  # basic, detailed, comprehensive
    preferred_provider: Optional[str] = None

@api_router.post("/research")
async def research_topic(request: ResearchRequest):
    """
    Research a topic using web search + AI synthesis
    """
    try:
        # Step 1: Web search
        search_results = await web_search.search(request.topic, max_results=5)
        
        if not search_results or "error" in search_results[0]:
            return {
                "success": False,
                "error": "Web search failed",
                "results": search_results
            }
        
        # Step 2: Format search results as context
        context = f"Research Topic: {request.topic}\n\nWeb Search Results:\n\n"
        for i, r in enumerate(search_results, 1):
            context += f"{i}. **{r.get('title', 'No title')}**\n"
            context += f"   {r.get('snippet', 'No description')}\n"
            context += f"   Source: {r.get('url', 'Unknown')}\n\n"
        
        # Step 3: Use AI to synthesize
        depth_prompts = {
            "basic": "Provide a brief summary (2-3 paragraphs) of the topic based on these search results.",
            "detailed": "Provide a detailed analysis (4-5 paragraphs) with key points and insights.",
            "comprehensive": "Provide a comprehensive research report with sections: Overview, Key Findings, Analysis, and Conclusion."
        }
        
        prompt = f"""{context}

Based on the search results above, {depth_prompts.get(request.depth, depth_prompts['basic'])}

Topic: {request.topic}"""
        
        # Route to best provider
        provider_name, model, category = query_router.route(
            prompt,
            request.preferred_provider or "groq"  # Groq is fast
        )
        
        provider = providers[provider_name]
        messages = [Message(role="user", content=prompt)]
        response = await provider.chat(messages, model)
        
        return {
            "success": True,
            "topic": request.topic,
            "depth": request.depth,
            "sources": [{"title": r.get("title"), "url": r.get("url")} for r in search_results],
            "synthesis": response.content,
            "provider": provider_name,
            "model": model
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)


