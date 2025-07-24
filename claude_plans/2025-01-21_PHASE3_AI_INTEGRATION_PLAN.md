# Phase 3: AI Integration Plan  
**Date**: January 21, 2025  
**Prerequisites**: Phase 1 (LibreOffice Service) + Phase 2 (Native Embedding)  
**Estimated Time**: 2 days

## GOAL: Seamless Document-to-AI Workflow

**Vision**: Users can select text in LibreOffice document and instantly chat with AI about it
**Core Features**:
- Text selection from embedded LibreOffice viewer
- Context-aware AI conversations about document content
- AI responses that reference specific document sections
- Bidirectional document-AI interaction

## AI INTEGRATION ARCHITECTURE

### Current AI Chat System
- Chat interface in right panel
- Text input and AI responses
- Basic conversation history

### Enhanced AI Integration
```
LibreOffice Document ↔ Text Selection ↔ AI Chat ↔ Document Context
```

### Key Components
1. **Text Extraction**: Get selected text from LibreOffice
2. **Context Management**: Maintain document context in AI conversations  
3. **Reverse Highlighting**: AI can reference document sections
4. **Smart Prompting**: Document metadata in AI prompts

## IMPLEMENTATION PLAN

### 3.1: Text Selection & Extraction System

#### LibreOffice UNO Text Selection
```python
# Add to uno_bridge.py or create text_selection_service.py

class DocumentTextSelector:
    def __init__(self, uno_bridge):
        self.bridge = uno_bridge
        self.selection_cache = {}
    
    def get_current_selection(self, doc_id):
        """Get currently selected text from LibreOffice document"""
        try:
            if doc_id not in self.bridge.loaded_documents:
                return {"success": False, "error": "Document not found"}
            
            doc = self.bridge.loaded_documents[doc_id]
            controller = doc.controller
            
            # Get selection from UNO
            selection = controller.getSelection()
            
            if selection.getCount() > 0:
                # Get first selected range
                selected_range = selection.getByIndex(0)
                selected_text = selected_range.getString()
                
                # Get additional context
                context = self.get_selection_context(selected_range)
                
                return {
                    "success": True,
                    "text": selected_text,
                    "context": context,
                    "document": doc.file_path,
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False, 
                    "error": "No text selected"
                }
                
        except Exception as e:
            logger.error(f"Error getting text selection: {e}")
            return {"success": False, "error": str(e)}
    
    def get_selection_context(self, selected_range):
        """Get context around selected text"""
        try:
            # Get paragraph containing selection
            cursor = selected_range.getText().createTextCursor()
            cursor.gotoRange(selected_range.getStart(), False)
            cursor.gotoStartOfParagraph(True)
            
            paragraph_start = cursor.getString()
            
            # Get surrounding paragraphs
            cursor.gotoEndOfParagraph(False)
            cursor.goRight(1, True)  # Include next paragraph
            
            context_text = cursor.getString()
            
            return {
                "paragraph": paragraph_start,
                "surrounding": context_text[:500],  # Limit context size
                "page_number": self.get_page_number(selected_range),
                "selection_start": selected_range.getStart(),
                "selection_end": selected_range.getEnd()
            }
            
        except Exception as e:
            logger.debug(f"Could not get selection context: {e}")
            return {}
    
    def get_page_number(self, text_range):
        """Get page number of selected text"""
        try:
            cursor = text_range.getText().createTextCursor() 
            cursor.gotoRange(text_range.getStart(), False)
            
            # Get page number property
            page_num = cursor.getPropertyValue("PageNumberOffset")
            return page_num + 1  # Convert from 0-based to 1-based
            
        except Exception as e:
            logger.debug(f"Could not get page number: {e}")
            return None
```

