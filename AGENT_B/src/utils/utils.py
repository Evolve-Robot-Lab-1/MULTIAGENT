import base64
import os
import time
from pathlib import Path
from typing import Dict, Optional
import json
import gradio as gr

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_mistralai import ChatMistralAI

# Predefined model names for common providers
model_names = {
    "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3-5-sonnet", "claude-3-5-haiku"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"],
    "google": [
        "gemini-2.5-pro-preview-03-25",
        "gemini-2.5-flash-preview-04-17", 
        "gemini-2.0-flash", 
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash-thinking-exp",
        "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-2.0-pro-exp-02-05",
        "gemini-1.5-pro", 
        "gemini-1.5-flash", 
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.0-pro",
        "gemini-exp-1206",
        "gemini-exp-1121"
    ],
    "ollama": ["llama3", "llama2", "mistral", "qwen2.5", "deepseek-r1", "phi3"],
    "azure_openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "mistral": ["mistral-large-latest", "mistral-small-latest", "pixtral-large-latest"]
}

# Callback to update the model name dropdown based on the selected provider
def update_model_dropdown(llm_provider):
    """
    Update the model name dropdown with predefined models for the selected provider.
    """
    provider = llm_provider.lower()
    if provider in model_names:
        return gr.Dropdown(choices=model_names[provider], value=model_names[provider][0])
    else:
        return gr.Dropdown(choices=["Model not available for this provider"], value="Model not available for this provider")

class MissingAPIKeyError(Exception):
    """Exception raised when an API key is required but not provided."""
    
    def __init__(self, provider: str, env_var: str):
        message = f"Missing API key for {provider}. Please set the {env_var} environment variable."
        super().__init__(message)
        
def encode_image(img_path):
    """Encode an image file to base64."""
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_latest_files(directory: str, file_types: list = ['.webm', '.zip']) -> Dict[str, Optional[str]]:
    """Get the latest files of specified types from a directory."""
    result = {ext: None for ext in file_types}
    
    try:
        path = Path(directory)
        if not path.exists():
            return result
            
        for ext in file_types:
            files = list(path.glob(f"*{ext}"))
            if files:
                latest = max(files, key=lambda x: x.stat().st_mtime)
                result[ext] = str(latest)
    except Exception as e:
        print(f"Error getting latest files: {e}")
        
    return result

async def capture_screenshot(browser_context):
    """Capture a screenshot of the current browser page and return base64 encoded data."""
    if not browser_context:
        return None
        
    try:
        # Access the playwright browser context directly
        playwright_browser = browser_context.browser.playwright_browser
        if not playwright_browser or not playwright_browser.contexts:
            return None
            
        playwright_context = playwright_browser.contexts[0]
        pages = playwright_context.pages
        
        # Find an active page (not about:blank)
        active_page = None
        if pages:
            for page in pages:
                if page.url and page.url != "about:blank":
                    active_page = page
                    break
            # If no active page found, use the first page
            if not active_page and pages:
                active_page = pages[0]
        
        if not active_page:
            return None
        
        # Take a screenshot and return base64 encoded data
        # Note: PNG format doesn't support quality parameter
        screenshot_bytes = await active_page.screenshot(
            type='png',
            scale="css"
        )
        
        if screenshot_bytes:
            encoded_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            return encoded_screenshot
        
        return None
    except Exception as e:
        # Don't print errors for every screenshot attempt to avoid spam
        # Only log critical errors
        if "quality is unsupported" not in str(e):
            print(f"Error capturing screenshot: {e}")
        return None

def get_llm_model(provider: str, **kwargs):
    """
    Get an LLM model instance based on the provider.
    """
    if provider not in ["ollama"]:
        env_var = f"{provider.upper()}_API_KEY"
        api_key = kwargs.get("api_key", "") or os.getenv(env_var, "")
        if not api_key:
            raise MissingAPIKeyError(provider, env_var)
        kwargs["api_key"] = api_key

    if provider == "anthropic":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("ANTHROPIC_ENDPOINT", "https://api.anthropic.com")
        else:
            base_url = kwargs.get("base_url")

        return ChatAnthropic(
            model=kwargs.get("model_name", "claude-3-sonnet"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "openai":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=kwargs.get("model_name", "gemini-2.0-flash-exp"),
            temperature=kwargs.get("temperature", 0.0),
            api_key=api_key,
        )
    elif provider == "ollama":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
        else:
            base_url = kwargs.get("base_url")

        return ChatOllama(
            model=kwargs.get("model_name", "llama3"),
            temperature=kwargs.get("temperature", 0.0),
            num_ctx=kwargs.get("num_ctx", 8192),
            base_url=base_url,
        )
    elif provider == "azure_openai":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        else:
            base_url = kwargs.get("base_url")
        api_version = kwargs.get("api_version", "") or os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        return AzureChatOpenAI(
            model=kwargs.get("model_name", "gpt-4o"),
            temperature=kwargs.get("temperature", 0.0),
            api_version=api_version,
            azure_endpoint=base_url,
            api_key=api_key,
        )
    elif provider == "deepseek":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("DEEPSEEK_ENDPOINT", "https://api.deepseek.com")
        else:
            base_url = kwargs.get("base_url")

        return ChatOpenAI(
            model=kwargs.get("model_name", "deepseek-chat"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    elif provider == "mistral":
        if not kwargs.get("base_url", ""):
            base_url = os.getenv("MISTRAL_ENDPOINT", "https://api.mistral.ai/v1")
        else:
            base_url = kwargs.get("base_url")

        return ChatMistralAI(
            model=kwargs.get("model_name", "mistral-large-latest"),
            temperature=kwargs.get("temperature", 0.0),
            base_url=base_url,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}") 