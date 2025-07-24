/**
 * Viewer Mode Manager
 * Handles switching between HTML and Native document viewing modes
 */

class ViewerModeManager {
    constructor() {
        this.currentMode = localStorage.getItem('viewerMode') || 'html';
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
    
    toggleMode() {
        this.currentMode = this.currentMode === 'html' ? 'native' : 'html';
        localStorage.setItem('viewerMode', this.currentMode);
        
        console.log('Viewer mode switched to:', this.currentMode);
        
        // Update UI
        this.updateButtonText();
        
        // Reload current document in new mode if one is open
        if (this.currentDocument) {
            this.loadDocument(this.currentDocument);
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
    
    loadNativeDocument(filename) {
        const chatContainer = document.querySelector('.chat-container');
        if (!chatContainer) {
            console.error('Chat container not found');
            return;
        }
        
        // Show loading state
        chatContainer.innerHTML = `
            <div class="file-viewer">
                <div class="file-viewer-header">
                    <h3>📄 ${filename}</h3>
                    <div class="viewer-mode-toggle" id="viewerModeToggle" style="display: inline-block;">
                        <button class="btn btn-sm btn-outline-secondary" id="toggleViewerBtn" onclick="toggleViewerMode()" title="Toggle Viewer Mode">
                            <i class="fas fa-exchange-alt"></i>
                            <span id="viewerModeText">Native View</span>
                        </button>
                    </div>
                    <button onclick="closeFileViewer()" class="close-btn">✕</button>
                </div>
                <div class="file-viewer-content" style="text-align: center; padding: 50px;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 48px; color: #666;"></i>
                    <p>Loading native viewer...</p>
                </div>
            </div>
        `;
        
        // Update button text after DOM update
        setTimeout(() => this.updateButtonText(), 100);
        
        // Create iframe for PDF viewer
        const iframe = document.createElement('iframe');
        iframe.src = `http://localhost:8090/view_document_native/${encodeURIComponent(filename)}`;
        iframe.className = 'native-document-viewer';
        iframe.style.width = '100%';
        iframe.style.height = 'calc(100% - 60px)'; // Account for header
        iframe.style.border = 'none';
        
        // Handle iframe load events
        iframe.onload = () => {
            console.log('Native viewer loaded successfully');
            // Update the content area with the iframe
            const contentArea = chatContainer.querySelector('.file-viewer-content');
            if (contentArea) {
                contentArea.innerHTML = '';
                contentArea.style.padding = '0';
                contentArea.style.height = 'calc(100% - 50px)';
                contentArea.appendChild(iframe);
            }
        };
        
        iframe.onerror = (error) => {
            console.error('Native viewer failed to load:', error);
            this.handleNativeViewerError(filename);
        };
    }
    
    handleNativeViewerError(filename) {
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
                    <p>Unable to load document in native viewer mode.</p>
                    <button class="btn btn-primary" onclick="viewerManager.switchToHtmlView('${filename}')">
                        Switch to HTML View
                    </button>
                </div>
            </div>
        `;
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
    document.addEventListener('DOMContentLoaded', () => {
        viewerManager = new ViewerModeManager();
        window.viewerManager = viewerManager; // Make it globally accessible
    });
} else {
    // DOM already loaded
    viewerManager = new ViewerModeManager();
    window.viewerManager = viewerManager;
}