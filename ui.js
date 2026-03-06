/**
 * UI Manager - Handles user interface interactions
 */

class UIManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.theme = localStorage.getItem('theme') || 'light';
        this.applyTheme();
        this.setupEventListeners();
        // Delay setting loading to ensure ChatManager instance exists
        setTimeout(() => this.loadSettings(), 100);
    }

    setupEventListeners() {
        document.getElementById('toggleSidebar').addEventListener('click', () => this.toggleSidebar());
        document.getElementById('closeSidebar').addEventListener('click', () => this.closeSidebar());
        
        document.getElementById('newChatBtn').addEventListener('click', () => {
            if (window.chatManager) window.chatManager.createNewChat();
            if (window.innerWidth <= 640) this.closeSidebar();
        });
        
        document.getElementById('refreshChats').addEventListener('click', () => {
            if (window.chatManager) window.chatManager.loadChatList();
            if (window.showToast) showToast('Chat list refreshed', 'info');
        });
        
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        document.getElementById('personalityBtn').addEventListener('click', () => this.openModal('personalityModal'));
        document.getElementById('closePersonalityModal').addEventListener('click', () => this.closeModal('personalityModal'));
        document.getElementById('settingsBtn').addEventListener('click', () => this.openModal('settingsModal'));
        document.getElementById('closeSettingsModal').addEventListener('click', () => this.closeModal('settingsModal'));
        document.getElementById('moreOptions').addEventListener('click', (e) => this.showOptionsMenu(e));
        
        document.querySelectorAll('.personality-card').forEach(card => {
            card.addEventListener('click', () => {
                const personality = card.dataset.personality;
                if (window.chatManager) window.chatManager.setPersonality(personality);
                this.closeModal('personalityModal');
            });
        });
        
        document.getElementById('themeSelect').addEventListener('change', (e) => {
            this.theme = e.target.value;
            localStorage.setItem('theme', this.theme);
            this.applyTheme();
        });
        
        document.getElementById('fontSizeSelect').addEventListener('change', (e) => {
            const size = e.target.value;
            document.documentElement.style.fontSize = size === 'small' ? '14px' : size === 'large' ? '18px' : '16px';
            localStorage.setItem('font_size', size);
        });

        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all chat history?')) {
                if (window.chatManager) window.chatManager.clearChatHistory();
                this.closeModal('settingsModal');
            }
        });
        
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('input', () => {
            if (window.updateCharCount) window.updateCharCount();
            this.autoResize(messageInput);
            this.handleTyping();
        });
        
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());

        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => { if (e.target === modal) this.closeModal(modal.id); });
        });
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('active');
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
            overlay.addEventListener('click', () => this.closeSidebar());
        }
        overlay.classList.toggle('active', this.sidebar.classList.contains('active'));
    }

    closeSidebar() {
        this.sidebar.classList.remove('active');
        document.querySelector('.sidebar-overlay')?.classList.remove('active');
    }

    toggleTheme() {
        const themes = ['light', 'dark'];
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.applyTheme();
        const icon = document.querySelector('#themeToggle i');
        if (icon) icon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const select = document.getElementById('themeSelect');
        if (select) select.value = this.theme;
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
        document.body.style.overflow = '';
    }

    showOptionsMenu() { this.openModal('settingsModal'); }

    sendMessage() {
        const input = document.getElementById('messageInput');
        const content = input.value.trim();
        if (content && window.chatManager) window.chatManager.sendMessage(content);
    }

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }

    handleTyping() {
        if (window.chatManager?.wsManager && window.chatManager.currentChatId) {
            clearTimeout(window.chatManager.typingTimeout);
            if (!window.chatManager.isTyping) {
                window.chatManager.isTyping = true;
                window.chatManager.wsManager.sendTyping(window.chatManager.currentChatId, true);
            }
            window.chatManager.typingTimeout = setTimeout(() => {
                window.chatManager.isTyping = false;
                window.chatManager.wsManager.sendTyping(window.chatManager.currentChatId, false);
            }, 2000);
        }
    }

    loadSettings() {
        const fontSize = localStorage.getItem('font_size') || 'medium';
        document.getElementById('fontSizeSelect').value = fontSize;
        document.documentElement.style.fontSize = fontSize === 'small' ? '14px' : fontSize === 'large' ? '18px' : '16px';
        
        const personality = localStorage.getItem('ai_personality') || 'helpful';
        if (window.chatManager) window.chatManager.currentPersonality = personality;
    }
}

window.UIManager = UIManager;