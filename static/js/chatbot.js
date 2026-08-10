/**
 * TrackBot — AI Chatbot JavaScript
 * FreelanceTrack AI Assistant
 *
 * Handles: conversation management, message rendering,
 * auto-expand textarea, send/stop, markdown formatting,
 * copy, rename, delete, search, theme-aware UI.
 */

(function () {
  'use strict';

  // ── State ────────────────────────────────────────────────────
  let activeConversationId = null;
  let isGenerating = false;
  let abortController = null;
  let allConversations = [];   // [{id, title, updated_at}]
  let searchQuery = '';

  // ── DOM refs ─────────────────────────────────────────────────
  const messagesArea   = document.getElementById('tbMessagesArea');
  const textarea       = document.getElementById('tbTextarea');
  const sendBtn        = document.getElementById('tbSendBtn');
  const stopBtn        = document.getElementById('tbStopBtn');
  const convList       = document.getElementById('tbConvList');
  const searchInput    = document.getElementById('tbSearchInput');
  const chatTitleEl    = document.getElementById('tbChatTitle');
  const sidebarEl      = document.getElementById('tbSidebar');
  const sidebarToggle  = document.getElementById('tbSidebarToggle');
  const welcomeScreen  = document.getElementById('tbWelcomeScreen');

  // ── Init ─────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    initConversations();
    initTextarea();
    initSend();
    initSearch();
    initSidebarToggle();
    initSuggestions();
    scrollToBottom();

    // Load active conversation from template data
    const convIdEl = document.getElementById('tbActiveConvId');
    if (convIdEl && convIdEl.value) {
      activeConversationId = convIdEl.value;
      markActiveConv(activeConversationId);
    }
  });

  // ── Load conversations list ──────────────────────────────────
  function initConversations() {
    loadConversations();
  }

  async function loadConversations() {
    try {
      const data = await apiFetch('/api/v1/chat/conversations/');
      allConversations = data;
      renderConvList(data);
    } catch (e) {
      // fail silently — sidebar list not critical
    }
  }

  function renderConvList(convs) {
    if (!convList) return;
    convList.innerHTML = '';

    const filtered = searchQuery
      ? convs.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase()))
      : convs;

    if (!filtered.length) {
      convList.innerHTML = `<div style="text-align:center;padding:24px 12px;color:var(--text-muted);font-size:12.5px;">
        ${searchQuery ? 'No matching conversations.' : 'No conversations yet.<br>Start chatting to create one!'}
      </div>`;
      return;
    }

    // Group by date
    const groups = { Today: [], Yesterday: [], Older: [] };
    const now = new Date();
    filtered.forEach(c => {
      const d = new Date(c.updated_at);
      const diffDays = Math.floor((now - d) / 86400000);
      if (diffDays < 1) groups.Today.push(c);
      else if (diffDays < 2) groups.Yesterday.push(c);
      else groups.Older.push(c);
    });

    Object.entries(groups).forEach(([label, items]) => {
      if (!items.length) return;
      const groupLabel = document.createElement('div');
      groupLabel.className = 'tb-conv-group-label';
      groupLabel.textContent = label;
      convList.appendChild(groupLabel);

      items.forEach(conv => {
        convList.appendChild(buildConvItem(conv));
      });
    });
  }

  function buildConvItem(conv) {
    const item = document.createElement('div');
    item.className = 'tb-conv-item' + (conv.id === activeConversationId ? ' active' : '');
    item.dataset.id = conv.id;
    item.innerHTML = `
      <div class="tb-conv-item-icon"><i class="fas fa-comment"></i></div>
      <span class="tb-conv-item-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
      <div class="tb-conv-item-actions">
        <button class="tb-conv-action-btn" data-action="rename" data-id="${conv.id}" title="Rename">
          <i class="fas fa-pen"></i>
        </button>
        <button class="tb-conv-action-btn danger" data-action="delete" data-id="${conv.id}" title="Delete">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    `;

    // Click to open conversation
    item.addEventListener('click', function (e) {
      if (e.target.closest('.tb-conv-item-actions')) return;
      openConversation(conv.id);
    });

    // Rename button
    item.querySelector('[data-action="rename"]').addEventListener('click', function (e) {
      e.stopPropagation();
      showRenameModal(conv.id, conv.title);
    });

    // Delete button
    item.querySelector('[data-action="delete"]').addEventListener('click', function (e) {
      e.stopPropagation();
      deleteConversation(conv.id, conv.title);
    });

    return item;
  }

  function markActiveConv(id) {
    document.querySelectorAll('.tb-conv-item').forEach(el => {
      el.classList.toggle('active', el.dataset.id === id);
    });
  }

  // ── Open conversation (navigate to its URL) ─────────────────
  function openConversation(id) {
    if (id === activeConversationId && !isGenerating) return;
    window.location.href = `/chat/${id}/`;
  }

  // ── Send message ─────────────────────────────────────────────
  function initSend() {
    if (sendBtn) {
      sendBtn.addEventListener('click', sendMessage);
    }
  }

  async function sendMessage() {
    if (!textarea || isGenerating) return;
    const msg = textarea.value.trim();
    if (!msg) return;

    textarea.value = '';
    autoResizeTextarea();
    updateSendBtn(true);

    // Hide welcome screen
    if (welcomeScreen) welcomeScreen.style.display = 'none';

    // Render user bubble
    appendMessage({ role: 'user', content: msg });

    // Show typing indicator
    const typingEl = showTyping();
    scrollToBottom();

    // Abort controller for stop
    abortController = new AbortController();
    isGenerating = true;
    showStopBtn(true);

    try {
      const payload = {
        message: msg,
        conversation_id: activeConversationId || '',
      };

      const resp = await fetch('/api/v1/chat/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });

      removeTyping(typingEl);

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || `Server error ${resp.status}`);
      }

      const data = await resp.json();

      // Update conversation ID + URL (first message creates a new conversation)
      if (data.conversation_id && data.conversation_id !== activeConversationId) {
        activeConversationId = data.conversation_id;
        window.history.replaceState({}, '', `/chat/${activeConversationId}/`);
        // Refresh sidebar to show new conversation
        await loadConversations();
        markActiveConv(activeConversationId);
      }

      // Update sidebar title if it changed
      if (data.conversation_title && chatTitleEl) {
        chatTitleEl.textContent = data.conversation_title;
      }

      // Update sidebar item title
      updateConvTitle(activeConversationId, data.conversation_title);

      // Render AI response
      if (data.message) {
        appendMessage(data.message);
      }

    } catch (err) {
      removeTyping(typingEl);
      if (err.name === 'AbortError') {
        appendMessage({
          role: 'assistant',
          content: '⚠️ Response generation was stopped.',
          is_error: true,
        });
      } else {
        appendMessage({
          role: 'assistant',
          content: `⚠️ ${err.message || 'Something went wrong. Please try again.'}`,
          is_error: true,
        });
      }
    } finally {
      isGenerating = false;
      showStopBtn(false);
      updateSendBtn(false);
      scrollToBottom();
    }
  }

  // ── Render message bubble ─────────────────────────────────────
  function appendMessage(msg) {
    if (!messagesArea) return;

    const wrapper = document.createElement('div');
    wrapper.className = `tb-message ${msg.role}`;
    wrapper.dataset.id = msg.id || '';

    const avatarContent = msg.role === 'user'
      ? '<i class="fas fa-user"></i>'
      : '<i class="fas fa-robot"></i>';

    const formattedContent = msg.role === 'assistant'
      ? formatMarkdown(msg.content)
      : escapeHtml(msg.content).replace(/\n/g, '<br>');

    const timeStr = msg.created_at
      ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const actionsHtml = msg.role === 'assistant' ? `
      <div class="tb-message-actions">
        <button class="tb-msg-action-btn" data-action="copy" title="Copy response">
          <i class="fas fa-copy"></i> Copy
        </button>
      </div>` : `
      <div class="tb-message-actions">
        <button class="tb-msg-action-btn" data-action="copy-user" title="Copy message">
          <i class="fas fa-copy"></i>
        </button>
      </div>`;

    wrapper.innerHTML = `
      <div class="tb-message-avatar">${avatarContent}</div>
      <div class="tb-message-body">
        <div class="tb-message-bubble">${formattedContent}</div>
        <div class="tb-message-time">${timeStr}</div>
        ${actionsHtml}
      </div>
    `;

    // Copy button
    wrapper.querySelector('[data-action="copy"], [data-action="copy-user"]')?.addEventListener('click', function () {
      const text = msg.content;
      navigator.clipboard.writeText(text).then(() => {
        this.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
          this.innerHTML = msg.role === 'assistant'
            ? '<i class="fas fa-copy"></i> Copy'
            : '<i class="fas fa-copy"></i>';
        }, 2000);
      });
    });

    messagesArea.appendChild(wrapper);
    scrollToBottom();
  }

  // ── Typing indicator ─────────────────────────────────────────
  function showTyping() {
    if (!messagesArea) return null;
    const el = document.createElement('div');
    el.className = 'tb-typing';
    el.id = 'tbTypingIndicator';
    el.innerHTML = `
      <div class="tb-message-avatar" style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#07111D,#39444D);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:13px;border:2px solid var(--border-color);">
        <i class="fas fa-robot"></i>
      </div>
      <div class="tb-typing-dots">
        <div class="tb-typing-dot"></div>
        <div class="tb-typing-dot"></div>
        <div class="tb-typing-dot"></div>
      </div>
    `;
    messagesArea.appendChild(el);
    return el;
  }

  function removeTyping(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  // ── Stop generation ───────────────────────────────────────────
  function showStopBtn(show) {
    if (!sendBtn || !stopBtn) return;
    sendBtn.style.display = show ? 'none' : 'flex';
    stopBtn.style.display = show ? 'flex' : 'none';
  }

  document.addEventListener('DOMContentLoaded', function () {
    const sb = document.getElementById('tbStopBtn');
    if (sb) {
      sb.addEventListener('click', function () {
        if (abortController) abortController.abort();
      });
    }
  });

  // ── Textarea auto-resize ─────────────────────────────────────
  function initTextarea() {
    if (!textarea) return;

    textarea.addEventListener('input', function () {
      autoResizeTextarea();
      updateSendBtn(false);
    });

    textarea.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!isGenerating && textarea.value.trim()) {
          sendMessage();
        }
      }
    });
  }

  function autoResizeTextarea() {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
  }

  function updateSendBtn(generating) {
    if (!sendBtn) return;
    const hasText = textarea && textarea.value.trim().length > 0;
    sendBtn.disabled = generating || !hasText;
  }

  // ── Sidebar toggle ────────────────────────────────────────────
  function initSidebarToggle() {
    if (sidebarToggle && sidebarEl) {
      sidebarToggle.addEventListener('click', function () {
        sidebarEl.classList.toggle('collapsed');
        const icon = this.querySelector('i');
        if (icon) {
          icon.className = sidebarEl.classList.contains('collapsed')
            ? 'fas fa-bars'
            : 'fas fa-times';
        }
      });
    }

    // Mobile overlay close
    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 768) {
        if (sidebarEl && !sidebarEl.classList.contains('collapsed')) {
          if (!sidebarEl.contains(e.target) && !sidebarToggle?.contains(e.target)) {
            sidebarEl.classList.add('collapsed');
          }
        }
      }
    });
  }

  // ── Search ────────────────────────────────────────────────────
  function initSearch() {
    if (!searchInput) return;
    searchInput.addEventListener('input', function () {
      searchQuery = this.value.trim();
      renderConvList(allConversations);
      if (activeConversationId) markActiveConv(activeConversationId);
    });
  }

  // ── Suggested questions ────────────────────────────────────────
  function initSuggestions() {
    document.querySelectorAll('.tb-suggestion-card').forEach(card => {
      card.addEventListener('click', function () {
        const question = this.dataset.question;
        if (textarea && question) {
          textarea.value = question;
          autoResizeTextarea();
          updateSendBtn(false);
          textarea.focus();
          sendMessage();
        }
      });
    });
  }

  // ── Rename modal ──────────────────────────────────────────────
  function showRenameModal(convId, currentTitle) {
    const overlay = document.createElement('div');
    overlay.className = 'tb-modal-overlay';
    overlay.innerHTML = `
      <div class="tb-modal">
        <h4><i class="fas fa-pen" style="color:var(--primary);margin-right:8px;"></i> Rename Conversation</h4>
        <input type="text" id="tbRenameInput" value="${escapeHtml(currentTitle)}" maxlength="200" placeholder="Enter a new title…" />
        <div class="tb-modal-actions">
          <button class="tb-modal-btn secondary" id="tbRenameCancel">Cancel</button>
          <button class="tb-modal-btn primary" id="tbRenameConfirm">Save</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const input = overlay.querySelector('#tbRenameInput');
    input.focus();
    input.select();

    overlay.querySelector('#tbRenameCancel').addEventListener('click', () => overlay.remove());
    overlay.querySelector('#tbRenameConfirm').addEventListener('click', () => doRename(convId, input.value, overlay));
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') doRename(convId, input.value, overlay);
      if (e.key === 'Escape') overlay.remove();
    });
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  }

  async function doRename(convId, newTitle, overlay) {
    const t = newTitle.trim();
    if (!t) return;
    try {
      const data = await apiFetch(`/api/v1/chat/conversations/${convId}/rename/`, {
        method: 'PATCH',
        body: JSON.stringify({ title: t }),
      });
      overlay.remove();
      updateConvTitle(convId, data.title);
      if (convId === activeConversationId && chatTitleEl) {
        chatTitleEl.textContent = data.title;
        document.title = `TrackBot — ${data.title}`;
      }
      if (window.showToast) window.showToast('Conversation renamed.', 'success');
    } catch (e) {
      if (window.showToast) window.showToast('Failed to rename conversation.', 'danger');
    }
  }

  // ── Delete conversation ───────────────────────────────────────
  async function deleteConversation(convId, title) {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await apiFetch(`/api/v1/chat/conversations/${convId}/delete/`, { method: 'DELETE' });
      allConversations = allConversations.filter(c => c.id !== convId);
      renderConvList(allConversations);
      if (convId === activeConversationId) {
        window.location.href = '/chat/';
      }
      if (window.showToast) window.showToast('Conversation deleted.', 'success');
    } catch (e) {
      if (window.showToast) window.showToast('Failed to delete conversation.', 'danger');
    }
  }

  // ── Helpers ───────────────────────────────────────────────────
  function updateConvTitle(id, newTitle) {
    allConversations = allConversations.map(c =>
      c.id === id ? { ...c, title: newTitle } : c
    );
    const item = document.querySelector(`.tb-conv-item[data-id="${id}"] .tb-conv-item-title`);
    if (item) item.textContent = newTitle;
  }

  function scrollToBottom() {
    if (messagesArea) {
      setTimeout(() => {
        messagesArea.scrollTop = messagesArea.scrollHeight;
      }, 50);
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Minimal markdown formatter for AI responses.
   * Handles: **bold**, *italic*, `code`, bullet lists, line breaks.
   */
  function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);

    // Headings
    html = html.replace(/^### (.+)$/gm, '<strong style="font-size:14px;color:var(--primary);">$1</strong>');
    html = html.replace(/^## (.+)$/gm, '<strong style="font-size:15px;color:var(--primary);">$1</strong>');
    html = html.replace(/^# (.+)$/gm, '<strong style="font-size:16px;color:var(--primary);">$1</strong>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Inline code
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // Unordered lists (• - *)
    html = html.replace(/^[\•\-\*]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    // Clean up nested ul
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // Numbered lists
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = '<p>' + html + '</p>';
    html = html.replace(/<p><\/p>/g, '');

    return html;
  }

  // ── apiFetch (local copy using the global if available) ───────
  function apiFetch(endpoint, options = {}) {
    if (window.apiFetch) {
      // Use the global helper defined in main.js
      return window.apiFetch(endpoint, options);
    }
    // Fallback
    const headers = {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest',
      ...options.headers,
    };
    return fetch(endpoint, { credentials: 'same-origin', ...options, headers })
      .then(r => {
        if (!r.ok) return r.json().then(e => { throw new Error(e.error || `HTTP ${r.status}`); });
        return r.json();
      });
  }

  function getCookie(name) {
    let v = null;
    if (document.cookie) {
      for (const c of document.cookie.split(';')) {
        const t = c.trim();
        if (t.startsWith(name + '=')) {
          v = decodeURIComponent(t.slice(name.length + 1));
          break;
        }
      }
    }
    return v;
  }

})();
