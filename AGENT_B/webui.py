import pdb
import logging
import time
import os
import glob
import asyncio
import argparse
import base64

from dotenv import load_dotenv
load_dotenv()

# Apply browser_use initialization patch before any imports
import init_patch

logger = logging.getLogger(__name__)

import gradio as gr
from gradio.themes import Citrus, Default, Glass, Monochrome, Ocean, Origin, Soft, Base

# Import our custom classes
from src.utils.agent_state import AgentState
from src.utils.utils import get_llm_model, update_model_dropdown, capture_screenshot
from src.agent.custom_agent import CustomAgent
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext
from src.agent.custom_prompts import CustomSystemPrompt, CustomAgentMessagePrompt
from src.controller.custom_controller import CustomController

# Browser-use imports will be done lazily to prevent early logging setup
# from browser_use.browser.browser import BrowserConfig
# from browser_use.browser.context import BrowserContextConfig

# Global variables for persistence
_global_browser = None
_global_browser_context = None
_global_agent = None
_global_controller = None

# Create the global agent state instance
_global_agent_state = AgentState()

def resolve_sensitive_env_variables(text):
    """
    Replace environment variable placeholders ($SENSITIVE_*) with their values.
    Only replaces variables that start with SENSITIVE_.
    """
    if not text:
        return text
        
    import re
    
    # Find all $SENSITIVE_* patterns
    env_vars = re.findall(r'\$SENSITIVE_[A-Za-z0-9_]*', text)
    
    result = text
    for var in env_vars:
        # Remove the $ prefix to get the actual environment variable name
        env_name = var[1:]  # removes the $
        env_value = os.getenv(env_name)
        if env_value is not None:
            # Replace $SENSITIVE_VAR_NAME with its value
            result = result.replace(var, env_value)
        
    return result

async def run_browser_agent(
    task,
    llm_provider,
    llm_model_name,
    llm_temperature,
    max_steps
):
    """Run the browser agent with the given configuration."""
    global _global_browser, _global_browser_context, _global_agent, _global_controller, _global_agent_state
    
    # Lazy import browser-use components to prevent early logging setup
    from browser_use.browser.browser import BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    
    try:
        _global_agent_state.clear_stop()
        
        # Fixed browser configuration for background operation with screenshot capture
        window_w = 1280
        window_h = 720
        headless = True  # Run in background without opening browser window
        use_own_browser = False
        keep_browser_open = True
        
        # Initialize browser if needed
        if _global_browser is None:
            logger.info("Initializing new browser instance")
            extra_chromium_args = [
                f"--window-size={int(window_w)},{int(window_h)}",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",  # Better headless compatibility
                "--disable-gpu",  # Improve headless performance
                "--disable-dev-shm-usage",  # Overcome limited resource problems
                
                # Anti-detection arguments
                "--disable-blink-features=AutomationControlled",  # Hide automation signatures
                "--disable-extensions-file-access-check",
                "--disable-extensions-http-throttling", 
                "--disable-extensions",
                "--disable-plugins-discovery",
                "--disable-default-apps",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-ipc-flooding-protection",
                "--disable-hang-monitor",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--disable-translate",
                "--disable-component-update",
                "--disable-background-networking",
                "--disable-client-side-phishing-detection",
                "--disable-domain-reliability",
                "--disable-features=TranslateUI",
                "--disable-features=BlinkGenPropertyTrees",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--no-default-browser-check",
                "--password-store=basic",
                "--use-mock-keychain",
                
                # User agent and viewport spoofing
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=True,
                    browser_binary_path=None,
                    cdp_url=None,
                    extra_chromium_args=extra_chromium_args
                )
            )

        # Don't close existing browser context - reuse it for efficiency  
        if _global_browser_context is None:
            logger.info("Creating new enhanced browser context with anti-detection")
            # Initialize new CustomBrowserContext with anti-detection features
            _global_browser_context = CustomBrowserContext(
                browser=_global_browser,
            config=BrowserContextConfig(
                no_viewport=False,
                window_width=int(window_w),
                window_height=int(window_h),
            )
        )
        else:
            logger.info("Reusing existing enhanced browser context")
            
        # Reset the agent
        _global_agent = None
        
        # Resolve sensitive environment variables in task
        task = resolve_sensitive_env_variables(task)

        # Get LLM model
        llm = get_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            temperature=llm_temperature,
        )
        
        # Create custom agent
        _global_agent = CustomAgent(
            task=task,
            llm=llm,
            browser_context=_global_browser_context
        )
        
        # Create controller
        _global_controller = CustomController()
        
        # Run the agent
        result = await _global_controller.start(
            agent=_global_agent,
            task=task,
            max_steps=int(max_steps)
        )
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"Error running agent: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "output": "",
            "steps": 0
        }

