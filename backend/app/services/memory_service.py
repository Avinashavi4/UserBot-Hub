"""
Conversation Memory Service
Persistent conversation history with search and context retrieval
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib


class ConversationMemory:
    """Service for managing persistent conversation memory"""
    
    def __init__(self, storage_dir: str = "data/conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._load_all_conversations()
    
    def _load_all_conversations(self):
        """Load all conversations from disk"""
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conv_id = file.stem
                    self.conversations[conv_id] = data.get("messages", [])
            except Exception:
                pass
    
    def _save_conversation(self, conversation_id: str):
        """Save a conversation to disk"""
        filepath = self.storage_dir / f"{conversation_id}.json"
        data = {
            "id": conversation_id,
            "messages": self.conversations.get(conversation_id, []),
            "updated_at": datetime.now().isoformat()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_conversation(self, title: str = "New Conversation") -> str:
        """
        Create a new conversation
        
        Args:
            title: Conversation title
            
        Returns:
            Conversation ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_suffix = hashlib.md5(f"{timestamp}{title}".encode()).hexdigest()[:8]
        conv_id = f"conv_{timestamp}_{hash_suffix}"
        
        self.conversations[conv_id] = [{
            "role": "system",
            "content": f"Conversation: {title}",
            "timestamp": datetime.now().isoformat()
        }]
        self._save_conversation(conv_id)
        
        return conv_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: Conversation ID
            role: 'user', 'assistant', or 'system'
            content: Message content
            metadata: Optional metadata (sources, tokens, etc.)
            
        Returns:
            The added message
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[conversation_id].append(message)
        self._save_conversation(conversation_id)
        
        return message
    
    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_system: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation
        
        Args:
            conversation_id: Conversation ID
            limit: Max messages to return (most recent)
            include_system: Include system messages
            
        Returns:
            List of messages
        """
        messages = self.conversations.get(conversation_id, [])
        
        if not include_system:
            messages = [m for m in messages if m.get("role") != "system"]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_context_window(
        self,
        conversation_id: str,
        max_messages: int = 10,
        max_tokens: int = 4000
    ) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM context
        
        Args:
            conversation_id: Conversation ID
            max_messages: Max messages to include
            max_tokens: Approximate token limit
            
        Returns:
            List of messages in LLM format
        """
        messages = self.get_messages(conversation_id, include_system=False)
        
        # Get recent messages
        recent = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # Format for LLM
        formatted = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough char to token ratio
        
        for msg in reversed(recent):
            content = msg.get("content", "")
            if total_chars + len(content) > char_limit:
                break
            formatted.insert(0, {
                "role": msg["role"],
                "content": content
            })
            total_chars += len(content)
        
        return formatted
    
    def search_conversations(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search across all conversations
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching messages with context
        """
        results = []
        query_lower = query.lower()
        
        for conv_id, messages in self.conversations.items():
            for i, msg in enumerate(messages):
                content = msg.get("content", "")
                if query_lower in content.lower():
                    results.append({
                        "conversation_id": conv_id,
                        "message_index": i,
                        "message": msg,
                        "snippet": content[:200] + "..." if len(content) > 200 else content
                    })
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations with metadata
        
        Returns:
            List of conversation summaries
        """
        summaries = []
        
        for conv_id, messages in self.conversations.items():
            if not messages:
                continue
            
            # Get title from first system message or first user message
            title = "Untitled"
            for msg in messages:
                if msg.get("role") == "system":
                    content = msg.get("content", "")
                    if content.startswith("Conversation: "):
                        title = content.replace("Conversation: ", "")
                        break
                elif msg.get("role") == "user":
                    title = msg.get("content", "")[:50]
                    break
            
            # Get timestamps
            first_msg = messages[0] if messages else {}
            last_msg = messages[-1] if messages else {}
            
            summaries.append({
                "id": conv_id,
                "title": title,
                "message_count": len(messages),
                "created_at": first_msg.get("timestamp"),
                "updated_at": last_msg.get("timestamp")
            })
        
        # Sort by updated time
        summaries.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return summaries
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
            filepath = self.storage_dir / f"{conversation_id}.json"
            if filepath.exists():
                filepath.unlink()
            
            return True
        return False
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear messages from a conversation but keep it
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if cleared
        """
        if conversation_id in self.conversations:
            title = "Cleared Conversation"
            for msg in self.conversations[conversation_id]:
                if msg.get("role") == "system":
                    content = msg.get("content", "")
                    if content.startswith("Conversation: "):
                        title = content.replace("Conversation: ", "")
                        break
            
            self.conversations[conversation_id] = [{
                "role": "system",
                "content": f"Conversation: {title}",
                "timestamp": datetime.now().isoformat()
            }]
            self._save_conversation(conversation_id)
            return True
        return False


# Global instance
memory_service = ConversationMemory()
