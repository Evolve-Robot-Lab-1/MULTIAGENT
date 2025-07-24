import pdb
import logging
import sys
import os

# Add the parent directory to Python path to access the local browser_use package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

load_dotenv()
import os
import glob
import asyncio
import argparse

logger = logging.getLogger(__name__)

import gradio as gr

from browser_use.agent.service import Agent
from playwright.async_api import async_playwright
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from langchain_ollama import ChatOllama
from playwright.async_api import async_playwright
from src.utils.agent_state import AgentState

from src.utils import utils
from src.agent.custom_agent import CustomAgent
from src.browser.custom_browser import CustomBrowser
from src.agent.custom_prompts import CustomSystemPrompt, CustomAgentMessagePrompt
from src.browser.custom_context import BrowserContextConfig, CustomBrowserContext
from src.controller.custom_controller import CustomController
from gradio.themes import Citrus, Default, Glass, Monochrome, Ocean, Origin, Soft, Base
from src.utils.utils import update_model_dropdown, get_latest_files, capture_screenshot


# Global variables for persistence
_global_browser = None
_global_browser_context = None
_global_agent = None

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

async def stop_agent():
    """Request the agent to stop and update UI with enhanced feedback"""
    global _global_agent_state, _global_browser_context, _global_browser, _global_agent

    try:
        # Request stop through agent state
        _global_agent_state.request_stop()
        
        # Check if agent exists before trying to stop it
        if _global_agent is not None and hasattr(_global_agent, 'stop'):
            _global_agent.stop()
        
        # Update UI immediately
        message = "Stop requested - the agent will halt at the next safe point"
        logger.info(f"🛑 {message}")

        # Return UI updates
        return (
            message,                                        # errors_output
            gr.update(value="Stop", interactive=True),  # stop_button
            gr.update(interactive=True),                      # run_button
        )
    except Exception as e:
        import traceback
        error_msg = f"Error during stop: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return (
            error_msg,
            gr.update(value="Stop", interactive=True),
            gr.update(interactive=True)
        )

async def run_browser_agent(
        agent_type,
        llm_provider,
        llm_model_name,
        llm_num_ctx,
        llm_temperature,
        llm_base_url,
        llm_api_key,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        enable_recording,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method,
        chrome_cdp
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state, _global_agent
        _global_agent_state.clear_stop()

        # Start Chrome with remote debugging enabled
        import subprocess
        import time
        import random
        
        # Generate a random debugging port
        debug_port = random.randint(9222, 9999)
        
        # Get Chrome path from environment
        chrome_path = os.getenv("CHROME_PATH", "chrome")
        
        # Launch Chrome with remote debugging
        chrome_process = subprocess.Popen([
            chrome_path,
            f"--remote-debugging-port={debug_port}",
            "--new-window",
            "--start-maximized",
            "--disable-extensions"
        ])
        
        # Wait for Chrome to start
        time.sleep(2)
        
        # Set CDP URL to connect to the Chrome instance
        cdp_url = f"http://localhost:{debug_port}"
        
        # Initialize browser using CDP
        if _global_browser is None or True:  # Always create a new browser instance
            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=False,  # Not headless so we can see it
                    disable_security=disable_security,
                    cdp_url=cdp_url,  # Connect to our Chrome instance
                    chrome_instance_path=None,  # Don't launch another Chrome
                    extra_chromium_args=[]
                )
            )

        # Close existing browser context if it exists
        if _global_browser_context:
            await _global_browser_context.close()
            _global_browser_context = None
            
        # Reset the agent
        _global_agent = None

        # Initialize new browser context
        _global_browser_context = await _global_browser.new_context(
            config=BrowserContextConfig(
                trace_path=save_trace_path if save_trace_path else None,
                save_recording_path=save_recording_path if save_recording_path else None,
                no_viewport=False,
                window_width=window_w,
                window_height=window_h
            )
        )

        # Store the Chrome process to kill it later if needed
        _global_browser.chrome_process = chrome_process
        
        task = resolve_sensitive_env_variables(task)

        # Run the agent
        llm = utils.get_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            num_ctx=llm_num_ctx,
            temperature=llm_temperature,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )

        if agent_type == "org":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_org_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method,
                chrome_cdp=chrome_cdp
            )
        elif agent_type == "custom":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_custom_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                add_infos=add_infos,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method,
                chrome_cdp=chrome_cdp
            )
        else:
            raise ValueError(f"Invalid agent type: {agent_type}")

        return (
            final_result,
            errors,
            model_actions,
            model_thoughts,
            None,
            trace_file,
            history_file,
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )

    except gr.Error:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return (
            '',                                         # final_result
            errors,                                     # errors
            '',                                         # model_actions
            '',                                         # model_thoughts
            None,                                       # latest_video
            None,                                       # history_file
            None,                                       # trace_file
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )


