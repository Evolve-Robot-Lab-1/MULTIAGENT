#!/usr/bin/env python3
"""
Improved LibreOffice UNO API converter with enhanced reliability and error handling
"""

import os
import sys
import time
import subprocess
import shutil
import tempfile
import socket
import psutil
import logging
import json
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class ImprovedLibreOfficeConverter:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='uno_convert_')
        self.lo_process = None
        self.port = self._find_free_port()
        self.max_retries = 3
        
    def _find_free_port(self):
        """Find a free port for LibreOffice"""
        for port in range(2002, 2010):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('localhost', port))
                sock.close()
                return port
            except OSError:
                continue
        return 2002  # Default fallback
    
    def _kill_existing_libreoffice(self):
        """Kill any existing LibreOffice processes"""
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and ('soffice' in proc.info['name'] or 'libreoffice' in proc.info['name']):
                    logger.info(f"Killing existing LibreOffice process: {proc.info['pid']}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        killed_count += 1
                    except psutil.TimeoutExpired:
                        proc.kill()
                        killed_count += 1
                elif proc.info['cmdline'] and any('soffice' in str(cmd) or 'libreoffice' in str(cmd) for cmd in proc.info['cmdline']):
                    logger.info(f"Killing LibreOffice command process: {proc.info['pid']}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        killed_count += 1
                    except psutil.TimeoutExpired:
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass
        
        if killed_count > 0:
            logger.info(f"Killed {killed_count} LibreOffice processes")
            time.sleep(2)  # Give time for cleanup
    
    def _start_libreoffice_service(self):
        """Start LibreOffice in headless mode with retry logic"""
        self._kill_existing_libreoffice()
        
        env = os.environ.copy()
        env['SAL_DISABLE_JAVALDX'] = '1'
        env['SAL_USE_VCLPLUGIN'] = 'gen'
        env['SAL_DISABLE_OPENCL'] = '1'
        
        cmd = [
            'libreoffice',
            '--headless',
            '--invisible',
            '--nodefault',
            '--nolockcheck',
            '--nologo',
            '--norestore',
            '--nofirststartwizard',
            f'--accept=socket,host=localhost,port={self.port};urp;StarOffice.ServiceManager'
        ]
        
        try:
            logger.info(f"Starting LibreOffice service on port {self.port}")
            self.lo_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                start_new_session=True
            )
            
            # Wait for service to be ready
            for i in range(30):  # 30 second timeout
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect(('localhost', self.port))
                    sock.close()
                    logger.info(f"✅ LibreOffice service ready on port {self.port}")
                    return True
                except socket.error:
                    if self.lo_process.poll() is not None:
                        stdout, stderr = self.lo_process.communicate()
                        logger.error(f"LibreOffice process died: {stderr.decode()}")
                        return False
                    time.sleep(1)
            
            logger.error("LibreOffice service failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start LibreOffice: {str(e)}")
            return False
    
    def convert_with_uno(self, input_path, retry_count=0):
        """Convert document using UNO API with retry logic"""
        if retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) reached for {input_path}")
            return None
            
        try:
            # Ensure LibreOffice service is running
            if not self.lo_process or self.lo_process.poll() is not None:
                logger.info(f"Starting LibreOffice service (attempt {retry_count + 1})")
                if not self._start_libreoffice_service():
                    return self.convert_with_uno(input_path, retry_count + 1)
            
            # Test connection before proceeding
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect(('localhost', self.port))
                sock.close()
            except socket.error:
                logger.warning("LibreOffice service not responding, restarting...")
                self._kill_existing_libreoffice()
                self.lo_process = None
                return self.convert_with_uno(input_path, retry_count + 1)
            
            import uno
            from com.sun.star.beans import PropertyValue
            from com.sun.star.connection import NoConnectException
            
            # Connect to LibreOffice
            local_context = uno.getComponentContext()
            resolver = local_context.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", local_context
            )
            
            try:
                context = resolver.resolve(
                    f"uno:socket,host=localhost,port={self.port};urp;StarOffice.ComponentContext"
                )
            except NoConnectException:
                logger.warning("UNO connection failed, restarting LibreOffice...")
                self._kill_existing_libreoffice()
                self.lo_process = None
                return self.convert_with_uno(input_path, retry_count + 1)
            
            desktop = context.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", context
            )
            
            # Validate input file
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Copy file to temp directory to avoid locking issues
            temp_input = os.path.join(self.temp_dir, f"input_{int(time.time())}.docx")
            shutil.copy2(input_path, temp_input)
            
            # Load document
            file_url = uno.systemPathToFileUrl(os.path.abspath(temp_input))
            
            load_props = []
            load_props.append(self._make_property_value("Hidden", True))
            load_props.append(self._make_property_value("ReadOnly", True))
            load_props.append(self._make_property_value("UpdateDocMode", 0))
            
            logger.info(f"Loading document: {file_url}")
            document = desktop.loadComponentFromURL(
                file_url, "_blank", 0, load_props
            )
            
            if not document:
                raise Exception("Failed to load document")
            
            # Convert to HTML with embedded images
            output_path = os.path.join(self.temp_dir, f"output_{int(time.time())}.html")
            output_url = uno.systemPathToFileUrl(output_path)
            
            filter_props = []
            filter_props.append(self._make_property_value("FilterName", "HTML (StarWriter)"))
            filter_props.append(self._make_property_value("Overwrite", True))
            
            # Enhanced HTML export options for full document fidelity
            filter_data = []
            filter_data.append(self._make_property_value("EmbedImages", True))
            filter_data.append(self._make_property_value("UseCSS1", True))  # Better CSS support
            filter_data.append(self._make_property_value("UsePrettyPrinting", True))
            filter_data.append(self._make_property_value("ExportLinkedGraphics", True))  # Export linked images
            filter_data.append(self._make_property_value("ExportTextFrameAsParagraph", True))  # Better text box handling
            filter_data.append(self._make_property_value("ConvertOLEObjectsToImages", True))  # Convert embedded objects
            filter_data.append(self._make_property_value("ExportFormFields", True))  # Export form fields
            filter_data.append(self._make_property_value("ExportNotes", True))  # Export notes/comments
            filter_data.append(self._make_property_value("ExportBookmarks", True))  # Export bookmarks as anchors
            filter_data.append(self._make_property_value("ExportHiddenText", False))  # Don't export hidden text
            filter_data.append(self._make_property_value("ExportTextPlaceholder", True))  # Export placeholders
            filter_data.append(self._make_property_value("WriterSpecificSettings", True))  # Use Writer-specific settings
            
            filter_props.append(self._make_property_value("FilterData", filter_data))
            
            logger.info(f"Converting document to HTML: {output_url}")
            
            # Extract additional document properties before conversion
            doc_props = self._extract_document_properties(document) or {}
            
            # Extract headers/footers and other elements before conversion
            headers_footers = self._extract_headers_footers(document) or {'headers': [], 'footers': []}
            styles_info = self._extract_styles(document) or {}
            advanced_elements = self._extract_advanced_elements(document) or {}
            
            # Perform the conversion
            document.storeToURL(output_url, filter_props)
            
            document.close(True)
            
            # Read and process HTML
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                # Process embedded images
                html_with_images = self._process_embedded_images(html_content, output_path)
                
                # Enhanced post-processing
                enhanced_html = self._enhance_html_with_metadata(
                    html_with_images, 
                    doc_props, 
                    headers_footers,
                    styles_info,
                    advanced_elements
                )
                
                # Log conversion stats
                self._log_conversion_stats(input_path, True)
                
                return {
                    'success': True,
                    'content': enhanced_html,
                    'method': 'uno-api-improved-enhanced',
                    'images_found': enhanced_html.count('<img'),
                    'tables_found': enhanced_html.count('<table'),
                    'headers_footers': headers_footers is not None,
                    'styles_preserved': len(styles_info) if styles_info else 0,
                    'port': self.port,
                    'metadata': doc_props
                }
            else:
                raise Exception(f"Output file not created: {output_path}")
            
        except Exception as e:
            logger.error(f"UNO conversion error (attempt {retry_count + 1}): {str(e)}")
            self._log_conversion_stats(input_path, False, str(e))
            
            # Kill and retry on certain errors
            if any(keyword in str(e).lower() for keyword in ['connection', 'service', 'timeout', 'load']):
                self._kill_existing_libreoffice()
                self.lo_process = None
                time.sleep(2)  # Brief pause before retry
                return self.convert_with_uno(input_path, retry_count + 1)
            else:
                # Don't retry on file-specific errors
                return None
    
    def _make_property_value(self, name, value):
        """Create a PropertyValue for UNO"""
        try:
            import uno
            from com.sun.star.beans import PropertyValue
            prop = PropertyValue()
            prop.Name = name
            prop.Value = value
            return prop
        except ImportError:
            logger.error("UNO modules not available")
            return None
    
    def _extract_advanced_elements(self, document):
        """Extract advanced document elements like text boxes, shapes, and footnotes"""
        try:
            advanced_elements = {
                'text_frames': [],
                'shapes': [],
                'footnotes': [],
                'endnotes': [],
                'comments': [],
                'hyperlinks': []
            }
            
            # Extract text frames (text boxes)
            if hasattr(document, 'TextFrames'):
                text_frames = document.TextFrames
                for i in range(text_frames.getCount()):
                    try:
                        frame = text_frames.getByIndex(i)
                        if hasattr(frame, 'String'):
                            frame_info = {
                                'text': frame.String,
                                'name': frame.Name if hasattr(frame, 'Name') else f'Frame{i}',
                                'width': frame.Width if hasattr(frame, 'Width') else 0,
                                'height': frame.Height if hasattr(frame, 'Height') else 0
                            }
                            advanced_elements['text_frames'].append(frame_info)
                    except Exception as e:
                        logger.debug(f"Error extracting text frame {i}: {str(e)}")
            
            # Extract shapes
            if hasattr(document, 'DrawPage'):
                draw_page = document.DrawPage
                for i in range(draw_page.getCount()):
                    try:
                        shape = draw_page.getByIndex(i)
                        shape_type = shape.getShapeType() if hasattr(shape, 'getShapeType') else 'unknown'
                        if 'TextShape' in shape_type and hasattr(shape, 'String'):
                            shape_info = {
                                'type': shape_type,
                                'text': shape.String,
                                'width': shape.Size.Width if hasattr(shape, 'Size') else 0,
                                'height': shape.Size.Height if hasattr(shape, 'Size') else 0
                            }
                            advanced_elements['shapes'].append(shape_info)
                    except Exception as e:
                        logger.debug(f"Error extracting shape {i}: {str(e)}")
            
            # Extract footnotes
            if hasattr(document, 'Footnotes'):
                footnotes = document.Footnotes
                for i in range(footnotes.getCount()):
                    try:
                        footnote = footnotes.getByIndex(i)
                        if hasattr(footnote, 'String'):
                            advanced_elements['footnotes'].append({
                                'index': i + 1,
                                'text': footnote.String
                            })
                    except Exception as e:
                        logger.debug(f"Error extracting footnote {i}: {str(e)}")
            
            # Extract endnotes
            if hasattr(document, 'Endnotes'):
                endnotes = document.Endnotes
                for i in range(endnotes.getCount()):
                    try:
                        endnote = endnotes.getByIndex(i)
                        if hasattr(endnote, 'String'):
                            advanced_elements['endnotes'].append({
                                'index': i + 1,
                                'text': endnote.String
                            })
                    except Exception as e:
                        logger.debug(f"Error extracting endnote {i}: {str(e)}")
            
            logger.info(f"Extracted advanced elements: {len(advanced_elements['text_frames'])} text frames, "
                       f"{len(advanced_elements['shapes'])} shapes, {len(advanced_elements['footnotes'])} footnotes")
            
            return advanced_elements
            
        except Exception as e:
            logger.error(f"Error extracting advanced elements: {str(e)}")
            return None

    def _enhance_tables_and_lists(self, soup):
        """Enhance tables and lists with better formatting"""
        try:
            # Enhance tables
            for table in soup.find_all('table'):
                # Add responsive wrapper
                wrapper = soup.new_tag('div', attrs={'class': 'table-wrapper'})
                table.wrap(wrapper)
                
                # Add table class
                table['class'] = table.get('class', []) + ['enhanced-table']
                
                # Process header rows
                first_row = table.find('tr')
                if first_row:
                    # Check if first row should be header
                    cells = first_row.find_all(['td', 'th'])
                    if all(cell.name == 'td' for cell in cells):
                        # Convert to th if all are td and look like headers
                        all_bold = all(
                            cell.find('b') or cell.find('strong') or 
                            (cell.get('style') and 'bold' in cell.get('style', ''))
                            for cell in cells
                        )
                        if all_bold:
                            for cell in cells:
                                cell.name = 'th'
                
                # Add alternating row colors
                rows = table.find_all('tr')
                for i, row in enumerate(rows):
                    if i > 0:  # Skip header row
                        row['class'] = ['even-row'] if i % 2 == 0 else ['odd-row']
            
            # Enhance lists
            for ul in soup.find_all('ul'):
                # Check for nested lists
                if ul.find_parent('li'):
                    ul['class'] = ul.get('class', []) + ['nested-list']
                else:
                    ul['class'] = ul.get('class', []) + ['main-list']
            
            for ol in soup.find_all('ol'):
                # Check list style
                if ol.find_parent('li'):
                    ol['class'] = ol.get('class', []) + ['nested-list']
                else:
                    ol['class'] = ol.get('class', []) + ['main-list']
                
                # Check for custom numbering
                start = ol.get('start')
                if start:
                    ol['data-start'] = start
            
            return soup
            
        except Exception as e:
            logger.error(f"Error enhancing tables and lists: {str(e)}")
            return soup

    def _process_embedded_images(self, html_content, output_path):
        """Process and embed images in HTML"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not available, returning raw HTML")
            return html_content
        
        soup = BeautifulSoup(html_content, 'html.parser')
        output_dir = os.path.dirname(output_path)
        
        # Find all image references
        image_count = 0
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith('data:'):
                # Load external image and embed
                img_path = os.path.join(output_dir, src)
                if os.path.exists(img_path):
                    try:
                        with open(img_path, 'rb') as f:
                            img_data = f.read()
                        
                        # Determine image type
                        ext = os.path.splitext(src)[1].lower()
                        mime_type = {
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.gif': 'image/gif',
                            '.bmp': 'image/bmp'
                        }.get(ext, 'image/png')
                        
                        # Embed as base64
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        img['src'] = f"data:{mime_type};base64,{img_base64}"
                        
                        # Add responsive styling
                        img['style'] = 'max-width: 100%; height: auto; margin: 10px 0;'
                        
                        image_count += 1
                        logger.info(f"✅ Embedded image: {src} ({len(img_data)} bytes)")
                        
                    except Exception as e:
                        logger.error(f"Failed to embed image {src}: {str(e)}")
        
        logger.info(f"Total embedded images: {image_count}")
        
        # Add custom styles for better rendering
        if soup.head:
            style_tag = soup.new_tag('style')
            style_tag.string = """
                body { 
                    font-family: 'Calibri', Arial, sans-serif; 
                    line-height: 1.6; 
                    margin: 20px;
                    background: white;
                }
                img { 
                    max-width: 100%; 
                    height: auto; 
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .word-image-container { 
                    margin: 15px 0; 
                    text-align: center; 
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                }
                td, th {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
            """
            soup.head.append(style_tag)
        
        return str(soup)
    
    def _extract_document_properties(self, document):
        """Extract document properties and metadata"""
        try:
            props = {}
            
            # Get document properties
            if hasattr(document, 'DocumentProperties'):
                doc_props = document.DocumentProperties
                props['title'] = doc_props.Title if hasattr(doc_props, 'Title') else ''
                props['author'] = doc_props.Author if hasattr(doc_props, 'Author') else ''
                props['subject'] = doc_props.Subject if hasattr(doc_props, 'Subject') else ''
                props['keywords'] = doc_props.Keywords if hasattr(doc_props, 'Keywords') else []
                props['description'] = doc_props.Description if hasattr(doc_props, 'Description') else ''
            
            # Get page settings
            if hasattr(document, 'StyleFamilies'):
                page_styles = document.StyleFamilies.getByName("PageStyles")
                if page_styles.hasByName("Standard"):
                    standard_page = page_styles.getByName("Standard")
                    props['page_width'] = standard_page.Width if hasattr(standard_page, 'Width') else 0
                    props['page_height'] = standard_page.Height if hasattr(standard_page, 'Height') else 0
                    props['margin_top'] = standard_page.TopMargin if hasattr(standard_page, 'TopMargin') else 0
                    props['margin_bottom'] = standard_page.BottomMargin if hasattr(standard_page, 'BottomMargin') else 0
                    props['margin_left'] = standard_page.LeftMargin if hasattr(standard_page, 'LeftMargin') else 0
                    props['margin_right'] = standard_page.RightMargin if hasattr(standard_page, 'RightMargin') else 0
            
            logger.info(f"Extracted document properties: {props}")
            return props
            
        except Exception as e:
            logger.error(f"Error extracting document properties: {str(e)}")
            return {}
    
    def _extract_headers_footers(self, document):
        """Extract headers and footers from document"""
        try:
            headers_footers = {'headers': [], 'footers': []}
            
            # Get page styles
            if hasattr(document, 'StyleFamilies'):
                page_styles = document.StyleFamilies.getByName("PageStyles")
                
                # Iterate through page styles
                for i in range(page_styles.getCount()):
                    page_style = page_styles.getByIndex(i)
                    
                    # Check for headers
                    if hasattr(page_style, 'HeaderIsOn') and page_style.HeaderIsOn:
                        if hasattr(page_style, 'HeaderText'):
                            header_text = page_style.HeaderText.getString()
                            if header_text:
                                headers_footers['headers'].append({
                                    'style': page_style.Name,
                                    'text': header_text
                                })
                    
                    # Check for footers
                    if hasattr(page_style, 'FooterIsOn') and page_style.FooterIsOn:
                        if hasattr(page_style, 'FooterText'):
                            footer_text = page_style.FooterText.getString()
                            if footer_text:
                                headers_footers['footers'].append({
                                    'style': page_style.Name,
                                    'text': footer_text
                                })
            
            logger.info(f"Extracted headers/footers: {len(headers_footers['headers'])} headers, {len(headers_footers['footers'])} footers")
            return headers_footers
            
        except Exception as e:
            logger.error(f"Error extracting headers/footers: {str(e)}")
            return None
    
    def _extract_styles(self, document):
        """Extract paragraph and character styles"""
        try:
            styles_info = {
                'paragraph_styles': [],
                'character_styles': [],
                'table_styles': [],
                'list_styles': []
            }
            
            if hasattr(document, 'StyleFamilies'):
                # Extract paragraph styles
                if document.StyleFamilies.hasByName("ParagraphStyles"):
                    para_styles = document.StyleFamilies.getByName("ParagraphStyles")
                    for i in range(min(para_styles.getCount(), 50)):  # Limit to prevent overload
                        style = para_styles.getByIndex(i)
                        if hasattr(style, 'Name') and hasattr(style, 'DisplayName'):
                            style_info = {
                                'name': style.Name,
                                'display_name': style.DisplayName,
                                'font_name': style.CharFontName if hasattr(style, 'CharFontName') else '',
                                'font_size': style.CharHeight if hasattr(style, 'CharHeight') else 0,
                                'bold': style.CharWeight > 100 if hasattr(style, 'CharWeight') else False,
                                'italic': style.CharPosture > 0 if hasattr(style, 'CharPosture') else False
                            }
                            styles_info['paragraph_styles'].append(style_info)
                
                # Extract character styles
                if document.StyleFamilies.hasByName("CharacterStyles"):
                    char_styles = document.StyleFamilies.getByName("CharacterStyles")
                    for i in range(min(char_styles.getCount(), 30)):
                        style = char_styles.getByIndex(i)
                        if hasattr(style, 'Name'):
                            styles_info['character_styles'].append(style.Name)
            
            logger.info(f"Extracted {len(styles_info['paragraph_styles'])} paragraph styles")
            return styles_info
            
        except Exception as e:
            logger.error(f"Error extracting styles: {str(e)}")
            return {}
    
    def _enhance_html_with_metadata(self, html_content, doc_props, headers_footers, styles_info, advanced_elements):
        """Enhance HTML with extracted metadata and additional formatting"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add metadata to head
            if soup.head:
                # Add document properties as meta tags
                for key, value in doc_props.items():
                    if value and key in ['title', 'author', 'subject', 'description']:
                        meta_tag = soup.new_tag('meta', attrs={'name': key, 'content': str(value)})
                        soup.head.append(meta_tag)
                
                # Enhanced styles with full document support
                style_tag = soup.new_tag('style')
                style_tag.string = self._generate_enhanced_css(doc_props, styles_info)
                soup.head.append(style_tag)
            
            # Add headers/footers container
            if headers_footers and soup.body:
                # Add headers
                if headers_footers.get('headers'):
                    header_div = soup.new_tag('div', attrs={'class': 'document-headers', 'style': 'display: none;'})
                    for header in headers_footers['headers']:
                        h = soup.new_tag('div', attrs={'class': f'header-{header["style"]}'})
                        h.string = header['text']
                        header_div.append(h)
                    soup.body.insert(0, header_div)
                
                # Add footers
                if headers_footers.get('footers'):
                    footer_div = soup.new_tag('div', attrs={'class': 'document-footers', 'style': 'display: none;'})
                    for footer in headers_footers['footers']:
                        f = soup.new_tag('div', attrs={'class': f'footer-{footer["style"]}'})
                        f.string = footer['text']
                        footer_div.append(f)
                    soup.body.append(footer_div)
            
            # Add document wrapper with page dimensions
            if soup.body and doc_props:
                # Create wrapper div
                wrapper = soup.new_tag('div', attrs={
                    'class': 'document-wrapper',
                    'data-page-width': str(doc_props.get('page_width', 0)),
                    'data-page-height': str(doc_props.get('page_height', 0)),
                    'data-margin-top': str(doc_props.get('margin_top', 0)),
                    'data-margin-bottom': str(doc_props.get('margin_bottom', 0)),
                    'data-margin-left': str(doc_props.get('margin_left', 0)),
                    'data-margin-right': str(doc_props.get('margin_right', 0))
                })
                
                # Move all body content into wrapper
                body_contents = list(soup.body.children)
                for content in body_contents:
                    content.extract()
                    wrapper.append(content)
                
                soup.body.append(wrapper)
            
            # Add advanced elements
            if advanced_elements and soup.body:
                # Add text frames as floating divs
                if advanced_elements.get('text_frames'):
                    for frame in advanced_elements['text_frames']:
                        frame_div = soup.new_tag('div', attrs={
                            'class': 'text-frame floating-element',
                            'style': f'width: {frame["width"]/100}mm; min-height: {frame["height"]/100}mm;'
                        })
                        frame_div.string = frame['text']
                        soup.body.append(frame_div)
                
                # Add footnotes section
                if advanced_elements.get('footnotes'):
                    footnotes_div = soup.new_tag('div', attrs={'class': 'footnotes-section'})
                    footnotes_title = soup.new_tag('h3')
                    footnotes_title.string = 'Footnotes'
                    footnotes_div.append(footnotes_title)
                    
                    footnotes_list = soup.new_tag('ol')
                    for footnote in advanced_elements['footnotes']:
                        li = soup.new_tag('li')
                        li.string = footnote['text']
                        footnotes_list.append(li)
                    footnotes_div.append(footnotes_list)
                    soup.body.append(footnotes_div)
                
                # Add endnotes section
                if advanced_elements.get('endnotes'):
                    endnotes_div = soup.new_tag('div', attrs={'class': 'endnotes-section'})
                    endnotes_title = soup.new_tag('h3')
                    endnotes_title.string = 'Endnotes'
                    endnotes_div.append(endnotes_title)
                    
                    endnotes_list = soup.new_tag('ol')
                    for endnote in advanced_elements['endnotes']:
                        li = soup.new_tag('li')
                        li.string = endnote['text']
                        endnotes_list.append(li)
                    endnotes_div.append(endnotes_list)
                    soup.body.append(endnotes_div)
            
            # Enhance tables and lists
            soup = self._enhance_tables_and_lists(soup)
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Error enhancing HTML: {str(e)}")
            return html_content
    
    def _generate_enhanced_css(self, doc_props, styles_info):
        """Generate enhanced CSS based on document properties and styles"""
        css = """
            /* Enhanced Document Styles */
            body { 
                font-family: 'Calibri', 'Arial', sans-serif; 
                line-height: 1.6; 
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }
            
            .document-wrapper {
                background: white;
                margin: 20px auto;
                padding: 40px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                max-width: 210mm; /* A4 width */
                min-height: 297mm; /* A4 height */
            }
            
            /* Enhanced image styles */
            img { 
                max-width: 100%; 
                height: auto; 
                display: block;
                margin: 10px auto;
            }
            
            /* Floating images */
            img[style*="float: left"] {
                margin: 10px 20px 10px 0;
            }
            
            img[style*="float: right"] {
                margin: 10px 0 10px 20px;
            }
            
            /* Enhanced table styles */
            .table-wrapper {
                overflow-x: auto;
                margin: 20px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border-radius: 8px;
            }
            
            table, .enhanced-table {
                border-collapse: collapse;
                width: 100%;
                font-size: 0.95em;
                background: white;
            }
            
            td, th {
                border: 1px solid #e0e0e0;
                padding: 10px 12px;
                text-align: left;
                vertical-align: top;
            }
            
            th {
                background-color: #2c3e50;
                font-weight: bold;
                color: white;
                text-transform: uppercase;
                font-size: 0.9em;
                letter-spacing: 0.5px;
            }
            
            tr:hover {
                background-color: #f5f5f5;
                transition: background-color 0.2s;
            }
            
            tr.even-row {
                background-color: #fafafa;
            }
            
            tr.odd-row {
                background-color: white;
            }
            
            /* Multi-level lists */
            .main-list {
                margin: 10px 0;
                padding-left: 20px;
            }
            
            .nested-list {
                margin: 5px 0;
                padding-left: 20px;
            }
            
            ol.nested-list {
                list-style-type: lower-alpha;
            }
            
            ol.nested-list ol {
                list-style-type: lower-roman;
            }
            
            /* Text formatting */
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50;
                margin-top: 1em;
                margin-bottom: 0.5em;
                line-height: 1.3;
            }
            
            h1 { font-size: 2.5em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
            h2 { font-size: 2em; }
            h3 { font-size: 1.5em; }
            
            p {
                margin: 0.5em 0 1em 0;
                text-align: justify;
            }
            
            /* Lists */
            ul, ol {
                margin: 0.5em 0 1em 2em;
                padding: 0;
            }
            
            li {
                margin: 0.3em 0;
            }
            
            /* Text effects */
            .text-highlight {
                background-color: yellow;
                padding: 2px 4px;
            }
            
            .text-underline {
                text-decoration: underline;
            }
            
            .text-strikethrough {
                text-decoration: line-through;
            }
            
            .text-superscript {
                vertical-align: super;
                font-size: 0.8em;
            }
            
            .text-subscript {
                vertical-align: sub;
                font-size: 0.8em;
            }
            
            /* Text boxes and frames */
            .text-frame {
                border: 1px solid #ddd;
                padding: 10px;
                margin: 10px 0;
                background: #fafafa;
                border-radius: 4px;
            }
            
            /* Footnotes */
            .footnote {
                font-size: 0.85em;
                color: #666;
                vertical-align: super;
            }
            
            /* Page break for printing */
            .page-break {
                page-break-after: always;
                height: 0;
                margin: 0;
                border: none;
            }
            
            /* Headers and footers (for display) */
            .document-headers, .document-footers {
                background: #f8f9fa;
                padding: 10px;
                margin: 10px 0;
                border: 1px dashed #ddd;
                font-size: 0.9em;
                color: #666;
            }
            
            /* Hyperlinks */
            a {
                color: #0066cc;
                text-decoration: none;
            }
            
            a:hover {
                text-decoration: underline;
            }
            
            /* Form fields */
            input[type="text"], textarea {
                border: 1px solid #ddd;
                padding: 5px;
                font-family: inherit;
                font-size: inherit;
            }
            
            /* Floating elements (text frames) */
            .floating-element {
                position: relative;
                float: right;
                margin: 10px 0 10px 20px;
                padding: 15px;
                border: 1px solid #e0e0e0;
                background: #f9f9f9;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-radius: 4px;
                max-width: 40%;
            }
            
            /* Footnotes and endnotes */
            .footnotes-section, .endnotes-section {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #e0e0e0;
                font-size: 0.9em;
            }
            
            .footnotes-section h3, .endnotes-section h3 {
                font-size: 1.2em;
                color: #555;
                margin-bottom: 10px;
            }
            
            .footnotes-section ol, .endnotes-section ol {
                margin-left: 20px;
            }
            
            .footnotes-section li, .endnotes-section li {
                margin-bottom: 5px;
                color: #666;
            }
            
            /* Print styles */
            @media print {
                body {
                    background: white;
                }
                
                .document-wrapper {
                    margin: 0;
                    padding: 0;
                    box-shadow: none;
                    max-width: none;
                }
                
                .document-headers, .document-footers {
                    display: none;
                }
            }
        """
        
        # Add dynamic styles based on document properties
        if doc_props and doc_props.get('page_width'):
            # Convert from UNO units (1/100 mm) to CSS
            width_mm = doc_props['page_width'] / 100
            css += f"\n.document-wrapper {{ max-width: {width_mm}mm; }}"
        
        # Add custom paragraph styles
        if styles_info and styles_info.get('paragraph_styles'):
            for style in styles_info['paragraph_styles'][:20]:  # Limit to prevent CSS bloat
                if style.get('name') and style.get('font_name'):
                    css += f"""
                    .style-{style['name'].replace(' ', '-')} {{
                        font-family: '{style['font_name']}', sans-serif;
                        font-size: {style.get('font_size', 12)}pt;
                        {('font-weight: bold;' if style.get('bold') else '')}
                        {('font-style: italic;' if style.get('italic') else '')}
                    }}
                    """
        
        return css
    
    def _log_conversion_stats(self, document_path, success, error=None):
        """Log conversion statistics"""
        try:
            stats_file = os.path.join(os.path.dirname(__file__), "conversion_stats.json")
            
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
            else:
                stats = {}
            
            doc_name = os.path.basename(document_path)
            if doc_name not in stats:
                stats[doc_name] = {'success': 0, 'failure': 0, 'errors': [], 'last_attempt': None}
            
            stats[doc_name]['last_attempt'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            if success:
                stats[doc_name]['success'] += 1
            else:
                stats[doc_name]['failure'] += 1
                if error:
                    stats[doc_name]['errors'].append({
                        'error': error,
                        'timestamp': stats[doc_name]['last_attempt']
                    })
            
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log conversion stats: {str(e)}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.lo_process:
                try:
                    self.lo_process.terminate()
                    self.lo_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.lo_process.kill()
                    self.lo_process.wait()
            
            self._kill_existing_libreoffice()
            
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

def render_document_with_uno_images(document_path):
    """Main entry point for document conversion"""
    logger.info(f"🚀 Starting improved UNO conversion for: {document_path}")
    
    # Check if UNO modules are available
    try:
        import uno
        logger.info("✅ UNO modules available")
    except ImportError:
        logger.error("❌ UNO modules not available")
        return {'success': False, 'error': 'UNO modules not available'}
    
    # Check if LibreOffice is installed
    try:
        result = subprocess.run(['libreoffice', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"✅ LibreOffice available: {result.stdout.strip()}")
        else:
            return {'success': False, 'error': 'LibreOffice not available'}
    except Exception as e:
        return {'success': False, 'error': f'LibreOffice check failed: {str(e)}'}
    
    converter = ImprovedLibreOfficeConverter()
    try:
        result = converter.convert_with_uno(document_path)
        if result:
            logger.info(f"✅ Conversion successful: {result.get('images_found', 0)} images embedded")
        return result or {'success': False, 'error': 'Conversion failed after retries'}
    finally:
        converter.cleanup()

if __name__ == "__main__":
    # Test the converter
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        result = render_document_with_uno_images(test_file)
        print(f"Result: {result}")
    else:
        print("Usage: python3 libreoffice_uno_converter_improved.py <document_path>")