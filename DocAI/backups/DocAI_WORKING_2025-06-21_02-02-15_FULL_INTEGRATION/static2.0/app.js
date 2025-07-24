document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');
    
    const chatbox = document.getElementById('chatbox');
    const userInputField = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const micBtn = document.getElementById('micBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const fontSelect = document.getElementById('fontSelect');
    const stopBtn = document.getElementById('stopBtn');
    const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8090'
    : window.location.origin;

                                

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let currentController = null;
    let isGenerating = false;

    let isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    let isToggleMode = isMobileDevice; // Use toggle mode for mobile devices

    const addMessage = (message, isUser = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        if (!isUser) {
            const logoImg = document.createElement('img');
            logoImg.src = 'Durga.png';
            logoImg.alt = 'AI Logo';
            logoImg.className = 'message-logo';
            messageDiv.appendChild(logoImg);
        }

        const textSpan = document.createElement('span');
        textSpan.textContent = message;
        textSpan.className = 'message-text';
        messageDiv.appendChild(textSpan);

        chatbox.appendChild(messageDiv);
        
        // Add show class after a small delay for animation
        if (!isUser) {
            setTimeout(() => {
                messageDiv.classList.add('show');
            }, 10);
        }
        
        // Only auto-scroll for AI messages, not user messages
        if (!isUser) {
            scrollToBottom();
        }
        return messageDiv;
    };

    // Helper function for smooth auto-scrolling
    const scrollToBottom = () => {
        chatbox.scrollTop = chatbox.scrollHeight;
        // Ensure it's at the bottom even if content is still loading
        setTimeout(() => {
            chatbox.scrollTop = chatbox.scrollHeight;
        }, 10);
    };

    const addInitialMessage = () => {
        const currentLanguage = localStorage.getItem('language') || 'tamil';
        const initialMessage = currentLanguage === 'english' 
            ? 'Hello! I am Durga AI, how can I help you?'
            : 'வணக்கம்! நான் துர்கா AI, உங்களுக்கு என்ன உதவி செய்ய வேண்டும்?';
        addMessage(initialMessage);
        userInputField.disabled = false;
        sendBtn.disabled = false;
        micBtn.disabled = false;
        userInputField.focus();
    };

    stopBtn.addEventListener('click', async () => {

        if (currentController) {
            isGenerating = false;  // This will trigger the !isGenerating condition in the while loop
            await currentController.abort();
            currentController = null;
        }
    });

    const cleanResponse = (text) => {
        const phrases = text.split('.');
        const uniquePhrases = [...new Set(phrases)];
        return uniquePhrases.join('. ').trim();
    };

    const addMessageWithRetry = (message, isUser = false) => {
        const messageDiv = addMessage(message, isUser);
        
        if (!isUser) {
            messageDiv.classList.add('loading');
            
            // Add retry button for bot messages
            const retryButton = document.createElement('button');
            retryButton.className = 'retry-button';
            retryButton.style.display = 'none';  // Hidden by default
            retryButton.textContent = 'மீண்டும் முயற்சி';
            retryButton.onclick = () => retryMessage(message, messageDiv);
            messageDiv.appendChild(retryButton);
        }
        
        return messageDiv;
    };

    const retryMessage = async (originalMessage, messageDiv) => {
        messageDiv.classList.add('loading');
        messageDiv.classList.remove('error');
        const retryButton = messageDiv.querySelector('.retry-button');
        if (retryButton) retryButton.style.display = 'none';
        
        try {
            await sendMessage(originalMessage);
            messageDiv.remove();  // Remove old message on success
        } catch (error) {
            messageDiv.classList.remove('loading');
            messageDiv.classList.add('error');
            if (retryButton) retryButton.style.display = 'inline';
        }
    };

    // Add this function to test the server connection
    async function testServerConnection() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/health`);
            const data = await response.json();
            console.log('Server health check:', data);
            return data.status === 'ok';
        } catch (error) {
            console.error('Server connection test failed:', error);
            return false;
        }
    }

    // Add this function to check the debug info
    async function checkDebugInfo() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/debug`);
            const data = await response.json();
            console.log('Debug info:', data);
            
            // Check if there are any critical issues
            if (!data.groq_api_key_set) {
                console.error('GROQ API key is not set!');
                return false;
            }
            
            if (data.groq_api_test !== 'success') {
                console.error('GROQ API test failed:', data.groq_api_error);
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('Debug check failed:', error);
            return false;
        }
    }

    // Add this simple function to test the basic chat functionality
    async function testSimpleChat() {
        try {
            // First test the hello endpoint
            const helloResponse = await fetch(`${API_BASE_URL}/api/hello`);
            const helloData = await helloResponse.json();
            console.log('Hello response:', helloData);
            
            // Create a placeholder for the AI response
            const aiMessageDiv = addMessage('Testing connection...', false);
            
            // Try the simple chat endpoint
            const response = await fetch(`${API_BASE_URL}/api/simple_chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: "Hello, can you respond with a simple greeting?" }),
                credentials: 'include'
            });
            
            const data = await response.json();
            console.log('Simple chat response:', data);
            
            if (data.status === 'success') {
                aiMessageDiv.querySelector('.message-text').textContent = data.response;
            } else {
                aiMessageDiv.querySelector('.message-text').textContent = 
                    `Error: ${data.error || 'Unknown error'}. Response: ${data.response}`;
                aiMessageDiv.classList.add('error');
            }
            
            return data.status === 'success';
        } catch (error) {
            console.error('Test simple chat failed:', error);
            const aiMessageDiv = addMessage(`Connection test failed: ${error.message}`, false);
            aiMessageDiv.classList.add('error');
            return false;
        }
    }

    // Add a button to test the connection
    function addTestButton() {
        const chatbox = document.getElementById('chatbox');
        const testButton = document.createElement('button');
        testButton.textContent = 'Test Connection';
        testButton.className = 'test-button';
        testButton.onclick = testSimpleChat;
        chatbox.appendChild(testButton);
    }

    // Test button removed for production

    // Update the sendMessage function to try the simple chat endpoint if streaming fails
    const sendMessage = async (inputText) => {
        const userInput = inputText.trim();
        if (userInput === '') return;

        // Add user message to chat
        addMessage(userInput, true);
        userInputField.value = '';
        
        // Disable input while processing
        userInputField.disabled = true;
        sendBtn.disabled = true;
        micBtn.disabled = true;
        stopBtn.style.display = 'block';

        // Create a placeholder for the AI response
        const aiMessageDiv = addMessage('', false);
        aiMessageDiv.classList.add('generating');
        
        // Get current language preference
        const currentLanguage = localStorage.getItem('language') || 'tamil';
        
        try {
            console.log('Using streaming endpoint with RAG');
            // Go directly to streaming endpoint which has RAG support
            await tryStreamingResponse(userInput, aiMessageDiv);
            
        } catch (error) {
            console.error('Error in sendMessage:', error);
            console.log('Trying streaming endpoint as fallback...');
            try {
                await tryStreamingResponse(userInput, aiMessageDiv);
            } catch (streamError) {
                console.error('Streaming also failed:', streamError);
                aiMessageDiv.classList.add('error');
                aiMessageDiv.querySelector('.message-text').textContent = 
                    'சேவையகத்துடன் தொடர்பு கொள்ள முடியவில்லை. மீண்டும் முயற்சிக்கவும்.';
            }
        } finally {
            // Reset UI state
            aiMessageDiv.classList.remove('generating');
            stopBtn.style.display = 'none';
            userInputField.disabled = false;
            sendBtn.disabled = false;
            micBtn.disabled = false;
            userInputField.focus();
        }
    };

    // Update the event listener for the send button
    sendBtn.addEventListener('click', () => {
        if (userInputField.value.trim() !== '' && !userInputField.disabled) {
            sendMessage(userInputField.value);
        }
    });

    // Add Enter key support for input field
    userInputField.addEventListener('keypress', (e) => {
        console.log('Key pressed:', e.key, 'Input disabled:', userInputField.disabled);
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (userInputField.value.trim() !== '' && !userInputField.disabled) {
                sendMessage(userInputField.value);
            }
        }
    });

    // Streaming response fallback function
    const tryStreamingResponse = async (userInput, aiMessageDiv) => {
        // Get current language preference
        let streamLanguage = localStorage.getItem('language') || 'tamil';
        
        const response = await fetch(`${API_BASE_URL}/api/query_stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                query: userInput,
                language: streamLanguage,
                use_rag: true 
            }),
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        let responseText = '';
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = new TextDecoder().decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === 'END_OF_STREAM') {
                            aiMessageDiv.classList.remove('generating');
                            return;
                        }
                        
                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.text) {
                                responseText += parsed.text;
                                aiMessageDiv.querySelector('.message-text').textContent = responseText;
                                // Auto-scroll to latest message during streaming
                                scrollToBottom();
                            }
                        } catch (e) {
                            console.log('Non-JSON data:', data);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
            // Final scroll to ensure complete AI response is visible
            scrollToBottom();
        }
    };


    // Initialize the application
    const initializeApp = async () => {
        console.log('Initializing application...');
        
        // Test server connection first
        const serverConnected = await testServerConnection();
        if (!serverConnected) {
            console.error('Server connection failed');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message bot-message error';
            errorDiv.innerHTML = '<img src="Durga.png" alt="AI"><span class="message-text">சேவையகத்துடன் இணைப்பு தோல்வியடைந்தது. பக்கத்தை மீண்டும் ஏற்றவும் அல்லது பிறகு முயற்சிக்கவும்.</span>';
            chatbox.appendChild(errorDiv);
            return;
        }

        // Check debug info
        const debugOk = await checkDebugInfo();
        if (!debugOk) {
            console.error('Debug check failed');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message bot-message error';
            errorDiv.innerHTML = '<img src="Durga.png" alt="AI"><span class="message-text">சேவையகத்துடன் இணைப்பு சரியாக இல்லை. API விசைகள் சரிபார்க்கவும் அல்லது பிறகு முயற்சிக்கவும்.</span>';
            chatbox.appendChild(errorDiv);
            return;
        }

        console.log('App initialization successful');
        addInitialMessage();
    };

    // Initialize app when DOM is ready
    initializeApp();
    
    // Debug: Test if input field is accessible
    console.log('UserInput field found:', !!userInputField);
    console.log('UserInput field enabled:', !userInputField.disabled);

    const clearChat = async () => {

        try {
            let currentLanguage = localStorage.getItem('language') || 'tamil';
            const response = await fetch(`${API_BASE_URL}/api/clear_chat`, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ language: currentLanguage }),
                credentials: 'include'
            });
            const data = await response.json();
            console.log('Clear Chat response:', data);
            chatbox.innerHTML = '';
            addInitialMessage();
            
            // Add system message with special styling
            const systemMessageDiv = document.createElement('div');
            systemMessageDiv.className = 'message bot-message system-message';
            
            const logoImg = document.createElement('img');
            logoImg.src = 'Durga.png';
            logoImg.alt = 'AI Logo';
            logoImg.className = 'message-logo';
            systemMessageDiv.appendChild(logoImg);

            const textSpan = document.createElement('span');
            currentLanguage = localStorage.getItem('language') || 'tamil';
            textSpan.textContent = currentLanguage === 'english' 
                ? "Chat history cleared!"
                : "உரையாடல் வரலாறு அழிக்கப்பட்டது!";
            textSpan.className = 'message-text';
            systemMessageDiv.appendChild(textSpan);

            chatbox.appendChild(systemMessageDiv);
            scrollToBottom();

            // Remove the system message after animation
            setTimeout(() => {
                systemMessageDiv.remove();
            }, 3000); // Match this with CSS animation duration
        } catch (error) {
            console.error('Error clearing chat history:', error);
        }
    };
    
    // Make clearChat globally accessible for language switching
    window.clearChat = clearChat;

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000
                }
            });
            
            // First record in webm (supported format)
            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm',
                audioBitsPerSecond: 16000
            });
            
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };
                                                                             
            mediaRecorder.onstop = async () => {
                // Convert to WAV before sending
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const wavBlob = await convertToWav(audioBlob);
                await sendAudioToServer(wavBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add('recording');
        } catch (error) {
            console.error('Error starting recording:', error);
            addMessage('ஒலிப்பதிவு தொடங்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.', false);
        }
    };

    // Add this function to convert webm to wav
    const convertToWav = async (webmBlob) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuffer = await webmBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        const wavBuffer = audioBufferToWav(audioBuffer);
        return new Blob([wavBuffer], { type: 'audio/wav' });
    };

    // Helper function to convert AudioBuffer to WAV format
    const audioBufferToWav = (buffer) => {
        const numChannels = buffer.numberOfChannels;
        const sampleRate = buffer.sampleRate;
        const format = 1; // PCM
        const bitDepth = 16;
        
        const bytesPerSample = bitDepth / 8;
        const blockAlign = numChannels * bytesPerSample;
        
        const dataSize = buffer.length * blockAlign;
        const headerSize = 44;
        const totalSize = headerSize + dataSize;
        
        const arrayBuffer = new ArrayBuffer(totalSize);
        const dataView = new DataView(arrayBuffer);
        
        // WAV header
        writeString(dataView, 0, 'RIFF');
        dataView.setUint32(4, totalSize - 8, true);
        writeString(dataView, 8, 'WAVE');
        writeString(dataView, 12, 'fmt ');
        dataView.setUint32(16, 16, true);
        dataView.setUint16(20, format, true);
        dataView.setUint16(22, numChannels, true);
        dataView.setUint32(24, sampleRate, true);
        dataView.setUint32(28, sampleRate * blockAlign, true);
        dataView.setUint16(32, blockAlign, true);
        dataView.setUint16(34, bitDepth, true);
        writeString(dataView, 36, 'data');
        dataView.setUint32(40, dataSize, true);
        
        // Write audio data
        const offset = 44;
        const channelData = [];
        for (let i = 0; i < numChannels; i++) {
            channelData[i] = buffer.getChannelData(i);
        }
        
        let pos = offset;
        for (let i = 0; i < buffer.length; i++) {
            for (let ch = 0; ch < numChannels; ch++) {
                const sample = Math.max(-1, Math.min(1, channelData[ch][i]));
                const int = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
                dataView.setInt16(pos, int, true);
                pos += 2;
            }
        }
        
        return arrayBuffer;
    };

    const writeString = (dataView, offset, string) => {
        for (let i = 0; i < string.length; i++) {
            dataView.setUint8(offset + i, string.charCodeAt(i));
        }
    };

    const stopRecording = () => {
        console.log('Stop recording called, isRecording:', isRecording);
        if (mediaRecorder && isRecording) {
            try {
                mediaRecorder.stop();
                isRecording = false;
                micBtn.classList.remove('recording');
                console.log('Recording stopped successfully');
            } catch (error) {
                console.error('Error stopping recording:', error);
                // Reset state even if error occurs
                isRecording = false;
                micBtn.classList.remove('recording');
            }
        }
    };

    const sendAudioToServer = async (audioBlob) => {
        if (!audioBlob || audioBlob.size === 0) {
            console.error('Empty audio blob');
            return;
        }

        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');  // Changed to .wav

        try {
            const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (response.ok && data.transcription) {
                userInputField.value = data.transcription;
                userInputField.focus();

                // Optional: Show a hint to edit if needed
                const hint = document.createElement('div');
                hint.className = 'transcription-hint';
                hint.textContent = 'உரையை சரிபார்த்து திருத்தம் செய்யலாம்';
                userInputField.parentNode.appendChild(hint);
                
                // Remove hint after 3 seconds
                setTimeout(() => hint.remove(), 6000);

                // Select text for easy editing
                userInputField.select();
            } else {
                console.error('Transcription error:', data.error);
                addMessage('ேச்சை ரையாக மாற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.', false);
            }
        } catch (error) {
            console.error('Audio processing error:', error);
            addMessage('ஒலி செயலாக்கம் தோல்வி. மீண்டும் முயற்சிக்கவும்.', false);
        }
    };

    // Add CSS for the hint
    const style = document.createElement('style');
    style.textContent = `
        .transcription-hint {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8em;
            animation: fadeInOut 3s ease-in-out forwards;
        }
    `;
    document.head.appendChild(style);


    clearChatBtn.addEventListener('click', () => {
        //console.log('Clear Chat button clicked');
        clearChat();
    });

    const setupMicButton = () => {
        let isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        let isToggleMode = isMobileDevice;

        if (isMobileDevice) {
            // Remove click event and use touchstart/touchend for better mobile response
            micBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Touch start on mic button');
                
                if (isRecording) {
                    console.log('Stopping recording...');
                    stopRecording();
                    micBtn.classList.remove('recording');
                } else {
                    console.log('Starting recording...');
                    startRecording();
                    micBtn.classList.add('recording');
                }
            });

            // Add touchend just to prevent any default behavior
            micBtn.addEventListener('touchend', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Touch end on mic button');
            });

            // Add touch cancel handler
            micBtn.addEventListener('touchcancel', (e) => {
                e.preventDefault();
                console.log('Touch cancelled');
                if (isRecording) {
                    stopRecording();
                    micBtn.classList.remove('recording');
                }
            });

            // Keep click event as fallback but with immediate response
            micBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Click on mic button (mobile fallback)');
                
                if (isRecording) {
                    stopRecording();
                    micBtn.classList.remove('recording');
                } else {
                    startRecording();
                    micBtn.classList.add('recording');
                }
            });
        } else {
            // Desktop behavior remains unchanged
            micBtn.addEventListener('mousedown', () => {
                startRecording();
            });

            micBtn.addEventListener('mouseup', () => {
                stopRecording();
            });

            micBtn.addEventListener('mouseleave', () => {
                if (isRecording) {
                    stopRecording();
                }
            });
        }
    };

    // Call this function when the page loads
    setupMicButton();

    // Update font selection functionality
    const updateFont = (fontType) => {
        chatbox.className = `font-${fontType}`;
        localStorage.setItem('preferredFont', fontType);
    };

    // Load saved preference with new font names
    const savedFont = localStorage.getItem('preferredFont');
    if (savedFont) {
        fontSelect.value = savedFont;
        updateFont(savedFont);
    } else {
        // Default to Thanjai if no preference
        updateFont('thanjai');
    }

    fontSelect.addEventListener('change', (e) => {
        updateFont(e.target.value);
    });

    // Update the stop button handler


    // Add this CSS to ensure the stop button is visible when needed
    const stopStyle = document.createElement('style');
    stopStyle.textContent = `
        #stopBtn {
            display: none;
            position: relative;
            z-index: 1000;
        }
    `;
    document.head.appendChild(stopStyle);

    // Add this CSS to your existing style definitions
    const micStyle = document.createElement('style');
    micStyle.textContent = `
        .mic-record-circle {
            fill: #2196F3;  /* Default blue color */
            transition: fill 0.3s ease;
        }

        .mic-center {
            fill: #333;  /* Default dark color */
            transition: fill 0.3s ease;
        }

        .recording .mic-record-circle {
            fill: #FF0000;  /* Red color when recording */
            animation: pulse 1.5s infinite;  /* Added pulse animation for recording state */
        }

        .recording .mic-center {
            fill: #FFFFFF;  /* White color when recording */
        }

        @keyframes pulse {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            50% {
                transform: scale(1.1);
                opacity: 0.7;
            }
            100% {
                transform: scale(1);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(micStyle);

    window.handleEditClick = function(filename) {
        const fileExt = filename.split('.').pop().toLowerCase();
        
        if (fileExt === 'pdf') {
            // Show loading indicator
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'loading-indicator';
            loadingMsg.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing PDF for editing...';
            document.body.appendChild(loadingMsg);
            
            // Convert PDF to editable format
            fetch('/convert-to-word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    filename: filename,
                    mode: 'convert_only'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Enable PDF editing mode
                    window.documentContext = {
                        isEditing: true,
                        documentType: 'pdf',
                        currentDocument: filename
                    };
                    
                    // Add edit mode indicator
                    const editIndicator = document.createElement('div');
                    editIndicator.className = 'edit-mode-indicator';
                    editIndicator.innerHTML = '<i class="fas fa-edit"></i> Edit Mode';
                    document.body.appendChild(editIndicator);
                    
                    // Get the document container
                    const docContainer = document.querySelector('.word-viewer-container');
                    if (docContainer) {
                        docContainer.classList.add('edit-mode');
                        const pages = docContainer.querySelectorAll('.word-page');
                        pages.forEach(page => {
                            page.contentEditable = 'true';
                            page.style.cursor = 'text';
                            page.style.userSelect = 'text';
                            page.style.WebkitUserSelect = 'text';
                            page.style.MozUserSelect = 'text';
                            page.style.msUserSelect = 'text';
                            
                            // Make all text elements editable
                            const textElements = page.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
                            textElements.forEach(el => {
                                el.contentEditable = 'true';
                                el.classList.add('editable');
                                
                                // Add direct input event listeners
                                el.addEventListener('input', function(e) {
                                    e.stopPropagation();
                                    console.log('Text edited:', e.target.textContent);
                                });
                                
                                el.addEventListener('focus', function() {
                                    this.style.outline = '2px solid #4a90e2';
                                });
                                
                                el.addEventListener('blur', function() {
                                    this.style.outline = 'none';
                                });
                            });
                        });
                    }
                    
                    showEditSuccess('PDF ready for editing');
                } else {
                    throw new Error(data.error || 'Failed to convert PDF');
                }
            })
            .catch(error => {
                console.error('Error converting PDF:', error);
                showEditError(error.message);
            })
            .finally(() => {
                // Remove loading indicator
                document.querySelector('.loading-indicator')?.remove();
            });
        } else if (['doc', 'docx'].includes(fileExt)) {
            enableEditMode(filename);
        }
    };

    // Update the enableEditMode function
    async function enableEditMode(filename) {
        try {
            window.documentContext = {
                isEditing: true,
                currentDocument: filename,
                selectedContent: null
            };

            const docContainer = document.querySelector('.word-viewer-container');
            if (!docContainer) {
                throw new Error('Document container not found');
            }

            docContainer.classList.add('edit-mode');
            const pages = docContainer.querySelectorAll('.word-page');
            
            pages.forEach((page, index) => {
                page.classList.add('edit-mode');
                page.contentEditable = 'true';
                page.style.cursor = 'text';
                page.style.userSelect = 'text';
                page.style.WebkitUserSelect = 'text';
                page.style.MozUserSelect = 'text';
                page.style.msUserSelect = 'text';
                
                // Make all text elements editable
                const textElements = page.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
                textElements.forEach(el => {
                    el.contentEditable = 'true';
                    el.classList.add('editable');
                    
                    // Add direct input event listeners
                    el.addEventListener('input', function(e) {
                        e.stopPropagation();
                        console.log('Text edited:', e.target.textContent);
                    });
                    
                    el.addEventListener('focus', function() {
                        this.style.outline = '2px solid #4a90e2';
                    });
                    
                    el.addEventListener('blur', function() {
                        this.style.outline = 'none';
                    });
                });
            });

            // Add global event listeners
            document.addEventListener('mouseup', handleTextSelection);
            document.addEventListener('keyup', handleTextSelection);
            
            console.log('Edit mode enabled successfully');
            
        } catch (error) {
            console.error('Error in enableEditMode:', error);
            alert('Error enabling edit mode: ' + error.message);
        }
    }

    // Add success/error message functions if not already present
    function showEditSuccess(message) {
        const successMsg = document.createElement('div');
        successMsg.className = 'edit-success-message';
        successMsg.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        document.body.appendChild(successMsg);
        setTimeout(() => successMsg.remove(), 3000);
    }

    function showEditError(message) {
        const errorMsg = document.createElement('div');
        errorMsg.className = 'edit-error-message';
        errorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        document.body.appendChild(errorMsg);
        setTimeout(() => errorMsg.remove(), 3000);
    }

    function handleBrowserAgent() {
        // Show browser agent iframe
        const chatContainer = document.querySelector('.chat-container');
        chatContainer.innerHTML = '<iframe id="browserAgentFrame" src="/browser-agent" style="width:100%; height:100%; border:none;"></iframe>';
        document.body.classList.add('browser-agent-active');
        
        // Add browser agent welcome message
        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'message bot-message';
        welcomeMsg.innerHTML = `<img src="Durga.png" alt="AI">Browser Agent activated. How can I help you browse the web?`;
        chatbox.appendChild(welcomeMsg);
    }

    // Update send button click handler
    sendBtn.addEventListener('click', async function() {
        const message = userInputField.value.trim();
        if (!message) return;

        // Add user message to chat
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.textContent = message;
        chatbox.appendChild(userMsg);

        // If browser agent is active, send to browser agent
        if (document.body.classList.contains('browser-agent-active')) {
            const iframe = document.querySelector('#browserAgentFrame');
            if (iframe && iframe.contentWindow) {
                try {
                    // Send message to browser agent
                    const response = await fetch('/api/browser-agent', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ message })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        // Add browser agent response to chat
                        const botMsg = document.createElement('div');
                        botMsg.className = 'message bot-message';
                        botMsg.innerHTML = `<img src="Durga.png" alt="AI">${data.message}`;
                        chatbox.appendChild(botMsg);
                    }
                } catch (error) {
                    console.error('Error sending message to browser agent:', error);
                }
            }
        }

        // Clear input (no auto-scroll for user input)
        userInputField.value = '';
    });

    // Add click handler for browser agent menu item
    document.querySelector('[onclick="handleBrowserAgent()"]').addEventListener('click', handleBrowserAgent);

    // Add or update the message handling function
    function handleUserMessage(message) {
        // Display user message
        appendMessage('user', message);
        
        // Disable input while processing
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        userInput.disabled = true;
        sendBtn.disabled = true;
        
        // Show stop button
        document.getElementById('stopBtn').style.display = 'inline-block';
        
        // Create EventSource for streaming response
        const eventSource = new EventSource(`/api/chat?message=${encodeURIComponent(message)}`);
        
        let assistantMessage = '';
        
        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (data.content) {
                    assistantMessage += data.content;
                    updateLastMessage('assistant', assistantMessage);
                    // Auto-scroll to latest message during streaming
                    scrollToBottom();
                }
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            eventSource.close();
            userInput.disabled = false;
            sendBtn.disabled = false;
            document.getElementById('stopBtn').style.display = 'none';
        };
        
        eventSource.onclose = function() {
            userInput.disabled = false;
            sendBtn.disabled = false;
            document.getElementById('stopBtn').style.display = 'none';
        };
    }
});