async def stop_agent():
    """Request the agent to stop and update UI with enhanced feedback"""
    global _global_agent_state, _global_browser_context, _global_browser, _global_agent, _global_controller

    try:
        # Request stop through agent state
        if _global_agent_state:
            _global_agent_state.request_stop()
        
        # Stop controller
        if _global_controller:
            _global_controller.stop()
        
        # Check if agent exists before trying to stop it
        if _global_agent is not None and hasattr(_global_agent, 'stop'):
            _global_agent.stop()
        
        # Update UI immediately
        message = "Stop requested - the agent will halt at the next safe point"
        logger.info(f"🛑 {message}")

        return message
        
    except Exception as e:
        import traceback
        error_msg = f"Error during stop: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return error_msg

async def get_live_browser_screenshot():
    """Capture a live screenshot from the current browser context"""
    global _global_browser_context
    
    try:
        if _global_browser_context:
            # Use the updated capture_screenshot function
            encoded_screenshot = await capture_screenshot(_global_browser_context)
            return encoded_screenshot
        return None
    except Exception as e:
        logger.error(f"Error capturing live screenshot: {e}")
        return None

async def close_global_browser():
    """Close the global browser and clean up resources"""
    global _global_browser, _global_browser_context, _global_agent, _global_controller
    
    try:
        if _global_browser_context:
            await _global_browser_context.close()
            _global_browser_context = None
        
        if _global_browser:
            await _global_browser.close()
            _global_browser = None
            
        _global_agent = None
        _global_controller = None
        
        logger.info("Browser closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing browser: {e}")

