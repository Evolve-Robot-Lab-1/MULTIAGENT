/**
 * API Compatibility Layer
 * Handles different API structures and provides fallbacks
 */

class APICompatibility {
    constructor() {
        this.apiReady = false;
        this.overlayAvailable = false;
        this.initPromise = null;
    }
    
    async initialize() {
        if (this.initPromise) return this.initPromise;
        
        this.initPromise = this._doInitialize();
        return this.initPromise;
    }
    
    async _doInitialize() {
        console.log('[APICompat] Initializing...');
        
        // Wait for PyWebView to be ready
        await this.waitForPyWebView();
        
        // Detect API structure
        this.detectAPIStructure();
        
        // Check features
        await this.checkFeatures();
        
        console.log('[APICompat] Initialization complete');
        return this.apiReady;
    }
    
    async waitForPyWebView(timeout = 5000) {
        const start = Date.now();
        
        while (Date.now() - start < timeout) {
            if (window.pywebview && window.pywebview.api) {
                this.apiReady = true;
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        console.error('[APICompat] PyWebView API not available after timeout');
        return false;
    }
    
    detectAPIStructure() {
        if (!window.pywebview?.api) return;
        
        const api = window.pywebview.api;
        console.log('[APICompat] Detecting API structure...');
        
        // Create normalized API access
        window.nativeAPI = {
            // File operations
            pickFile: api.pickFile?.bind(api),
            
            // Overlay operations - try different patterns
            overlay: {
                initialize: (
                    api.initializeOverlay?.bind(api) ||
                    api.overlay?.initialize?.bind(api.overlay) ||
                    null
                ),
                loadDocument: (
                    api.loadDocumentOverlay?.bind(api) ||
                    api.overlay?.load_document_overlay?.bind(api.overlay) ||
                    null
                ),
                updateBounds: (
                    api.updateContainerBounds?.bind(api) ||
                    api.overlay?.update_container_bounds?.bind(api.overlay) ||
                    null
                ),
                stop: (
                    api.stopOverlay?.bind(api) ||
                    api.overlay?.stop_overlay?.bind(api.overlay) ||
                    null
                ),
                getStatus: (
                    api.getOverlayStatus?.bind(api) ||
                    api.overlay?.get_overlay_status?.bind(api.overlay) ||
                    null
                ),
                updateWindowPosition: (
                    api.updateWindowPosition?.bind(api) ||
                    api.overlay?.update_window_position?.bind(api.overlay) ||
                    null
                ),
                configureSyncEngine: (
                    api.configureSyncEngine?.bind(api) ||
                    api.overlay?.configure_sync_engine?.bind(api.overlay) ||
                    null
                ),
                getSyncMetrics: (
                    api.getSyncMetrics?.bind(api) ||
                    api.overlay?.get_sync_metrics?.bind(api.overlay) ||
                    null
                )
            },
            
            // Feature detection
            getFeatures: api.getFeatures?.bind(api),
            setFeature: api.setFeature?.bind(api)
        };
        
        // Check what's available
        this.overlayAvailable = !!(
            window.nativeAPI.overlay.initialize &&
            window.nativeAPI.overlay.loadDocument
        );
        
        console.log('[APICompat] Structure detected:', {
            fileAPI: !!window.nativeAPI.pickFile,
            overlayAPI: this.overlayAvailable,
            features: !!window.nativeAPI.getFeatures
        });
    }
    
    async checkFeatures() {
        try {
            if (window.nativeAPI?.getFeatures) {
                const result = await window.nativeAPI.getFeatures();
                if (result.success) {
                    console.log('[APICompat] Features:', result.features);
                    this.features = result.features;
                    
                    // Update overlay availability based on feature flag
                    if (!result.features.overlay_viewer) {
                        this.overlayAvailable = false;
                        console.log('[APICompat] Overlay disabled by feature flag');
                    }
                }
            }
        } catch (error) {
            console.error('[APICompat] Failed to get features:', error);
        }
    }
    
    isOverlayAvailable() {
        return this.overlayAvailable && this.features?.overlay_viewer;
    }
    
    async testAPI() {
        console.log('[APICompat] Running API tests...');
        
        if (!this.apiReady) {
            console.error('[APICompat] API not ready for testing');
            return false;
        }
        
        const tests = {
            ping: false,
            features: false,
            overlay: false
        };
        
        try {
            // Test ping
            if (window.pywebview.api.ping) {
                const ping = await window.pywebview.api.ping();
                tests.ping = ping?.pong === true;
                console.log('[APICompat] Ping test:', tests.ping);
            }
            
            // Test features
            if (window.nativeAPI.getFeatures) {
                const features = await window.nativeAPI.getFeatures();
                tests.features = features?.success === true;
                console.log('[APICompat] Features test:', tests.features);
            }
            
            // Test overlay status
            if (window.nativeAPI.overlay.getStatus) {
                const status = await window.nativeAPI.overlay.getStatus();
                tests.overlay = status !== null;
                console.log('[APICompat] Overlay test:', tests.overlay);
            }
            
        } catch (error) {
            console.error('[APICompat] Test error:', error);
        }
        
        console.log('[APICompat] Test results:', tests);
        return tests;
    }
}

// Create global instance
window.apiCompat = new APICompatibility();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.apiCompat.initialize().then(() => {
        console.log('[APICompat] Ready, overlay available:', window.apiCompat.isOverlayAvailable());
        
        // Run tests in debug mode
        if (window.location.search.includes('debug')) {
            window.apiCompat.testAPI();
        }
    });
});

// Also try on pywebviewready event
window.addEventListener('pywebviewready', () => {
    console.log('[APICompat] PyWebView ready event received');
    window.apiCompat.initialize();
});