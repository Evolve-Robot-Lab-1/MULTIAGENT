import logging
import asyncio

logger = logging.getLogger(__name__)

class CustomController:
    """Custom controller implementation for managing agent execution."""
    
    def __init__(self):
        """Initialize a new controller instance."""
        logger.info("CustomController initialized")
        self.running = False
        self.event_loop = None
        
    async def start(self, agent, task, max_steps=15, additional_info=None, callback=None):
        """Start the agent with the given task and configuration."""
        logger.info(f"Starting agent with task: {task}")
        self.running = True
        
        try:
            # Initialize results
            result = {
                "success": False,
                "error": None,
                "output": "",
                "steps": 0
            }
            
            # Run the agent (task is already set in the agent)
            output = await agent.run(max_steps=max_steps)
            
            # Update results
            result["success"] = True
            result["output"] = str(output) if output else "Agent completed successfully"
            result["steps"] = getattr(agent.state, 'n_steps', max_steps)
            
            # Call the callback if provided
            if callback and callable(callback):
                callback(result)
                
            return result
            
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            
            # Update error result
            result["error"] = str(e)
            
            # Call the callback if provided
            if callback and callable(callback):
                callback(result)
                
            return result
            
        finally:
            self.running = False
            
    def stop(self):
        """Stop the controller and any running processes."""
        logger.info("Stopping controller")
        self.running = False 