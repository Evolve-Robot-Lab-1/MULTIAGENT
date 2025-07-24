/**
 * Viewer Mode Manager
 * Handles switching between HTML and Native document viewing modes
 */

class ViewerModeManager {
    constructor() {
        // Safe localStorage access
        try {
            this.currentMode = localStorage.getItem('viewerMode') || 'html';
        } catch (e) {
            console.warn('localStorage not available, defaulting to html mode');
            this.currentMode = 'html';
        }
        this.currentDocument = null;
        this.initializeUI();
        console.log('ViewerModeManager initialized with mode:', this.currentMode);
    }
    
    initializeUI() {
        // Update button text based on current mode
        this.updateButtonText();
    }
    
    updateButtonText() {
        const modeText = document.getElementById('viewerModeText');
        if (modeText) {
            modeText.textContent = this.currentMode === 'html' ? 'HTML View' : 'Native View';
        }
    }
    
    async toggleMode() {
        const newMode = this.currentMode === 'html' ? 'native' : 'html';
        
        // If switching to native mode, check if overlay system is available
        if (newMode === 'native' && window.overlayManager) {
            if (!window.overlayManager.initialized) {
                console.warn('Overlay system not initialized');
                alert('Native viewer is not available. Please try again later.');
                return;
            }
        }
        
        this.currentMode = newMode;
        
        // Safe localStorage access
        try {
            localStorage.setItem('viewerMode', this.currentMode);
        } catch (e) {
            console.warn('Could not save viewer mode preference');
        }
        
        console.log('Viewer mode switched to:', this.currentMode);
        
        // Update UI
        this.updateButtonText();
        
        // Reload current document in new mode if one is open
        if (this.currentDocument) {
            await this.loadDocument(this.currentDocument);
        }
    }
    
    loadDocument(filename) {
        this.currentDocument = filename;
        
        console.log(`Loading document '${filename}' in ${this.currentMode} mode`);
        
        if (this.currentMode === 'native') {
            this.loadNativeDocument(filename);
        } else {
            // Call existing function for HTML mode
            if (typeof window.displayDocumentFromBackend === 'function') {
                window.displayDocumentFromBackend(filename);
            } else {
                console.error('displayDocumentFromBackend function not found');
            }
        }
    }
    