def create_ui(theme_name="Ocean"):
    """Create the improved Gradio UI for Agent_B"""
    theme_map = {
        "Ocean": Ocean,
        "Default": Default,
        "Glass": Glass,
        "Monochrome": Monochrome,
        "Soft": Soft,
        "Citrus": Citrus,
        "Origin": Origin,
    }
    
    theme = theme_map.get(theme_name, Ocean)()
    
    with gr.Blocks(theme=theme, title="Agent_B - Browser Agent", css="""
        .agent-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .agent-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        .agent-name {
            font-size: 32px;
            font-weight: bold;
            color: white;
            margin: 0;
        }
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .task-input {
            margin: 20px 0;
        }
        .control-buttons {
            margin: 20px 0;
        }
        .browser-container {
            border: 3px solid #667eea;
            border-radius: 15px;
            padding: 0;
            margin-top: 30px;
            background: #ffffff;
            min-height: 500px;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }
    """) as demo:
        
        with gr.Column(elem_classes="main-container"):
            # Agent Header with Icon and Name
            with gr.Row(elem_classes="agent-header"):
                gr.HTML("""
                    <div style="text-align: center;">
                        <div class="agent-icon">🤖</div>
                        <h1 class="agent-name">Agent_B</h1>
                        <p style="color: #f0f0f0; margin: 5px 0;">Intelligent Browser Automation Agent</p>
                    </div>
                """)
            
            # Task Input Section
            with gr.Group(elem_classes="task-input"):
                task = gr.Textbox(
                    label="📝 Task Description",
                    placeholder="Describe what you want Agent_B to do in the browser...",
                    lines=4,
                    scale=1
                )
            
            # LLM & Model Selection Tab
            with gr.Accordion("🧠 LLM & Model Selection", open=False):
                with gr.Row():
                    with gr.Column():
                        llm_provider = gr.Dropdown(
                            ["google", "openai", "anthropic", "ollama", "azure_openai", "deepseek", "mistral"], 
                            label="LLM Provider", 
                            value="google"  # Default to Google as requested
                        )
                        llm_model_name = gr.Dropdown(
                            [
                                "gemini-2.0-flash-exp", "gemini-2.0-flash", "gemini-2.0-flash-thinking-exp",
                                "gemini-2.0-flash-thinking-exp-01-21", "gemini-2.0-pro-exp-02-05",
                                "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b", 
                                "gemini-1.5-flash-latest", "gemini-1.5-flash-8b-latest", "gemini-1.5-pro-latest"
                            ], 
                            label="Model", 
                            value="gemini-2.0-flash-exp"  # Default Google model
                        )
                    with gr.Column():
                        llm_temperature = gr.Slider(
                            minimum=0.0, 
                            maximum=1.0, 
                            value=0.1, 
                            step=0.1, 
                            label="Temperature"
                        )
                        max_steps = gr.Number(
                            label="Max Steps", 
                            value=15, 
                            precision=0
                        )
            
            # Control Buttons
            with gr.Row(elem_classes="control-buttons"):
                with gr.Column(scale=1):
                    run_button = gr.Button("🚀 Run Agent", variant="primary", size="lg")
                with gr.Column(scale=1):
                    stop_button = gr.Button("⏹️ Stop", variant="stop", size="lg")
            
            # Live Embedded Browser Section
            with gr.Group(elem_classes="browser-container"):
                browser_frame = gr.HTML(
                    value="""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                        <h3 style="margin: 0; text-align: center;">🌐 Live Browser</h3>
                    </div>
                    <div style="text-align: center; padding: 80px 40px; background: #f9f9f9; min-height: 500px;">
                        <h3 style="color: #667eea; margin-bottom: 15px;">🌐 Browser Ready</h3>
                        <p style="color: #666; margin: 0;">Enter a task above and click "🚀 Run Agent"</p>
                        <p style="color: #888; margin-top: 10px; font-size: 14px;">Live browser actions will appear here</p>
                    </div>
                    """
                )
        


        # Live browser streaming function
        async def run_with_stream(task_input, provider, model, temperature, steps):
            """Run agent with live browser screenshot streaming"""
            global _global_agent_state, _global_browser, _global_browser_context, _global_agent
            
            if not task_input.strip():
                yield """
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                    <h3 style="margin: 0; text-align: center;">🌐 Live Browser</h3>
                </div>
                <div style="text-align: center; padding: 40px; border: 2px dashed #f44336; background: #fff0f0; min-height: 500px;">
                    <h3 style="color: #f44336;">❌ No Task</h3>
                    <p>Please enter a task description above</p>
                </div>
                """
                return
            
            try:
                _global_agent_state.clear_stop()
                
                # Run the browser agent in the background
                agent_task = asyncio.create_task(
                    run_browser_agent(task_input, provider, model, temperature, steps)
                )

                # Initialize HTML content
                html_content = """
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                    <h3 style="margin: 0; text-align: center;">🌐 Live Browser - 🚀 Starting...</h3>
                </div>
                <div style="text-align: center; padding: 60px 40px; background: #f0f8ff; min-height: 500px;">
                    <h3 style="color: #2196F3;">🚀 Initializing Browser...</h3>
                    <p>Browser is starting up...</p>
                    <div style="margin-top: 20px;">
                        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #2196F3; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    </div>
                    <style>
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    </style>
                </div>
                """
                
                # Track browser failures
                browser_failure_count = 0
                max_browser_failures = 3
                last_error_time = None

                # Periodically update the stream while the agent task is running
                while not agent_task.done():
                    try:
                        # Make sure browser context exists
                        if _global_browser_context is None:
                            await asyncio.sleep(0.5)
                            
                            # Check for recurring failures
                            current_time = time.time()
                            if last_error_time and current_time - last_error_time < 5:
                                browser_failure_count += 1
                                if browser_failure_count >= max_browser_failures:
                                    logger.error(f"Browser context failed {max_browser_failures} times in quick succession, stopping agent")
                                    _global_agent_state.request_stop()
                                    if _global_agent:
                                        _global_agent.stop()
                                    break
                            else:
                                browser_failure_count = 0
                            
                            last_error_time = current_time
                            continue
                        
                        # Reset failure count if context exists
                        browser_failure_count = 0
                        last_error_time = None
                            
                        # Try to get a screenshot
                        try:
                            encoded_screenshot = await get_live_browser_screenshot()
                            if encoded_screenshot is not None:
                                html_content = f"""
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                                    <h3 style="margin: 0; text-align: center;">🌐 Live Browser - 🔄 Active</h3>
                                </div>
                                <img src="data:image/png;base64,{encoded_screenshot}" style="width:100%; height:600px; object-fit:contain; border:1px solid #eee; border-radius:0 0 12px 12px;">
                                <div style="background: #e8f5e8; padding: 8px; text-align: center; border-radius: 0 0 12px 12px;">
                                    <p style="margin: 2px 0; color: #4CAF50; font-size: 11px;"><strong>🔄 Live Browser Actions</strong></p>
                                </div>
                                """
                            else:
                                await asyncio.sleep(0.5)
                                continue
                        except Exception as e:
                            # Check if this is a browser closure error
                            if "Target page, context or browser has been closed" in str(e) or "Protocol error" in str(e):
                                browser_failure_count += 1
                                if browser_failure_count >= max_browser_failures:
                                    logger.error(f"Browser context failed {max_browser_failures} times in quick succession, stopping agent")
                                    _global_agent_state.request_stop()
                                    if _global_agent:
                                        _global_agent.stop()
                                    break
                            
                            # Don't log screenshot quality errors repeatedly
                            if "quality is unsupported" not in str(e):
                                logger.debug(f"Screenshot capture error: {e}")
                            
                            await asyncio.sleep(0.5)
                            continue
                    except Exception as e:
                        await asyncio.sleep(0.5)
                        continue

                    # Yield current state
                    yield html_content
                    await asyncio.sleep(0.3)  # Capture screenshots every 0.3 seconds

                # Once the agent task completes, get the results
                try:
                    result = await agent_task
                    # Get final screenshot
                    final_screenshot = await get_live_browser_screenshot()
                    if final_screenshot:
                        html_content = f"""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                            <h3 style="margin: 0; text-align: center;">🌐 Live Browser - ✅ Completed</h3>
                        </div>
                        <img src="data:image/png;base64,{final_screenshot}" style="width:100%; height:600px; object-fit:contain; border:1px solid #eee; border-radius:0 0 12px 12px;">
                        <div style="background: #e8f5e8; padding: 8px; text-align: center; border-radius: 0 0 12px 12px;">
                            <p style="margin: 2px 0; color: #4CAF50; font-size: 11px;"><strong>✅ Task Completed</strong></p>
                        </div>
                        """
                except Exception as e:
                    html_content = f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                        <h3 style="margin: 0; text-align: center;">🌐 Live Browser - ❌ Error</h3>
                    </div>
                    <div style="text-align: center; padding: 40px; background: #fff8f0; min-height: 500px;">
                        <h3 style="color: #ff9800; margin-bottom: 15px;">⚠️ Error</h3>
                        <p>Error: {str(e)[:100]}</p>
                    </div>
                    """

                yield html_content
                
            except Exception as e:
                yield f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                    <h3 style="margin: 0; text-align: center;">🌐 Live Browser - ❌ Error</h3>
                </div>
                <div style="text-align: center; padding: 40px; background: #fff8f0; min-height: 500px;">
                    <h3 style="color: #ff9800; margin-bottom: 15px;">⚠️ Error</h3>
                    <p>Error: {str(e)[:100]}</p>
                </div>
                """

        # Event Handlers - Simple wrapper for streaming
        async def run_agent_wrapper(task_input, provider, model, temperature, steps):
            """Simple wrapper that calls the streaming function"""
            async for result in run_with_stream(task_input, provider, model, temperature, steps):
                yield result
        
        async def stop_agent_wrapper():
            try:
                message = await stop_agent()
                # Show stopped state
                browser_html = """
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                    <h3 style="margin: 0; text-align: center;">🌐 Live Browser - ⏹️ Stopped</h3>
                </div>
                <div style="text-align: center; padding: 80px 40px; background: #fff8f0; min-height: 500px;">
                    <h3 style="color: #ff9800; margin-bottom: 15px;">⏹️ Agent Stopped</h3>
                    <p style="color: #666; margin: 0;">Agent has been stopped successfully</p>
                    <p style="color: #888; margin-top: 10px; font-size: 14px;">You can start a new task anytime</p>
                </div>
                """
                return browser_html
            except Exception as e:
                browser_html = """
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; margin: 0; border-radius: 12px 12px 0 0;">
                    <h3 style="margin: 0; text-align: center;">🌐 Live Browser</h3>
                </div>
                <div style="text-align: center; padding: 80px 40px; background: #f9f9f9; min-height: 500px;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">🌐 Browser Ready</h3>
                    <p style="color: #666; margin: 0;">Enter a task above and click "🚀 Run Agent"</p>
                    <p style="color: #888; margin-top: 10px; font-size: 14px;">Live browser actions will appear here</p>
                </div>
                """
                return browser_html
        
        # Update model dropdown when provider changes
        llm_provider.change(
            update_model_dropdown,
            inputs=[llm_provider],
            outputs=[llm_model_name]
        )
        
        # Connect buttons to functions
        run_button.click(
            run_agent_wrapper,
            inputs=[task, llm_provider, llm_model_name, llm_temperature, max_steps],
            outputs=[browser_frame]
        )
        
        stop_button.click(
            stop_agent_wrapper,
            inputs=[],
            outputs=[browser_frame]
        )
    
    return demo

def main():
    parser = argparse.ArgumentParser(description="Agent_B - Intelligent Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    demo.queue().launch(server_name=args.ip, server_port=args.port)

if __name__ == '__main__':
    main() 