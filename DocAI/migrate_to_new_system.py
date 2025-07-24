#!/usr/bin/env python3
"""
Migration script to move data from old DocAI system to new refactored system.
This script handles:
1. Document migration from file system
2. Chat history migration
3. User creation
4. RAG index migration
"""
import os
import sys
import json
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_database, create_tables, DatabaseSession
from app.database.models import Document, User, ChatSession, ChatMessage, DocumentChunk
from app.core.config import get_config
from app.models.document import DocumentType, DocumentStatus


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocAIMigrator:
    """Handles migration from old to new DocAI system."""
    
    def __init__(self, old_upload_path: str, dry_run: bool = False):
        """
        Initialize migrator.
        
        Args:
            old_upload_path: Path to old system's upload directory
            dry_run: If True, only simulate migration
        """
        self.old_upload_path = Path(old_upload_path)
        self.dry_run = dry_run
        self.config = get_config()
        
        # Statistics
        self.stats = {
            'documents_migrated': 0,
            'documents_failed': 0,
            'users_created': 0,
            'chat_sessions_migrated': 0,
            'errors': []
        }
        
        if not dry_run:
            # Initialize database
            init_database(self.config)
            create_tables()
    
    def migrate_all(self):
        """Run all migration steps."""
        logger.info(f"Starting migration (dry_run={self.dry_run})")
        
        # Step 1: Create default users
        self.create_default_users()
        
        # Step 2: Migrate documents
        self.migrate_documents()
        
        # Step 3: Migrate chat histories
        self.migrate_chat_histories()
        
        # Step 4: Migrate RAG data
        self.migrate_rag_data()
        
        # Print summary
        self.print_summary()
    
    def create_default_users(self):
        """Create default users for the system."""
        logger.info("Creating default users...")
        
        default_users = [
            {
                'email': 'admin@docai.local',
                'name': 'Admin User',
                'roles': ['admin', 'user'],
                'api_key': 'admin-api-key-12345'  # Change in production!
            },
            {
                'email': 'demo@docai.local',
                'name': 'Demo User',
                'roles': ['user', 'demo'],
                'api_key': 'demo-api-key-12345'  # Used in auth middleware
            }
        ]
        
        if not self.dry_run:
            with DatabaseSession() as session:
                for user_data in default_users:
                    # Check if user exists
                    existing = session.query(User).filter_by(
                        email=user_data['email']
                    ).first()
                    
                    if not existing:
                        user = User(
                            email=user_data['email'],
                            name=user_data['name'],
                            roles=user_data['roles'],
                            api_key=hashlib.sha256(
                                user_data['api_key'].encode()
                            ).hexdigest()[:64],
                            api_key_created_at=datetime.utcnow()
                        )
                        session.add(user)
                        self.stats['users_created'] += 1
                        logger.info(f"Created user: {user_data['email']}")
                    else:
                        logger.info(f"User already exists: {user_data['email']}")
                
                session.commit()
        else:
            logger.info(f"[DRY RUN] Would create {len(default_users)} users")
            self.stats['users_created'] = len(default_users)
    
    def migrate_documents(self):
        """Migrate documents from old file system to new database."""
        logger.info("Migrating documents...")
        
        # Look for documents in old upload directory
        old_docs_path = self.old_upload_path / 'documents'
        if not old_docs_path.exists():
            logger.warning(f"Old documents directory not found: {old_docs_path}")
            return
        
        # Get admin user for ownership
        admin_user = None
        if not self.dry_run:
            with DatabaseSession() as session:
                admin_user = session.query(User).filter_by(
                    email='admin@docai.local'
                ).first()
        
        # Process each document
        for file_path in old_docs_path.iterdir():
            if file_path.is_file():
                try:
                    self._migrate_document(file_path, admin_user)
                except Exception as e:
                    logger.error(f"Failed to migrate {file_path}: {e}")
                    self.stats['documents_failed'] += 1
                    self.stats['errors'].append(f"Document {file_path.name}: {str(e)}")
    
    def _migrate_document(self, old_path: Path, user: User = None):
        """Migrate a single document."""
        logger.info(f"Migrating document: {old_path.name}")
        
        # Determine document type
        file_ext = old_path.suffix.lower().lstrip('.')
        doc_type = DocumentType.from_extension(file_ext)
        
        if not doc_type:
            logger.warning(f"Unsupported file type: {old_path}")
            return
        
        # Generate new filename
        file_hash = self._calculate_file_hash(old_path)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{file_hash[:8]}_{old_path.name}"
        
        # Copy file to new location
        new_path = self.config.storage.documents_folder / new_filename
        
        if not self.dry_run:
            # Ensure directory exists
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(old_path, new_path)
            
            # Create database record
            with DatabaseSession() as session:
                document = Document(
                    filename=new_filename,
                    original_filename=old_path.name,
                    file_path=str(new_path),
                    file_type=doc_type.value,
                    file_size=old_path.stat().st_size,
                    file_hash=file_hash,
                    status=DocumentStatus.COMPLETED.value,
                    processed_at=datetime.utcnow(),
                    created_at=datetime.fromtimestamp(old_path.stat().st_ctime),
                    updated_at=datetime.fromtimestamp(old_path.stat().st_mtime)
                )
                
                # Add basic metadata
                document.title = old_path.stem
                document.metadata = {
                    'migrated': True,
                    'migration_date': datetime.utcnow().isoformat(),
                    'original_path': str(old_path)
                }
                
                session.add(document)
                session.commit()
                
                logger.info(f"Migrated document: {document.id}")
        else:
            logger.info(f"[DRY RUN] Would migrate {old_path.name} to {new_filename}")
        
        self.stats['documents_migrated'] += 1
    
    def migrate_chat_histories(self):
        """Migrate chat histories from old system."""
        logger.info("Migrating chat histories...")
        
        # Look for chat history files
        chat_history_file = self.old_upload_path.parent / 'chat_histories.json'
        
        if not chat_history_file.exists():
            logger.warning("No chat history file found")
            return
        
        try:
            with open(chat_history_file, 'r') as f:
                chat_data = json.load(f)
            
            if not self.dry_run:
                with DatabaseSession() as session:
                    # Get default user
                    default_user = session.query(User).filter_by(
                        email='admin@docai.local'
                    ).first()
                    
                    for session_id, messages in chat_data.items():
                        # Create chat session
                        chat_session = ChatSession(
                            user_id=default_user.id if default_user else None,
                            title=f"Migrated Session {session_id[:8]}",
                            created_at=datetime.utcnow()
                        )
                        session.add(chat_session)
                        session.flush()  # Get ID
                        
                        # Add messages
                        for msg in messages:
                            chat_message = ChatMessage(
                                session_id=chat_session.id,
                                role=msg.get('role', 'user'),
                                content=msg.get('content', ''),
                                created_at=datetime.fromisoformat(
                                    msg.get('timestamp', datetime.utcnow().isoformat())
                                ) if 'timestamp' in msg else datetime.utcnow()
                            )
                            session.add(chat_message)
                        
                        self.stats['chat_sessions_migrated'] += 1
                    
                    session.commit()
            else:
                logger.info(f"[DRY RUN] Would migrate {len(chat_data)} chat sessions")
                self.stats['chat_sessions_migrated'] = len(chat_data)
                
        except Exception as e:
            logger.error(f"Failed to migrate chat histories: {e}")
            self.stats['errors'].append(f"Chat histories: {str(e)}")
    
    def migrate_rag_data(self):
        """Migrate RAG index data."""
        logger.info("Migrating RAG data...")
        
        # Look for RAG data files
        rag_data_file = self.old_upload_path.parent / 'rag_index.json'
        
        if not rag_data_file.exists():
            logger.warning("No RAG index file found")
            return
        
        try:
            with open(rag_data_file, 'r') as f:
                rag_data = json.load(f)
            
            if not self.dry_run:
                with DatabaseSession() as session:
                    for doc_data in rag_data:
                        # Find corresponding document
                        document = session.query(Document).filter_by(
                            original_filename=doc_data.get('filename')
                        ).first()
                        
                        if document:
                            # Create chunks
                            for i, chunk_text in enumerate(doc_data.get('chunks', [])):
                                chunk = DocumentChunk(
                                    document_id=document.id,
                                    chunk_index=i,
                                    content=chunk_text,
                                    metadata={'migrated': True}
                                )
                                session.add(chunk)
                            
                            # Update document status
                            document.is_indexed = True
                            document.chunk_count = len(doc_data.get('chunks', []))
                    
                    session.commit()
            else:
                logger.info(f"[DRY RUN] Would migrate RAG data for {len(rag_data)} documents")
                
        except Exception as e:
            logger.error(f"Failed to migrate RAG data: {e}")
            self.stats['errors'].append(f"RAG data: {str(e)}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def print_summary(self):
        """Print migration summary."""
        logger.info("\n" + "="*50)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Documents migrated: {self.stats['documents_migrated']}")
        logger.info(f"Documents failed: {self.stats['documents_failed']}")
        logger.info(f"Users created: {self.stats['users_created']}")
        logger.info(f"Chat sessions migrated: {self.stats['chat_sessions_migrated']}")
        
        if self.stats['errors']:
            logger.error("\nERRORS:")
            for error in self.stats['errors']:
                logger.error(f"  - {error}")
        
        if self.dry_run:
            logger.info("\n[DRY RUN] No actual changes were made")
        else:
            logger.info("\nMigration completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate data from old DocAI to new system"
    )
    parser.add_argument(
        '--old-path',
        type=str,
        default='./uploads',
        help='Path to old system upload directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without making changes'
    )
    
    args = parser.parse_args()
    
    # Check if old path exists
    old_path = Path(args.old_path)
    if not old_path.exists():
        logger.error(f"Old upload path not found: {old_path}")
        sys.exit(1)
    
    # Run migration
    migrator = DocAIMigrator(str(old_path), dry_run=args.dry_run)
    
    try:
        migrator.migrate_all()
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()