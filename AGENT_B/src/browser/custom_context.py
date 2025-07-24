from browser_use.browser.context import BrowserContextConfig, BrowserContext
import logging

logger = logging.getLogger(__name__)

class CustomBrowserContext(BrowserContext):
    """Custom browser context extending the base BrowserContext class with anti-detection."""
    
    def __init__(self, browser, config: BrowserContextConfig = None):
        """Initialize a new browser context with the given configuration."""
        super().__init__(browser, config)
        logger.info("CustomBrowserContext initialized")
    
    async def get_session(self):
        """Get session with enhanced anti-detection scripts."""
        session = await super().get_session()
        
        # Add anti-detection scripts to the context
        if hasattr(session, 'context'):
            await self._add_anti_detection_scripts(session.context)
        
        return session
    
    async def _add_anti_detection_scripts(self, context):
        """Add anti-detection JavaScript to the browser context."""
        try:
            anti_detection_script = """
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock chrome runtime
            window.chrome = {
                runtime: {},
                app: {},
                csi: function() {},
                loadTimes: function() {},
            };
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Hide automation traces
            const getParameter = WebGLRenderingContext.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };
            
            // Mouse movement simulation for better CAPTCHA handling
            let mouseTrail = [];
            document.addEventListener('mousemove', function(e) {
                mouseTrail.push({x: e.clientX, y: e.clientY, time: Date.now()});
                if (mouseTrail.length > 10) mouseTrail.shift();
            });
            
            // Enhanced click simulation
            const originalClick = HTMLElement.prototype.click;
            HTMLElement.prototype.click = function() {
                // Add small random delay to simulate human behavior
                setTimeout(() => {
                    originalClick.call(this);
                }, Math.random() * 50 + 10);
            };
            
            // Better iframe handling for CAPTCHAs
            const originalCreateElement = document.createElement;
            document.createElement = function(tagName) {
                const element = originalCreateElement.call(document, tagName);
                if (tagName.toLowerCase() === 'iframe') {
                    element.addEventListener('load', function() {
                        // Allow iframe content to load fully
                        setTimeout(() => {
                            if (this.contentDocument) {
                                this.contentDocument.addEventListener('click', function(e) {
                                    e.stopPropagation();
                                });
                            }
                        }, 100);
                    });
                }
                return element;
            };
            """
            
            await context.add_init_script(anti_detection_script)
            logger.info("✅ Anti-detection scripts added to browser context")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to add anti-detection scripts: {e}")
    
    async def new_page(self):
        """Create a new page in the browser context with custom settings."""
        logger.info("Creating new page with custom settings")
        
        # Get the session first to access the context
        session = await self.get_session()
        
        # Create page using the playwright context directly
        page = await session.context.new_page()
        
        # Set additional page properties for better CAPTCHA handling
        try:
            # Set a realistic viewport
            await page.set_viewport_size({"width": 1280, "height": 720})
            
            # Set extra headers to appear more human-like
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            })
            
            logger.info("✅ Enhanced page settings applied")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to apply enhanced page settings: {e}")
        
        return page
    
    async def close(self):
        """Close the browser context with custom cleanup."""
        logger.info("Closing custom browser context")
        return await super().close() 