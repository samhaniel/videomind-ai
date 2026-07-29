/**
 * VideoMind AI - Micro-animations, Skeleton Loaders & Toast Engine
 */

class AnimationEngine {
  static showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';
    
    toast.innerHTML = `<span style="font-size: 1.1rem;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%) scale(0.9)';
      toast.style.transition = 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)';
      setTimeout(() => toast.remove(), 350);
    }, 3500);
  }

  static typeText(element, text, speed = 12, onComplete = null) {
    element.innerHTML = '';
    let index = 0;
    
    function step() {
      if (index < text.length) {
        element.innerHTML += text.charAt(index);
        index++;
        setTimeout(step, speed);
      } else {
        if (onComplete) onComplete();
      }
    }
    step();
  }

  static showSkeleton(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem; padding: 1.25rem;">
        <div class="skeleton" style="height: 36px; width: 45%; border-radius: var(--radius-md);"></div>
        <div class="skeleton" style="height: 20px; width: 90%; border-radius: var(--radius-sm);"></div>
        <div class="skeleton" style="height: 20px; width: 85%; border-radius: var(--radius-sm);"></div>
        <div class="skeleton" style="height: 160px; width: 100%; border-radius: var(--radius-lg);"></div>
      </div>
    `;
  }
}

window.AnimationEngine = AnimationEngine;