#### JavaScript Selection Bridge
```javascript
// Add to native-integration.js or create ai-integration.js

class DocumentAIIntegration {
    constructor() {
        this.currentDocument = null;
        this.selectionHistory = [];
        this.contextMemory = new Map();
    }
    
    async extractSelectedText() {
        """Get selected text from currently embedded document"""
        try {
            console.log('[AI Integration] Extracting selected text...');
            
            // Call native API to get selection
            const result = await pywebview.api.extractTextSelection();
            
            if (result.success) {
                console.log('[AI Integration] Text extracted:', result.text.substring(0, 100) + '...');
                
                // Store selection in history
                this.selectionHistory.push({
                    text: result.text,
                    context: result.context,
                    document: result.document,
                    timestamp: Date.now()
                });
                
                // Update context memory
                this.updateContextMemory(result);
                
                return result;
            } else {
                console.warn('[AI Integration] No text selected:', result.error);
                return null;
            }
            
        } catch (error) {
            console.error('[AI Integration] Selection extraction failed:', error);
            return null;
        }
    }
    
    updateContextMemory(selectionResult) {
        """Update AI context with document information"""
        const docKey = selectionResult.document;
        
        if (!this.contextMemory.has(docKey)) {
            this.contextMemory.set(docKey, {
                selections: [],
                metadata: {},
                conversation_count: 0
            });
        }
        
        const docContext = this.contextMemory.get(docKey);
        docContext.selections.push(selectionResult);
        
        // Keep only recent selections (last 10)
        if (docContext.selections.length > 10) {
            docContext.selections = docContext.selections.slice(-10);
        }
    }
    
    async sendSelectionToAI(prompt_type = 'explain') {
        """Send selected text to AI with context"""
        const selection = await this.extractSelectedText();
        
        if (!selection) {
            this.showNotification('Please select some text in the document first.', 'warning');
            return;
        }
        
        // Generate context-aware prompt
        const prompt = this.generateAIPrompt(selection, prompt_type);
        
        // Send to chat interface
        this.sendToChatInterface(prompt);
        
        // Focus on chat input for user interaction
        const chatInput = document.getElementById('userInput');
        if (chatInput) {
            chatInput.focus();
        }
    }
    
    generateAIPrompt(selection, prompt_type) {
        """Generate context-rich prompt for AI"""
        const text = selection.text;
        const context = selection.context;
        const docName = selection.document.split('/').pop();
        
        let prompt = '';
        
        switch (prompt_type) {
            case 'explain':
                prompt = `From document "${docName}"${context.page_number ? ` (page ${context.page_number})` : ''}:\n\n"${text}"\n\nPlease explain what this means.`;
                break;
                
            case 'summarize':
                prompt = `From document "${docName}":\n\n"${text}"\n\nPlease summarize this text in simple terms.`;
                break;
                
            case 'question':
                prompt = `I have a question about this text from "${docName}":\n\n"${text}"\n\n`;
                break;
                
            case 'context':
                prompt = `From document "${docName}"${context.page_number ? ` (page ${context.page_number})` : ''}:\n\n"${text}"\n\nWhat is the context and significance of this text within the document?`;
                break;
                
            default:
                prompt = `From document "${docName}":\n\n"${text}"\n\nWhat can you tell me about this?`;
        }
        
        return prompt;
    }
    
    sendToChatInterface(message) {
        """Send message to AI chat interface"""
        const chatInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (chatInput && sendBtn) {
            chatInput.value = message;
            
            // Trigger send
            if (typeof window.sendMessage === 'function') {
                window.sendMessage();
            } else {
                sendBtn.click();
            }
        }
    }
    
    showNotification(message, type = 'info') {
        """Show user notification"""
        // Create or update notification element
        let notification = document.getElementById('ai-integration-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'ai-integration-notification';
            notification.className = 'ai-notification';
            document.body.appendChild(notification);
        }
        
        notification.textContent = message;
        notification.className = `ai-notification ${type}`;
        notification.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
}

// Global instance
window.aiIntegration = new DocumentAIIntegration();
```

### 3.2: Enhanced Context Menu Integration

