/**
 * WebSocket Manager for Real-Time Communication
 * Handles connection, reconnection, and message handling
 */

class WebSocketManager {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.ws = null;
        this.userId = this.generateUserId();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = new Map();
        this.isConnected = false;
        this.connectionId = null;
    }

    generateUserId() {
        let userId = localStorage.getItem('chat_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chat_user_id', userId);
        }
        return userId;
    }

    connect() {
    // FIXED: correct websocket path
    const wsUrl = `${this.baseUrl.replace('http', 'ws')}/ws/chat/${this.userId}`;
    
    console.log(`🔌 Attempting to connect to: ${wsUrl}`);
    
    try {
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ WebSocket connection opened');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.emit('connected', { userId: this.userId });
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📩 Received:', data);

                this.emit(data.type, data);
            } catch (error) {
                console.error('❌ Error parsing message:', error);
            }
        };

        this.ws.onclose = (event) => {
            console.log(`🔌 WebSocket disconnected. Code: ${event.code}`);
            this.isConnected = false;
            this.emit('disconnected', {});

            if (event.code !== 1000) {
                this.attemptReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error observed:', error);
            this.emit('error', { error: 'Connection error' });
        };

    } catch (error) {
        console.error('❌ Failed to create WebSocket:', error);
        this.emit('error', { error: error.message });
    }
}

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
            this.emit('maxReconnectAttempts', {});
        }
    }

    send(type, data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('❌ WebSocket is not connected. Current State:', this.ws?.readyState);
            this.emit('error', { error: 'Not connected' });
            return false;
        }

        const message = {
            type,
            ...data,
            timestamp: new Date().toISOString()
        };

        try {
            this.ws.send(JSON.stringify(message));
            console.log('📤 Sent:', message);
            return true;
        } catch (error) {
            console.error('❌ Error sending message:', error);
            this.emit('error', { error: error.message });
            return false;
        }
    }

    sendMessage(content, chatId, personality = 'helpful') {
        if (!chatId) {
            console.error('❌ Cannot send message: No active Chat ID');
            return false;
        }
        return this.send('message', {
            content,
            chat_id: chatId,
            personality
        });
    }

    sendTyping(chatId, isTyping) {
        return this.send('typing', {
            chat_id: chatId,
            is_typing: isTyping,
            user_id: this.userId
        });
    }

    createChat(title = 'New Chat') {
        return this.send('chat:new', {
            title,
            user_id: this.userId
        });
    }

    getChatList() {
        return this.send('chat:list', {
            user_id: this.userId
        });
    }

    loadMessages(chatId, limit = 50) {
        return this.send('chat:load', {
            chat_id: chatId,
            limit,
            user_id: this.userId
        });
    }

    on(eventType, handler) {
        if (!this.messageHandlers.has(eventType)) {
            this.messageHandlers.set(eventType, []);
        }
        this.messageHandlers.get(eventType).push(handler);
        
        return () => {
            const handlers = this.messageHandlers.get(eventType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        };
    }

    emit(eventType, data) {
        const handlers = this.messageHandlers.get(eventType);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`❌ Error in handler for ${eventType}:`, error);
                }
            });
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close(1000, "User logout/disconnect");
            this.ws = null;
        }
        this.isConnected = false;
    }

    getStatus() {
        return {
            connected: this.isConnected,
            userId: this.userId,
            connectionId: this.connectionId,
            readyState: this.ws ? this.ws.readyState : -1
        };
    }
}

window.WebSocketManager = WebSocketManager;