"""
Chat-related models with validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

from app.utils.validators import validate_uuid


class ChatProvider(str, Enum):
    """Available chat providers."""
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class ChatModel(str, Enum):
    """Available chat models."""
    # Groq models
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    LLAMA_3_70B_TOOL = "llama3-groq-70b-8192-tool-use-preview"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    DEEPSEEK_R1 = "deepseek-r1-distill-llama-70b"
    
    # OpenAI models
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: Optional[ChatModel] = Field(None, description="Model to use")
    provider: Optional[ChatProvider] = Field(None, description="Provider to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="Maximum tokens to generate")
    use_rag: bool = Field(False, description="Use RAG for context")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    
    @field_validator('message')
    @classmethod
    def clean_message(cls, v):
        """Clean message."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")
        return cleaned
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID if provided."""
        if v:
            return validate_uuid(v)
        return v


class ChatStreamRequest(BaseModel):
    """Request model for streaming chat."""
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[str] = Field(None, description="Provider to use")
    use_rag: bool = Field(False, description="Use RAG for context")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="Maximum tokens")
    
    @field_validator('query')
    @classmethod
    def clean_query(cls, v):
        """Clean query."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Query cannot be empty")
        return cleaned


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., pattern="^(system|user|assistant)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    """Chat session model."""
    id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(None, max_length=255, description="Session title")
    messages: List[ChatMessage] = Field(default_factory=list)
    model: Optional[str] = None
    provider: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate session ID."""
        return validate_uuid(v)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the session."""
        message = ChatMessage(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message
    
    def get_context_window(self, max_messages: int = 20) -> List[ChatMessage]:
        """Get recent messages for context."""
        return self.messages[-max_messages:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'message_count': len(self.messages),
            'model': self.model,
            'provider': self.provider,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion."""
    response: str
    model: str
    provider: str
    session_id: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    session_id: str
    messages: List[ChatMessage]
    total_messages: int
    model: Optional[str] = None
    provider: Optional[str] = None