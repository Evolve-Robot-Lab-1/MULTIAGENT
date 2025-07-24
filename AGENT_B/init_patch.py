"""
Patch for browser_use initialization to prevent hanging
"""
import os
import sys
import logging

# Disable telemetry before any browser_use imports
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['BROWSER_USE_TELEMETRY'] = 'false'

# Save original logging state
_original_handlers = logging.root.handlers.copy()
_original_level = logging.root.level

def patch_browser_use_init():
    """Monkey patch browser_use to prevent early initialization"""
    # Temporarily redirect stdout/stderr during import
    import io
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    
    try:
        # Import browser_use to trigger its initialization
        import browser_use
        
        # Restore logging to original state
        logging.root.handlers = _original_handlers
        logging.root.level = _original_level
        
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr

# Apply the patch
patch_browser_use_init()