    async loadNativeDocument(filename) {
        const chatContainer = document.querySelector('.chat-container');
        if (!chatContainer) {
            console.error('Chat container not found');
            return;
        }
        
        // Check if overlay manager is available
        if (!window.overlayManager || !window.overlayManager.initialized) {
            console.error('Overlay manager not initialized');
            alert('Native viewer is not available. Switching to HTML view.');
            this.currentMode = 'html';
            this.updateButtonText();
            this.loadDocument(filename);
            return;
        }
        
        // Show loading state with viewer toggle
        chatContainer.innerHTML = `
            <div class="file-viewer">
                <div class="file-viewer-header">
                    <h3>📄 ${filename}</h3>
                    <div class="header-controls" style="display: flex; gap: 10px; align-items: center;">
                        <button id="viewer-mode-toggle" onclick="toggleViewerMode()" title="Toggle Viewer Mode">
                            <span id="viewer-mode-text">Native View</span>
                        </button>
                        <button onclick="closeFileViewer()" class="close-btn">✕</button>
                    </div>
                </div>
                <div class="file-viewer-content" id="native-viewer-container" style="position: relative; width: 100%; height: 100%;">
                    <!-- LibreOffice will be positioned here -->
                </div>
            </div>
        `;
        
        // Update button text after DOM update
        setTimeout(() => this.updateButtonText(), 100);
        
        // Load document using overlay manager
        try {
            const container = document.getElementById('native-viewer-container');
            if (container) {
                await window.overlayManager.loadDocumentNative(filename);
            }
        } catch (error) {
            console.error('Failed to load document in native viewer:', error);
            alert('Failed to load document in native viewer. Switching to HTML view.');
            this.currentMode = 'html';
            this.updateButtonText();
            this.loadDocument(filename);
        }
        
        try {
            // Get current window position and size for positioning native window
            const windowInfo = {
                x: window.screenX || 0,
                y: window.screenY || 0,
                width: window.innerWidth || 1200,
                height: window.innerHeight || 800
            };
            
            // Make API call to open native document window
            const response = await fetch(`/api/v1/view_document_native/${encodeURIComponent(filename)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(windowInfo)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                console.log('Native document window opened:', result);
                
                // Store document ID for control operations
                this.currentDocumentId = result.doc_id;
                
                // Update UI to show native controls
                this.showNativeControls(filename, result);
            } else {
                console.error('Failed to open native viewer:', result);
                this.handleNativeViewerError(filename, result.error || 'Failed to open native viewer');
            }
        } catch (error) {
            console.error('Error opening native viewer:', error);
            this.handleNativeViewerError(filename, error.message);
        }
    }
    
    showNativeControls(filename, documentInfo) {
        const chatContainer = document.querySelector('.chat-container');
        if (!chatContainer) return;
        
        const docInfo = documentInfo.info || {};
        const controls = documentInfo.controls || {};
        
        chatContainer.innerHTML = `
            <div class="file-viewer native-viewer-placeholder">
                <div class="file-viewer-header">
                    <h3>📄 ${filename}</h3>
                    <div class="viewer-mode-toggle" id="viewerModeToggle" style="display: inline-block;">
                        <button class="btn btn-sm btn-outline-secondary" id="toggleViewerBtn" onclick="toggleViewerMode()" title="Toggle Viewer Mode">
                            <i class="fas fa-exchange-alt"></i>
                            <span id="viewerModeText">Native View</span>
                        </button>
                    </div>
                    <button onclick="viewerManager.closeNativeDocument()" class="close-btn">✕</button>
                </div>
                <div class="native-viewer-info" style="padding: 30px; text-align: center;">
                    <div style="background: #f0f0f0; border-radius: 10px; padding: 30px; margin: 20px auto; max-width: 600px;">
                        <i class="fas fa-window-restore" style="font-size: 48px; color: #2196F3; margin-bottom: 20px;"></i>
                        <h3>Document Opened in Native Viewer</h3>
                        <p style="margin: 20px 0; color: #666;">
                            The document is displayed in a separate LibreOffice window for full native functionality.
                        </p>
                        
                        <div class="document-info" style="text-align: left; margin: 20px 0;">
                            <p><strong>Title:</strong> ${docInfo.title || filename}</p>
                            ${docInfo.pages ? `<p><strong>Pages:</strong> ${docInfo.pages}</p>` : ''}
                            ${docInfo.author ? `<p><strong>Author:</strong> ${docInfo.author}</p>` : ''}
                        </div>
                        
                        <div class="native-controls" style="margin-top: 30px;">
                            <h4>Document Controls</h4>
                            <div style="display: flex; gap: 10px; justify-content: center; margin-top: 15px;">
                                <button class="btn btn-primary" onclick="viewerManager.zoomDocument(75)">
                                    <i class="fas fa-search-minus"></i> 75%
                                </button>
                                <button class="btn btn-primary" onclick="viewerManager.zoomDocument(100)">
                                    <i class="fas fa-search"></i> 100%
                                </button>
                                <button class="btn btn-primary" onclick="viewerManager.zoomDocument(125)">
                                    <i class="fas fa-search-plus"></i> 125%
                                </button>
                            </div>
                            
                            ${docInfo.pages > 1 ? `
                            <div style="margin-top: 20px;">
                                <h5>Page Navigation</h5>
                                <div style="display: flex; gap: 10px; align-items: center; justify-content: center; margin-top: 10px;">
                                    <button class="btn btn-secondary" onclick="viewerManager.previousPage()">
                                        <i class="fas fa-chevron-left"></i> Previous
                                    </button>
                                    <input type="number" id="pageNumber" value="1" min="1" max="${docInfo.pages}" 
                                           style="width: 60px; text-align: center;" 
                                           onchange="viewerManager.goToPage(this.value)">
                                    <span>/ ${docInfo.pages}</span>
                                    <button class="btn btn-secondary" onclick="viewerManager.nextPage()">
                                        Next <i class="fas fa-chevron-right"></i>
                                    </button>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                        
                        <div style="margin-top: 30px;">
                            <p style="font-size: 14px; color: #888;">
                                <i class="fas fa-info-circle"></i> 
                                The document window may be behind this window. Check your taskbar.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Update button text
        this.updateButtonText();
        
        // Store page info for navigation
        this.currentPageInfo = {
            current: 1,
            total: docInfo.pages || 1
        };
    }
    
    handleNativeViewerError(filename, errorMessage = 'Unable to load document in native viewer mode.') {
        // Show error message with option to switch to HTML view
        const chatContainer = document.querySelector('.chat-container');
        if (!chatContainer) return;
        
        chatContainer.innerHTML = `
            <div class="file-viewer">
                <div class="file-viewer-header">
                    <h3>📄 ${filename}</h3>
                    <button onclick="closeFileViewer()" class="close-btn">✕</button>
                </div>
                <div class="file-viewer-content" style="text-align: center; padding: 50px;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #f44336;"></i>
                    <h3>Native Viewer Error</h3>
                    <p>${errorMessage}</p>
                    <button class="btn btn-primary" onclick="viewerManager.switchToHtmlView('${filename}')">
                        Switch to HTML View
                    </button>
                </div>
            </div>
        `;
    }
    
    async zoomDocument(zoomLevel) {
        if (!this.currentDocumentId) {
            console.error('No document currently open');
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/document/${this.currentDocumentId}/zoom`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ zoom: zoomLevel })
            });
            
