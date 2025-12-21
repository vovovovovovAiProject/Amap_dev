/**
 * 对话管理模块
 */

class ChatManager {
    constructor() {
        this.messages = [];  // 对话历史
        this.currentTrip = null;
        this.isProcessing = false;
        this.conversationId = this.generateConversationId();
        this.collectedInfo = {};  // 收集到的信息
        this.conversations = [];  // 所有对话列表

        this.messagesContainer = document.getElementById('chatMessages');
        this.inputElement = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendBtn');
        this.quickSuggestions = document.getElementById('quickSuggestions');
        this.newChatButton = document.getElementById('newChatBtn');
        this.toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
        this.expandSidebarBtn = document.getElementById('expandSidebarBtn');
        this.chatSidebar = document.getElementById('chatSidebar');
        this.conversationList = document.getElementById('conversationList');

        this.init();
    }

    init() {
        // 绑定发送按钮
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // 绑定回车发送
        this.inputElement.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 自动调整输入框高度
        this.inputElement.addEventListener('input', () => {
            this.inputElement.style.height = 'auto';
            this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 120) + 'px';
        });

        // 绑定快捷建议
        this.quickSuggestions.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const text = chip.dataset.text;
                this.inputElement.value = text;
                this.sendMessage();
            });
        });

        // 绑定新建对话按钮
        if (this.newChatButton) {
            this.newChatButton.addEventListener('click', () => this.startNewChat());
        }

        // 绑定侧边栏切换按钮
        if (this.toggleSidebarBtn) {
            this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        }

        if (this.expandSidebarBtn) {
            this.expandSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // 加载对话历史
        this.loadConversations();
        this.renderConversationList();
    }

    toggleSidebar() {
        if (this.chatSidebar) {
            this.chatSidebar.classList.toggle('collapsed');
            if (this.expandSidebarBtn) {
                this.expandSidebarBtn.classList.toggle('hidden', !this.chatSidebar.classList.contains('collapsed'));
            }
        }
    }

    loadConversations() {
        try {
            const saved = localStorage.getItem('chat_conversations');
            if (saved) {
                this.conversations = JSON.parse(saved);
            }
        } catch (e) {
            console.error('Failed to load conversations:', e);
            this.conversations = [];
        }
    }

    saveConversations() {
        try {
            // 只保留最近20个对话
            const toSave = this.conversations.slice(0, 20);
            localStorage.setItem('chat_conversations', JSON.stringify(toSave));
        } catch (e) {
            console.error('Failed to save conversations:', e);
        }
    }

    saveCurrentConversation() {
        if (this.messages.length === 0) return;

        // 获取对话标题（第一条用户消息的前20个字符）
        const firstUserMsg = this.messages.find(m => m.role === 'user');
        const title = firstUserMsg ? firstUserMsg.content.slice(0, 25) + (firstUserMsg.content.length > 25 ? '...' : '') : '新对话';

        // 查找是否已存在
        const existingIndex = this.conversations.findIndex(c => c.id === this.conversationId);

        const convData = {
            id: this.conversationId,
            title: title,
            messages: this.messages,
            collectedInfo: this.collectedInfo,
            currentTrip: this.currentTrip,
            updatedAt: Date.now()
        };

        if (existingIndex >= 0) {
            this.conversations[existingIndex] = convData;
        } else {
            this.conversations.unshift(convData);
        }

        this.saveConversations();
        this.renderConversationList();
    }

    renderConversationList() {
        if (!this.conversationList) return;

        if (this.conversations.length === 0) {
            this.conversationList.innerHTML = `
                <div class="conversation-empty">
                    <p>暂无对话历史</p>
                    <p>开始新对话吧！</p>
                </div>
            `;
            return;
        }

        this.conversationList.innerHTML = this.conversations.map(conv => `
            <div class="conversation-item ${conv.id === this.conversationId ? 'active' : ''}" data-id="${conv.id}">
                <span class="conv-icon">💬</span>
                <span class="conv-title">${this.escapeHtml(conv.title)}</span>
                <button class="conv-delete" data-id="${conv.id}" title="删除对话">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                </button>
            </div>
        `).join('');

        // 绑定点击事件
        this.conversationList.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.conv-delete')) {
                    this.loadConversation(item.dataset.id);
                }
            });
        });

        // 绑定删除按钮
        this.conversationList.querySelectorAll('.conv-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteConversation(btn.dataset.id);
            });
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    loadConversation(convId) {
        const conv = this.conversations.find(c => c.id === convId);
        if (!conv) return;

        // 保存当前对话
        this.saveCurrentConversation();

        // 加载选中的对话
        this.conversationId = conv.id;
        this.messages = conv.messages || [];
        this.collectedInfo = conv.collectedInfo || {};
        this.currentTrip = conv.currentTrip || null;

        // 重新渲染消息
        this.messagesContainer.innerHTML = '';
        this.messages.forEach(msg => {
            if (msg.role === 'user') {
                this.addMessage('user', msg.content, null, false);
            } else {
                this.addMessage('ai', msg.content, null, false);
            }
        });

        // 如果没有消息，显示欢迎消息
        if (this.messages.length === 0) {
            this.addWelcomeMessage();
        }

        // 隐藏快捷建议
        this.quickSuggestions.style.display = this.messages.length === 0 ? 'flex' : 'none';

        // 更新列表高亮
        this.renderConversationList();

        this.showToast('已加载对话');
    }

    deleteConversation(convId) {
        const index = this.conversations.findIndex(c => c.id === convId);
        if (index < 0) return;

        this.conversations.splice(index, 1);
        this.saveConversations();

        // 如果删除的是当前对话，开始新对话
        if (convId === this.conversationId) {
            this.startNewChat(false);
        }

        this.renderConversationList();
        this.showToast('对话已删除');
    }

    startNewChat(showToast = true) {
        // 如果正在处理消息，不允许新建
        if (this.isProcessing) return;

        // 保存当前对话
        this.saveCurrentConversation();

        // 重置所有状态
        this.messages = [];
        this.currentTrip = null;
        this.conversationId = this.generateConversationId();
        this.collectedInfo = {};

        // 清空消息容器并添加欢迎消息
        this.messagesContainer.innerHTML = '';
        this.addWelcomeMessage();

        // 显示快捷建议
        this.quickSuggestions.style.display = 'flex';

        // 清空输入框
        this.inputElement.value = '';
        this.inputElement.style.height = 'auto';
        this.inputElement.focus();

        // 更新列表
        this.renderConversationList();

        // 显示提示
        if (showToast) {
            this.showToast('已开始新对话');
        }
    }

    addWelcomeMessage() {
        const welcomeHtml = `
            <div class="message ai-message">
                <div class="message-avatar">
                    <div class="avatar-icon ai-avatar">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                            <circle cx="7.5" cy="14.5" r="1.5"/>
                            <circle cx="16.5" cy="14.5" r="1.5"/>
                        </svg>
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-text">
                        嗨！我是小智，你的专属旅行规划师 ✨<br><br>
                        告诉我你想去哪里，我来帮你安排一切！比如：
                        <ul class="suggestion-list">
                            <li>🏖️ 想去三亚玩5天，预算5000</li>
                            <li>🏔️ 周末带爸妈去杭州，老人家走不动太多路</li>
                            <li>🍜 成都3日游，主要想吃吃吃！</li>
                        </ul>
                        或者随便聊聊，问我任何旅行相关的问题~
                    </div>
                </div>
            </div>
        `;
        this.messagesContainer.innerHTML = welcomeHtml;
    }

    showToast(message) {
        // 创建 toast 元素
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        // 显示动画
        setTimeout(() => toast.classList.add('show'), 10);

        // 3秒后移除
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async sendMessage() {
        const text = this.inputElement.value.trim();
        if (!text || this.isProcessing) return;

        // 清空输入框
        this.inputElement.value = '';
        this.inputElement.style.height = 'auto';

        // 隐藏快捷建议
        this.quickSuggestions.style.display = 'none';

        // 添加用户消息到历史
        this.messages.push({ role: 'user', content: text });

        // 添加用户消息到界面
        this.addMessage('user', text);

        // 显示加载状态
        this.isProcessing = true;
        this.sendButton.disabled = true;

        // 始终先调用意图分析接口
        await this.sendMessageWithIntent(text);
    }

    async sendMessageWithIntent(text) {
        // 先显示普通加载状态
        let loadingMessage = this.addTypingIndicator();

        try {
            const response = await api.chat({
                message: text,
                conversation_id: this.conversationId,
                current_trip: this.currentTrip,
                conversation_history: this.messages.slice(-10),
                collected_info: this.collectedInfo
            });

            // 移除加载状态
            loadingMessage.remove();

            if (response.success) {
                // 更新收集到的信息
                if (response.collected_info) {
                    this.collectedInfo = { ...this.collectedInfo, ...response.collected_info };
                    console.log('Updated collectedInfo:', this.collectedInfo);
                }

                // 如果是纯聊天，使用流式输出重新请求
                if (response.action === 'chat' || response.action === 'info') {
                    await this.streamReply(text);
                } else if (response.action === 'generate_trip' && response.trip_data) {
                    // 生成行程时显示特殊提示
                    this.messages.push({ role: 'assistant', content: response.reply });
                    this.addMessage('ai', response.reply, response.trip_data);

                    // 更新当前行程
                    this.currentTrip = response.trip_data;
                    if (typeof updateTripDisplay === 'function') {
                        updateTripDisplay(response.trip_data);
                    }

                    // 显示成功提示
                    this.showToast('🎉 行程规划完成！');
                } else if (response.action === 'generate_trip' && !response.trip_data) {
                    // 正在生成行程但还没有数据（需要等待）
                    // 显示生成中的提示
                    loadingMessage = this.addTypingIndicator('🗺️ 正在为您规划行程，搜索景点中...');

                    // 这种情况一般不会发生，因为后端是同步返回的
                    // 但保留这个逻辑以防万一
                    this.messages.push({ role: 'assistant', content: response.reply });
                    this.addMessage('ai', response.reply);
                    loadingMessage.remove();
                } else {
                    // 其他情况直接显示回复
                    this.messages.push({ role: 'assistant', content: response.reply });
                    this.addMessage('ai', response.reply, response.trip_data);

                    // 如果有行程数据，更新当前行程
                    if (response.trip_data) {
                        this.currentTrip = response.trip_data;
                        if (typeof updateTripDisplay === 'function') {
                            updateTripDisplay(response.trip_data);
                        }
                    }
                }
            } else {
                this.addMessage('ai', response.reply || '抱歉，我遇到了一些问题，请稍后再试。');
            }
        } catch (error) {
            console.error('Chat error:', error);
            loadingMessage.remove();
            this.addMessage('ai', `抱歉，出现错误：${error.message || '网络问题'}`);
        } finally {
            this.isProcessing = false;
            this.sendButton.disabled = false;
        }
    }

    async streamReply(text) {
        // 创建AI消息容器（用于流式显示）
        const messageDiv = this.createStreamingMessage();
        const textElement = messageDiv.querySelector('.message-text');
        let fullText = '';
        let searchResults = [];

        try {
            await api.chatStream(
                {
                    message: text,
                    conversation_id: this.conversationId,
                    current_trip: this.currentTrip,
                    conversation_history: this.messages.slice(-10),
                    collected_info: this.collectedInfo
                },
                // onChunk
                (chunk) => {
                    fullText += chunk;
                    textElement.innerHTML = this.formatText(fullText);
                    this.scrollToBottom();
                },
                // onDone
                () => {
                    this.messages.push({ role: 'assistant', content: fullText });
                    // 如果有搜索结果，添加可折叠的搜索结果卡片
                    if (searchResults.length > 0) {
                        const searchCard = this.createSearchResultsCard(searchResults);
                        messageDiv.querySelector('.message-content').appendChild(searchCard);
                    }
                },
                // onError
                (error) => {
                    textElement.innerHTML = this.formatText(`抱歉，出现了一些问题：${error}`);
                },
                // onSearch
                (results) => {
                    searchResults = results;
                    textElement.innerHTML = '<span class="searching">🔍 正在搜索最新信息...</span>';
                }
            );
        } catch (error) {
            console.error('Stream error:', error);
            textElement.innerHTML = this.formatText('抱歉，网络出现问题，请稍后再试。');
        }
    }

    createSearchResultsCard(results) {
        const card = document.createElement('div');
        card.className = 'search-results-card';

        const resultsHtml = results.map((result, index) => `
            <div class="search-result-item">
                <div class="search-result-title">${index + 1}. ${result.title || '无标题'}</div>
                <div class="search-result-content">${(result.content || '').slice(0, 150)}...</div>
                ${result.url ? `<a href="${result.url}" target="_blank" class="search-result-link">查看来源 →</a>` : ''}
            </div>
        `).join('');

        card.innerHTML = `
            <div class="search-results-header" onclick="this.parentElement.classList.toggle('expanded')">
                <span class="search-results-icon">🔍</span>
                <span class="search-results-title">已联网搜索 (${results.length}条结果)</span>
                <span class="search-results-toggle">▼</span>
            </div>
            <div class="search-results-body">
                ${resultsHtml}
            </div>
        `;

        return card;
    }

    async sendMessageStream(text) {
        // 创建AI消息容器（用于流式显示）
        const messageDiv = this.createStreamingMessage();
        const textElement = messageDiv.querySelector('.message-text');
        let fullText = '';

        try {
            await api.chatStream(
                {
                    message: text,
                    conversation_id: this.conversationId,
                    current_trip: this.currentTrip,
                    conversation_history: this.messages.slice(-10),
                    collected_info: this.collectedInfo
                },
                // onChunk
                (chunk) => {
                    fullText += chunk;
                    textElement.innerHTML = this.formatText(fullText);
                    this.scrollToBottom();
                },
                // onDone
                () => {
                    // 添加到消息历史
                    this.messages.push({ role: 'assistant', content: fullText });

                    // 尝试从回复中提取信息更新 collectedInfo
                    this.extractInfoFromReply(fullText);

                    this.isProcessing = false;
                    this.sendButton.disabled = false;
                },
                // onError
                (error) => {
                    textElement.innerHTML = this.formatText(`抱歉，出现了一些问题：${error}`);
                    this.isProcessing = false;
                    this.sendButton.disabled = false;
                }
            );
        } catch (error) {
            console.error('Stream error:', error);
            textElement.innerHTML = this.formatText('抱歉，网络出现问题，请稍后再试。');
            this.isProcessing = false;
            this.sendButton.disabled = false;
        }
    }

    async sendMessageWithTrip(text) {
        const loadingMessage = this.addTypingIndicator();

        try {
            // 调用后端对话API，传递对话历史和收集的信息
            const response = await api.chat({
                message: text,
                conversation_id: this.conversationId,
                current_trip: this.currentTrip,
                conversation_history: this.messages.slice(-10),
                collected_info: this.collectedInfo
            });

            // 移除加载状态
            loadingMessage.remove();

            if (response.success) {
                // 更新收集到的信息
                if (response.collected_info) {
                    this.collectedInfo = { ...this.collectedInfo, ...response.collected_info };
                }

                // 添加AI回复到历史
                this.messages.push({ role: 'assistant', content: response.reply });

                // 添加AI回复到界面
                this.addMessage('ai', response.reply, response.trip_data);

                // 如果有行程数据，更新当前行程
                if (response.trip_data) {
                    this.currentTrip = response.trip_data;
                    // 通知 app.js 更新地图
                    if (typeof updateTripDisplay === 'function') {
                        updateTripDisplay(response.trip_data);
                    }
                }
            } else {
                this.addMessage('ai', response.reply || '抱歉，我遇到了一些问题，请稍后再试。');
            }
        } catch (error) {
            console.error('Chat error:', error);
            loadingMessage.remove();
            let errorMsg = '抱歉，网络出现问题，请稍后再试。';
            if (error.message) {
                errorMsg = `抱歉，出现错误：${error.message}`;
            }
            this.addMessage('ai', errorMsg);
        } finally {
            this.isProcessing = false;
            this.sendButton.disabled = false;
        }
    }

    createStreamingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-icon ai-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                        <circle cx="7.5" cy="14.5" r="1.5"/>
                        <circle cx="16.5" cy="14.5" r="1.5"/>
                    </svg>
                </div>
            </div>
            <div class="message-content">
                <div class="message-text"></div>
            </div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    }

    extractInfoFromReply(reply) {
        // 简单的信息提取逻辑，从AI回复中提取确认的信息
        // 这是一个简化版本，实际可以更智能
        const cityMatch = reply.match(/目的地[：:]\s*(\S+)/);
        const daysMatch = reply.match(/天数[：:]\s*(\d+)/);

        if (cityMatch) {
            this.collectedInfo.city = cityMatch[1];
        }
        if (daysMatch) {
            this.collectedInfo.duration = parseInt(daysMatch[1]);
        }
    }

    addMessage(type, text, tripData = null, saveToHistory = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        // 使用更好看的头像
        const avatarHtml = type === 'ai'
            ? '<div class="avatar-icon ai-avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/><circle cx="7.5" cy="14.5" r="1.5"/><circle cx="16.5" cy="14.5" r="1.5"/></svg></div>'
            : '<div class="avatar-icon user-avatar"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg></div>';

        let contentHtml = `
            <div class="message-avatar">${avatarHtml}</div>
            <div class="message-content">
                <div class="message-text">${this.formatText(text)}</div>
        `;

        // 如果有行程数据，添加行程卡片预览
        if (tripData && tripData.days && tripData.days.length > 0) {
            contentHtml += this.renderTripPreview(tripData);
        }

        contentHtml += '</div>';
        messageDiv.innerHTML = contentHtml;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        // 绑定查看地图按钮事件
        const viewMapBtn = messageDiv.querySelector('.view-map-btn');
        if (viewMapBtn) {
            viewMapBtn.addEventListener('click', () => {
                switchTab('map');
            });
        }

        // 保存对话到本地存储
        if (saveToHistory) {
            this.saveCurrentConversation();
        }

        return messageDiv;
    }

    renderTripPreview(tripData) {
        const trip = tripData.trip || {};
        const days = tripData.days || [];

        // 收集所有景点
        const allPois = [];
        days.forEach(day => {
            if (day.items) {
                day.items.slice(0, 3).forEach(item => {
                    allPois.push(item.name);
                });
            }
        });

        const poisHtml = allPois.slice(0, 6).map(name =>
            `<span class="poi-tag">${name}</span>`
        ).join('');

        return `
            <div class="trip-card-preview">
                <div class="trip-card-preview-header">
                    <span class="trip-card-preview-title">${trip.title || '行程规划'}</span>
                    <span class="trip-card-preview-badge">${trip.days || days.length}天</span>
                </div>
                <div class="trip-card-preview-pois">
                    ${poisHtml}
                    ${allPois.length > 6 ? `<span class="poi-tag">+${allPois.length - 6}个景点</span>` : ''}
                </div>
                <button class="view-map-btn">
                    <span>🗺️</span> 查看地图
                </button>
            </div>
        `;
    }

    addTypingIndicator(message = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message typing-message';

        if (message) {
            // 带文字的加载提示
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <div class="avatar-icon ai-avatar">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                            <circle cx="7.5" cy="14.5" r="1.5"/>
                            <circle cx="16.5" cy="14.5" r="1.5"/>
                        </svg>
                    </div>
                </div>
                <div class="message-content">
                    <div class="generating-indicator">
                        <div class="generating-spinner"></div>
                        <span class="generating-text">${message}</span>
                    </div>
                </div>
            `;
        } else {
            // 默认打字指示器
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <div class="avatar-icon ai-avatar">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                            <circle cx="7.5" cy="14.5" r="1.5"/>
                            <circle cx="16.5" cy="14.5" r="1.5"/>
                        </svg>
                    </div>
                </div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `;
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    }

    /**
     * 更新加载提示文字
     */
    updateTypingIndicator(messageDiv, text) {
        const textElement = messageDiv.querySelector('.generating-text');
        if (textElement) {
            textElement.textContent = text;
        }
    }

    formatText(text) {
        // 增强的文本格式化
        let formatted = text
            // 换行
            .replace(/\n/g, '<br>')
            // 加粗 **text**
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // 斜体 *text*
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // 列表项 - item 或 • item
            .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
            // 数字列表 1. item
            .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

        // 包装连续的 li 标签
        formatted = formatted.replace(/(<li>.*?<\/li>)+/g, '<ul class="chat-list">$&</ul>');

        return formatted;
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    // 加载已保存的行程到对话
    loadSavedTrip(tripData) {
        this.currentTrip = tripData;
        const trip = tripData.trip || {};

        this.addMessage('ai',
            `已加载行程：${trip.title}\n\n你可以继续修改这个行程，比如：\n• 帮我加个餐厅\n• 把第一天的景点换一下\n• 删除某个景点`,
            tripData
        );
    }

    // 清空对话
    clearChat() {
        this.messages = [];
        this.currentTrip = null;
        this.conversationId = this.generateConversationId();
        this.collectedInfo = {};  // 清空收集的信息

        // 保留欢迎消息
        const welcomeMessage = this.messagesContainer.querySelector('.ai-message');
        this.messagesContainer.innerHTML = '';
        if (welcomeMessage) {
            this.messagesContainer.appendChild(welcomeMessage.cloneNode(true));
        }

        // 显示快捷建议
        this.quickSuggestions.style.display = 'flex';
    }
}

// 全局实例
let chatManager = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    chatManager = new ChatManager();
});
