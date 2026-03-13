/**
* CalendAI PRO — Chat interactivity
* Handles message sending and receiving via fetch API.
*/

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('chat-send-btn');
    const recordBtn = document.getElementById('chat-record-btn');

    const sidebarHistory = document.getElementById('sidebar-history');
    const syncTimeText = document.getElementById('sync-time-text');

    let mediaRecorder;
    let audioChunks = [];

    if (!form || !input || !messages) return;

    // ── History Loading ──────────────────────────────────
    // ── History Loading ──────────────────────────────────
    async function loadHistory() {
        try {
            const response = await fetch('/chat/history');
            const data = await response.json();
            
            if (sidebarHistory) {
                sidebarHistory.innerHTML = '';
                if (data.length === 0) {
                    sidebarHistory.innerHTML = '<div class="history-skeleton">Nenhuma conversa anterior.</div>';
                } else {
                    data.forEach(item => {
                        const el = document.createElement('div');
                        el.className = 'history-item';
                        el.dataset.date = item.date;
                        el.innerHTML = `<i data-lucide="message-square"></i> <span>${item.label}</span>`;
                        
                        el.addEventListener('click', () => loadDayMessages(item.date, el));
                        sidebarHistory.appendChild(el);
                    });
                    if (window.lucide) lucide.createIcons();
                }

                if (syncTimeText) {
                    const now = new Date();
                    syncTimeText.textContent = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                }
            }
        } catch (err) {
            console.error('Error loading history:', err);
        }
    }

    async function loadDayMessages(date, element) {
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
        if (element) element.classList.add('active');

        messages.innerHTML = '<div class="chat-bubble chat-bubble-ai"><div class="bubble-content">Carregando mensagens...</div></div>';

        try {
            const response = await fetch(`/chat/history/${date}`);
            const data = await response.json();

            messages.innerHTML = '';
            if (data.length === 0) {
                appendBubble('Nenhuma mensagem encontrada para esta data.', 'ai');
            } else {
                data.forEach(msg => {
                    appendBubble(msg.content, msg.role, false);
                });
                scrollToBottom();
            }
        } catch (err) {
            appendBubble('Erro ao carregar mensagens históricas.', 'ai');
        }
    }

// Initial load
loadHistory();

// ── Audio Recording ──────────────────────────────────
if (recordBtn) {
    recordBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.addEventListener('dataavailable', (event) => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener('stop', async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                // Stop all tracks in the stream
                stream.getTracks().forEach(track => track.stop());

                recordBtn.classList.remove('recording');
                recordBtn.innerHTML = '<i data-lucide="mic"></i>';
                if (window.lucide) lucide.createIcons();

                if (audioBlob.size > 0) {
                    await sendAudioMessage(audioBlob);
                }
            });

            mediaRecorder.start();
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<i data-lucide="square"></i>';
            if (window.lucide) lucide.createIcons();

        } catch (err) {
            console.error('Microphone access denied:', err);
            alert('Não foi possível acessar o microfone. Verifique as permissões do seu navegador.');
        }
    });
}

async function sendAudioMessage(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');

    // Add user visual feedback
    appendBubble('🎤 Mensagem de áudio enviada...', 'user');
    const typingEl = showTyping();

    try {
        const response = await fetch('/chat/audio', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        typingEl.remove();

        if (data.error) {
            appendBubble('Erro ao processar áudio: ' + (data.error || 'Erro interno'), 'ai');
        } else {
            // The backend transcribes it, and we might want to update the bubble with transcription
            // if the backend provides it, but usually the orchestrator just replies.
            appendBubble(data.reply, 'ai');
        }
    } catch (err) {
        typingEl.remove();
        appendBubble('Erro ao enviar áudio. Verifique sua conexão.', 'ai');
    } finally {
        scrollToBottom();
    }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const text = input.value.trim();
    if (!text) return;

    // Add user bubble
    appendBubble(text, 'user');
    input.value = '';
    input.focus();
    sendBtn.disabled = true;

    // Show typing indicator
    const typingEl = showTyping();

    try {
        const response = await fetch('/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        const data = await response.json();

        // Remove typing indicator
        typingEl.remove();

        if (data.error) {
            appendBubble('Desculpe, ocorreu um erro. Tente novamente.', 'ai');
        } else {
            appendBubble(data.reply, 'ai');
        }
    } catch (err) {
        typingEl.remove();
        appendBubble('Erro de conexão. Verifique sua internet e tente novamente.', 'ai');
    } finally {
        sendBtn.disabled = false;
        scrollToBottom();
    }
});

function appendBubble(text, role) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble chat-bubble-${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'bubble-avatar';
    avatar.innerHTML = role === 'ai'
        ? '<i data-lucide="sparkles"></i>'
        : '<i data-lucide="user"></i>';

    const content = document.createElement('div');
    content.className = 'bubble-content';

    // Safety check for empty text
    const display_text = text || (role === 'ai' ? '...' : '');

    // Support simple HTML from AI responses (bold, lists, etc.)
    if (role === 'ai') {
        content.innerHTML = formatMessage(display_text);
    } else {
        content.textContent = display_text;
    }

    bubble.appendChild(avatar);
    bubble.appendChild(content);
    messages.appendChild(bubble);

    // Re-initialize Lucide icons for new elements
    if (window.lucide) lucide.createIcons();

    scrollToBottom();
}

function formatMessage(text) {
    // Convert markdown-like formatting to HTML
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');
}

function showTyping() {
    const typing = document.createElement('div');
    typing.className = 'chat-bubble chat-bubble-ai';
    typing.innerHTML = `
            <div class="bubble-avatar"><i data-lucide="sparkles"></i></div>
            <div class="bubble-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
    messages.appendChild(typing);
    if (window.lucide) lucide.createIcons();
    scrollToBottom();
    return typing;
}

function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
}

// Scroll to bottom immediately on load to show initial messages
scrollToBottom();
});
