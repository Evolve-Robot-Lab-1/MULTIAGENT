#!/usr/bin/env python3
"""
DocAI - Document Intelligence Platform
Main entry point for the refactored application.
"""
import os
import sys
import asyncio
import signal
import threading
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app_with_services
from app.core.config import get_config, Config
from app.core.logging import get_logger
from app.services.agent_manager import AgentManager


# Global app instance for signal handlers
app = None
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = get_logger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    shutdown_event.set()
    
    # Stop Flask server
    if app:
        # TODO: Implement graceful Flask shutdown
        pass
    
    sys.exit(0)


async def initialize_services(app):
    """Initialize all async services."""
    logger = get_logger(__name__)
    
    try:
        # Initialize all services in container
        await app.container.initialize_all()
        logger.info("All services initialized successfully")
        
        # Auto-start browser agent if configured
        if app.docai_config.agent.auto_start_browser_agent:
            logger.info("Auto-starting browser agent...")
            agent_manager = app.container.get(AgentManager)
            await agent_manager.start_browser_agent()
            
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise


async def cleanup_services(app):
    """Clean up all services."""
    logger = get_logger(__name__)
    
    try:
        # Stop all agents
        agent_manager = app.container.get(AgentManager)
        await agent_manager.stop_all_agents()
        
        # Clean up all services
        await app.container.cleanup_all()
        logger.info("All services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)


def run_async_initialization(app):
    """Run async initialization in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(initialize_services(app))
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Async initialization failed: {e}")
    finally:
        loop.close()


def main():
    """Main entry point."""
    global app
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = get_config()
        
        # Create Flask app with services
        app = create_app_with_services(config)
        
        # Get logger after app creation
        logger = get_logger(__name__)
        
        logger.info(
            "Starting DocAI application",
            extra={
                'version': '2.0.0',
                'environment': config.environment,
                'host': config.server.host,
                'port': config.server.port,
                'debug': config.server.debug
            }
        )
        
        # Run async initialization in background
        init_thread = threading.Thread(
            target=run_async_initialization,
            args=(app,),
            daemon=True
        )
        init_thread.start()
        
        # Run Flask app
        app.run(
            host=config.server.host,
            port=config.server.port,
            debug=config.server.debug,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
        
    except Exception as e:
        print(f"Failed to start application: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up on exit
        if app:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(cleanup_services(app))
            loop.close()


if __name__ == '__main__':
    main()