/**
 * Native Integration for DocAI Native
 * Handles native desktop functionality through PyWebView bridge
 */

// Check if running in native mode
const isNative = typeof pywebview !== 'undefined';

// Native API wrapper
const NativeAPI = {
    // Check if native mode is available
    isAvailable() {
        return isNative;
    },

    // File Operations
    async pickFile() {
        if (!isNative) {
            console.warn('Native API not available');
            return null;
        }
        
        try {
            console.log('pywebview available:', typeof pywebview !== 'undefined');
            console.log('pywebview.api available:', typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined');
            
            if (typeof pywebview === 'undefined' || typeof pywebview.api === 'undefined') {
                console.error('pywebview.api is not available');
                return null;
            }
            
            // Debug: List all available methods
            console.log('API type:', typeof pywebview.api);
            try {
                const keys = Object.keys(pywebview.api);
                console.log('API methods available:', keys);
            } catch (e) {
                console.log('Cannot enumerate API methods:', e);
            }
            
            console.log('Calling pywebview.api.pickFile()...');
            // Try direct method call
            if (typeof pywebview.api.pickFile === 'function') {
                const result = await pywebview.api.pickFile();
                console.log('File picked:', result);
                return result;
            } else {
                console.error('pickFile is not a function, type:', typeof pywebview.api.pickFile);
                return null;
            }
        } catch (error) {
            console.error('Error picking file:', error);
            return null;
        }
    },

    async pickMultipleFiles() {
        if (!isNative) return [];
        
        try {
            const method = pywebview.api.pickMultipleFiles || pywebview.api.pick_multiple_files;
            const result = await method.call(pywebview.api);
            console.log('Multiple files picked:', result);
            return result;
        } catch (error) {
            console.error('Error picking multiple files:', error);
            return [];
        }
    },

    async pickFolder() {
        if (!isNative) return null;
        
        try {
            const method = pywebview.api.pickFolder || pywebview.api.pick_folder;
            const result = await method.call(pywebview.api);
            console.log('Folder picked:', result);
            return result;
        } catch (error) {
            console.error('Error picking folder:', error);
            return null;
        }
    },

    async saveFile(suggestedName = 'document.docx') {
        if (!isNative) return null;
        
        try {
            const method = pywebview.api.saveFile || pywebview.api.save_file;
            const result = await method.call(pywebview.api, suggestedName);
            console.log('Save location:', result);
            return result;
        } catch (error) {
            console.error('Error choosing save location:', error);
            return null;
        }
    },

    // LibreOffice Integration
    async embedLibreOffice(containerId, filePath) {
        if (!isNative) return null;
        
        try {
            const result = await pywebview.api.embed_libreoffice(containerId, filePath);
            console.log('LibreOffice embed result:', result);
            return result;
        } catch (error) {
            console.error('Error embedding LibreOffice:', error);
            return null;
        }
    },

    // System Integration
    async showMessage(title, message, type = 'info') {
        if (!isNative) {
            alert(`${title}: ${message}`);
            return;
        }
        
        try {
            await pywebview.api.show_message(title, message, type);
        } catch (error) {
            console.error('Error showing message:', error);
        }
    },

    async getPlatformInfo() {
        if (!isNative) return null;
        
        try {
            const result = await pywebview.api.get_platform_info();
            console.log('Platform info:', result);
            return result;
        } catch (error) {
            console.error('Error getting platform info:', error);
            return null;
        }
    },

    // Logging
    async logMessage(level, message) {
        if (!isNative) {
            console[level](message);
            return;
        }
        
        try {
            await pywebview.api.log_message(level, message);
        } catch (error) {
            console.error('Error logging message:', error);
        }
    }
};

// Native file handlers
async function handleNativeOpenFile() {
    console.log('handleNativeOpenFile called');
    try {
        console.log('Calling NativeAPI.pickFile()...');
        const filePath = await NativeAPI.pickFile();
        console.log('pickFile returned:', filePath);
        if (filePath) {
            // Extract filename from path
            const fileName = filePath.split(/[/\\]/).pop();
            const fileExt = fileName.split('.').pop().toLowerCase();
            
            // Add to file container for display with file path
            if (typeof addFileToContainer === 'function') {
                // Store the file path in the file item's data
                const fileItem = addFileToContainer(fileName, fileExt, filePath);
            }
            
            // Show success message
            let lang = 'tamil';
            try {
                lang = localStorage.getItem('language') || 'tamil';
            } catch (e) {
                console.warn('localStorage not available for language preference');
            }
            const t = typeof translations !== 'undefined' ? 
                translations[lang] : 
                { openedFile: 'Opened file: ' };
            
            const message = document.createElement('div');
            message.className = 'message bot-message';
            message.innerHTML = `<img src="static/assets/Durga.png" alt="AI">${t.openedFile}${fileName}`;
            const chatbox = document.getElementById('chatbox');
            if (chatbox) {
                chatbox.appendChild(message);
                chatbox.scrollTop = chatbox.scrollHeight;
            }
            
            // Open the document
            await openDocumentFromPath(filePath);
        }
    } catch (error) {
        console.error('Error opening file:', error);
        NativeAPI.showMessage('Error', 'Failed to open file: ' + error.message, 'error');
    }
}

async function handleNativeOpenMultiple() {
    try {
        const filePaths = await NativeAPI.pickMultipleFiles();
        if (filePaths && filePaths.length > 0) {
            // For now, just open the first file
            // TODO: Implement multi-document interface
            await openDocumentFromPath(filePaths[0]);
            
            if (filePaths.length > 1) {
                NativeAPI.showMessage(
                    'Multiple Files',
                    `Opened first file. Multiple document support coming soon!`,
                    'info'
                );
            }
        }
    } catch (error) {
        console.error('Error opening multiple files:', error);
        NativeAPI.showMessage('Error', 'Failed to open files: ' + error.message, 'error');
    }
}

async function handleOpenFolder() {
    try {
        const folderPath = await NativeAPI.pickFolder();
        if (folderPath) {
            console.log('Folder selected:', folderPath);
            // TODO: Implement folder browsing
            NativeAPI.showMessage('Folder Selected', `Selected: ${folderPath}`, 'info');
        }
    } catch (error) {
        console.error('Error opening folder:', error);
        NativeAPI.showMessage('Error', 'Failed to open folder: ' + error.message, 'error');
    }
}

async function handleSaveAs() {
    try {
        const savePath = await NativeAPI.saveFile();
        if (savePath) {
            console.log('Save location selected:', savePath);
            // TODO: Implement save functionality
            NativeAPI.showMessage('Save Location', `Selected: ${savePath}`, 'info');
        }
    } catch (error) {
        console.error('Error choosing save location:', error);
        NativeAPI.showMessage('Error', 'Failed to choose save location: ' + error.message, 'error');
    }
}

// Document operations
async function openDocumentFromPath(filePath) {
    try {
        console.log('Opening document:', filePath);
        
        // Show loading
        showLoading('Opening document...');
        
        // Extract filename from path
        const fileName = filePath.split(/[/\\]/).pop();
        
        // For native mode, use direct file path endpoint
        const response = await fetch('/view_document_direct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filePath: filePath })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                // Display document in chat container
                const chatContainer = document.querySelector('.chat-container');
                if (chatContainer) {
                    chatContainer.innerHTML = `
                        <div class="word-viewer">
                            <div class="word-toolbar">
                                <div class="word-toolbar-group">
                                    <span>${fileName}</span>
                                    <div class="viewer-mode-toggle" id="viewerModeToggle" style="display: inline-block;">
                                        <button class="btn btn-sm btn-outline-secondary" id="toggleViewerBtn" onclick="toggleViewerMode()" title="Toggle Viewer Mode">
                                            <i class="fas fa-exchange-alt"></i>
                                            <span id="viewerModeText">HTML View</span>
                                        </button>
                                    </div>
                                    <button class="edit-button" onclick="enableEditMode('${fileName}')" title="Edit Document">
                                        <i class="fas fa-edit"></i> Edit
                                    </button>
                                    <div class="close-document" onclick="closeFileViewer()" title="Close">
                                        <i class="fas fa-times"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="word-viewer-container">
                                <div class="word-content">
                                    ${data.pages ? data.pages.map((page, index) => `
                                        <div class="word-page">
                                            ${page}
                                        </div>
                                    `).join('') : '<pre>' + (data.content || 'No content available') + '</pre>'}
                                </div>
                            </div>
                        </div>
                    `;
                }
            } else {
                throw new Error(data.error || 'Failed to load document');
            }
        } else {
            throw new Error('Failed to open document');
        }
        
    } catch (error) {
        console.error('Error opening document:', error);
        NativeAPI.showMessage('Error', 'Failed to open document: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function displayDocument(documentData) {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    // Create document display
    let content = '';
    
    if (documentData.type === 'text') {
        content = `
            <div class="document-viewer">
                <div class="document-header">
                    <h3>📄 ${documentData.path.split('/').pop()}</h3>
                    <button onclick="closeDocument()" class="close-btn">✕</button>
                </div>
                <div class="document-content">
                    <pre>${documentData.content}</pre>
                </div>
            </div>
        `;
    } else {
        content = `
            <div class="document-viewer">
                <div class="document-header">
                    <h3>📄 ${documentData.path.split('/').pop()}</h3>
                    <div class="document-tools">
                        <button onclick="toggleNativeView()" class="tool-btn">🔄 Native View</button>
                        <button onclick="closeDocument()" class="close-btn">✕</button>
                    </div>
                </div>
                <div id="doc-container" class="document-content">
                    <p>Document loaded. Mode: ${documentData.mode}</p>
                    <p>Type: ${documentData.type}</p>
                    <p>Path: ${documentData.path}</p>
                </div>
            </div>
        `;
    }
    
    chatContainer.innerHTML = content;
}

function showNativeView(embedResult) {
    const container = document.getElementById('doc-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="native-view-info">
            <p>✅ LibreOffice Native View Active</p>
            <p>Mode: ${embedResult.mode}</p>
            <p>Port: ${embedResult.port}</p>
            <small>This is a prototype implementation. Full embedding coming soon!</small>
        </div>
    `;
}

function closeDocument() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.innerHTML = '<div class="welcome-message">Select a document to view</div>';
    }
}

function toggleNativeView() {
    console.log('Toggle native view');
    // TODO: Implement view switching
    NativeAPI.showMessage('Coming Soon', 'View toggle functionality will be implemented next!', 'info');
}

// Utility functions
function showLoading(message = 'Loading...') {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
        loading.textContent = message;
    }
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

// Initialize native features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Native Integration Initialization ===');
    console.log('isNative:', isNative);
    console.log('typeof pywebview:', typeof pywebview);
    
    if (isNative) {
        console.log('Native mode detected');
        
        // Check API availability with delay
        setTimeout(() => {
            console.log('Checking API after delay...');
            console.log('pywebview:', pywebview);
            console.log('pywebview.api:', pywebview?.api);
            
            if (pywebview && pywebview.api) {
                console.log('API is available!');
                try {
                    const methods = Object.keys(pywebview.api);
                    console.log('Available methods:', methods);
                } catch (e) {
                    console.log('Error listing methods:', e);
                }
            } else {
                console.error('API not available after delay');
            }
        }, 1000);
        
        // Update title to show native mode
        document.title += ' (Native Mode)';
        
        // Show welcome message
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer && !chatContainer.innerHTML.trim()) {
            chatContainer.innerHTML = `
                <div class="welcome-message">
                    <h2>Welcome to Durga AI Native!</h2>
                    <p>🚀 Native desktop mode is active</p>
                    <p>Use the File menu to open documents</p>
                </div>
            `;
        }
    } else {
        console.log('Running in web mode - native features disabled');
    }
});

// Also check on pywebviewready event
window.addEventListener('pywebviewready', function() {
    console.log('=== pywebviewready Event Fired ===');
    console.log('pywebview:', pywebview);
    console.log('pywebview.api:', pywebview?.api);
    
    if (pywebview && pywebview.api) {
        try {
            const methods = Object.keys(pywebview.api);
            console.log('API methods on ready:', methods);
        } catch (e) {
            console.log('Error listing methods:', e);
        }
    }
});

// Handle command line arguments (if file passed to open)
if (isNative && pywebview.api.get_config) {
    pywebview.api.get_config('STARTUP_FILE').then(startupFile => {
        if (startupFile) {
            console.log('Opening startup file:', startupFile);
            openDocumentFromPath(startupFile);
        }
    }).catch(err => {
        console.log('No startup file specified');
    });
}

// Export for global access
window.NativeAPI = NativeAPI;
window.handleNativeOpenFile = handleNativeOpenFile;
window.handleNativeOpenMultiple = handleNativeOpenMultiple;
window.handleOpenFolder = handleOpenFolder;
window.handleSaveAs = handleSaveAs;