async def run_org_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method,
        chrome_cdp
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state, _global_agent
        
        # Clear any previous stop request
        _global_agent_state.clear_stop()

        extra_chromium_args = [f"--window-size={window_w},{window_h}"]
        cdp_url = chrome_cdp

        if use_own_browser:
            cdp_url = os.getenv("CHROME_CDP", chrome_cdp)
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            chrome_user_data = os.getenv("CHROME_USER_DATA", None)
            if chrome_user_data:
                extra_chromium_args += [f"--user-data-dir={chrome_user_data}"]
        else:
            chrome_path = None
            
        if _global_browser is None:

            _global_browser = Browser(
                config=BrowserConfig(
                    headless=headless,
                    cdp_url=cdp_url,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

        if _global_browser_context is None:
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    cdp_url=cdp_url,
                    no_viewport=False,
                    window_width=window_w,
                    window_height=window_h
                )
            )

        if _global_agent is None:
            _global_agent = Agent(
                task=task,
                llm=llm,
                use_vision=use_vision,
                browser=_global_browser,
                browser_context=_global_browser_context,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        
        if not hasattr(_global_agent, 'agent_id'):
            _global_agent.agent_id = _global_agent.generate_agent_id()

        history = await _global_agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{_global_agent.agent_id}.json")
        _global_agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        _global_agent = None
        # Handle cleanup based on persistence configuration
        if not keep_browser_open:
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_custom_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method,
        chrome_cdp
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state, _global_agent

        # Clear any previous stop request
        _global_agent_state.clear_stop()

        extra_chromium_args = [f"--window-size={window_w},{window_h}"]
        cdp_url = chrome_cdp
        if use_own_browser:
            cdp_url = os.getenv("CHROME_CDP", chrome_cdp)

            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            chrome_user_data = os.getenv("CHROME_USER_DATA", None)
            if chrome_user_data:
                extra_chromium_args += [f"--user-data-dir={chrome_user_data}"]
        else:
            chrome_path = None

        controller = CustomController()

        # Initialize global browser if needed
        #if chrome_cdp not empty string nor None
        if ((_global_browser is None) or (cdp_url and cdp_url != "" and cdp_url != None)) :
            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    cdp_url=cdp_url,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

        if (_global_browser_context is None  or (chrome_cdp and cdp_url != "" and cdp_url != None)):
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    no_viewport=False,
                    window_width=window_w,
                    window_height=window_h
                )
            )


        # Create and run agent
        if _global_agent is None:
            _global_agent = CustomAgent(
                task=task,
                add_infos=add_infos,
                use_vision=use_vision,
                llm=llm,
                browser=_global_browser,
                browser_context=_global_browser_context,
                controller=controller,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
            
            # Add agent_id attribute if it doesn't exist
            if not hasattr(_global_agent, 'agent_id'):
                import uuid
                _global_agent.agent_id = f"custom_agent_{uuid.uuid4().hex[:8]}"
                
        history = await _global_agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{_global_agent.agent_id}.json")
        _global_agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)        

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        _global_agent = None
        # Handle cleanup based on persistence configuration
        if not keep_browser_open:
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_with_stream(
    agent_type,
    llm_provider,
    llm_model_name,
    llm_num_ctx,
    llm_temperature,
    llm_base_url,
    llm_api_key,
    use_own_browser,
    keep_browser_open,
    headless,
    disable_security,
    window_w,
    window_h,
    save_recording_path,
    save_agent_history_path,
    save_trace_path,
    enable_recording,
    task,
    add_infos,
    max_steps,
    use_vision,
    max_actions_per_step,
    tool_calling_method,
    chrome_cdp
):
    global _global_agent_state
    stream_vw = 100  # Make it full width
    stream_vh = 60   # Taller height for better visibility
    
    try:
        _global_agent_state.clear_stop()
        # Run the browser agent in the background
        agent_task = asyncio.create_task(
            run_browser_agent(
                agent_type=agent_type,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                llm_num_ctx=llm_num_ctx,
                llm_temperature=llm_temperature,
                llm_base_url=llm_base_url,
                llm_api_key=llm_api_key,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                enable_recording=enable_recording,
                task=task,
                add_infos=add_infos,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method,
                chrome_cdp=chrome_cdp
            )
        )

        # Initialize values for streaming
        html_content = f'<div style="width:100%; height:600px; display:flex; align-items:center; justify-content:center; background: white; border-radius:10px;"></div>'
        final_result = errors = model_actions = model_thoughts = ""
        latest_videos = trace = history_file = None

        # Periodically update the stream while the agent task is running
        while not agent_task.done():
            try:
                # Add debug output
                print("Attempting to capture screenshot...")
                
                # Make sure browser context exists
                if _global_browser_context is None:
                    print("Browser context is None, waiting...")
                    await asyncio.sleep(0.5)
                    continue
                    
                encoded_screenshot = await capture_screenshot(_global_browser_context)
                if encoded_screenshot is not None:
                    print(f"Screenshot captured, length: {len(encoded_screenshot)}")
                    html_content = f'<img src="data:image/jpeg;base64,{encoded_screenshot}" style="width:100%; height:600px; object-fit:contain; border:1px solid #eee; border-radius:10px;">'
                else:
                    print("Screenshot capture returned None")
                    await asyncio.sleep(0.5)
                    continue
            except Exception as e:
                print(f"Error capturing screenshot: {str(e)}")
                await asyncio.sleep(0.5)
                continue

            # Output to UI
            yield [
                html_content,  # This should show the browser screenshot
                final_result,
                errors,
                model_actions,
                model_thoughts,
                latest_videos,
                trace,
                history_file,
                gr.update(value="Stop", interactive=True),
                gr.update(interactive=True)
            ]
            
            await asyncio.sleep(0.2)  # Capture screenshots frequently

        # Once the agent task completes, get the results
        try:
            result = await agent_task
            final_result, errors, model_actions, model_thoughts, latest_videos, trace, history_file, stop_button, run_button = result
        except gr.Error:
            final_result = ""
            model_actions = ""
            model_thoughts = ""
            latest_videos = trace = history_file = None

        except Exception as e:
            errors = f"Agent error: {str(e)}"

        yield [
            html_content,
            final_result,
            errors,
            model_actions,
            model_thoughts,
            latest_videos,
            trace,
            history_file,
            stop_button,
            run_button
        ]

    except Exception as e:
        import traceback
        yield [
            f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>",
            "",
            f"Error: {str(e)}\n{traceback.format_exc()}",
            "",
            "",
            None,
            None,
            None,
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        ]

