import os
import logging
from dotenv import load_dotenv

# Load environment variables at the module level
load_dotenv()

class Config:
    # Load environment variables with explicit default values
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    USER_AGENT = os.getenv("USER_AGENT", "DurgaAI/1.0")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    RAG_INDEX_PATH = os.getenv("RAG_INDEX_PATH", "faiss_persistent_index.pkl")
    
    @classmethod
    def setup_environment(cls):
        """Set up environment variables and configurations"""
        # Ensure environment variables are set in os.environ
        if cls.GROQ_API_KEY:
            os.environ["GROQ_API_KEY"] = cls.GROQ_API_KEY
        os.environ["USER_AGENT"] = cls.USER_AGENT
        if cls.OLLAMA_BASE_URL:
            os.environ["OLLAMA_API_BASE"] = cls.OLLAMA_BASE_URL
    
    @classmethod
    def validate(cls):
        # Set up environment first
        cls.setup_environment()
        
        if not cls.GROQ_API_KEY:
            logging.error("GROQ_API_KEY is not set")
            return False
            
        logging.info(f"GROQ_API_KEY is set and starts with: {cls.GROQ_API_KEY[:10]}...")
        return True