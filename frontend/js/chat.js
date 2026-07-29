/**
 * VideoMind AI - Interactive Intelligence Studio & Chat Controller
 * Built for high reliability, strict transcript grounding, and ChatGPT-style UX.
 */

class StudioController {
  constructor() {
    this.currentVideoId = null;
    this.currentMetadata = null;
    this.currentSummaryContent = '';
    this.hasTranscript = false;
    this.isAnalyzing = false;
    this.isChatting = false;

    this.flashcardsData = [];
    this.currentCardIndex = 0;
    this.quizData = [];
    this.currentQuizIndex = 0;
    this.quizScore = 0;
    this.lastQuestion = '';
    
    this.initEventListeners();
    this.checkUrlParams();
  }

  initEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.currentTarget.dataset.tab;
        this.switchTab(tab);
      });
    });

    // Chat form submission
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleUserChatMessage();
      });
    }

    // ChatGPT-style Enter key handler (Enter to send, Shift+Enter for newline)
    const chatInput = document.getElementById('chatInputField');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleUserChatMessage();
        }
      });
    }

    // Header URL input form
    const urlForm = document.getElementById('studioUrlForm');
    if (urlForm) {
      urlForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('studioUrlInput');
        if (input && input.value.trim()) {
          this.analyzeVideoUrl(input.value.trim());
        }
      });
    }

    // Clear chat button
    const clearBtn = document.getElementById('clearChatBtn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearChatHistory());
    }

    // Regenerate response button
    const regenBtn = document.getElementById('regenerateBtn');
    if (regenBtn) {
      regenBtn.addEventListener('click', () => this.regenerateLastResponse());
    }
  }

  checkUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const videoUrl = params.get('url') || params.get('v');
    if (videoUrl) {
      const urlInput = document.getElementById('studioUrlInput');
      if (urlInput) urlInput.value = videoUrl;
      this.analyzeVideoUrl(videoUrl);
    }
  }

  renderProgressPipeline(stepIndex, statusMessage) {
    const panel = document.getElementById('summaryTabPanel');
    if (!panel) return;

    const steps = [
      "Extract Video ID & Validate Link",
      "Fetching Spoken Transcript",
      "Chunking Transcript into Semantic Units",
      "Generating Knowledge Base with Gemini",
      "Grounded Chat Enabled"
    ];

    const stepsHtml = steps.map((stepText, idx) => {
      let icon = "⚪";
      let style = "color: var(--text-muted);";
      if (idx < stepIndex) {
        icon = "✅";
        style = "color: #00f2fe; font-weight: 600;";
      } else if (idx === stepIndex) {
        icon = "⏳";
        style = "color: #fff; font-weight: bold;";
      }
      return `
        <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; ${style}">
          <span style="font-size: 1.2rem;">${icon}</span>
          <span>${stepText}</span>
        </div>
      `;
    }).join('');

    panel.innerHTML = `
      <div class="glass-card" style="max-width: 600px; margin: 3rem auto; padding: 2.5rem; text-align: left;">
        <h3 style="font-size: 1.3rem; margin-bottom: 1rem; color: var(--accent-cyan); display: flex; align-items: center; gap: 0.5rem;">
          <span class="typing-dot" style="display: inline-block; width: 10px; height: 10px; background: var(--accent-cyan); border-radius: 50%;"></span>
          ${statusMessage}
        </h3>
        <div style="display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 1.5rem;">
          ${stepsHtml}
        </div>
        <div class="skeleton" style="height: 6px; width: 100%; border-radius: 4px; overflow: hidden;">
          <div style="height: 100%; width: ${((stepIndex + 1) / steps.length) * 100}%; background: linear-gradient(90deg, #4facfe, #00f2fe); transition: width 0.4s ease;"></div>
        </div>
      </div>
    `;
  }

  async analyzeVideoUrl(url) {
    if (this.isAnalyzing) return;

    const videoId = YouTubeHelper.extractVideoId(url);
    if (!videoId) {
      AnimationEngine.showToast('Please enter a valid YouTube URL.', 'error');
      return;
    }

    this.isAnalyzing = true;
    this.currentVideoId = videoId;
    this.hasTranscript = false;

    // Update form controls state
    const submitBtn = document.querySelector('#studioUrlForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    // Load video iframe
    const playerWrapper = document.getElementById('playerWrapper');
    if (playerWrapper) {
      playerWrapper.innerHTML = `<iframe id="ytPlayer" src="${YouTubeHelper.getEmbedUrl(videoId)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
    }

    // Step 1: Validating URL
    this.renderProgressPipeline(0, "Validating YouTube URL...");

    try {
      // Step 2: Fetching transcript
      await new Promise(r => setTimeout(r, 400));
      this.renderProgressPipeline(1, "Fetching video transcript...");

      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url, user_id: firebaseManager.getUserId() })
      });

      const resJson = await response.json();
      const isSuccess = resJson.success;
      const dataPayload = resJson.data || resJson;

      if (!isSuccess || !dataPayload.has_transcript) {
        const errorMsg = resJson.error || dataPayload.error || "No transcript available for this video.";
        this.renderNoTranscriptState(errorMsg);
        AnimationEngine.showToast('Transcript unavailable for this video.', 'error');
        return;
      }

      // Step 3: Chunking & Knowledge Base
      this.renderProgressPipeline(2, "Chunking transcript into semantic units...");
      await new Promise(r => setTimeout(r, 300));

      this.renderProgressPipeline(3, "Building Knowledge Base with Gemini...");
      await new Promise(r => setTimeout(r, 300));

      // Step 4: Completed
      this.renderProgressPipeline(4, "Analysis completed!");

      this.currentMetadata = dataPayload.metadata || { title: `YouTube Video (${videoId})`, author: "Creator" };
      this.hasTranscript = true;

      // Update UI title and metadata
      const titleEl = document.getElementById('videoTitleEl');
      if (titleEl) titleEl.innerText = this.currentMetadata.title;

      const authorEl = document.getElementById('videoAuthorEl');
      if (authorEl) authorEl.innerText = `By ${this.currentMetadata.author} • ${dataPayload.duration || ''} • ${dataPayload.word_count || 0} words analyzed`;

      // Save to local history
      firebaseManager.saveVideoToHistory({
        video_id: videoId,
        metadata: this.currentMetadata,
        duration: dataPayload.duration,
        word_count: dataPayload.word_count
      });

      // Load initial summary
      await this.loadSummaryStyle('quick');
      AnimationEngine.showToast('Video transcript analyzed successfully! Grounded Chat enabled.', 'success');

    } catch (e) {
      console.error('Analyze error:', e);
      this.renderNoTranscriptState('Server connection error. Please ensure Flask server is running.');
      AnimationEngine.showToast('Failed to connect to backend server.', 'error');
    } finally {
      this.isAnalyzing = false;
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  renderNoTranscriptState(errorMessage) {
    this.hasTranscript = false;
    const panel = document.getElementById('summaryTabPanel');
    if (panel) {
      panel.innerHTML = `
        <div class="glass-card" style="border-color: rgba(255,8,68,0.3); text-align: center; padding: 3.5rem 2rem;">
          <span style="font-size: 3.5rem;">⚠️</span>
          <h3 style="font-size: 1.4rem; margin: 1rem 0 0.5rem 0; color: #ff4d4d;">No Transcript Available</h3>
          <p style="color: var(--text-secondary); max-width: 580px; margin: 0 auto 1.5rem auto; line-height: 1.6; font-size: 0.98rem;">
            ${errorMessage}
          </p>
          <p style="color: var(--text-muted); font-size: 0.88rem; margin-bottom: 2rem;">
            Summarize Chatbot requires closed captions to ground all AI answers and eliminate hallucinations.
          </p>
          <a href="/" class="btn btn-primary">Try Another Video 🚀</a>
        </div>
      `;
    }
  }

  switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content-panel').forEach(p => p.classList.remove('active'));

    const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    const targetPanel = document.getElementById(`${tabName}TabPanel`);

    if (targetBtn) targetBtn.classList.add('active');
    if (targetPanel) targetPanel.classList.add('active');

    if (tabName === 'summary' && !this.currentSummaryContent && this.hasTranscript) {
      this.loadSummaryStyle('quick');
    } else if (tabName === 'flashcards' && this.flashcardsData.length === 0 && this.hasTranscript) {
      this.generateAsset('flashcards');
    } else if (tabName === 'quiz' && this.quizData.length === 0 && this.hasTranscript) {
      this.generateAsset('quiz');
    }
  }

  async loadSummaryStyle(styleName) {
    if (!this.currentVideoId || !this.hasTranscript) return;

    AnimationEngine.showSkeleton('summaryTabPanel');

    try {
      const response = await fetch('/api/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_id: this.currentVideoId, style: styleName })
      });

      const resJson = await response.json();
      const isSuccess = resJson.success;
      const payload = resJson.data || resJson;

      if (isSuccess && payload.content) {
        this.currentSummaryContent = payload.content;
        this.renderSummaryPanel(payload.content);
      } else {
        AnimationEngine.showToast(resJson.error || 'Could not load analysis style.', 'error');
      }
    } catch (e) {
      console.error('Summary style error:', e);
      AnimationEngine.showToast('Error loading summary.', 'error');
    }
  }

  renderSummaryPanel(markdownContent) {
    const panel = document.getElementById('summaryTabPanel');
    if (!panel) return;

    let formattedContent = markdownContent.replace(/\[(\d{2}:\d{2}(?::\d{2})?)\]/g, (match, p1) => {
      return `<a class="timestamp-link" onclick="YouTubeHelper.seekIframeToTimestamp('ytPlayer', '${p1}')">⏱️ ${p1}</a>`;
    });

    formattedContent = formattedContent
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

    panel.innerHTML = `
      <div class="voice-bar">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <button class="btn btn-secondary btn-icon" onclick="voiceReader.speak(studioController.currentSummaryContent)" title="Read Aloud">🔊</button>
          <button class="btn btn-secondary btn-icon" onclick="voiceReader.stop()" title="Stop Audio">⏹️</button>
          <span style="font-size: 0.85rem; color: var(--text-secondary);">Voice Output</span>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-secondary" onclick="ExportEngine.copyToClipboard(studioController.currentSummaryContent, 'Summary')">📋 Copy</button>
          <button class="btn btn-secondary" onclick="ExportEngine.exportMarkdown(studioController.currentMetadata?.title || 'Video', studioController.currentSummaryContent)">📥 Export MD</button>
          <button class="btn btn-secondary" onclick="ExportEngine.exportPDF(studioController.currentMetadata?.title || 'Video', studioController.currentSummaryContent)">📄 Export PDF</button>
        </div>
      </div>
      <div class="glass-card" style="line-height: 1.7; font-size: 1.02rem;">
        ${formattedContent}
      </div>
    `;
  }

  async handleUserChatMessage() {
    if (this.isChatting) return;

    if (!this.currentVideoId) {
      AnimationEngine.showToast('Please paste and analyze a YouTube video link first.', 'info');
      return;
    }

    if (!this.hasTranscript) {
      this.appendChatBubble('assistant', 'No transcript available for this video.');
      return;
    }

    const input = document.getElementById('chatInputField');
    if (!input || !input.value.trim()) return;

    const question = input.value.trim();
    this.lastQuestion = question;
    input.value = '';

    this.isChatting = true;
    const sendBtn = document.querySelector('#chatForm button[type="submit"]');
    if (sendBtn) sendBtn.disabled = true;
    input.disabled = true;

    this.appendChatBubble('user', question);
    const typingId = this.appendTypingIndicator();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: this.currentVideoId,
          question: question
        })
      });

      const resJson = await response.json();
      this.removeTypingIndicator(typingId);

      const isSuccess = resJson.success;
      const payload = resJson.data || resJson;

      if (isSuccess && payload.answer) {
        this.appendChatBubbleStreaming('assistant', payload.answer);
      } else {
        const errorMsg = resJson.error || "No transcript available for this video.";
        this.appendChatBubble('assistant', errorMsg);
      }
    } catch (e) {
      console.error('Chat error:', e);
      this.removeTypingIndicator(typingId);
      this.appendChatBubble('assistant', 'Connection error. Please ensure Flask server is running.');
    } finally {
      this.isChatting = false;
      if (sendBtn) sendBtn.disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  appendChatBubble(role, content) {
    const container = document.getElementById('chatMessagesContainer');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    const avatarText = role === 'user' ? 'U' : 'AI';

    let formattedContent = content.replace(/\[(\d{2}:\d{2}(?::\d{2})?)\]/g, (match, p1) => {
      return `<a class="timestamp-link" onclick="YouTubeHelper.seekIframeToTimestamp('ytPlayer', '${p1}')">⏱️ ${p1}</a>`;
    });

    formattedContent = formattedContent
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    const contentDiv = document.createElement('div');
    contentDiv.className = 'chat-content';
    contentDiv.innerHTML = formattedContent;

    if (role === 'assistant') {
      const actionDiv = document.createElement('div');
      actionDiv.style.cssText = 'margin-top: 0.65rem; display: flex; gap: 0.5rem;';
      const copyBtn = document.createElement('button');
      copyBtn.className = 'btn btn-secondary';
      copyBtn.style.cssText = 'padding: 0.25rem 0.6rem; font-size: 0.78rem; border-radius: var(--radius-full);';
      copyBtn.innerHTML = '📋 Copy Text';
      copyBtn.addEventListener('click', () => ExportEngine.copyToClipboard(content, 'Answer'));
      actionDiv.appendChild(copyBtn);
      contentDiv.appendChild(actionDiv);
    }

    bubble.innerHTML = `<div class="chat-avatar">${avatarText}</div>`;
    bubble.appendChild(contentDiv);

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  appendChatBubbleStreaming(role, content) {
    const container = document.getElementById('chatMessagesContainer');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'chat-content';
    
    bubble.innerHTML = `<div class="chat-avatar">AI</div>`;
    bubble.appendChild(contentDiv);
    container.appendChild(bubble);

    AnimationEngine.typeText(contentDiv, content, 10, () => {
      let formatted = content.replace(/\[(\d{2}:\d{2}(?::\d{2})?)\]/g, (match, p1) => {
        return `<a class="timestamp-link" onclick="YouTubeHelper.seekIframeToTimestamp('ytPlayer', '${p1}')">⏱️ ${p1}</a>`;
      });
      formatted = formatted
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
      
      contentDiv.innerHTML = formatted;

      if (role === 'assistant') {
        const actionDiv = document.createElement('div');
        actionDiv.style.cssText = 'margin-top: 0.65rem; display: flex; gap: 0.5rem;';
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-secondary';
        copyBtn.style.cssText = 'padding: 0.25rem 0.6rem; font-size: 0.78rem; border-radius: var(--radius-full);';
        copyBtn.innerHTML = '📋 Copy Text';
        copyBtn.addEventListener('click', () => ExportEngine.copyToClipboard(content, 'Answer'));
        actionDiv.appendChild(copyBtn);
        contentDiv.appendChild(actionDiv);
      }
    });

    container.scrollTop = container.scrollHeight;
  }

  appendTypingIndicator() {
    const container = document.getElementById('chatMessagesContainer');
    if (!container) return null;

    const id = 'typing_' + Date.now();
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'chat-bubble assistant';
    bubble.innerHTML = `
      <div class="chat-avatar">AI</div>
      <div class="chat-content">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return id;
  }

  removeTypingIndicator(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  regenerateLastResponse() {
    if (this.lastQuestion) {
      document.getElementById('chatInputField').value = this.lastQuestion;
      this.handleUserChatMessage();
    } else {
      AnimationEngine.showToast('No previous question to regenerate.', 'info');
    }
  }

  clearChatHistory() {
    const container = document.getElementById('chatMessagesContainer');
    if (container) {
      container.innerHTML = `
        <div class="chat-bubble assistant">
          <div class="chat-avatar">AI</div>
          <div class="chat-content">
            Conversation cleared. How can I assist you with this video transcript?
          </div>
        </div>
      `;
      AnimationEngine.showToast('Chat cleared.', 'info');
    }
  }

  async generateAsset(assetType) {
    if (!this.currentVideoId || !this.hasTranscript) return;

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_id: this.currentVideoId, asset_type: assetType })
      });

      const resJson = await response.json();
      const isSuccess = resJson.success;
      const payload = resJson.data || resJson;

      if (isSuccess && payload) {
        if (assetType === 'flashcards' && Array.isArray(payload.data)) {
          this.flashcardsData = payload.data;
          this.renderFlashcard();
        } else if (assetType === 'quiz' && Array.isArray(payload.data)) {
          this.quizData = payload.data;
          this.currentQuizIndex = 0;
          this.quizScore = 0;
          this.renderQuizQuestion();
        }
      }
    } catch (e) {
      console.error('Asset error:', e);
    }
  }

  renderFlashcard() {
    const panel = document.getElementById('flashcardsTabPanel');
    if (!panel || this.flashcardsData.length === 0) return;

    const card = this.flashcardsData[this.currentCardIndex];
    panel.innerHTML = `
      <div style="text-align: center; margin-bottom: 1rem;">
        <span class="hero-tag">Flashcard ${this.currentCardIndex + 1} of ${this.flashcardsData.length}</span>
      </div>
      <div class="flashcard-wrapper" id="flashcardDeck" onclick="this.classList.toggle('flipped')">
        <div class="flashcard-inner">
          <div class="flashcard-front">
            <div class="flashcard-label">Question (Click to Flip 🔄)</div>
            <div class="flashcard-text">${card.question}</div>
          </div>
          <div class="flashcard-back">
            <div class="flashcard-label">Answer</div>
            <div class="flashcard-text">${card.answer}</div>
          </div>
        </div>
      </div>
      <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
        <button class="btn btn-secondary" onclick="studioController.prevCard()">⬅️ Previous</button>
        <button class="btn btn-primary" onclick="studioController.nextCard()">Next ➡️</button>
      </div>
    `;
  }

  prevCard() {
    if (this.currentCardIndex > 0) {
      this.currentCardIndex--;
      this.renderFlashcard();
    }
  }

  nextCard() {
    if (this.currentCardIndex < this.flashcardsData.length - 1) {
      this.currentCardIndex++;
      this.renderFlashcard();
    }
  }

  renderQuizQuestion() {
    const panel = document.getElementById('quizTabPanel');
    if (!panel || this.quizData.length === 0) return;

    if (this.currentQuizIndex >= this.quizData.length) {
      panel.innerHTML = `
        <div class="glass-card" style="text-align: center; padding: 3rem;">
          <h2 style="font-size: 2rem; margin-bottom: 1rem;">🏆 Quiz Completed!</h2>
          <p style="font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 2rem;">
            You scored <strong style="color: var(--accent-cyan);">${this.quizScore}</strong> out of <strong>${this.quizData.length}</strong>!
          </p>
          <button class="btn btn-primary" onclick="studioController.generateAsset('quiz')">🔄 Retry Quiz</button>
        </div>
      `;
      return;
    }

    const q = this.quizData[this.currentQuizIndex];
    let optionsHtml = '';
    q.options.forEach((opt, idx) => {
      optionsHtml += `<button class="quiz-option-btn" onclick="studioController.checkQuizAnswer(${idx}, this)">${opt}</button>`;
    });

    panel.innerHTML = `
      <div class="quiz-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <span class="hero-tag">Question ${this.currentQuizIndex + 1} / ${this.quizData.length}</span>
          <span style="font-weight: 600; color: var(--accent-cyan);">Score: ${this.quizScore}</span>
        </div>
        <div class="glass-card">
          <h3 style="font-size: 1.2rem; margin-bottom: 1.5rem;">${q.question}</h3>
          <div id="quizOptionsContainer">${optionsHtml}</div>
          <div id="quizExplanationBox" style="display: none; margin-top: 1.25rem; padding: 1rem; background: rgba(0,242,254,0.1); border-radius: 10px; font-size: 0.95rem;"></div>
          <div style="display: flex; justify-content: flex-end; margin-top: 1.5rem;">
            <button id="quizNextBtn" class="btn btn-primary" style="display: none;" onclick="studioController.nextQuizQuestion()">Next Question ➡️</button>
          </div>
        </div>
      </div>
    `;
  }

  checkQuizAnswer(selectedIndex, btnElement) {
    const q = this.quizData[this.currentQuizIndex];
    const container = document.getElementById('quizOptionsContainer');
    if (!container) return;

    container.querySelectorAll('.quiz-option-btn').forEach(btn => btn.disabled = true);

    if (selectedIndex === q.correct_index) {
      btnElement.classList.add('correct');
      this.quizScore++;
    } else {
      btnElement.classList.add('incorrect');
      container.children[q.correct_index].classList.add('correct');
    }

    const expBox = document.getElementById('quizExplanationBox');
    if (expBox) {
      expBox.style.display = 'block';
      expBox.innerHTML = `💡 <strong>Explanation</strong>: ${q.explanation}`;
    }

    const nextBtn = document.getElementById('quizNextBtn');
    if (nextBtn) nextBtn.style.display = 'inline-flex';
  }

  nextQuizQuestion() {
    this.currentQuizIndex++;
    this.renderQuizQuestion();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.studioController = new StudioController();
});
