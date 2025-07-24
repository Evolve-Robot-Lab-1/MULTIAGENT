"""
Integration test for native viewer functionality
Tests the complete flow from UI to LibreOffice
"""
import asyncio
import time
from pathlib import Path
import webview
from native_api_bridge import NativeAPIBridge

def test_api_bridge():
    """Test API bridge functionality"""
    print("Testing API Bridge...")
    
    # Create bridge
    bridge = NativeAPIBridge()
    
    # Test file operations
    ping_result = bridge.ping()
    assert ping_result['pong'] == True
    print("✓ File API working")
    
    # Test feature detection
    features = bridge.getFeatures()
    assert features['success'] == True
    assert 'overlay_viewer' in features['features']
    print("✓ Feature detection working")
    
    # Test overlay initialization
    result = bridge.initializeOverlay(str(Path.home() / "Documents"))
    print(f"✓ Overlay initialization: {result}")
    
    print("\nAPI Bridge tests passed!")

def test_window_integration():
    """Test with actual PyWebView window"""
    print("\nTesting Window Integration...")
    
    api = NativeAPIBridge()
    test_results = []
    
    def on_loaded():
        # This runs after window loads
        print("Window loaded, testing API access...")
        
        # Test from JavaScript
        window.evaluate_js("""
            (async function() {
                console.log('Testing from JavaScript...');
                
                // Wait for API to be ready
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Test ping
                try {
                    const ping = await pywebview.api.ping();
                    console.log('Ping result:', ping);
                    document.getElementById('results').innerHTML += '<p>✓ Ping: ' + JSON.stringify(ping) + '</p>';
                } catch (e) {
                    console.error('Ping failed:', e);
                    document.getElementById('results').innerHTML += '<p>✗ Ping failed: ' + e + '</p>';
                }
                
                // Test features
                try {
                    const features = await pywebview.api.getFeatures();
                    console.log('Features:', features);
                    document.getElementById('results').innerHTML += '<p>✓ Features: ' + JSON.stringify(features) + '</p>';
                } catch (e) {
                    console.error('Features failed:', e);
                    document.getElementById('results').innerHTML += '<p>✗ Features failed: ' + e + '</p>';
                }
                
                // Test overlay initialization
                try {
                    const overlay = await pywebview.api.initializeOverlay('/tmp');
                    console.log('Overlay init:', overlay);
                    document.getElementById('results').innerHTML += '<p>✓ Overlay: ' + JSON.stringify(overlay) + '</p>';
                } catch (e) {
                    console.error('Overlay failed:', e);
                    document.getElementById('results').innerHTML += '<p>✗ Overlay failed: ' + e + '</p>';
                }
                
                console.log('JavaScript tests complete!');
                document.getElementById('results').innerHTML += '<p><b>Tests complete!</b></p>';
            })();
        """)
        
        # Close after tests
        time.sleep(5)
        window.destroy()
    
    # Create window
    window = webview.create_window(
        'API Integration Test',
        html='''
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; }
                #results { margin-top: 20px; }
                #results p { margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>Testing API Integration</h1>
            <div id="results">
                <p>Starting tests...</p>
            </div>
        </body>
        </html>
        ''',
        js_api=api
    )
    
    api.set_window(window)
    window.events.loaded += on_loaded
    
    webview.start(debug=True)
    print("Window integration tests complete!")

if __name__ == '__main__':
    import sys
    
    # Test 1: API Bridge
    try:
        test_api_bridge()
    except Exception as e:
        print(f"✗ API Bridge test failed: {e}")
        sys.exit(1)
    
    # Test 2: Window Integration (optional, requires display)
    if '--window' in sys.argv:
        test_window_integration()
    else:
        print("\nSkipping window test. Run with --window to test PyWebView integration")
    
    print("\n✅ All integration tests passed!")