# Define the theme map globally
theme_map = {
    "Default": Default(),
    "Soft": Soft(),
    "Monochrome": Monochrome(),
    "Glass": Glass(),
    "Origin": Origin(),
    "Citrus": Citrus(),
    "Ocean": Ocean(),
    "Base": Base()
}

async def close_global_browser():
    global _global_browser, _global_browser_context

    if _global_browser_context:
        await _global_browser_context.close()
        _global_browser_context = None

    if _global_browser:
        # Kill the Chrome process if it exists
        if hasattr(_global_browser, 'chrome_process'):
            try:
                _global_browser.chrome_process.terminate()
            except:
                pass
                
        await _global_browser.close()
        _global_browser = None
        

def create_ui(theme_name="Soft"):
    # Clear any existing configurations
    config_dict = {
        "task": "",
        "save_recording_path": "./tmp/record_videos",
        "save_trace_path": "./tmp/traces",
        "save_agent_history_path": "./tmp/agent_history"
    }
    
    css = """
    /* Hide Gradio footer elements and API button */
    footer, .api-btn, .settings-btn {
        display: none !important;
    }
    
    /* Rest of your existing CSS */
    .gradio-container {
        background: white !important;
    }
    
    /* Base styling to match Durga AI aesthetic */
    .gradio-container {
        width: 100vw !important; 
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        font-family: 'Mukta Malar', 'Baloo Thambi 2', 'Catamaran', sans-serif;
    }
    
    /* Header styling without gradient */
    .header-text {
        text-align: center;
        margin: 0 !important;
        padding: 15px 0;
        color: #333;
        font-weight: 500;
        background: transparent !important;
        border-radius: 0 !important;
        width: 100% !important;
    }
    
    /* Remove background from the title */
    .header-text h1, .header-text p {
        background: transparent !important;
        margin: 0;
        padding: 0;
    }
    
    /* Section styling */
    .theme-section {
        margin: 0 !important;
        padding: 15px;
        background-color: white;  /* Changed to white */
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border-radius: 0 !important;
    }
    
    /* Container adjustments */
    .contain {
        margin: 0 !important;
        padding: 0 !important;
        max-width: 100% !important;
        background: white !important;  /* Added white background */
    }
    
    /* Row adjustments */
    .row {
        margin: 0 !important;
        padding: 0 !important;
        max-width: 100% !important;
        background: white !important;  /* Added white background */
    }
    
    /* Results area styling */
    .results-area {
        margin: 0 !important;
        padding: 15px;
        background-color: white;  /* Changed to white */
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border-radius: 0 !important;
    }
    
    /* Center text */
    .center-text {
        text-align: center;
        font-weight: 500;
        color: #333;
    }
    
    /* Button styling - slightly larger than previous reduction */
    .primary {
        background: linear-gradient(to right, rgb(108, 114, 239), rgb(255, 107, 139)) !important;
        border: none !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 7px 14px !important;      /* Slightly increased padding */
        min-width: 100px !important;       /* Slightly increased width */
        font-size: 14px !important;        /* Slightly increased font */
        height: 32px !important;           /* Slightly increased height */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
    }
    
    .stop {
        background: rgb(255, 107, 139) !important;
        border: none !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 7px 14px !important;      /* Slightly increased padding */
        min-width: 100px !important;       /* Slightly increased width */
        font-size: 14px !important;        /* Slightly increased font */
        height: 32px !important;           /* Slightly increased height */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
    }
    
    /* Input field styling */
    .theme-section input {
        height: 45px !important;
        border-radius: 25px !important;
        background: linear-gradient(to right, rgba(255, 192, 203, 0.2), rgba(255, 228, 225, 0.1)) !important;
        border: none !important;
        padding: 0 20px !important;
        color: rgb(107, 114, 128) !important;
        box-shadow: none !important;
    }
    
    /* Task Description label styling */
    .theme-section label span:first-child {
        color: rgb(99, 102, 241) !important;
        font-weight: 500;
    }

    /* Description text styling */
    .theme-section .info {
        color: rgb(156, 163, 175) !important;
    }

    .theme-section input::placeholder {
        color: rgb(156, 163, 175) !important;
    }
    
    /* Remove extra padding/margins */
    .gradio-container {
        padding-top: 0 !important;
    }
    
    .header-text {
        margin-bottom: 0 !important;
    }
    """

    with gr.Blocks(
            title="துர்கா AI - Browser Agent", 
            theme=theme_map[theme_name], 
            css=css
    ) as demo:
        with gr.Row(elem_classes=["header-text"]):
            gr.Markdown(
                """
                # 🌐 Browser Agent
                """,
            )

        # Create hidden components for fixed values
        agent_type = gr.Textbox(value="custom", visible=False)
        llm_provider = gr.Textbox(value="google", visible=False)
        llm_model_name = gr.Textbox(value="gemini-2.0-flash", visible=False)
        llm_num_ctx = gr.Number(value=1024, visible=False)
        llm_temperature = gr.Number(value=0.7, visible=False)
        llm_base_url = gr.Textbox(value="", visible=False)
        llm_api_key = gr.Textbox(value=os.getenv("GOOGLE_API_KEY", ""), visible=False)
        use_own_browser = gr.Checkbox(value=True, visible=False)
        keep_browser_open = gr.Checkbox(value=False, visible=False)
        headless = gr.Checkbox(value=True, visible=False)
        disable_security = gr.Checkbox(value=False, visible=False)
        window_w = gr.Number(value=1280, visible=False)
        window_h = gr.Number(value=720, visible=False)
        save_recording_path = gr.Textbox(value="./tmp/record_videos", visible=False)
        save_agent_history_path = gr.Textbox(value="./tmp/agent_history", visible=False)
        save_trace_path = gr.Textbox(value="./tmp/traces", visible=False)
        enable_recording = gr.Checkbox(value=False, visible=False)
        max_steps = gr.Number(value=10, visible=False)
        use_vision = gr.Checkbox(value=False, visible=False)
        max_actions_per_step = gr.Number(value=5, visible=False)
        tool_calling_method = gr.Textbox(value="auto", visible=False)
        chrome_cdp = gr.Textbox(value="", visible=False)

        # Visible components with Durga AI styling
        with gr.Group(elem_classes=["theme-section"]):
            with gr.Row(equal_height=True, variant="panel"):
                task = gr.Textbox(
                    label="Task Description",
                    lines=1,
                    value=None,
                    placeholder="Enter your task here...",
                    info="Describe what you want the agent to do",
                    interactive=True,
                    scale=6,  # Increased scale for wider textbox
                    container=False  # Removes container padding
                )
                with gr.Column(scale=2, min_width=300):  # Column for buttons
                    with gr.Row(equal_height=True):
                        run_button = gr.Button("▶ Run Agent", variant="primary", size="lg")
                        stop_button = gr.Button("Stop", variant="stop", size="lg")

        with gr.Row():
            browser_view = gr.HTML(
                value="<div style='width:100%; height:600px; display:flex; align-items:center; justify-content:center; background: white; border-radius:10px;'></div>",
                elem_classes=["browser-view"],
                visible=True  # Make sure this is visible
            )

        # Create hidden components for outputs (needed for the run_with_stream function)
        final_result_output = gr.Textbox(visible=False)
        errors_output = gr.Textbox(visible=False)
        model_actions_output = gr.Textbox(visible=False)
        model_thoughts_output = gr.Textbox(visible=False)
        recording_gif = gr.Image(visible=False)
        trace_file = gr.File(visible=False)
        agent_history_file = gr.File(visible=False)

        # Bind the stop button click event
        stop_button.click(
            fn=stop_agent,
            inputs=[],
            outputs=[
                errors_output,  # Make sure this is connected to display errors
                stop_button, 
                run_button
            ],
        )

        # Run button click handler
        run_button.click(
            fn=run_with_stream,
            inputs=[
                agent_type, llm_provider, llm_model_name, llm_num_ctx, llm_temperature, 
                llm_base_url, llm_api_key, use_own_browser, keep_browser_open, headless, 
                disable_security, window_w, window_h, save_recording_path, 
                save_agent_history_path, save_trace_path, enable_recording,
                task, gr.Textbox(value="", visible=False), max_steps, use_vision, max_actions_per_step, 
                tool_calling_method, chrome_cdp
            ],
            outputs=[
                browser_view,
                final_result_output,
                errors_output,
                model_actions_output,
                model_thoughts_output,
                recording_gif,
                trace_file,
                agent_history_file,
                stop_button,
                run_button
            ]
        )

    return demo

def main():
    parser = argparse.ArgumentParser(description="Gradio UI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Soft", choices=theme_map.keys(), help="Theme to use for the UI")
    parser.add_argument("--dark-mode", action="store_true", help="Enable dark mode")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    demo.launch(server_name=args.ip, server_port=args.port, share=True)

if __name__ == '__main__':
    main()