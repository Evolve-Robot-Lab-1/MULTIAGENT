from browser_use.agent.prompts import SystemPrompt, AgentMessagePrompt
import logging

logger = logging.getLogger(__name__)

class CustomSystemPrompt(SystemPrompt):
    """Extended custom system prompt for the agent with detailed instructions."""
    
    def __init__(self):
        super().__init__()
        
    def get_prompt(self):
        """Get the detailed custom system prompt text."""
        return """You are a powerful AI agent controlling a web browser. You can help the user accomplish their task by browsing the web.
        
Follow these guidelines:
1. Use the tools available to you to accomplish the user's task
2. Be efficient and thorough in your exploration
3. Explain your thought process clearly as you work
4. Ask for clarification if the task is ambiguous
5. When you've completed the task, summarize what you did and what you found
6. If you encounter any errors, describe them and suggest alternatives

You have these browser capabilities:
- Navigate to URLs
- Click on elements
- Type text into forms
- Extract information from pages
- Take screenshots
- Scroll and manipulate the page
- Wait for elements to appear

Follow web best practices:
- Respect website terms of service
- Don't try to bypass security measures
- Be careful with sensitive information
- Consider user privacy
"""

class CustomAgentMessagePrompt(AgentMessagePrompt):
    """Extended custom message prompt for the agent with additional context handling."""
    
    def __init__(self):
        super().__init__()
        
    def get_prompt(self, task, additional_info=None):
        """Get the extended custom message prompt text with enhanced formatting."""
        prompt = f"""# Task: {task}
        
I'll help you accomplish this task by browsing the web. I'll use the tools available to me and explain my approach as I work through it."""
        
        if additional_info:
            prompt += f"\n\n## Additional Context:\n{additional_info}"
            
        prompt += """

## Approach:
1. I'll start by understanding what needs to be done
2. I'll plan the necessary browsing steps
3. I'll execute each step carefully
4. I'll extract the relevant information
5. I'll provide a clear summary of my findings

Let me begin..."""
            
        return prompt 