// Enhanced JavaScript functionality for the Ask Rumi app

// Extended functionality for better user experience
class RumiApp {
    constructor() {
        // Auto-detect API base - use current origin when running on tunnel
        this.API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? 'http://127.0.0.1:8001' 
            : window.location.origin;
        
        this.selectedModel = 'qwen3:0.6b';
        this.currentConversationId = null;
        this.isRecording = false;
        this.recognition = null;
        this.speechSynthesis = window.speechSynthesis;
        this.settings = {
            tts: true,
            voiceInput: true,
            darkMode: false,
            defaultModel: 'qwen3:0.6b',
            autoSpeak: true,
            typingSpeed: 30,
            soundEffects: true,
            // LLM Behavior Settings
            historyDepth: 2,
            maxTokensWisdom: 180,
            maxTokensEmpathy: 220,
            maxTokensCasual: 80,
            temperature: 0.8,
            maxQuotes: 3
        };
        this.conversations = [];
        this.isTyping = false;
    }

    async init() {
        console.log('🚀 RumiApp init started');
        this.setupSpeechRecognition();
        this.setupEventListeners();
        this.loadSettings();
        
        // Wait for DOM to be fully ready
        await new Promise(resolve => setTimeout(resolve, 100));
        
        await this.loadInitialData();
        
        // Force reload chat models after everything is ready
        console.log('✅ Force reloading chat models after init...');
        if (this.availableModels && this.availableModels.length > 0) {
            this.loadChatModelSelector(this.availableModels);
        }
        
        this.setupKeyboardShortcuts();
        this.setupServiceWorker();
    }

    setupSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isRecording = true;
                this.updateVoiceButton();
                this.showToast('Listening...', 'info');
            };
            
            this.recognition.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                const chatInput = document.getElementById('chatInput');
                chatInput.value = finalTranscript || interimTranscript;
                
                if (finalTranscript) {
                    this.isRecording = false;
                    this.updateVoiceButton();
                    this.showToast('Voice input received', 'success');
                }
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isRecording = false;
                this.updateVoiceButton();
                this.showToast('Voice input error: ' + event.error, 'error');
            };
            
            this.recognition.onend = () => {
                this.isRecording = false;
                this.updateVoiceButton();
            };
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const page = tab.dataset.page;
                this.switchPage(page);
            });
        });

        // Model selection - handled dynamically in loadChatModelSelector
        // No need to add listeners here as buttons don't exist yet

        // Chat functionality
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        const voiceBtn = document.getElementById('voiceBtn');

        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });

        sendBtn.addEventListener('click', () => this.sendMessage());
        voiceBtn.addEventListener('click', () => this.toggleVoiceInput());

        // Header actions
        document.getElementById('clearChatBtn').addEventListener('click', () => this.clearChat());
        document.getElementById('newChatBtn').addEventListener('click', () => this.newChat());

        // Settings
        this.setupSettingsListeners();
    }

    setupSettingsListeners() {
        document.getElementById('ttsToggle').addEventListener('click', () => {
            this.settings.tts = !this.settings.tts;
            document.getElementById('ttsToggle').classList.toggle('active');
            this.saveSettings();
        });

        document.getElementById('voiceToggle').addEventListener('click', () => {
            this.settings.voiceInput = !this.settings.voiceInput;
            document.getElementById('voiceToggle').classList.toggle('active');
            this.saveSettings();
        });

        document.getElementById('darkModeToggle').addEventListener('click', () => {
            this.settings.darkMode = !this.settings.darkMode;
            document.getElementById('darkModeToggle').classList.toggle('active');
            this.toggleDarkMode();
            this.saveSettings();
        });

        document.getElementById('defaultModelSelect').addEventListener('change', (e) => {
            this.settings.defaultModel = e.target.value;
            this.selectedModel = e.target.value;
            this.saveSettings();
        });
        
        // LLM Behavior Settings
        document.getElementById('saveBehaviorBtn').addEventListener('click', () => {
            this.saveBehaviorSettings();
        });
        
        // Prompt Templates
        document.getElementById('savePromptTemplatesBtn').addEventListener('click', () => {
            this.savePromptTemplates();
        });
        
        document.getElementById('resetPromptTemplatesBtn').addEventListener('click', () => {
            this.resetPromptTemplates();
        });
        
        // LLM Settings Page
        document.getElementById('llm-saveBehaviorBtn').addEventListener('click', () => {
            this.saveLLMBehaviorSettings();
        });
        
        document.getElementById('llm-savePromptTemplatesBtn').addEventListener('click', () => {
            this.saveLLMPromptTemplates();
        });
        
        document.getElementById('llm-resetPromptTemplatesBtn').addEventListener('click', () => {
            this.resetLLMPromptTemplates();
        });
        
        // Emotion & Keyword Tags
        document.getElementById('llm-saveTagsBtn').addEventListener('click', () => {
            this.saveEmotionKeywords();
        });
        
        document.getElementById('llm-resetTagsBtn').addEventListener('click', () => {
            if (confirm('Reset all emotion and keyword tags to default?')) {
                this.loadEmotionKeywords();
            }
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for new chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.newChat();
            }
            
            // Ctrl/Cmd + / for settings
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.switchPage('settings');
            }
            
            // Escape to stop speaking
            if (e.key === 'Escape') {
                this.speechSynthesis.cancel();
            }
        });
    }

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadModels(),
            this.loadSystemInfo(),
            this.loadConversations()
        ]);
    }

    async switchPage(pageName) {
        console.log(`🔄 Switching to page: ${pageName}`);
        
        // Update navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(`${pageName}-page`).classList.add('active');

        // Load page-specific data
        switch(pageName) {
            case 'chat':
                // Ensure models are loaded for chat page
                if (!this.availableModels || this.availableModels.length === 0) {
                    console.log('🔄 Chat page: models not loaded, loading now...');
                    await this.loadModels();
                }
                break;
            case 'models':
                this.loadModels();
                break;
            case 'system':
                this.loadSystemInfo();
                break;
            case 'history':
                this.loadConversations();
                break;
            case 'settings':
                // Regular settings page
                break;
           case 'llm-settings':
                   this.loadLLMBehaviorSettings();
                   this.loadEmotionKeywords();
                   break;
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        input.style.height = 'auto';

        // Show typing indicator
        const typingId = this.addTypingIndicator();

        console.log(`💬 Sending message with model: ${this.selectedModel}`);

        try {
            const response = await fetch(`${this.API_BASE}/api/chat/ask-rumi`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: this.selectedModel,
                    temperature: 0.8,
                    conversation_id: this.currentConversationId
                })
            });

            const data = await response.json();

            // Remove typing indicator
            this.removeMessage(typingId);

            if (data.response) {
                // Add Rumi's response with typing effect
                const messageId = this.addMessage('', 'rumi');
                this.currentConversationId = data.conversation_id;
                
                // Type out the response
                await this.typeMessage(messageId, data.response);
                
                // Speak response if TTS is enabled
                if (this.settings.tts && this.settings.autoSpeak) {
                    setTimeout(() => {
                        this.speakText(document.querySelector(`[data-message-id="${messageId}"] .action-btn`));
                    }, 1000);
                }

                this.showToast(`Response received in ${data.inference_time?.toFixed(2)}s`, 'success');
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'rumi');
                this.showToast('Error: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.removeMessage(typingId);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'rumi');
            this.showToast('Error: ' + error.message, 'error');
        }
    }

    addMessage(text, sender, isLoading = false) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.dataset.messageId = messageId;

        const avatar = sender === 'user' ? '👤' : '🧠';
        const actions = isLoading ? '' : `
            <div class="message-actions">
                <button class="action-btn" onclick="rumiApp.speakText(this)" title="Speak">🔊</button>
                <button class="action-btn" onclick="rumiApp.copyText(this)" title="Copy">📋</button>
            </div>
        `;

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${text}</div>
                ${actions}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return messageId;
    }

    addTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingId = 'typing_' + Date.now();

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message rumi';
        typingDiv.dataset.messageId = typingId;

        typingDiv.innerHTML = `
            <div class="message-avatar">🧠</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span>Rumi is thinking</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return typingId;
    }

    async typeMessage(messageId, text) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"] .message-text`);
        messageElement.textContent = '';
        
        this.isTyping = true;
        
        for (let i = 0; i < text.length; i++) {
            if (!this.isTyping) break;
            
            messageElement.textContent += text[i];
            
            // Scroll to bottom
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            await new Promise(resolve => setTimeout(resolve, this.settings.typingSpeed));
        }
        
        this.isTyping = false;
    }

    removeMessage(messageId) {
        const message = document.querySelector(`[data-message-id="${messageId}"]`);
        if (message) {
            message.remove();
        }
    }

    speakText(button) {
        const messageText = button.closest('.message-content').querySelector('.message-text').textContent;

        if (this.speechSynthesis.speaking) {
            this.speechSynthesis.cancel();
            button.textContent = '🔊';
            return;
        }

        const utterance = new SpeechSynthesisUtterance(messageText);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;

        // Try to use a more natural voice
        const voices = this.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.name.includes('Google') || 
            voice.name.includes('Microsoft') ||
            voice.name.includes('Alex')
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        utterance.onstart = () => {
            button.textContent = '⏸️';
        };

        utterance.onend = () => {
            button.textContent = '🔊';
        };

        utterance.onerror = () => {
            button.textContent = '🔊';
            this.showToast('Speech synthesis error', 'error');
        };

        this.speechSynthesis.speak(utterance);
    }

    copyText(button) {
        const messageText = button.closest('.message-content').querySelector('.message-text').textContent;
        navigator.clipboard.writeText(messageText).then(() => {
            this.showToast('Text copied to clipboard', 'success');
        }).catch(() => {
            this.showToast('Failed to copy text', 'error');
        });
    }

    toggleVoiceInput() {
        if (!this.recognition) {
            this.showToast('Voice input not supported in this browser', 'error');
            return;
        }

        if (!this.settings.voiceInput) {
            this.showToast('Voice input is disabled in settings', 'error');
            return;
        }

        if (this.isRecording) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    updateVoiceButton() {
        const voiceBtn = document.getElementById('voiceBtn');
        if (this.isRecording) {
            voiceBtn.classList.add('recording');
            voiceBtn.textContent = '⏹️';
        } else {
            voiceBtn.classList.remove('recording');
            voiceBtn.textContent = '🎤';
        }
    }

    clearChat() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = `
            <div class="message rumi">
                <div class="message-avatar">🧠</div>
                <div class="message-content">
                    <div class="message-text">Welcome, seeker of wisdom. I am Rumi, your spiritual guide. Ask me anything about life, love, wisdom, or the mysteries of existence. What would you like to explore today?</div>
                    <div class="message-actions">
                        <button class="action-btn" onclick="rumiApp.speakText(this)" title="Speak">🔊</button>
                        <button class="action-btn" onclick="rumiApp.copyText(this)" title="Copy">📋</button>
                    </div>
                </div>
            </div>
        `;
        this.currentConversationId = null;
        this.showToast('Chat cleared', 'success');
    }

    newChat() {
        this.clearChat();
        this.showToast('New conversation started', 'success');
    }

    async loadModels() {
        try {
            console.log('📦 Loading models from API...');
            const response = await fetch(`${this.API_BASE}/api/models/`);
            const data = await response.json();
            console.log(`📦 Received ${data.models.length} models from API`);

            // Store models for later use
            this.availableModels = data.models;

            // Load models for chat header selector - with retry
            if (!this.loadChatModelSelector(data.models)) {
                console.log('⏳ Retrying chatModelSelector in 100ms...');
                setTimeout(() => {
                    this.loadChatModelSelector(this.availableModels);
                }, 100);
            }

            const modelsGrid = document.getElementById('modelsGrid');
            if (modelsGrid) {
                modelsGrid.innerHTML = '';

                data.models.forEach(model => {
                const modelCard = document.createElement('div');
                modelCard.className = `model-card ${model.status === 'available' ? 'active' : ''}`;
                if (model.name === this.selectedModel) {
                    modelCard.classList.add('active');
                }

                modelCard.innerHTML = `
                    <div class="model-header">
                        <div class="model-name">${model.display_name}</div>
                        <span class="model-status ${model.status === 'available' ? 'status-available' : 'status-not-available'}">
                            ${model.status}
                        </span>
                    </div>
                    <div class="model-info">
                        <div class="info-item">
                            <div class="info-label">Size</div>
                            <div class="info-value">${model.size_gb} GB</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Provider</div>
                            <div class="info-value">${model.provider}</div>
                        </div>
                    </div>
                    <div class="model-description">${model.description}</div>
                    <div class="model-actions">
                        ${model.status === 'available' ? 
                            `<button class="btn btn-primary" onclick="rumiApp.selectModel('${model.name}')">Select</button>` :
                            `<button class="btn btn-secondary" onclick="rumiApp.downloadModel('${model.name}')">Download</button>`
                        }
                        <button class="btn btn-secondary" onclick="rumiApp.testModel('${model.name}')">Test</button>
                    </div>
                `;

                modelsGrid.appendChild(modelCard);
                });
            }
        } catch (error) {
            console.error('Error loading models:', error);
            this.showToast('Error loading models', 'error');
        }
    }

    loadChatModelSelector(models) {
        console.log('🔍 Looking for chatModelSelector element...');
        const selector = document.getElementById('chatModelSelector');
        console.log('🔍 Selector element:', selector);
        
        if (!selector) {
            console.error('❌ chatModelSelector element not found!');
            console.error('Available elements:', document.querySelectorAll('.model-selector'));
            return false;
        }

        console.log('✅ chatModelSelector found, populating models...');
        selector.innerHTML = '';
        
        // Filter to only available chat models (exclude whisper, etc.)
        const availableModels = models.filter(model => 
            model.status === 'available' && 
            !model.name.toLowerCase().includes('whisper') &&
            model.capabilities && 
            model.capabilities.includes('chat')
        );
        
        console.log(`Available chat models:`, availableModels.map(m => m.name));
        
        availableModels.forEach(model => {
            const btn = document.createElement('button');
            btn.className = 'model-btn';
            btn.dataset.model = model.name;
            btn.textContent = model.display_name || model.name;
            
            if (model.name === this.selectedModel) {
                btn.classList.add('active');
            }
            
            btn.addEventListener('click', () => {
                this.selectModel(model.name);
            });
            
            selector.appendChild(btn);
        });
        
        console.log(`✅ Loaded ${availableModels.length} chat models`);
        return true;
    }

    selectModel(modelName) {
        this.selectedModel = modelName;
        console.log(`🔄 Selected model changed to: ${modelName}`);
        document.querySelectorAll('.model-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.model === modelName) {
                btn.classList.add('active');
            }
        });
        this.showToast(`Switched to ${modelName}`, 'success');
        // Don't switch page, stay on chat
    }

    async downloadModel(modelName) {
        try {
            const response = await fetch(`${this.API_BASE}/api/models/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: modelName,
                    priority: 'normal'
                })
            });

            const data = await response.json();
            this.showToast(`Download started for ${modelName}`, 'info');
        } catch (error) {
            this.showToast('Error starting download', 'error');
        }
    }

    async testModel(modelName) {
        try {
            const response = await fetch(`${this.API_BASE}/api/models/${modelName}/test`, {
                method: 'POST'
            });

            const data = await response.json();
            this.showToast(data.message, data.test_passed ? 'success' : 'error');
        } catch (error) {
            this.showToast('Error testing model', 'error');
        }
    }

    async loadSystemInfo() {
        try {
            const response = await fetch(`${this.API_BASE}/api/system/info`);
            const data = await response.json();

            const systemGrid = document.getElementById('systemGrid');
            systemGrid.innerHTML = `
                <div class="system-card">
                    <h3>Platform</h3>
                    <div class="system-value">${data.platform}</div>
                    <div class="system-label">Operating System</div>
                </div>
                <div class="system-card">
                    <h3>Python</h3>
                    <div class="system-value">${data.python_version}</div>
                    <div class="system-label">Version</div>
                </div>
                <div class="system-card">
                    <h3>PyTorch</h3>
                    <div class="system-value">${data.torch_version}</div>
                    <div class="system-label">Version</div>
                </div>
                <div class="system-card">
                    <h3>CPU Cores</h3>
                    <div class="system-value">${data.cpu_count}</div>
                    <div class="system-label">Available</div>
                </div>
                <div class="system-card">
                    <h3>Memory</h3>
                    <div class="system-value">${data.memory_total.toFixed(1)} GB</div>
                    <div class="system-label">Total</div>
                </div>
                <div class="system-card">
                    <h3>Available</h3>
                    <div class="system-value">${data.memory_available.toFixed(1)} GB</div>
                    <div class="system-label">Memory</div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading system info:', error);
        }
    }

    async loadConversations() {
        try {
            const response = await fetch(`${this.API_BASE}/api/chat/conversations`);
            const data = await response.json();

            const conversationList = document.getElementById('conversationList');
            conversationList.innerHTML = '';

            if (data.conversations.length === 0) {
                conversationList.innerHTML = '<div class="loading">No conversations yet. Start chatting to see your history here!</div>';
                return;
            }

            data.conversations.forEach(conv => {
                const convItem = document.createElement('div');
                convItem.className = 'conversation-item';
                convItem.dataset.conversationId = conv.id;
                
                // Get first message as preview
                let preview = 'New conversation';
                if (conv.messages && conv.messages.length > 0) {
                    const firstUserMsg = conv.messages.find(m => m.role === 'user');
                    if (firstUserMsg) {
                        preview = firstUserMsg.content.substring(0, 60) + (firstUserMsg.content.length > 60 ? '...' : '');
                    }
                }
                
                convItem.innerHTML = `
                    <div class="conversation-header">
                        <div class="conversation-title">📝 ${conv.id}</div>
                        <button class="btn-delete-conv" data-conv-id="${conv.id}" title="Delete">🗑️</button>
                    </div>
                    <div class="conversation-preview">
                        ${preview}
                    </div>
                    <div class="conversation-meta">
                        ${conv.message_count} messages • ${new Date(conv.updated_at).toLocaleDateString()}
                    </div>
                `;

                convItem.addEventListener('click', (e) => {
                    if (e.target.classList.contains('btn-delete-conv')) return;
                    this.loadConversation(conv.id);
                });
                
                // Delete button
                const deleteBtn = convItem.querySelector('.btn-delete-conv');
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteConversation(conv.id);
                });

                conversationList.appendChild(convItem);
            });
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }
    
    async loadConversation(convId) {
        try {
            const response = await fetch(`${this.API_BASE}/api/chat/conversations`);
            const data = await response.json();
            
            const conversation = data.conversations.find(c => c.id === convId);
            if (!conversation) {
                this.showToast('Conversation not found', 'error');
                return;
            }
            
            // Set current conversation
            this.currentConversationId = convId;
            
            // Clear current chat
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = '';
            
            // Load messages
            conversation.messages.forEach(msg => {
                const role = msg.role;
                const content = msg.content;
                
                this.addMessageWithoutSpeaking(content, role, false);
            });
            
            // Switch to chat page
            this.switchPage('chat');
            this.showToast(`Loaded conversation ${convId}`, 'success');
            
        } catch (error) {
            console.error('Error loading conversation:', error);
            this.showToast('Error loading conversation', 'error');
        }
    }
    
    async deleteConversation(convId) {
        try {
            if (!confirm('Delete this conversation?')) return;
            
            const response = await fetch(`${this.API_BASE}/api/chat/conversations/${convId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showToast('Conversation deleted', 'success');
                this.loadConversations();
                
                // If deleted conversation was current, reset
                if (this.currentConversationId === convId) {
                    this.currentConversationId = null;
                    this.clearChat();
                }
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            this.showToast('Error deleting conversation', 'error');
        }
    }
    
    addMessageWithoutSpeaking(text, sender, isLoading = false) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.dataset.messageId = messageId;

        const avatar = sender === 'user' ? '👤' : '🧠';
        const actions = isLoading ? '' : `
            <div class="message-actions">
                <button class="action-btn" onclick="rumiApp.speakText(this)" title="Speak">🔊</button>
                <button class="action-btn" onclick="rumiApp.copyText(this)" title="Copy">📋</button>
            </div>
        `;

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${text}</div>
                ${actions}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        return messageId;
    }

    loadSettings() {
        const savedSettings = localStorage.getItem('rumiSettings');
        if (savedSettings) {
            this.settings = { ...this.settings, ...JSON.parse(savedSettings) };
        }

        // Apply UI settings
        document.getElementById('ttsToggle').classList.toggle('active', this.settings.tts);
        document.getElementById('voiceToggle').classList.toggle('active', this.settings.voiceInput);
        document.getElementById('darkModeToggle').classList.toggle('active', this.settings.darkMode);
        document.getElementById('defaultModelSelect').value = this.settings.defaultModel;
        this.selectedModel = this.settings.defaultModel;
        
        // Apply LLM behavior settings
        if (document.getElementById('historyDepth')) {
            document.getElementById('historyDepth').value = this.settings.historyDepth;
            document.getElementById('maxTokensWisdom').value = this.settings.maxTokensWisdom;
            document.getElementById('maxTokensEmpathy').value = this.settings.maxTokensEmpathy;
            document.getElementById('maxTokensCasual').value = this.settings.maxTokensCasual;
            document.getElementById('temperature').value = this.settings.temperature;
            document.getElementById('maxQuotes').value = this.settings.maxQuotes;
        }
    }
    
    async saveBehaviorSettings() {
        try {
            const settings = {
                conversation_history_depth: parseInt(document.getElementById('historyDepth').value),
                max_tokens_wisdom: parseInt(document.getElementById('maxTokensWisdom').value),
                max_tokens_empathetic: parseInt(document.getElementById('maxTokensEmpathy').value),
                max_tokens_casual: parseInt(document.getElementById('maxTokensCasual').value),
                temperature: parseFloat(document.getElementById('temperature').value),
                max_quotes_retrieved: parseInt(document.getElementById('maxQuotes').value)
            };
            
            const response = await fetch(`${this.API_BASE}/api/chat/behavior-settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            this.showToast('LLM behavior settings saved to server!', 'success');
        } catch (error) {
            this.showToast('Error saving settings: ' + error.message, 'error');
        }
    }
    
    async loadBehaviorSettings() {
        try {
            const response = await fetch(`${this.API_BASE}/api/chat/behavior-settings`);
            const data = await response.json();
            
            if (data.config) {
                const config = data.config;
                // Load basic settings
                if (document.getElementById('historyDepth')) {
                    document.getElementById('historyDepth').value = config.conversation_history_depth || 2;
                    document.getElementById('maxTokensWisdom').value = config.max_tokens_wisdom || 180;
                    document.getElementById('maxTokensEmpathy').value = config.max_tokens_empathetic || 220;
                    document.getElementById('maxTokensCasual').value = config.max_tokens_casual || 80;
                    document.getElementById('temperature').value = config.temperature || 0.8;
                    document.getElementById('maxQuotes').value = config.max_quotes_retrieved || 3;
                }
                
                // Load prompt templates editor
                if (document.getElementById('promptTemplatesEditor')) {
                    const templatesToShow = {
                        prompt_templates: config.prompt_templates,
                        quote_formatting: config.quote_formatting,
                        response_guidelines: config.response_guidelines,
                        post_processing: config.post_processing
                    };
                    document.getElementById('promptTemplatesEditor').value = 
                        JSON.stringify(templatesToShow, null, 2);
                }
            }
        } catch (error) {
            console.error('Error loading behavior settings:', error);
        }
    }
    
    async savePromptTemplates() {
        try {
            const editor = document.getElementById('promptTemplatesEditor');
            const templates = JSON.parse(editor.value);
            
            const response = await fetch(`${this.API_BASE}/api/chat/behavior-settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(templates)
            });
            
            const data = await response.json();
            this.showToast('Prompt templates saved!', 'success');
        } catch (error) {
            this.showToast('Error saving templates: ' + error.message, 'error');
        }
    }
    
    resetPromptTemplates() {
        const defaultTemplates = {
            prompt_templates: {
                casual: {
                    role: "friendly, approachable person",
                    instructions: "Respond naturally. Vary your responses. Keep it short (1-2 sentences). Be warm but not philosophical.",
                    word_limit: [20, 80]
                },
                empathetic: {
                    role: "caring, wise companion speaking to someone in distress",
                    structure_instructions: "1. First paragraph: Acknowledge their emotion with gentle understanding (2-3 sentences)\n2. HIT ENTER (line break)\n3. Second paragraph: Then naturally weave in wisdom to offer perspective",
                    word_limit: [140, 200],
                    includes_quotes: true
                },
                wisdom: {
                    role: "Rumi",
                    structure_instructions: "1. First, write a conversational, empathetic response (2-3 sentences)\n2. HIT ENTER (line break)\n3. Then integrate your teachings naturally from above",
                    word_limit: [100, 180],
                    includes_quotes: true,
                    quote_source: "rumi_knowledge_base.json"
                }
            },
            quote_formatting: {
                show_ids: true,
                show_sources: true,
                header: "YOUR TEACHINGS (use these directly):",
                max_display: 3
            },
            response_guidelines: {
                emphasize_current_question: true,
                ignore_old_questions: true,
                natural_integration: true
            },
            post_processing: {
                markers_to_remove: [
                    "Your response:",
                    "Begin your response:",
                    "Response:",
                    "You are Rumi",
                    "The seeker asks",
                    "[Your wisdom]",
                    "Your wisdom to draw upon"
                ],
                skip_patterns: [
                    "you are",
                    "rules:",
                    "seeker's",
                    "teaching:",
                    "answer as",
                    "[your wisdom]",
                    "[conversation context]",
                    "conversation so far:"
                ],
                max_word_limit: 150,
                min_word_limit: 30,
                trim_to_sentence: true
            }
        };
        
        document.getElementById('promptTemplatesEditor').value = 
            JSON.stringify(defaultTemplates, null, 2);
        this.showToast('Templates reset to default', 'info');
    }

    saveSettings() {
        localStorage.setItem('rumiSettings', JSON.stringify(this.settings));
    }

    toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
    }

    async loadLLMBehaviorSettings() {
        try {
            const response = await fetch(`${this.API_BASE}/api/chat/behavior-settings`);
            const data = await response.json();
            
            if (data.config) {
                const config = data.config;
                // Load into LLM settings page fields
                if (document.getElementById('llm-historyDepth')) {
                    document.getElementById('llm-historyDepth').value = config.conversation_history_depth || 2;
                    document.getElementById('llm-maxTokensWisdom').value = config.max_tokens_wisdom || 300;
                    document.getElementById('llm-maxTokensEmpathy').value = config.max_tokens_empathetic || 280;
                    document.getElementById('llm-maxTokensCasual').value = config.max_tokens_casual || 220;
                    document.getElementById('llm-temperature').value = config.temperature || 0.8;
                    document.getElementById('llm-maxQuotes').value = config.max_quotes_retrieved || 3;
                }
                
                // Load prompt templates editor
                if (document.getElementById('llm-promptTemplatesEditor')) {
                    const templatesToShow = {
                        prompt_templates: config.prompt_templates,
                        quote_formatting: config.quote_formatting,
                        response_guidelines: config.response_guidelines,
                        post_processing: config.post_processing
                    };
                    document.getElementById('llm-promptTemplatesEditor').value = 
                        JSON.stringify(templatesToShow, null, 2);
                }
            }
        } catch (error) {
            console.error('Error loading LLM behavior settings:', error);
        }
    }
    
    async saveLLMBehaviorSettings() {
        try {
            const settings = {
                conversation_history_depth: parseInt(document.getElementById('llm-historyDepth').value),
                max_tokens_wisdom: parseInt(document.getElementById('llm-maxTokensWisdom').value),
                max_tokens_empathetic: parseInt(document.getElementById('llm-maxTokensEmpathy').value),
                max_tokens_casual: parseInt(document.getElementById('llm-maxTokensCasual').value),
                temperature: parseFloat(document.getElementById('llm-temperature').value),
                max_quotes_retrieved: parseInt(document.getElementById('llm-maxQuotes').value)
            };
            
            const response = await fetch(`${this.API_BASE}/api/chat/behavior-settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            this.showToast('LLM behavior settings saved!', 'success');
        } catch (error) {
            this.showToast('Error saving settings: ' + error.message, 'error');
        }
    }
    
    async saveLLMPromptTemplates() {
        try {
            const editor = document.getElementById('llm-promptTemplatesEditor');
            const templates = JSON.parse(editor.value);
            
            const response = await fetch(`${this.API_BASE}/api/chat/behavior-settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(templates)
            });
            
            const data = await response.json();
            this.showToast('Prompt templates saved!', 'success');
        } catch (error) {
            this.showToast('Error saving templates: ' + error.message, 'error');
        }
    }
    
    resetLLMPromptTemplates() {
        const defaultTemplates = {
            prompt_templates: {
                casual: {
                    role: "friendly, approachable person",
                    instructions: "Respond naturally. Vary your responses. Be warm, engaging, and conversational (5-6 sentences).",
                    word_limit: [60, 180],
                    prompt_template: "You are {role}, engaged in a warm, natural conversation.\n{history}\n\nUser just said: \"{query}\"\n\nRESPOND NOW with 4-6 complete sentences:\n- Acknowledge what they said warmly\n- Share something about yourself or your perspective\n- Ask them a thoughtful follow-up question\n- Show genuine interest in their response\n- Make it natural, engaging, and conversational\n\nTarget: 80-180 words. Be authentic and engaging."
                },
                empathetic: {
                    role: "caring, wise companion speaking to someone in distress",
                    structure_instructions: "1. First paragraph: Acknowledge their emotion with gentle understanding (2-3 sentences)\n2. HIT ENTER (line break)\n3. Second paragraph: Then naturally weave in wisdom to offer perspective",
                    word_limit: [140, 200],
                    includes_quotes: true,
                    prompt_template: "You are {role}.\n{history}\nCURRENT message you need to respond to:\n{wisdom_instruction}"
                },
                wisdom: {
                    role: "Rumi",
                    structure_instructions: "1. First, write a conversational, empathetic response (2-3 sentences)\n2. HIT ENTER (line break)\n3. Then integrate your teachings naturally from above",
                    word_limit: [150, 280],
                    includes_quotes: true,
                    quote_source: "rumi_knowledge_base.json",
                    prompt_template: "You are Rumi. Someone asks: \"{query}\"\n\nYour teachings to guide you:\n{quotes_text}\n\nRespond as Rumi would. First engage with them conversationally (2-3 sentences), then naturally weave in your teachings from above. Make it complete and rich (150-250 words)."
                }
            },
            quote_formatting: {
                show_ids: true,
                show_sources: true,
                header: "YOUR TEACHINGS (use these directly):",
                max_display: 3
            },
            response_guidelines: {
                emphasize_current_question: true,
                ignore_old_questions: true,
                natural_integration: true
            },
            post_processing: {
                markers_to_remove: [
                    "Your response:",
                    "Begin your response:",
                    "Response:",
                    "You are Rumi",
                    "The seeker asks",
                    "[Your wisdom]",
                    "Your wisdom to draw upon"
                ],
                skip_patterns: [
                    "you are",
                    "rules:",
                    "seeker's",
                    "teaching:",
                    "answer as",
                    "[your wisdom]",
                    "[conversation context]",
                    "conversation so far:"
                ],
                max_word_limit: 150,
                min_word_limit: 30,
                trim_to_sentence: true
            }
        };
        
        document.getElementById('llm-promptTemplatesEditor').value = 
            JSON.stringify(defaultTemplates, null, 2);
        this.showToast('Templates reset to default', 'info');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    async loadEmotionKeywords() {
        try {
            const response = await fetch(`${this.API_BASE}/api/chat/emotion-keywords`);
            const data = await response.json();
            
            if (data.config) {
                this.currentEmotionConfig = data.config;
                this.renderTagEditor(data.config);
            }
        } catch (error) {
            console.error('Error loading emotion keywords:', error);
            this.showToast('Error loading emotion keywords', 'error');
        }
    }
    
    renderTagEditor(config) {
        // Render emotion keywords
        const emotionContainer = document.getElementById('emotionTagsContainer');
        if (emotionContainer) {
            emotionContainer.innerHTML = '<h4 style="margin-bottom: 1rem;">Emotion Keywords</h4>';
            
            for (const [emotion, keywords] of Object.entries(config.emotion_keywords || {})) {
                const card = document.createElement('div');
                card.style.cssText = 'background: var(--card-bg); padding: 1rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid var(--border-color);';
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="text-transform: capitalize;">${emotion}</strong>
                        <button class="tag-remove-btn" onclick="rumiApp.removeEmotionTag('${emotion}')" style="color: #ff4757; background: none; border: none; cursor: pointer; font-size: 1.2rem;">×</button>
                    </div>
                    <div class="tag-list" data-emotion="${emotion}">
                        ${keywords.map(k => `<span class="tag" data-keyword="${k}" data-emotion="${emotion}">${k} <button onclick="rumiApp.removeKeyword('${k}', '${emotion}')" style="margin-left: 0.5rem; background: rgba(255,71,87,0.2); border: none; border-radius: 4px; padding: 0.15rem 0.5rem; cursor: pointer; color: #ff4757;">×</button></span>`).join('')}
                    </div>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <input type="text" id="new-${emotion}" placeholder="Add keyword..." style="flex: 1; padding: 0.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <button onclick="rumiApp.addKeyword('${emotion}', 'new-${emotion}')" style="padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 8px; cursor: pointer;">Add</button>
                    </div>
                `;
                emotionContainer.appendChild(card);
            }
            
            // Add new emotion section
            const addSection = document.createElement('div');
            addSection.style.cssText = 'background: var(--card-bg); padding: 1rem; margin-top: 1rem; border-radius: 8px; border: 1px dashed var(--border-color);';
            addSection.innerHTML = `
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" id="new-emotion-name" placeholder="New emotion..." style="flex: 1; padding: 0.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                    <button onclick="rumiApp.addEmotionCategory()" style="padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 8px; cursor: pointer;">Add Emotion</button>
                </div>
            `;
            emotionContainer.appendChild(addSection);
        }
        
        // Render theme keywords
        const themeContainer = document.getElementById('themeTagsContainer');
        if (themeContainer) {
            themeContainer.innerHTML = '<h4 style="margin-bottom: 1rem;">Theme Keywords</h4>';
            
            for (const [theme, keywords] of Object.entries(config.theme_keywords || {})) {
                const card = document.createElement('div');
                card.style.cssText = 'background: var(--card-bg); padding: 1rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid var(--border-color);';
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="text-transform: capitalize;">${theme}</strong>
                        <button class="tag-remove-btn" onclick="rumiApp.removeThemeTag('${theme}')" style="color: #ff4757; background: none; border: none; cursor: pointer; font-size: 1.2rem;">×</button>
                    </div>
                    <div class="tag-list" data-theme="${theme}">
                        ${keywords.map(k => `<span class="tag" data-keyword="${k}" data-theme="${theme}">${k} <button onclick="rumiApp.removeKeyword('${k}', '${theme}')" style="margin-left: 0.5rem; background: rgba(255,71,87,0.2); border: none; border-radius: 4px; padding: 0.15rem 0.5rem; cursor: pointer; color: #ff4757;">×</button></span>`).join('')}
                    </div>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <input type="text" id="theme-${theme}" placeholder="Add keyword..." style="flex: 1; padding: 0.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                        <button onclick="rumiApp.addThemeKeyword('${theme}', 'theme-${theme}')" style="padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 8px; cursor: pointer;">Add</button>
                    </div>
                `;
                themeContainer.appendChild(card);
            }
        }
        
        // Render empathy triggers
        const empathyContainer = document.getElementById('empathyTriggersContainer');
        if (empathyContainer) {
            empathyContainer.innerHTML = '<h4 style="margin-bottom: 1rem;">Empathy Triggers</h4>';
            
            const patternsDiv = document.createElement('div');
            patternsDiv.style.cssText = 'background: var(--card-bg); padding: 1rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid var(--border-color);';
            patternsDiv.innerHTML = `
                <strong style="display: block; margin-bottom: 0.5rem;">Distress Patterns</strong>
                <textarea id="distress-patterns" style="width: 100%; min-height: 100px; padding: 0.5rem; border-radius: 8px; border: 1px solid var(--border-color);" placeholder="Enter patterns, one per line">${(config.empathy_triggers?.distress_patterns || []).join('\n')}</textarea>
            `;
            empathyContainer.appendChild(patternsDiv);
            
            const emoticonsDiv = document.createElement('div');
            emoticonsDiv.style.cssText = 'background: var(--card-bg); padding: 1rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid var(--border-color);';
            emoticonsDiv.innerHTML = `
                <strong style="display: block; margin-bottom: 0.5rem;">Emoticons</strong>
                <textarea id="emoticons" style="width: 100%; min-height: 80px; padding: 0.5rem; border-radius: 8px; border: 1px solid var(--border-color);" placeholder="Enter emoticons, one per line">${(config.empathy_triggers?.emoticons || []).join('\n')}</textarea>
            `;
            empathyContainer.appendChild(emoticonsDiv);
        }
    }
    
    addKeyword(emotion, inputId) {
        const input = document.getElementById(inputId);
        const keyword = input.value.trim();
        if (!keyword) return;
        
        const tagList = document.querySelector(`[data-emotion="${emotion}"]`);
        if (tagList && !tagList.querySelector(`[data-keyword="${keyword}"]`)) {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.dataset.keyword = keyword;
            tag.dataset.emotion = emotion;
            tag.innerHTML = `${keyword} <button onclick="rumiApp.removeKeyword('${keyword}', '${emotion}')" style="margin-left: 0.5rem; background: rgba(255,71,87,0.2); border: none; border-radius: 4px; padding: 0.15rem 0.5rem; cursor: pointer; color: #ff4757;">×</button>`;
            tagList.appendChild(tag);
            input.value = '';
        }
    }
    
    addThemeKeyword(theme, inputId) {
        const input = document.getElementById(inputId);
        const keyword = input.value.trim();
        if (!keyword) return;
        
        const tagList = document.querySelector(`[data-theme="${theme}"]`);
        if (tagList && !tagList.querySelector(`[data-keyword="${keyword}"]`)) {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.dataset.keyword = keyword;
            tag.dataset.theme = theme;
            tag.innerHTML = `${keyword} <button onclick="rumiApp.removeKeyword('${keyword}', '${theme}')" style="margin-left: 0.5rem; background: rgba(255,71,87,0.2); border: none; border-radius: 4px; padding: 0.15rem 0.5rem; cursor: pointer; color: #ff4757;">×</button>`;
            tagList.appendChild(tag);
            input.value = '';
        }
    }
    
    removeKeyword(keyword, category) {
        document.querySelectorAll(`[data-keyword="${keyword}"]`).forEach(el => el.remove());
    }
    
    addEmotionCategory() {
        const input = document.getElementById('new-emotion-name');
        const emotionName = input.value.trim().toLowerCase();
        if (!emotionName) return;
        
        this.renderTagEditor({
            emotion_keywords: {
                ...this.currentEmotionConfig?.emotion_keywords,
                [emotionName]: []
            },
            theme_keywords: this.currentEmotionConfig?.theme_keywords,
            empathy_triggers: this.currentEmotionConfig?.empathy_triggers
        });
        input.value = '';
    }
    
    removeEmotionTag(emotion) {
        const tagSection = document.querySelector(`[data-emotion="${emotion}"]`)?.parentElement;
        if (tagSection) {
            tagSection.remove();
        }
    }
    
    removeThemeTag(theme) {
        const tagSection = document.querySelector(`[data-theme="${theme}"]`)?.parentElement;
        if (tagSection) {
            tagSection.remove();
        }
    }
    
    async saveEmotionKeywords() {
        try {
            const config = {
                emotion_keywords: {},
                theme_keywords: {},
                empathy_triggers: {
                    distress_patterns: [],
                    emoticons: []
                }
            };
            
            // Extract emotion keywords
            document.querySelectorAll('[data-emotion]').forEach(list => {
                const emotion = list.dataset.emotion;
                const keywords = Array.from(list.querySelectorAll('.tag')).map(t => t.dataset.keyword);
                config.emotion_keywords[emotion] = keywords;
            });
            
            // Extract theme keywords
            document.querySelectorAll('[data-theme]').forEach(list => {
                const theme = list.dataset.theme;
                const keywords = Array.from(list.querySelectorAll('.tag')).map(t => t.dataset.keyword);
                config.theme_keywords[theme] = keywords;
            });
            
            // Extract empathy triggers
            const distressEl = document.getElementById('distress-patterns');
            const emoticonsEl = document.getElementById('emoticons');
            
            if (distressEl) {
                const distressText = distressEl.value;
                config.empathy_triggers.distress_patterns = distressText.split('\n').map(l => l.trim()).filter(l => l);
            }
            
            if (emoticonsEl) {
                const emoticonsText = emoticonsEl.value;
                config.empathy_triggers.emoticons = emoticonsText.split('\n').map(l => l.trim()).filter(l => l);
            }
            
            const response = await fetch(`${this.API_BASE}/api/chat/emotion-keywords`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                this.showToast('Emotion keywords saved!', 'success');
                await this.loadEmotionKeywords();
            } else {
                this.showToast('Error saving emotion keywords', 'error');
            }
        } catch (error) {
            console.error('Error saving emotion keywords:', error);
            this.showToast('Error saving emotion keywords', 'error');
        }
    }
}

// Initialize the app
let rumiApp;
document.addEventListener('DOMContentLoaded', function() {
    rumiApp = new RumiApp();
    rumiApp.init();
});
