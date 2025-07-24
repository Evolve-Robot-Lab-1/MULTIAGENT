/**
 * Debug Panel for PyWebView API Testing
 */

// Debug panel functions
let debugPanel = null;
let debugContent = null;

window.toggleDebugPanel = function() {
    if (!debugPanel) {
        debugPanel = document.getElementById('debugPanel');
        debugContent = document.getElementById('debugContent');
    }
    if (debugPanel) {
        debugPanel.style.display = debugPanel.style.display === 'none' ? 'block' : 'none';
    }
}

window.clearDebugPanel = function() {
    if (!debugContent) {
        debugContent = document.getElementById('debugContent');
    }
    if (debugContent) {
        debugContent.innerHTML = '';
    }
}

window.debugLog = function(message, type = 'info') {
    if (!debugContent) {
        debugContent = document.getElementById('debugContent');
    }
    if (debugContent) {
        const timestamp = new Date().toLocaleTimeString();
        const color = type === 'error' ? '#f44336' : type === 'success' ? '#4CAF50' : '#9cdcfe';
        const entry = '<div style="color: ' + color + '; margin: 2px 0;">[' + timestamp + '] ' + message + '</div>';
        debugContent.innerHTML += entry;
        debugContent.scrollTop = debugContent.scrollHeight;
    }
}

window.testAPIDebug = function() {
    debugLog('=== Testing PyWebView API ===', 'info');
    
    // Check pywebview
    debugLog('typeof pywebview: ' + typeof pywebview, typeof pywebview !== 'undefined' ? 'success' : 'error');
    
    if (typeof pywebview !== 'undefined') {
        debugLog('pywebview exists', 'success');
        
        // Check api
        debugLog('typeof pywebview.api: ' + typeof pywebview.api, typeof pywebview.api !== 'undefined' ? 'success' : 'error');
        
        if (typeof pywebview.api !== 'undefined') {
            debugLog('pywebview.api exists', 'success');
            
            // Add a delay to allow API to fully initialize
            debugLog('Waiting 1 second for API to fully initialize...', 'info');
            setTimeout(function() {
                debugLog('Checking API after delay...', 'info');
                
                // Try to list methods
                try {
                    const keys = Object.keys(pywebview.api);
                    debugLog('API methods: ' + keys.join(', '), 'success');
                    
                    // Check specific methods
                    keys.forEach(function(key) {
                        const type = typeof pywebview.api[key];
                        debugLog('  ' + key + ': ' + type, type === 'function' ? 'success' : 'info');
                    });
                } catch (e) {
                    debugLog('Error listing methods: ' + e.message, 'error');
                }
                
                // Test specific methods we expect
                const expectedMethods = ['pickFile', 'checkLibreOffice', 'embedDocument', 'ping', 'getAvailableMethods'];
                debugLog('Checking expected methods:', 'info');
                expectedMethods.forEach(function(method) {
                    const exists = method in pywebview.api;
                    const isFunction = exists && typeof pywebview.api[method] === 'function';
                    debugLog('  ' + method + ': ' + (isFunction ? 'function' : exists ? typeof pywebview.api[method] : 'NOT FOUND'), 
                             isFunction ? 'success' : 'error');
                });
                
                // Test ping if available
                if (typeof pywebview.api.ping === 'function') {
                    pywebview.api.ping().then(function(result) {
                        debugLog('ping() result: ' + result, 'success');
                    }).catch(function(e) {
                        debugLog('ping() error: ' + e.message, 'error');
                    });
                }
                
                // Test getAvailableMethods if available
                if (typeof pywebview.api.getAvailableMethods === 'function') {
                    pywebview.api.getAvailableMethods().then(function(methods) {
                        debugLog('getAvailableMethods() result: ' + JSON.stringify(methods), 'success');
                    }).catch(function(e) {
                        debugLog('getAvailableMethods() error: ' + e.message, 'error');
                    });
                }
            }, 1000);  // End of setTimeout
        } else {
            debugLog('pywebview.api is undefined!', 'error');
            
            // Check if it's a timing issue
            debugLog('Will check again in 2 seconds...', 'info');
            setTimeout(function() {
                if (typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined') {
                    debugLog('API appeared after delay!', 'success');
                    testAPIDebug(); // Re-run the test
                } else {
                    debugLog('API still not available after delay', 'error');
                }
            }, 2000);
        }
    } else {
        debugLog('pywebview is undefined!', 'error');
    }
}

window.testNativeAPI = function() {
    // Ensure debug panel is visible
    const panel = document.getElementById('debugPanel');
    if (panel && panel.style.display === 'none') {
        toggleDebugPanel();
    }
    // Run test
    testAPIDebug();
}

// Auto-check on load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Debug panel script loaded');
});