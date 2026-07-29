/**
 * VideoMind AI - Application Controller & Theme Manager
 */

class AppManager {
  constructor() {
    this.settingsKey = 'videomind_settings';
    this.init();
  }

  init() {
    this.loadSettings();
    this.applyTheme();
    this.initThemeToggle();
  }

  loadSettings() {
    const defaultSettings = {
      theme: 'dark',
      voiceSpeed: 1.0,
      expertMode: false
    };
    try {
      const saved = JSON.parse(localStorage.getItem(this.settingsKey));
      this.settings = { ...defaultSettings, ...saved };
    } catch (e) {
      this.settings = defaultSettings;
    }
  }

  saveSettings(newSettings) {
    this.settings = { ...this.settings, ...newSettings };
    localStorage.setItem(this.settingsKey, JSON.stringify(this.settings));
    this.applyTheme();
  }

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.settings.theme || 'dark');
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
      themeSelect.value = this.settings.theme || 'dark';
    }
  }

  toggleTheme() {
    const newTheme = this.settings.theme === 'light' ? 'dark' : 'light';
    this.saveSettings({ theme: newTheme });
  }

  initThemeToggle() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => this.toggleTheme());
      themeToggleBtn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggleTheme();
        }
      });
    }
  }
}

window.appManager = new AppManager();