```javascript
// Document context menu for AI interactions
class DocumentContextMenu {
    constructor() {
        this.menu = null;
        this.initializeContextMenu();
    }
    
    initializeContextMenu() {
        // Listen for right-clicks in document embedding container
        document.addEventListener('contextmenu', (e) => {
            const embeddingContainer = e.target.closest('.document-embedding-container');
            if (embeddingContainer) {
                e.preventDefault();
                this.showContextMenu(e.pageX, e.pageY);
            }
        });
        
        // Hide menu on click elsewhere
        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
    }
    
    showContextMenu(x, y) {
        this.hideContextMenu(); // Remove existing menu
        
        this.menu = document.createElement('div');
        this.menu.className = 'document-context-menu';
        this.menu.innerHTML = `
            <div class="context-menu-item" onclick="aiIntegration.sendSelectionToAI('explain')">
                <i class="fas fa-question-circle"></i> Ask AI to Explain This
            </div>
            <div class="context-menu-item" onclick="aiIntegration.sendSelectionToAI('summarize')">
                <i class="fas fa-compress-alt"></i> Summarize This
            </div>
            <div class="context-menu-item" onclick="aiIntegration.sendSelectionToAI('context')">
                <i class="fas fa-search"></i> Get Context
            </div>
            <div class="context-menu-separator"></div>
            <div class="context-menu-item" onclick="aiIntegration.sendSelectionToAI('question')">
                <i class="fas fa-comment-dots"></i> Ask a Question
            </div>
            <div class="context-menu-item" onclick="this.copySelection()">
                <i class="fas fa-copy"></i> Copy Selection
            </div>
        `;
        
        // Position menu
        this.menu.style.position = 'fixed';
        this.menu.style.left = x + 'px';
        this.menu.style.top = y + 'px';
        this.menu.style.zIndex = '10000';
        
        document.body.appendChild(this.menu);
    }
    
    hideContextMenu() {
        if (this.menu) {
            this.menu.remove();
            this.menu = null;
        }
    }
    
    async copySelection() {
        const selection = await aiIntegration.extractSelectedText();
        if (selection && selection.text) {
            try {
                await navigator.clipboard.writeText(selection.text);
                aiIntegration.showNotification('Text copied to clipboard', 'success');
            } catch (error) {
                console.error('Failed to copy to clipboard:', error);
            }
        }
        this.hideContextMenu();
    }
}

// Initialize context menu
window.documentContextMenu = new DocumentContextMenu();
```

### 3.3: AI Response Enhancement

```python
# Add to chat handling (wherever AI responses are processed)

class DocumentAwareAIHandler:
    def __init__(self):
        self.document_context = {}
        
    def enhance_ai_prompt(self, user_message, document_context=None):
        """Add document context to AI prompts"""
        
        if document_context:
            # Add document metadata to system prompt
            system_context = f"""
            The user is working with a document: {document_context.get('document_name', 'Unknown')}
            
            Recent selections from the document:
            {self.format_recent_selections(document_context.get('recent_selections', []))}
            
            Please provide responses that are relevant to this document context.
            When referring to the document, you can mention specific sections or pages if provided.
            """
            
            return {
                "system": system_context,
                "user": user_message,
                "context": document_context
            }
        
        return {"user": user_message}
    
    def format_recent_selections(self, selections):
        """Format recent selections for AI context"""
        if not selections:
            return "No recent selections."
            
        formatted = []
        for i, selection in enumerate(selections[-3:], 1):  # Last 3 selections
            page_info = f" (page {selection['context']['page_number']})" if selection['context'].get('page_number') else ""
            formatted.append(f"{i}. {selection['text'][:100]}...{page_info}")
            
        return "\n".join(formatted)
    
    def process_ai_response(self, response, document_context=None):
        """Process AI response and potentially highlight document sections"""
        
        # Check if AI response references specific document sections
        if self.contains_document_references(response):
            # Could implement document highlighting here
            self.highlight_referenced_sections(response, document_context)
            
        return response
    
    def contains_document_references(self, response):
        """Check if AI response references document sections"""
        reference_patterns = [
            r"on page \d+",
            r"in the (paragraph|section) where",
            r"the text you selected",
            r"in your document"
        ]
        
        import re
        for pattern in reference_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
                
        return False
```

### 3.4: Native API Integration

