from browser_use.browser.browser import Browser, BrowserConfig
import logging
import os

logger = logging.getLogger(__name__)

class CustomBrowser(Browser):
    """Custom browser implementation extending the base Browser class."""
    
    def __init__(self, config: BrowserConfig = None):
        """Initialize a new browser instance with the given configuration."""
        super().__init__(config)
        logger.info("CustomBrowser initialized")
    
    async def launch(self):
        """Launch the browser with custom settings."""
        logger.info("Launching browser with custom settings")
        return await super().launch()
    
    async def close(self):
        """Close the browser with custom cleanup."""
        logger.info("Closing custom browser")
        return await super().close() 