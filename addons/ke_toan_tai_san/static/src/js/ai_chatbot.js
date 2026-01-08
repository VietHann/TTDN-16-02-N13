/* AI Chatbot JavaScript với Markdown Support */
odoo.define('ke_toan_tai_san.AIChatbot', function (require) {
    'use strict';

    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.view_registry');

    var AIChatbotController = FormController.extend({
        events: _.extend({}, FormController.prototype.events, {
            'click #send-button': '_onSendMessage',
            'keydown #chat-input': '_onKeyPress',
            'input #chat-input': '_onInputChange',
            'click #clear-button': '_onClearHistory',
        }),

        start: function () {
            this._super.apply(this, arguments);
            // Tạo conversation ID mới mỗi lần mở chat
            this.conversationId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            this.isTyping = false;
            // Tắt load chat history cũ - user muốn chat mới mỗi lần
            // this._loadChatHistory();
            this._setupChatInterface();
            this._loadMarkedLibrary();
        },

        _loadMarkedLibrary: function () {
            var self = this;
            // Load marked.js library for markdown rendering
            if (!window.marked) {
                // Try to load from CDN
                var script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/marked@4.3.0/lib/marked.umd.js';
                script.onload = function() {
                    console.log('Marked.js loaded successfully');
                    self.markedLoaded = true;
                };
                script.onerror = function() {
                    console.warn('Failed to load marked.js, falling back to basic formatting');
                    self.markedLoaded = false;
                };
                document.head.appendChild(script);
            } else {
                self.markedLoaded = true;
            }
        },

        _setupChatInterface: function () {
            var self = this;

            // Setup auto-resize for textarea (sẽ được gọi sau khi DOM ready)
            setTimeout(function() {
                var chatInput = self.$('#chat-input');
                if (chatInput.length > 0) {
                    // Focus on input
                    chatInput.focus();

                    // Setup auto-resize for textarea
                    chatInput.on('input', function() {
                        self._autoResizeTextarea(this);
                    });

                    // Setup initial textarea size
                    self._autoResizeTextarea(chatInput[0]);
                }
            }, 100);
        },

        _loadChatHistory: function () {
            var self = this;

            this._rpc({
                route: '/api/ai/history',
                params: {
                    conversation_id: this.conversationId,
                    limit: 20
                }
            }).then(function (result) {
                if (result.success && result.data.history) {
                    // Clear existing messages
                    self.$('#chat-messages').empty();

                    // Add messages in chronological order
                    result.data.history.forEach(function (msg) {
                        self._addMessage({
                            type: msg.type,
                            content: msg.message,
                            timestamp: msg.timestamp
                        });
                    });

                    // Scroll to bottom
                    self._scrollToBottom();
                }
            }).catch(function (error) {
                console.error('Error loading chat history:', error);
            });
        },

        _onSendMessage: function () {
            var message = this.$('#chat-input').val().trim();
            var sendButton = this.$('#send-button');

            if (!message || this.isTyping) {
                return;
            }

            // Disable send button
            if (sendButton.length > 0) {
                sendButton.prop('disabled', true);
            }

            // Add user message to UI
            this._addMessage({
                type: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });

            // Clear input
            var chatInput = this.$('#chat-input');
            chatInput.val('');
            if (chatInput.length > 0) {
                this._autoResizeTextarea(chatInput[0]);
            }

            // Show typing indicator
            this._showTypingIndicator();

            // Send to AI
            this._sendToAI(message);
        },

        _onKeyPress: function (event) {
            if (event.key === 'Enter' && !event.shiftKey) { // Enter key without Shift
                event.preventDefault();
                this._onSendMessage();
            }
        },

        _sendToAI: function (message) {
            var self = this;

            this._rpc({
                route: '/api/ai/chat',
                params: {
                    message: message,
                    conversation_id: this.conversationId
                }
            }).then(function (result) {
                // Hide typing indicator
                self._hideTypingIndicator();

                // Re-enable send button
                var sendButton = self.$('#send-button');
                if (sendButton.length > 0) {
                    sendButton.prop('disabled', false);
                }

                if (result.success) {
                    // Add AI response
                    self._addMessage({
                        type: 'assistant',
                        content: result.data.response,
                        timestamp: result.data.timestamp
                    });
                } else {
                    // Show error
                    self._addMessage({
                        type: 'error',
                        content: 'Xin lỗi, có lỗi xảy ra: ' + (result.message || 'Unknown error'),
                        timestamp: new Date().toISOString()
                    });
                }
            }).catch(function (error) {
                self._hideTypingIndicator();
                var sendButton = self.$('#send-button');
                if (sendButton.length > 0) {
                    sendButton.prop('disabled', false);
                }
                console.error('Error sending message to AI:', error);
                self._addMessage({
                    type: 'error',
                    content: 'Không thể kết nối đến AI. Vui lòng thử lại sau.',
                    timestamp: new Date().toISOString()
                });
            });
        },

        _onClearHistory: function () {
            var self = this;

            if (!confirm('Bạn có chắc muốn xóa toàn bộ lịch sử trò chuyện?')) {
                return;
            }

            this._rpc({
                route: '/api/ai/clear',
                params: {
                    conversation_id: this.conversationId
                }
            }).then(function (result) {
                if (result.success) {
                    // Clear UI
                    self.$('#chat-messages').empty();
                    self._addMessage({
                        type: 'assistant',
                        content: 'Lịch sử trò chuyện đã được xóa. Chúng ta bắt đầu lại nhé!',
                        timestamp: new Date().toISOString()
                    });
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Lỗi',
                        message: result.message || 'Không thể xóa lịch sử'
                    });
                }
            }).catch(function (error) {
                console.error('Error clearing history:', error);
                self.displayNotification({
                    type: 'danger',
                    title: 'Lỗi',
                    message: 'Không thể xóa lịch sử'
                });
            });
        },

        _addMessage: function (messageData) {
            var messageItemClass = messageData.type === 'user' ? 'user-message' : 'message-item';
            var avatarIcon = messageData.type === 'user' ? 'fa-user' : 'fa-robot';
            var avatarClass = messageData.type === 'user' ? 'user-avatar' : 'ai-avatar';
            var bubbleClass = messageData.type === 'error' ? 'error-message' : '';

            var messageHtml = `
                <div class="message-item ${messageItemClass} ${bubbleClass}">
                    <div class="${avatarClass}">
                        <i class="fa ${avatarIcon}"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-bubble ${messageData.type === 'user' ? 'user-message' : 'ai-message'}">
                            <div class="message-markdown">
                                ${this._formatMessage(messageData.content)}
                            </div>
                        </div>
                        <div class="message-time">${this._formatTimestamp(messageData.timestamp)}</div>
                    </div>
                </div>
            `;

            this.$('#chat-messages').append(messageHtml);
            this._scrollToBottom();
        },

        _showTypingIndicator: function () {
            this.isTyping = true;
            this.$('#typing-indicator').show();
            this._scrollToBottom();
        },

        _hideTypingIndicator: function () {
            this.isTyping = false;
            this.$('#typing-indicator').hide();
        },

        _autoResizeTextarea: function (textarea) {
            if (!textarea || !textarea.style) {
                return;
            }
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        },

        _onInputChange: function () {
            var chatInput = this.$('#chat-input');
            if (chatInput.length > 0) {
                this._autoResizeTextarea(chatInput[0]);
            }
        },

        _formatMessage: function (content) {
            if (!content) return '';

            // If marked.js is loaded, use it for markdown rendering
            if (this.markedLoaded && window.marked) {
                try {
                    // Configure marked options
                    marked.setOptions({
                        breaks: true,
                        gfm: true,
                        headerIds: false,
                        mangle: false,
                    });

                    // Render markdown
                    var rendered = marked.parse(content);

                    // Add syntax highlighting class to code blocks
                    rendered = rendered.replace(/<pre><code/g, '<pre class="language-text"><code');

                    return rendered;
                } catch (e) {
                    console.warn('Markdown rendering failed, falling back to basic formatting:', e);
                }
            }

            // Fallback: Basic text formatting
            return this._basicTextFormatting(content);
        },

        _basicTextFormatting: function (content) {
            if (!content) return '';

            // Convert line breaks to <br>
            var formatted = content.replace(/\n/g, '<br>');

            // Basic markdown-like formatting
            formatted = formatted
                // Headers
                .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                .replace(/^# (.*$)/gm, '<h1>$1</h1>')

                // Bold
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/__(.*?)__/g, '<strong>$1</strong>')

                // Italic
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/_(.*?)_/g, '<em>$1</em>')

                // Strikethrough
                .replace(/~~(.*?)~~/g, '<del>$1</del>')

                // Lists
                .replace(/^\* (.*$)/gm, '<li>$1</li>')
                .replace(/^- (.*$)/gm, '<li>$1</li>')
                .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')

                // Links
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')

                // Inline code
                .replace(/`([^`]+)`/g, '<code>$1</code>')

                // Blockquotes
                .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')

                // Horizontal rules
                .replace(/^---$/gm, '<hr>');

            // Wrap consecutive list items
            formatted = formatted.replace(/(<li>.*<\/li>\s*)+/g, function(match) {
                return '<ul>' + match + '</ul>';
            });

            return formatted;
        },

        _formatTimestamp: function (timestamp) {
            var date = new Date(timestamp);
            return date.toLocaleTimeString('vi-VN', {
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        _scrollToBottom: function () {
            var chatMessages = this.$('#chat-messages');
            if (chatMessages.length > 0) {
                var container = chatMessages[0];
                container.scrollTop = container.scrollHeight;
            }
        },
    });

    var AIChatbotView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: AIChatbotController,
        }),
    });

    viewRegistry.add('ai_chatbot_form', AIChatbotView);

    return {
        AIChatbotController: AIChatbotController,
        AIChatbotView: AIChatbotView,
    };
});