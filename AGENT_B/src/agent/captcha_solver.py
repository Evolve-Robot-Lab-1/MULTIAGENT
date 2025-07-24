#!/usr/bin/env python3
"""
CAPTCHA Solver module for Agent_B
Handles Cloudflare Turnstile and other CAPTCHA challenges
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

class CaptchaSolver:
    """Specialized CAPTCHA solver for Agent_B"""
    
    def __init__(self, page):
        self.page = page
    
    async def detect_captcha_type(self):
        """Detect the type of CAPTCHA present on the page"""
        try:
            title = await self.page.title()
            content = await self.page.content()
            
            # Check for Cloudflare challenge
            if "just a moment" in title.lower():
                logger.info("🛡️ Detected Cloudflare challenge")
                return "cloudflare"
            
            # Check for other CAPTCHA types
            captcha_indicators = {
                "recaptcha": ["recaptcha", "g-recaptcha"],
                "hcaptcha": ["hcaptcha", "h-captcha"],
                "turnstile": ["turnstile", "cf-turnstile"],
                "generic": ["captcha", "verify", "challenge"]
            }
            
            for captcha_type, indicators in captcha_indicators.items():
                if any(indicator in content.lower() for indicator in indicators):
                    logger.info(f"🛡️ Detected {captcha_type} challenge")
                    return captcha_type
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA type: {e}")
            return None
    
    async def wait_for_captcha_elements(self, max_wait=30):
        """Wait for CAPTCHA elements to appear"""
        logger.info("⏳ Waiting for CAPTCHA elements to load...")
        
        for attempt in range(max_wait):
            try:
                # Look for Cloudflare specific elements
                cf_elements = await self.page.query_selector_all('[id*="cf-chl-widget"], .cf-turnstile, [data-sitekey]')
                
                # Look for general CAPTCHA elements
                general_elements = await self.page.query_selector_all('iframe[src*="captcha"], iframe[src*="turnstile"], input[type="checkbox"], [role="checkbox"]')
                
                all_captcha_elements = cf_elements + general_elements
                
                if all_captcha_elements:
                    logger.info(f"✅ Found {len(all_captcha_elements)} CAPTCHA elements after {attempt + 1} seconds")
                    return all_captcha_elements
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error checking for CAPTCHA elements: {e}")
                await asyncio.sleep(1)
        
        logger.warning(f"❌ No CAPTCHA elements found after {max_wait} seconds")
        return []
    
    async def solve_cloudflare_challenge(self):
        """Solve Cloudflare Turnstile challenge"""
        try:
            logger.info("🔧 Attempting to solve Cloudflare challenge...")
            
            # Wait for challenge elements to load
            elements = await self.wait_for_captcha_elements()
            
            if not elements:
                logger.warning("No CAPTCHA elements found")
                return False
            
            # Strategy 1: Look for the specific Cloudflare widget input
            cf_widget_input = None
            for element in elements:
                try:
                    element_id = await element.evaluate('el => el.id || ""')
                    if 'cf-chl-widget' in element_id:
                        cf_widget_input = element
                        logger.info(f"🎯 Found Cloudflare widget input: {element_id}")
                        break
                except Exception as e:
                    continue
            
            if cf_widget_input:
                # Try to interact with the widget input
                try:
                    logger.info("🖱️ Attempting to interact with Cloudflare widget...")
                    
                    # Even if not visible, try to focus and trigger events
                    await cf_widget_input.focus()
                    await asyncio.sleep(0.5)
                    
                    # Try to trigger common events that might activate the challenge
                    await cf_widget_input.evaluate('''
                        element => {
                            // Simulate various events that might trigger the challenge
                            element.dispatchEvent(new Event('focus'));
                            element.dispatchEvent(new Event('click'));
                            element.dispatchEvent(new Event('input'));
                            element.dispatchEvent(new Event('change'));
                        }
                    ''')
                    
                    await asyncio.sleep(2)
                    
                    # Check if challenge completed
                    new_title = await self.page.title()
                    if "just a moment" not in new_title.lower():
                        logger.info("✅ Cloudflare challenge appears to be completed!")
                        return True
                    
                except Exception as e:
                    logger.warning(f"Error interacting with widget: {e}")
            
            # Strategy 2: Look for iframes and try to interact within them
            iframes = await self.page.query_selector_all('iframe')
            for iframe in iframes:
                try:
                    src = await iframe.evaluate('el => el.src || ""')
                    if any(keyword in src.lower() for keyword in ['turnstile', 'cloudflare', 'challenge']):
                        logger.info(f"🖼️ Found challenge iframe: {src[:80]}")
                        
                        # Try to access iframe content
                        iframe_content = await iframe.content_frame()
                        if iframe_content:
                            # Look for checkboxes within iframe
                            checkboxes = await iframe_content.query_selector_all('input[type="checkbox"], [role="checkbox"]')
                            for checkbox in checkboxes:
                                try:
                                    logger.info("🖱️ Attempting to click iframe checkbox...")
                                    await checkbox.click()
                                    await asyncio.sleep(3)
                                    
                                    # Check if completed
                                    new_title = await self.page.title()
                                    if "just a moment" not in new_title.lower():
                                        logger.info("✅ Challenge completed via iframe interaction!")
                                        return True
                                        
                                except Exception as e:
                                    logger.debug(f"Error clicking iframe checkbox: {e}")
                
                except Exception as e:
                    logger.debug(f"Error with iframe: {e}")
            
            # Strategy 3: Try waiting longer for automatic completion
            logger.info("⏳ Waiting for automatic challenge completion...")
            for wait_time in range(10):
                await asyncio.sleep(1)
                new_title = await self.page.title()
                if "just a moment" not in new_title.lower():
                    logger.info("✅ Challenge completed automatically!")
                    return True
            
            logger.warning("❌ Cloudflare challenge could not be completed")
            return False
            
        except Exception as e:
            logger.error(f"Error solving Cloudflare challenge: {e}")
            return False
    
    async def solve_generic_captcha(self):
        """Solve generic CAPTCHA challenges"""
        try:
            logger.info("🔧 Attempting to solve generic CAPTCHA...")
            
            # Look for checkboxes
            checkboxes = await self.page.query_selector_all('input[type="checkbox"], [role="checkbox"]')
            for checkbox in checkboxes:
                try:
                    is_visible = await checkbox.evaluate('el => el.offsetParent !== null')
                    if is_visible:
                        logger.info("🖱️ Clicking visible checkbox...")
                        await checkbox.click()
                        await asyncio.sleep(2)
                        return True
                except Exception as e:
                    continue
            
            # Look for verify buttons
            verify_buttons = await self.page.query_selector_all('button, input[type="submit"], [role="button"]')
            for button in verify_buttons:
                try:
                    text = await button.evaluate('el => el.textContent || el.value || ""')
                    if any(keyword in text.lower() for keyword in ['verify', 'continue', 'proceed', 'submit']):
                        is_visible = await button.evaluate('el => el.offsetParent !== null')
                        if is_visible:
                            logger.info(f"🖱️ Clicking verify button: {text[:30]}")
                            await button.click()
                            await asyncio.sleep(2)
                            return True
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error solving generic CAPTCHA: {e}")
            return False
    
    async def solve_captcha(self):
        """Main CAPTCHA solving method"""
        try:
            captcha_type = await self.detect_captcha_type()
            
            if not captcha_type:
                logger.info("✅ No CAPTCHA detected")
                return True
            
            logger.info(f"🛡️ Attempting to solve {captcha_type} CAPTCHA...")
            
            if captcha_type == "cloudflare":
                return await self.solve_cloudflare_challenge()
            else:
                return await self.solve_generic_captcha()
                
        except Exception as e:
            logger.error(f"Error in CAPTCHA solver: {e}")
            return False 