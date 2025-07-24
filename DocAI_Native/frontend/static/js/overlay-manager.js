/**
 * LibreOffice Overlay Manager for Frontend
 * 
 * Handles interaction with the native overlay positioning system
 */

class OverlayManager {
    constructor() {
        this.initialized = false;
        this.currentState = 'idle';
        this.container = null;
        this.overlayActive = false;
        this.viewMode = 'html'; // 'html' or 'native'
        
        // Performance monitoring
        this.positionUpdateInterval = null;
        this.lastBounds = null;
        
        // Callbacks
        this.onStateChange = null;
        this.onError = null;
    }
    
    /**
     * Initialize overlay manager
     * @param {string} containerId - ID of container element
     * @param {string} documentsDir - Path to documents directory
     */
    async initialize(containerId, documentsDir) {
        try {
            // Ensure API compatibility layer is ready
            await window.apiCompat.initialize();
            
            if (!window.apiCompat.isOverlayAvailable()) {
                console.warn('Overlay API not available');
                return false;
            }
            
            this.container = document.getElementById(containerId);
            if (!this.container) {
                throw new Error(`Container ${containerId} not found`);
            }
            
            // Use normalized API
            const result = await window.nativeAPI.overlay.initialize(documentsDir);
            
            if (result.success) {
                this.initialized = true;
                this.setupEventListeners();
                this.startPositionMonitoring();
                
                console.log('Overlay manager initialized:', result);
                return true;
            } else {
                throw new Error(result.error || 'Failed to initialize overlay');
            }
            
        } catch (error) {
            console.error('Failed to initialize overlay manager:', error);
            this.handleError(error.message);
            return false;
        }
    }
    
    /**
     * Load document with overlay positioning
     * @param {string} filename - Document filename
     */
    async loadDocumentNative(filename) {
        if (!this.initialized) {
            console.error('Overlay manager not initialized');
            return false;
        }
        
        try {
            // Get container bounds
            const bounds = this.getContainerBounds();
            
            // Show loading state
            this.showLoading();
            
            // Load document with overlay
            const result = await window.nativeAPI.overlay.loadDocument(
                filename,
                bounds
            );
            
            if (result.success) {
                this.overlayActive = true;
                this.viewMode = 'native';
                this.currentState = result.state;
                
                // Hide loading state
                this.hideLoading();
                
                // Update UI
                this.updateViewModeUI();
                
                return true;
            } else {
                throw new Error(result.error || 'Failed to load document');
            }
            
        } catch (error) {
            console.error('Failed to load document with overlay:', error);
            this.handleError(error.message);
            this.hideLoading();
            return false;
        }
    }
    
    /**
     * Stop overlay and return to HTML view
     */
    async stopOverlay() {
        if (!this.overlayActive) {
            return;
        }
        
        try {
            const result = await window.nativeAPI.overlay.stop();
            
            if (result.success) {
                this.overlayActive = false;
                this.viewMode = 'html';
                this.currentState = 'idle';
                
                // Update UI
                this.updateViewModeUI();
                
                // Clear container
                if (this.container) {
                    this.container.innerHTML = '';
                }
            }
            
        } catch (error) {
            console.error('Failed to stop overlay:', error);
            this.handleError(error.message);
        }
    }
    
