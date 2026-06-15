/**
 * PetXpert AI Diagnosis — Chat Application
 *
 * Handles:
 * - JWT token management (uses PetXpert's localStorage keys)
 * - Auto-creates a session on page load
 * - Message sending (text + image via FormData)
 * - SSE streaming responses with typing animation
 * - Chat UI state management
 * - Image upload with preview
 */
(function () {
    "use strict";

    // ── Configuration ───────────────────────────────────────────────────
    const CONFIG = window.VETAI_CONFIG || {};
    const API_BASE = CONFIG.apiBaseUrl || "/api/v1";

    // ── State ───────────────────────────────────────────────────────────
    const state = {
        accessToken: localStorage.getItem("access_token") || CONFIG.serverAccessToken || null,
        refreshToken: localStorage.getItem("refresh_token") || CONFIG.serverRefreshToken || null,
        activeSessionId: null,
        messages: [],
        selectedImage: null, // { file: File, previewUrl: string }
        isLoading: false,
        isStreaming: false,
    };

    // ── DOM References ──────────────────────────────────────────────────
    const $ = (sel) => document.querySelector(sel);

    const dom = {
        messagesArea: $("#messages-area"),
        welcomeScreen: $("#welcome-screen"),
        messagesContainer: $("#messages-container"),
        thinkingIndicator: $("#thinking-indicator"),
        errorBanner: $("#error-banner"),
        btnNewChat: $("#btn-new-chat"),
        messageInput: $("#message-input"),
        btnSend: $("#btn-send"),
        btnImageUpload: $("#btn-image-upload"),
        imageInput: $("#image-input"),
        imagePreviewContainer: $("#image-preview-container"),
    };

    // ── API Helpers ─────────────────────────────────────────────────────

    function getAuthHeaders() {
        const headers = {};
        if (state.accessToken) {
            headers["Authorization"] = "Bearer " + state.accessToken;
        }
        return headers;
    }

    async function apiFetch(url, options) {
        options = options || {};
        const config = {
            headers: Object.assign({}, getAuthHeaders(), options.headers || {}),
        };
        delete options.headers;
        Object.assign(config, options);

        let response = await fetch(API_BASE + url, config);

        // Handle 401 — try token refresh using PetXpert's refresh endpoint
        if (response.status === 401 && state.refreshToken) {
            const refreshed = await tryRefreshToken();
            if (refreshed) {
                config.headers["Authorization"] = "Bearer " + state.accessToken;
                response = await fetch(API_BASE + url, config);
            }
        }

        return response;
    }

    async function tryRefreshToken() {
        try {
            const res = await fetch("/api/token/refresh/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh: state.refreshToken }),
            });
            if (res.ok) {
                const data = await res.json();
                state.accessToken = data.access;
                localStorage.setItem("access_token", data.access);
                if (data.refresh) {
                    state.refreshToken = data.refresh;
                    localStorage.setItem("refresh_token", data.refresh);
                }
                return true;
            }
        } catch (e) {
            // Token refresh failed
        }
        // Clear tokens and redirect to login
        clearAuth();
        window.location.href = "/signin/";
        return false;
    }

    function clearAuth() {
        state.accessToken = null;
        state.refreshToken = null;
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
    }

    // ── Session Management ──────────────────────────────────────────────

    async function autoCreateSession() {
        try {
            const res = await apiFetch("/chat/sessions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({}),
            });

            if (!res.ok) throw new Error("HTTP " + res.status);

            const session = await res.json();
            state.activeSessionId = session.id;
            dom.welcomeScreen.classList.remove("hidden");
            dom.messagesContainer.classList.add("hidden");
        } catch (err) {
            showError("Failed to create session. Please refresh the page.");
        }
    }

    function resetChat() {
        state.messages = [];
        state.activeSessionId = null;
        dom.messagesContainer.innerHTML = "";
        dom.messagesContainer.classList.add("hidden");
        dom.welcomeScreen.classList.remove("hidden");
        dom.errorBanner.classList.add("hidden");
        dom.messagesArea.classList.remove("chat-scroll-active");
        clearImagePreview();
        autoCreateSession();
    }

    // ── Messages ────────────────────────────────────────────────────────

    async function loadMessages(sessionId) {
        try {
            const res = await apiFetch("/chat/sessions/" + sessionId + "/messages");
            if (!res.ok) throw new Error("HTTP " + res.status);

            const messages = await res.json();
            state.messages = Array.isArray(messages) ? messages : [];
            renderMessages();
        } catch (err) {
            state.messages = [];
            renderMessages();
        }
    }

    async function sendMessageStream() {
        const content = dom.messageInput.value.trim();
        if (!content || state.isLoading) return;

        const sessionId = state.activeSessionId;
        if (!sessionId) {
            showError("Session not ready. Please wait or refresh the page.");
            return;
        }

        state.isLoading = true;
        state.isStreaming = true;
        dom.btnSend.disabled = true;
        dom.messageInput.disabled = true;
        dom.errorBanner.classList.add("hidden");
        dom.thinkingIndicator.classList.remove("hidden");
        dom.welcomeScreen.classList.add("hidden");
        dom.messagesContainer.classList.remove("hidden");
        dom.messagesArea.classList.add("chat-scroll-active");

        // Add temporary user message
        const tempUserMsg = {
            id: "temp-" + Date.now(),
            session_id: sessionId,
            role: "user",
            content: content,
            image_url: state.selectedImage ? state.selectedImage.previewUrl : null,
            created_at: new Date().toISOString(),
        };
        state.messages.push(tempUserMsg);
        renderMessages();

        dom.messageInput.value = "";
        dom.messageInput.style.height = "auto";
        const sentImage = state.selectedImage;
        clearImagePreview();

        try {
            const formData = new FormData();
            formData.append("content", content);
            if (sentImage && sentImage.file) {
                formData.append("image", sentImage.file);
            }

            const headers = Object.assign({}, getAuthHeaders());

            const res = await fetch(API_BASE + "/chat/sessions/" + sessionId + "/messages/stream", {
                method: "POST",
                headers: headers,
                body: formData,
            });

            if (!res.ok) {
                const errData = await res.json().catch(function() { return {}; });
                throw new Error(errData.detail || "Server error: " + res.status);
            }

            // Remove temp user message, add real one
            state.messages = state.messages.filter(function(m) { return m.id !== tempUserMsg.id; });
            state.messages.push({
                id: "user-" + Date.now(),
                session_id: sessionId,
                role: "user",
                content: content,
                image_url: sentImage ? sentImage.previewUrl : null,
                created_at: new Date().toISOString(),
            });

            // Create placeholder for streaming assistant message
            const assistantId = "streaming-" + Date.now();
            const assistantMsg = {
                id: assistantId,
                session_id: sessionId,
                role: "assistant",
                content: "",
                image_url: null,
                created_at: new Date().toISOString(),
            };
            state.messages.push(assistantMsg);
            dom.thinkingIndicator.classList.add("hidden");

            renderMessages();
            scrollToBottom();

            const streamingEl = document.querySelector('[data-msg-id="' + assistantId + '"] .streaming-text');
            let textEl = streamingEl || dom.messagesContainer.querySelector(".streaming-text");

            // Read SSE stream
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let streamingDone = false;
            let streamedText = "";
            let pendingTokens = "";
            let typingActive = false;

            async function typeNextChar() {
                if (typingActive) return;
                typingActive = true;
                while (pendingTokens.length > 0) {
                    const ch = pendingTokens[0];
                    pendingTokens = pendingTokens.slice(1);
                    streamedText += ch;
                    if (!textEl) {
                        textEl = dom.messagesContainer.querySelector(".streaming-text");
                    }
                    if (textEl) {
                        textEl.textContent = streamedText;
                        scrollToBottom();
                    }
                    await new Promise(function(r) { return setTimeout(r, 18); });
                }
                typingActive = false;
            }

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (var i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.token) {
                            pendingTokens += data.token;
                            if (!typingActive) {
                                typeNextChar();
                            }
                        }
                        if (data.error) {
                            throw new Error(data.error);
                        }
                        if (data.done) {
                            streamingDone = true;
                        }
                    } catch (e) {
                        if (e instanceof SyntaxError) continue;
                        throw e;
                    }
                }
            }

            // Wait for typing to finish
            while (pendingTokens.length > 0) {
                await new Promise(function(r) { return setTimeout(r, 50); });
            }

            // Remove streaming placeholder once done
            if (streamingDone) {
                state.messages = state.messages.filter(function(m) { return m.id !== assistantId; });
                await loadMessages(sessionId);
                renderMessages();
                scrollToBottom();
            }
        } catch (err) {
            state.messages = state.messages.filter(
                function(m) { return !m.id.startsWith("streaming-") && m.id !== tempUserMsg.id; }
            );
            dom.messageInput.value = content;
            if (sentImage) {
                state.selectedImage = sentImage;
                renderImagePreview();
            }
            showError(err.message || "Stream failed.");
            renderMessages();
        } finally {
            state.isLoading = false;
            state.isStreaming = false;
            dom.btnSend.disabled = false;
            dom.messageInput.disabled = false;
            dom.thinkingIndicator.classList.add("hidden");
            dom.messageInput.focus();
        }
    }

    // ── Rendering ───────────────────────────────────────────────────────

    function renderMessages() {
        dom.messagesContainer.innerHTML = "";

        if (state.messages.length === 0) {
            dom.messagesContainer.innerHTML =
                '<div class="text-center text-gray-400 py-8 text-sm">No messages yet.</div>';
            dom.messagesArea.classList.remove("chat-scroll-active");
            return;
        }

        dom.messagesArea.classList.add("chat-scroll-active");

        state.messages.forEach(function(msg, index) {
            const isUser = msg.role === "user";
            const isStreaming = msg.id && msg.id.startsWith("streaming-");
            const wrapper = document.createElement("div");

            wrapper.className =
                "flex gap-3 " + (isUser ? "flex-row-reverse" : "") + " " +
                (index < state.messages.length - 1 ? "mb-5" : "");
            wrapper.classList.add(isUser ? "message-user" : "message-assistant");
            wrapper.dataset.msgId = msg.id;

            // Avatar
            const avatar = document.createElement("div");
            avatar.className = "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 " +
                (isUser
                    ? "bg-[var(--primary)] text-white"
                    : "bg-[var(--surface-container-low)] border border-gray-100 text-[var(--primary)]");
            avatar.innerHTML = isUser
                ? '<i data-lucide="user" class="w-4 h-4"></i>'
                : '<i data-lucide="brain" class="w-4 h-4"></i>';
            wrapper.appendChild(avatar);

            // Content container
            const contentDiv = document.createElement("div");
            contentDiv.className = "max-w-[75%] " + (isUser ? "flex flex-col items-end" : "flex flex-col items-start");

            // Image (user messages only)
            if (isUser && msg.image_url) {
                const imgDiv = document.createElement("div");
                imgDiv.className = "mb-2";
                const img = document.createElement("img");
                img.src = getFullImageUrl(msg.image_url);
                img.alt = "Uploaded symptom";
                img.className = "max-w-[200px] max-h-[200px] rounded-lg border border-gray-200 object-cover";
                imgDiv.appendChild(img);
                contentDiv.appendChild(imgDiv);
            }

            // Message bubble
            const bubble = document.createElement("div");
            bubble.className = isUser
                ? "message-bubble-user px-4 py-2.5 text-sm leading-relaxed"
                : "message-bubble-ai px-4 py-2.5 text-sm leading-relaxed";

            if (isUser) {
                bubble.innerHTML = "<p class=\"whitespace-pre-wrap\">" + escapeHtml(msg.content) + "</p>";
            } else if (isStreaming) {
                bubble.innerHTML = "<p class=\"whitespace-pre-wrap streaming-cursor streaming-text\">" + escapeHtml(msg.content) + "</p>";
            } else {
                bubble.classList.add("message-bubble");
                bubble.innerHTML = formatMessageContent(msg.content);
            }
            contentDiv.appendChild(bubble);

            // Timestamp
            const timestamp = document.createElement("div");
            timestamp.className = "message-timestamp";
            timestamp.textContent = formatTimestamp(msg.created_at);
            contentDiv.appendChild(timestamp);

            // Diagnosis card (assistant only, if available)
            if (!isUser && msg.diagnosis && !isStreaming) {
                contentDiv.appendChild(renderDiagnosisCard(msg.diagnosis));
            }

            wrapper.appendChild(contentDiv);
            dom.messagesContainer.appendChild(wrapper);
        });

        // Re-init Lucide icons
        if (typeof lucide !== "undefined") lucide.createIcons();
        scrollToBottom();

        // Animate new messages with ScrollReveal
        if (typeof ScrollReveal !== "undefined") {
            ScrollReveal().reveal(".message-assistant", {
                origin: "bottom",
                distance: "16px",
                duration: 300,
                interval: 50,
                cleanup: true,
            });
        }
    }

    function renderDiagnosisCard(diagnosis) {
        const diseaseClasses = {
            "Skin Infection": "skin",
            "Ear Infection": "ear",
            "Eye Infection": "eye",
            Parasites: "parasite",
            "Digestive Issues": "digestive",
        };
        const cssClass = diseaseClasses[diagnosis.disease] || "skin";

        const card = document.createElement("div");
        card.className = "diagnosis-card " + cssClass;

        const confidenceLabel =
            diagnosis.confidence !== null && diagnosis.confidence !== undefined
                ? diagnosis.confidence >= 0.8
                    ? "High"
                    : diagnosis.confidence >= 0.5
                    ? "Medium"
                    : "Low"
                : "Unknown";
        const confidencePct =
            diagnosis.confidence !== null && diagnosis.confidence !== undefined
                ? " (" + Math.round(diagnosis.confidence * 100) + "%)"
                : "";

        card.innerHTML =
            '<div class="flex items-center gap-2 mb-3">' +
                '<div class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">' +
                    '<i data-lucide="stethoscope" class="w-4 h-4"></i>' +
                '</div>' +
                '<div>' +
                    '<h4 class="font-semibold text-sm">' + escapeHtml(diagnosis.disease) + '</h4>' +
                    '<div class="flex items-center gap-1.5">' +
                        '<i data-lucide="activity" class="w-3 h-3"></i>' +
                        '<span class="text-xs font-medium">' + confidenceLabel + ' confidence' + confidencePct + '</span>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            (diagnosis.symptoms_summary
                ? '<div class="mb-2">' +
                    '<p class="text-xs font-medium uppercase tracking-wider mb-1" style="color: inherit; opacity: 0.7;">Symptoms Identified</p>' +
                    '<p class="text-sm leading-relaxed" style="opacity: 0.9;">' + escapeHtml(diagnosis.symptoms_summary) + '</p>' +
                  '</div>'
                : "") +
            (diagnosis.treatment_plan
                ? '<div>' +
                    '<p class="text-xs font-medium uppercase tracking-wider mb-1" style="color: inherit; opacity: 0.7;">Treatment Plan</p>' +
                    '<div class="text-sm leading-relaxed whitespace-pre-line" style="opacity: 0.9;">' + escapeHtml(diagnosis.treatment_plan) + '</div>' +
                  '</div>'
                : "") +
            '<div class="mt-3 pt-3 border-t border-black/10 flex items-start gap-1.5">' +
                '<i data-lucide="alert-triangle" class="w-3 h-3 mt-0.5 flex-shrink-0" style="opacity: 0.6;"></i>' +
                '<p class="text-xs" style="opacity: 0.6;">AI-generated guidance. Please consult a licensed veterinarian for definitive diagnosis.</p>' +
            '</div>';

        return card;
    }

    // ── UI Helpers ──────────────────────────────────────────────────────

    function showError(message) {
        dom.errorBanner.classList.remove("hidden");
        dom.errorBanner.textContent = message;
        setTimeout(function() {
            dom.errorBanner.classList.add("hidden");
        }, 5000);
    }

    function scrollToBottom() {
        const area = document.getElementById("messages-area");
        if (area) {
            area.scrollTop = area.scrollHeight;
        }
    }

    // ── Image Upload ────────────────────────────────────────────────────

    function handleImageSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        const previewUrl = URL.createObjectURL(file);
        state.selectedImage = { file: file, previewUrl: previewUrl };
        renderImagePreview();
        e.target.value = "";
    }

    function clearImagePreview() {
        state.selectedImage = null;
        dom.imagePreviewContainer.classList.add("hidden");
        dom.imagePreviewContainer.innerHTML = "";
    }

    function renderImagePreview() {
        if (!state.selectedImage) {
            clearImagePreview();
            return;
        }

        dom.imagePreviewContainer.classList.remove("hidden");
        dom.imagePreviewContainer.innerHTML =
            '<div class="image-preview">' +
                '<img src="' + state.selectedImage.previewUrl + '" alt="Preview" class="h-20 w-20 object-cover">' +
                '<button class="remove-btn" title="Remove image">&times;</button>' +
            '</div>';
        dom.imagePreviewContainer.querySelector(".remove-btn").addEventListener("click", clearImagePreview);
    }

    // ── Utility Functions ───────────────────────────────────────────────

    function formatMessageContent(text) {
        if (!text) return "";
        let formatted = escapeHtml(text);
        // Bold
        formatted = formatted.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        // Italic
        formatted = formatted.replace(/\*(.+?)\*/g, "<em>$1</em>");
        // Inline code
        formatted = formatted.replace(/`(.+?)`/g, "<code>$1</code>");
        // Newlines to paragraphs
        formatted = formatted
            .split("\n\n")
            .map(function(p) { return "<p>" + p.replace(/\n/g, "<br>") + "</p>"; })
            .join("");
        // Bullet points
        formatted = formatted.replace(/• (.+?)(?=<br>|<\/p>|<p>|$)/g, "<li>$1</li>");
        formatted = formatted.replace(/(<li>.*?<\/li>)+/g, "<ul>$&</ul>");

        return formatted;
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function getFullImageUrl(url) {
        if (!url) return "";
        if (url.startsWith("http") || url.startsWith("blob:")) return url;
        return url;
    }

    function formatTimestamp(isoString) {
        try {
            const d = new Date(isoString);
            return d.toLocaleTimeString("en-US", {
                hour: "numeric",
                minute: "2-digit",
                hour12: true,
            });
        } catch (e) {
            return "";
        }
    }

    // ── Event Listeners ─────────────────────────────────────────────────

    // New chat button
    dom.btnNewChat.addEventListener("click", function() {
        resetChat();
    });

    // Send message
    dom.btnSend.addEventListener("click", function() {
        sendMessageStream();
    });

    // Enter to send, Shift+Enter for newline
    dom.messageInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessageStream();
        }
    });

    // Auto-resize textarea
    dom.messageInput.addEventListener("input", function() {
        dom.messageInput.style.height = "auto";
        dom.messageInput.style.height = Math.min(dom.messageInput.scrollHeight, 150) + "px";
    });

    // Image upload
    dom.btnImageUpload.addEventListener("click", function() {
        dom.imageInput.click();
    });
    dom.imageInput.addEventListener("change", handleImageSelect);

    // ── Initialization ──────────────────────────────────────────────────

    function init() {
        // Check auth — redirect if no token
        const token = localStorage.getItem("access_token");
        if (!token && !CONFIG.serverAccessToken) {
            window.location.href = "/signin/";
            return;
        }

        // Auto-create a session on page load
        autoCreateSession();

        // Focus input
        dom.messageInput.focus();
    }

    // Start application
    init();
})();
