from browser_use.agent.service import Agent
from browser_use.agent.prompts import SystemPrompt, AgentMessagePrompt
import logging
import asyncio
from .captcha_solver import CaptchaSolver

logger = logging.getLogger(__name__)

class CustomSystemPrompt(SystemPrompt):
    """Custom system prompt for the agent."""
    
    def __init__(self):
        super().__init__()
        
    def get_prompt(self):
        """Get the custom system prompt text."""
        return """You are a powerful AI agent controlling a web browser. You can help the user accomplish their task by browsing the web.
        
Follow these guidelines:
1. Use the tools available to you to accomplish the user's task
2. Be efficient and thorough
3. Explain your thought process
4. Ask for clarification if needed
5. When you've completed the task, summarize what you did
6. If you encounter CAPTCHA or verification challenges, wait for them to be automatically handled
7. If asked to solve a CAPTCHA manually, explain that automatic CAPTCHA solving is built-in
8. For sites with human verification, be patient and allow time for the challenge to complete
"""

class CustomAgentMessagePrompt(AgentMessagePrompt):
    """Custom message prompt for the agent."""
    
    def __init__(self):
        super().__init__()
        
    def get_prompt(self, task, additional_info=None):
        """Get the custom message prompt text."""
        prompt = f"""Task: {task}
        
I'll help you accomplish this task by browsing the web. I'll use the tools available to me."""
        
        if additional_info:
            prompt += f"\n\nAdditional information: {additional_info}"
            
        return prompt

class CustomAgent(Agent):
    """Custom agent implementation extending the base Agent class."""
    
    def __init__(self, task, llm, browser_context=None, **kwargs):
        """Initialize a new agent with the given task, LLM, and browser context."""
        # Remove config from kwargs if it exists since Agent doesn't accept it
        kwargs.pop('config', None)
        
        super().__init__(
            task=task,
            llm=llm,
            browser_context=browser_context,
            **kwargs
        )
        logger.info("CustomAgent initialized")
        
    async def _check_and_solve_captcha(self):
        """Check for and solve any CAPTCHA challenges before proceeding"""
        try:
            if self.browser_context:
                session = await self.browser_context.get_session()
                page = session.active_tab
                
                if page:
                    captcha_solver = CaptchaSolver(page)
                    captcha_detected = await captcha_solver.detect_captcha_type()
                    
                    if captcha_detected:
                        logger.info(f"🛡️ CAPTCHA detected: {captcha_detected}")
                        success = await captcha_solver.solve_captcha()
                        
                        if success:
                            logger.info("✅ CAPTCHA solved successfully")
                            # Wait a moment for page to update
                            await asyncio.sleep(2)
                        else:
                            logger.warning("⚠️ CAPTCHA solving failed")
                        
                        return success
                    else:
                        logger.debug("No CAPTCHA detected")
                        return True
                        
        except Exception as e:
            logger.error(f"Error in CAPTCHA check: {e}")
            return False
        
        return True
        
    async def run(self, max_steps=15, **kwargs):
        """Run the agent with custom implementation including CAPTCHA handling."""
        logger.info(f"Running custom agent for task: {self.task}")
        
        # Check for CAPTCHA before starting main task
        captcha_handled = await self._check_and_solve_captcha()
        if not captcha_handled:
            logger.warning("⚠️ CAPTCHA handling failed, but continuing with task...")
        
        return await super().run(max_steps=max_steps, **kwargs)
        
    def stop(self):
        """Stop the agent with custom cleanup."""
        logger.info("Stopping custom agent")
        super().stop() 