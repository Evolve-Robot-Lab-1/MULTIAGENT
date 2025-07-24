"""
SQLAlchemy database models.
"""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, 
    Float, JSON, ForeignKey, Index, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base


# Association tables
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', String(36), ForeignKey('documents.id')),
    Column('tag_id', String(36), ForeignKey('tags.id'))
)


class Document(Base):
    """Document model."""
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    
    # Status
    status = Column(String(20), default='pending')
    processed_at = Column(DateTime)
    processing_time = Column(Float)
    error = Column(Text)
    
    # Metadata
    title = Column(String(255))
    author = Column(String(255))
    page_count = Column(Integer)
    word_count = Column(Integer)
    language = Column(String(10))
    metadata = Column(JSON)
    
    # RAG
    is_indexed = Column(Boolean, default=False)
    chunk_count = Column(Integer)
    embedding_model = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunks = relationship('DocumentChunk', back_populates='document', cascade='all, delete-orphan')
    tags = relationship('Tag', secondary=document_tags, back_populates='documents')
    
    # Indexes
    __table_args__ = (
        Index('idx_document_status', 'status'),
        Index('idx_document_created', 'created_at'),
        Index('idx_document_file_type', 'file_type'),
    )


class DocumentChunk(Base):
    """Document chunk for RAG."""
    __tablename__ = 'document_chunks'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey('documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    metadata = Column(JSON)
    embedding = Column(JSON)  # Store as JSON array for simplicity
    
    # Relationships
    document = relationship('Document', back_populates='chunks')
    
    # Indexes
    __table_args__ = (
        Index('idx_chunk_document', 'document_id'),
        Index('idx_chunk_index', 'document_id', 'chunk_index'),
    )


class ChatSession(Base):
    """Chat session model."""
    __tablename__ = 'chat_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    title = Column(String(255))
    model = Column(String(50))
    provider = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan')
    user = relationship('User', back_populates='chat_sessions')


class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = 'chat_messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('chat_sessions.id'), nullable=False)
    role = Column(String(20), nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship('ChatSession', back_populates='messages')
    
    # Indexes
    __table_args__ = (
        Index('idx_message_session', 'session_id'),
        Index('idx_message_created', 'created_at'),
    )


class User(Base):
    """User model."""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    api_key = Column(String(64), unique=True)
    api_key_created_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    roles = Column(JSON, default=lambda: ['user'])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship('ChatSession', back_populates='user')
    api_usage = relationship('APIUsage', back_populates='user')
    
    @hybrid_property
    def has_api_key(self):
        return self.api_key is not None


class Tag(Base):
    """Tag model for document categorization."""
    __tablename__ = 'tags'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7))  # Hex color
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship('Document', secondary=document_tags, back_populates='tags')


class APIUsage(Base):
    """API usage tracking model."""
    __tablename__ = 'api_usage'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    tokens_used = Column(Integer)
    response_time = Column(Float)  # in seconds
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='api_usage')
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_user', 'user_id'),
        Index('idx_usage_created', 'created_at'),
        Index('idx_usage_endpoint', 'endpoint'),
    )


class AgentStatus(Base):
    """Agent status tracking model."""
    __tablename__ = 'agent_status'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), nullable=False)  # running, stopped, error
    initialized = Column(Boolean, default=False)
    pid = Column(Integer)
    port = Column(Integer)
    error_message = Column(Text)
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    last_health_check = Column(DateTime)
    metadata = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)