// Enhanced Document Viewer for Full LibreOffice Capability
(function() {
    'use strict';

    // Enhanced viewer state
    window.enhancedViewer = {
        currentDocument: null,
        viewMode: 'normal', // normal, zoom, fullscreen
        zoomLevel: 100,
        showMetadata: false,
        showStyles: false,
        showHeaderFooter: false
    };

    // Initialize enhanced viewer features
    window.initEnhancedViewer = function(documentData) {
        console.log('Initializing enhanced viewer with:', documentData);
        
        // Add viewer controls
        addEnhancedControls();
        
        // Process document metadata
        if (documentData.metadata) {
            processDocumentMetadata(documentData.metadata);
        }
        
        // Apply enhanced styles
        applyEnhancedStyles();
        
        // Initialize advanced features
        initializeAdvancedFeatures(documentData);
    };

    // Add enhanced viewer controls
    function addEnhancedControls() {
        const toolbar = document.querySelector('.word-toolbar');
        if (!toolbar) return;

        // Check if enhanced controls already exist
        if (toolbar.querySelector('.enhanced-controls')) return;

        const enhancedControls = document.createElement('div');
        enhancedControls.className = 'word-toolbar-group enhanced-controls';
        enhancedControls.innerHTML = `
            <button class="word-toolbar-button" onclick="toggleZoom()" title="Zoom">
                <i class="fas fa-search-plus"></i>
                <span class="zoom-level">${window.enhancedViewer.zoomLevel}%</span>
            </button>
            <button class="word-toolbar-button" onclick="toggleFullscreen()" title="Fullscreen">
                <i class="fas fa-expand"></i>
            </button>
            <button class="word-toolbar-button" onclick="toggleMetadata()" title="Document Properties">
                <i class="fas fa-info-circle"></i>
            </button>
            <button class="word-toolbar-button" onclick="toggleHeaderFooter()" title="Show Headers/Footers">
                <i class="fas fa-heading"></i>
            </button>
            <button class="word-toolbar-button" onclick="toggleStyles()" title="Style Inspector">
                <i class="fas fa-palette"></i>
            </button>
            <button class="word-toolbar-button" onclick="printDocument()" title="Print">
                <i class="fas fa-print"></i>
            </button>
        `;
        
        toolbar.appendChild(enhancedControls);
    }

    // Process document metadata
    function processDocumentMetadata(metadata) {
        // Create metadata panel
        const metadataPanel = document.createElement('div');
        metadataPanel.className = 'metadata-panel';
        metadataPanel.style.display = 'none';
        metadataPanel.innerHTML = `
            <div class="metadata-header">
                <h3>Document Properties</h3>
                <button onclick="toggleMetadata()" class="close-btn">&times;</button>
            </div>
            <div class="metadata-content">
                ${metadata.title ? `<div><strong>Title:</strong> ${metadata.title}</div>` : ''}
                ${metadata.author ? `<div><strong>Author:</strong> ${metadata.author}</div>` : ''}
                ${metadata.subject ? `<div><strong>Subject:</strong> ${metadata.subject}</div>` : ''}
                ${metadata.page_width ? `
                    <div><strong>Page Size:</strong> ${Math.round(metadata.page_width/100)}mm × ${Math.round(metadata.page_height/100)}mm</div>
                ` : ''}
                ${metadata.margin_top ? `
                    <div><strong>Margins:</strong> 
                        T: ${Math.round(metadata.margin_top/100)}mm, 
                        B: ${Math.round(metadata.margin_bottom/100)}mm,
                        L: ${Math.round(metadata.margin_left/100)}mm,
                        R: ${Math.round(metadata.margin_right/100)}mm
                    </div>
                ` : ''}
            </div>
        `;
        
        document.body.appendChild(metadataPanel);
    }

    // Apply enhanced styles for better rendering
    function applyEnhancedStyles() {
        // Check if enhanced styles already exist
        if (document.getElementById('enhanced-viewer-styles')) return;

        const styleSheet = document.createElement('style');
        styleSheet.id = 'enhanced-viewer-styles';
        styleSheet.textContent = `
            /* Fix scrolling issues */
            .center-section {
                overflow: visible !important;
            }
            
            .word-viewer {
                display: flex;
                flex-direction: column;
                height: 100vh;
                overflow: hidden;
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
            }
            
            .word-viewer-container {
                flex: 1;
                overflow-y: auto;
                overflow-x: hidden;
                height: calc(100vh - 60px); /* Adjust for toolbar height */
                background: #f5f5f5;
            }
            
            .word-content {
                max-width: 900px;
                margin: 0 auto;
                padding: 40px;
                background: white;
                min-height: 100%;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            
            /* Ensure all pages are visible when scrolling */
            .word-page {
                display: block !important; /* Override inline display:none */
                margin-bottom: 40px;
                page-break-after: always;
            }
            
            /* Enhanced viewer controls */
            .enhanced-controls {
                display: flex;
                gap: 10px;
                align-items: center;
                margin-left: auto;
            }
            
            .zoom-level {
                font-size: 0.8em;
                margin-left: 5px;
            }
            
            /* Metadata panel */
            .metadata-panel {
                position: fixed;
                top: 100px;
                right: 20px;
                width: 300px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                padding: 20px;
            }
            
            .metadata-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            
            .metadata-header h3 {
                margin: 0;
                font-size: 1.1em;
                color: #333;
            }
            
            .close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #999;
                padding: 0;
                width: 30px;
                height: 30px;
            }
            
            .metadata-content div {
                margin: 8px 0;
                font-size: 0.9em;
            }
            
            /* Zoom functionality */
            .word-content.zoomed {
                transform-origin: top center;
                transition: transform 0.3s ease;
                width: fit-content;
                margin: 0 auto;
            }
            
            /* Hide navigation since we show all pages */
            .word-navigation {
                display: none !important;
            }
            
            /* Fullscreen mode */
            .word-viewer.fullscreen {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 9999;
                background: #f5f5f5;
            }
            
            /* Header/Footer display */
            .document-headers, .document-footers {
                display: none;
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border: 1px dashed #ccc;
                font-size: 0.9em;
                color: #666;
            }
            
            .show-headers-footers .document-headers,
            .show-headers-footers .document-footers {
                display: block;
            }
            
            /* Style inspector */
            .style-inspector {
                position: fixed;
                left: 20px;
                top: 100px;
                width: 300px;
                max-height: 70vh;
                overflow-y: auto;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                padding: 20px;
                display: none;
            }
            
            /* Scroll indicator */
            .scroll-indicator {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                z-index: 1000;
                display: none;
            }
            
            .word-viewer-container:hover .scroll-indicator {
                display: block;
            }
            
            /* Print optimization */
            @media print {
                .word-toolbar,
                .metadata-panel,
                .style-inspector,
                .word-navigation,
                .scroll-indicator {
                    display: none !important;
                }
                
                .word-content {
                    transform: none !important;
                }
                
                .word-page {
                    page-break-after: always;
                    display: block !important;
                }
            }
            
            /* Enhanced table display */
            .table-wrapper {
                margin: 20px 0;
                overflow-x: auto;
            }
            
            /* Text frame indicators */
            .text-frame {
                position: relative;
                border: 2px dashed #007bff;
                background: rgba(0, 123, 255, 0.05);
                transition: all 0.3s ease;
            }
            
            .text-frame:hover {
                border-color: #0056b3;
                background: rgba(0, 123, 255, 0.1);
            }
            
            /* Footnote references */
            .footnote-ref {
                vertical-align: super;
                font-size: 0.8em;
                color: #007bff;
                cursor: pointer;
                margin: 0 2px;
            }
            
            .footnote-ref:hover {
                text-decoration: underline;
            }
        `;
        
        document.head.appendChild(styleSheet);
    }

    // Initialize advanced features
    function initializeAdvancedFeatures(documentData) {
        // Add footnote tooltips
        addFootnoteTooltips();
        
        // Initialize table sorting
        initializeTableSorting();
        
        // Add image lightbox
        initializeImageLightbox();
        
        // Setup keyboard shortcuts
        setupKeyboardShortcuts();
        
        // Add scroll tracking
        addScrollTracking();
    }
    
    // Add scroll tracking
    function addScrollTracking() {
        const container = document.querySelector('.word-viewer-container');
        if (!container) return;
        
        // Create scroll indicator
        const indicator = document.createElement('div');
        indicator.className = 'scroll-indicator';
        container.appendChild(indicator);
        
        // Track scroll position
        container.addEventListener('scroll', () => {
            const pages = document.querySelectorAll('.word-page');
            let currentPage = 1;
            
            pages.forEach((page, index) => {
                const rect = page.getBoundingClientRect();
                const containerRect = container.getBoundingClientRect();
                
                if (rect.top < containerRect.top + containerRect.height / 2) {
                    currentPage = index + 1;
                }
            });
            
            indicator.textContent = `Page ${currentPage} of ${pages.length}`;
            window.currentPageNumber = currentPage;
        });
    }

    // Toggle zoom
    window.toggleZoom = function() {
        const zoomLevels = [50, 75, 100, 125, 150, 200];
        const currentIndex = zoomLevels.indexOf(window.enhancedViewer.zoomLevel);
        const nextIndex = (currentIndex + 1) % zoomLevels.length;
        window.enhancedViewer.zoomLevel = zoomLevels[nextIndex];
        
        const wordContent = document.querySelector('.word-content');
        if (wordContent) {
            wordContent.style.transform = `scale(${window.enhancedViewer.zoomLevel / 100})`;
            wordContent.classList.add('zoomed');
        }
        
        // Update zoom display
        const zoomDisplay = document.querySelector('.zoom-level');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${window.enhancedViewer.zoomLevel}%`;
        }
    };

    // Toggle fullscreen
    window.toggleFullscreen = function() {
        const viewer = document.querySelector('.word-viewer');
        if (!viewer) return;
        
        if (!document.fullscreenElement) {
            viewer.requestFullscreen().catch(err => {
                console.error('Error entering fullscreen:', err);
            });
            viewer.classList.add('fullscreen');
        } else {
            document.exitFullscreen();
            viewer.classList.remove('fullscreen');
        }
    };

    // Toggle metadata panel
    window.toggleMetadata = function() {
        const panel = document.querySelector('.metadata-panel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            window.enhancedViewer.showMetadata = panel.style.display !== 'none';
        }
    };

    // Toggle header/footer display
    window.toggleHeaderFooter = function() {
        const content = document.querySelector('.word-content');
        if (content) {
            content.classList.toggle('show-headers-footers');
            window.enhancedViewer.showHeaderFooter = content.classList.contains('show-headers-footers');
        }
    };

    // Toggle style inspector
    window.toggleStyles = function() {
        let inspector = document.querySelector('.style-inspector');
        if (!inspector) {
            inspector = createStyleInspector();
            document.body.appendChild(inspector);
        }
        
        inspector.style.display = inspector.style.display === 'none' ? 'block' : 'none';
        window.enhancedViewer.showStyles = inspector.style.display !== 'none';
    };

    // Create style inspector
    function createStyleInspector() {
        const inspector = document.createElement('div');
        inspector.className = 'style-inspector';
        inspector.innerHTML = `
            <div class="metadata-header">
                <h3>Style Inspector</h3>
                <button onclick="toggleStyles()" class="close-btn">&times;</button>
            </div>
            <div class="style-content">
                <p>Click on any element to inspect its styles.</p>
            </div>
        `;
        
        // Add click handler for style inspection
        document.addEventListener('click', function(e) {
            if (window.enhancedViewer.showStyles && !e.target.closest('.style-inspector')) {
                const styles = window.getComputedStyle(e.target);
                const styleContent = inspector.querySelector('.style-content');
                styleContent.innerHTML = `
                    <div><strong>Element:</strong> ${e.target.tagName.toLowerCase()}</div>
                    <div><strong>Class:</strong> ${e.target.className || '(none)'}</div>
                    <div><strong>Font:</strong> ${styles.fontFamily}</div>
                    <div><strong>Size:</strong> ${styles.fontSize}</div>
                    <div><strong>Color:</strong> ${styles.color}</div>
                    <div><strong>Background:</strong> ${styles.backgroundColor}</div>
                    <div><strong>Margin:</strong> ${styles.margin}</div>
                    <div><strong>Padding:</strong> ${styles.padding}</div>
                `;
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        return inspector;
    }

    // Print document
    window.printDocument = function() {
        // Show all pages for printing
        const pages = document.querySelectorAll('.word-page');
        pages.forEach(page => page.style.display = 'block');
        
        // Print
        window.print();
        
        // Restore single page view
        pages.forEach((page, index) => {
            page.style.display = index === window.currentPageNumber - 1 ? 'block' : 'none';
        });
    };

    // Add footnote tooltips
    function addFootnoteTooltips() {
        const footnoteRefs = document.querySelectorAll('.footnote-ref');
        footnoteRefs.forEach(ref => {
            ref.addEventListener('mouseenter', function(e) {
                const tooltip = document.createElement('div');
                tooltip.className = 'footnote-tooltip';
                tooltip.textContent = ref.getAttribute('data-footnote-text') || 'Footnote content';
                tooltip.style.position = 'absolute';
                tooltip.style.left = e.pageX + 'px';
                tooltip.style.top = (e.pageY + 20) + 'px';
                document.body.appendChild(tooltip);
                
                ref.addEventListener('mouseleave', () => tooltip.remove(), { once: true });
            });
        });
    }

    // Initialize table sorting
    function initializeTableSorting() {
        const tables = document.querySelectorAll('.enhanced-table');
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => sortTable(table, index));
            });
        });
    }

    // Sort table by column
    function sortTable(table, columnIndex) {
        const tbody = table.querySelector('tbody') || table;
        const rows = Array.from(tbody.querySelectorAll('tr')).slice(1); // Skip header
        
        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].textContent;
            const bText = b.cells[columnIndex].textContent;
            return aText.localeCompare(bText, undefined, { numeric: true });
        });
        
        rows.forEach(row => tbody.appendChild(row));
    }

    // Initialize image lightbox
    function initializeImageLightbox() {
        const images = document.querySelectorAll('.word-content img');
        images.forEach(img => {
            img.style.cursor = 'pointer';
            img.addEventListener('click', function() {
                const lightbox = document.createElement('div');
                lightbox.className = 'image-lightbox';
                lightbox.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                    cursor: pointer;
                `;
                
                const lightboxImg = document.createElement('img');
                lightboxImg.src = img.src;
                lightboxImg.style.cssText = `
                    max-width: 90%;
                    max-height: 90%;
                    object-fit: contain;
                `;
                
                lightbox.appendChild(lightboxImg);
                document.body.appendChild(lightbox);
                
                lightbox.addEventListener('click', () => lightbox.remove());
            });
        });
    }

    // Setup keyboard shortcuts
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Only if viewer is active
            if (!document.querySelector('.word-viewer')) return;
            
            // Ctrl/Cmd + P: Print
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                e.preventDefault();
                window.printDocument();
            }
            
            // Ctrl/Cmd + F: Fullscreen
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                window.toggleFullscreen();
            }
            
            // Ctrl/Cmd + Plus/Minus: Zoom
            if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
                e.preventDefault();
                window.toggleZoom();
            }
            
            // PageUp/PageDown: Navigate pages
            if (e.key === 'PageUp') {
                e.preventDefault();
                window.previousPage();
            } else if (e.key === 'PageDown') {
                e.preventDefault();
                window.nextPage();
            }
        });
    }

})();