    /**
     * Get container element bounds
     */
    getContainerBounds() {
        if (!this.container) {
            return null;
        }
        
        const rect = this.container.getBoundingClientRect();
        return {
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height,
            top: rect.top,
            left: rect.left,
            bottom: rect.bottom,
            right: rect.right
        };
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', this.debounce(() => {
            this.updateContainerBounds();
        }, 100));
        
        // Container mutations
        if (this.container) {
            const observer = new ResizeObserver(() => {
                this.updateContainerBounds();
            });
            observer.observe(this.container);
        }
        
        // Window move detection (if supported)
        this.detectWindowMove();
    }
    
    /**
     * Start position monitoring
     */
    startPositionMonitoring() {
        // Update position at 30 FPS
        this.positionUpdateInterval = setInterval(() => {
            if (this.overlayActive) {
                this.updateContainerBounds();
            }
        }, 33); // ~30 FPS
    }
    
    /**
     * Stop position monitoring
     */
    stopPositionMonitoring() {
        if (this.positionUpdateInterval) {
            clearInterval(this.positionUpdateInterval);
            this.positionUpdateInterval = null;
        }
    }
    
    /**
     * Update container bounds if changed
     */
    async updateContainerBounds() {
        if (!this.overlayActive) {
            return;
        }
        
        const bounds = this.getContainerBounds();
        
        // Check if bounds changed significantly
        if (this.boundsChanged(bounds, this.lastBounds)) {
            this.lastBounds = bounds;
            
            try {
                await window.nativeAPI.overlay.updateBounds(bounds);
            } catch (error) {
                console.error('Failed to update container bounds:', error);
            }
        }
    }
    
    /**
     * Check if bounds changed significantly
     */
    boundsChanged(bounds1, bounds2, threshold = 2) {
        if (!bounds1 || !bounds2) {
            return true;
        }
        
        return Math.abs(bounds1.x - bounds2.x) > threshold ||
               Math.abs(bounds1.y - bounds2.y) > threshold ||
               Math.abs(bounds1.width - bounds2.width) > threshold ||
               Math.abs(bounds1.height - bounds2.height) > threshold;
    }
    
    /**
     * Detect window move events
     */
    detectWindowMove() {
        let lastX = window.screenX;
        let lastY = window.screenY;
        
        setInterval(async () => {
            if (window.screenX !== lastX || window.screenY !== lastY) {
                lastX = window.screenX;
                lastY = window.screenY;
                
                if (this.overlayActive) {
                    try {
                        await window.nativeAPI.overlay.updateWindowPosition(
                            lastX,
                            lastY
                        );
                    } catch (error) {
                        console.error('Failed to update window position:', error);
                    }
                }
            }
        }, 100);
    }
    
    /**
     * Toggle between HTML and native view
     */
    async toggleViewMode() {
        if (this.viewMode === 'html') {
            // Switch to native view
            const currentFile = this.getCurrentFile();
            if (currentFile) {
                await this.loadDocumentNative(currentFile);
            }
        } else {
            // Switch to HTML view
            await this.stopOverlay();
            
            // Reload document in HTML mode
            const currentFile = this.getCurrentFile();
            if (currentFile && window.documentViewer) {
                window.documentViewer.loadDocumentHTML(currentFile);
            }
        }
    }
    
    /**
     * Get current loaded file
     */
    getCurrentFile() {
        // This should be implemented based on your document viewer
        return window.currentDocument || null;
    }
    
    /**
     * Configure sync engine settings
     */
    async configureSyncEngine(settings) {
        try {
            const result = await window.nativeAPI.overlay.configureSyncEngine(settings);
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to configure sync engine');
            }
            
        } catch (error) {
            console.error('Failed to configure sync engine:', error);
            this.handleError(error.message);
        }
    }
    
    /**
     * Get overlay status
     */
    async getStatus() {
        try {
            return await window.nativeAPI.overlay.getStatus();
        } catch (error) {
            console.error('Failed to get overlay status:', error);
            return null;
        }
    }
    
    /**
     * Get sync metrics
     */
    async getSyncMetrics() {
        try {
            return await window.nativeAPI.overlay.getSyncMetrics();
        } catch (error) {
            console.error('Failed to get sync metrics:', error);
            return null;
        }
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        if (this.container) {
            this.container.innerHTML = `
                <div class="overlay-loading">
                    <div class="spinner"></div>
                    <p>Loading LibreOffice...</p>
                </div>
            `;
        }
    }
    
    /**
     * Hide loading state
     */
    hideLoading() {
        const loading = this.container?.querySelector('.overlay-loading');
        if (loading) {
            loading.remove();
        }
    }
    
    /**
     * Update view mode UI
     */
    updateViewModeUI() {
        // Update toggle button
        const toggleBtn = document.getElementById('viewer-mode-toggle');
        if (toggleBtn) {
            const modeText = toggleBtn.querySelector('#viewer-mode-text');
            if (modeText) {
                modeText.textContent = this.viewMode === 'html' ? 'HTML View' : 'Native View';
            }
        }
        
        // Update container class
        if (this.container) {
            this.container.classList.toggle('native-mode', this.viewMode === 'native');
            this.container.classList.toggle('html-mode', this.viewMode === 'html');
        }
    }
    
    /**
     * Handle errors
     */
    handleError(message) {
        console.error('Overlay error:', message);
        
        if (this.onError) {
            this.onError(message);
        }
        
        // Show error in UI
        if (this.container && this.overlayActive) {
            this.container.innerHTML = `
                <div class="overlay-error">
                    <p>Error: ${message}</p>
                    <button onclick="overlayManager.stopOverlay()">Return to HTML View</button>
                </div>
            `;
        }
    }
    
    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Cleanup
     */
    destroy() {
        this.stopPositionMonitoring();
        if (this.overlayActive) {
            this.stopOverlay();
        }
    }
}

// Create global instance
window.overlayManager = new OverlayManager();