            const result = await response.json();
            if (!response.ok || !result.success) {
                console.error('Zoom failed:', result);
                this.showModeNotification('Failed to set zoom level', 'error');
            }
        } catch (error) {
            console.error('Error setting zoom:', error);
            this.showModeNotification('Failed to set zoom level', 'error');
        }
    }
    
    async goToPage(pageNum) {
        if (!this.currentDocumentId) {
            console.error('No document currently open');
            return;
        }
        
        const page = parseInt(pageNum);
        if (isNaN(page) || page < 1 || page > this.currentPageInfo.total) {
            this.showModeNotification('Invalid page number', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/document/${this.currentDocumentId}/page`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ page: page })
            });
            
            const result = await response.json();
            if (response.ok && result.success) {
                this.currentPageInfo.current = page;
                // Update page input if it exists
                const pageInput = document.getElementById('pageNumber');
                if (pageInput) {
                    pageInput.value = page;
                }
            } else {
                console.error('Page navigation failed:', result);
                this.showModeNotification('Failed to navigate to page', 'error');
            }
        } catch (error) {
            console.error('Error navigating to page:', error);
            this.showModeNotification('Failed to navigate to page', 'error');
        }
    }
    
    previousPage() {
        if (this.currentPageInfo.current > 1) {
            this.goToPage(this.currentPageInfo.current - 1);
        }
    }
    
    nextPage() {
        if (this.currentPageInfo.current < this.currentPageInfo.total) {
            this.goToPage(this.currentPageInfo.current + 1);
        }
    }
    
    async closeNativeDocument() {
        if (!this.currentDocumentId) {
            // Just close the viewer UI
            closeFileViewer();
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/document/${this.currentDocumentId}/close`, {
                method: 'POST'
            });
            
            const result = await response.json();
            if (!response.ok || !result.success) {
                console.error('Failed to close document:', result);
            }
        } catch (error) {
            console.error('Error closing document:', error);
        }
        
        // Always close the UI regardless of API result
        this.currentDocumentId = null;
        this.currentDocument = null;
        closeFileViewer();
    }
    
    switchToHtmlView(filename) {
        this.currentMode = 'html';
        localStorage.setItem('viewerMode', 'html');
        this.updateButtonText();
        
        // Load document in HTML mode
        if (typeof window.displayDocumentFromBackend === 'function') {
            window.displayDocumentFromBackend(filename);
        }
    }
    
    showModeNotification(message, type = 'info') {
        // Create or update notification element
        let notification = document.getElementById('modeNotification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'modeNotification';
            notification.style.cssText = `
                position: fixed;
                top: 70px;
                right: 20px;
                background: ${type === 'info' ? '#2196F3' : '#f44336'};
                color: white;
                padding: 15px 20px;
                border-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 9999;
                max-width: 300px;
            `;
            document.body.appendChild(notification);
        }
        
        notification.innerHTML = `
            ${message}
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                color: white;
                float: right;
                cursor: pointer;
                font-size: 20px;
                line-height: 1;
                margin-left: 10px;
            ">&times;</button>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (notification && notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize viewer manager when DOM is ready
let viewerManager;

// Global function for toggle button
function toggleViewerMode() {
    if (viewerManager) {
        viewerManager.toggleMode();
    } else {
        console.error('ViewerManager not initialized');
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        viewerManager = new ViewerModeManager();
        window.viewerManager = viewerManager; // Make it globally accessible
        
        // Initialize overlay manager if available
        if (window.overlayManager) {
            try {
                const documentsDir = '/home/user/Documents'; // Or get from config
                await window.overlayManager.initialize('chat-container', documentsDir);
                console.log('[ViewerMode] Overlay manager initialized');
            } catch (error) {
                console.error('[ViewerMode] Failed to initialize overlay manager:', error);
            }
        }
    });
} else {
    // DOM already loaded
    viewerManager = new ViewerModeManager();
    window.viewerManager = viewerManager;
    
    // Initialize overlay manager if available
    if (window.overlayManager) {
        window.overlayManager.initialize('chat-container', '/home/user/Documents')
            .then(() => console.log('[ViewerMode] Overlay manager initialized'))
            .catch(error => console.error('[ViewerMode] Failed to initialize overlay manager:', error));
    }
}