"""
Minimal Native API for debugging PyWebView
"""

import logging

logger = logging.getLogger(__name__)

# The absolute simplest API possible
minimal_api = {
    "test": lambda: "API is working!",
    "add": lambda x, y: x + y,
    "echo": lambda msg: f"Echo: {msg}"
}

logger.info("Minimal API created with 3 methods: test, add, echo")