```python
# Add to SimpleNativeAPI

def extractTextSelection(self):
    """Extract selected text from LibreOffice document"""
    logger.info("extractTextSelection called")
    
    try:
        # Get active UNO bridge
        from app.services.uno_bridge import get_uno_bridge
        bridge = get_uno_bridge()
        
        if not bridge:
            return {"success": False, "error": "UNO bridge not available"}
        
        # Get current document selection
        text_selector = DocumentTextSelector(bridge)
        
        # For now, assume single active document
        # In full implementation, track which document is active
        active_doc_id = bridge.get_active_document_id()
        
        if active_doc_id:
            result = text_selector.get_current_selection(active_doc_id)
            return result
        else:
            return {"success": False, "error": "No active document"}
            
    except Exception as e:
        logger.error(f"Error in extractTextSelection: {e}")
        return {"success": False, "error": str(e)}

def getDocumentContext(self):
    """Get current document context for AI"""
    try:
        from app.services.uno_bridge import get_uno_bridge
        bridge = get_uno_bridge()
        
        if not bridge:
            return {"success": False, "error": "UNO bridge not available"}
        
        active_doc_id = bridge.get_active_document_id()
        if active_doc_id:
            doc = bridge.loaded_documents[active_doc_id]
            
            return {
                "success": True,
                "document_name": Path(doc.file_path).name,
                "document_path": doc.file_path,
                "page_count": bridge.get_page_count(active_doc_id),
                "current_page": bridge.get_current_page(active_doc_id),
                "recent_selections": []  # Would be populated from selection history
            }
        else:
            return {"success": False, "error": "No active document"}
            
    except Exception as e:
        logger.error(f"Error getting document context: {e}")
        return {"success": False, "error": str(e)}
```

### 3.5: CSS for AI Integration Elements

```css
/* Add to stylenew.css */

.document-context-menu {
    background: white;
    border: 1px solid #ccc;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 8px 0;
    min-width: 200px;
    font-size: 14px;
}

.context-menu-item {
    padding: 10px 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: background-color 0.2s;
}

.context-menu-item:hover {
    background-color: #f0f0f0;
}

.context-menu-separator {
    height: 1px;
    background: #e0e0e0;
    margin: 4px 0;
}

.ai-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    z-index: 10001;
    display: none;
    animation: slideInRight 0.3s ease;
}

.ai-notification.info {
    background: #2196F3;
}

.ai-notification.success {
    background: #4CAF50;
}

.ai-notification.warning {
    background: #FF9800;
}

.ai-notification.error {
    background: #f44336;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Highlight selected text in chat responses */
.chat-message .document-reference {
    background: #fff3cd;
    border-left: 3px solid #ffc107;
    padding: 8px 12px;
    margin: 8px 0;
    border-radius: 4px;
}

.chat-message .selected-text {
    font-style: italic;
    background: #e3f2fd;
    padding: 2px 6px;
    border-radius: 3px;
}
```

## TESTING PLAN

### User Workflow Tests
1. **Select & Explain**: Select text in LibreOffice → Right-click → "Ask AI to Explain" → Verify AI gets text with context
2. **Multiple Selections**: Make several selections → Verify AI maintains context of previous selections  
3. **Page References**: Select text from specific page → Verify AI response includes page reference
4. **Document Context**: Switch between documents → Verify AI maintains separate context per document

### Technical Tests
```python
def test_text_selection():
    """Test text can be extracted from LibreOffice"""
    
def test_context_generation():
    """Test document context is properly formatted for AI"""
    
def test_prompt_enhancement():
    """Test AI prompts include document context"""
    
def test_selection_history():
    """Test selection history is maintained correctly"""
```

## SUCCESS CRITERIA

✅ **Text Selection Works**: Can extract selected text from embedded LibreOffice  
✅ **Context Menu**: Right-click shows AI options for selected text  
✅ **AI Integration**: Selected text appears in chat with proper context  
✅ **Document Awareness**: AI knows which document user is working with  
✅ **History**: AI remembers previous selections from same document  
✅ **Page References**: AI can reference specific pages/sections  
✅ **Smooth UX**: Process feels natural and responsive  

## ROLLBACK PLAN

If AI integration becomes complex:
1. Start with basic text extraction only
2. Simple "Send to AI" button instead of context menu
3. Basic prompt without document context
4. Gradual enhancement of features

This plan creates a seamless bridge between LibreOffice documents and AI chat, enabling natural document-based conversations.