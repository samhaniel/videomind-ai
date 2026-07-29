/**
 * VideoMind AI - User Preferences & Settings Manager
 */

class AuthManager {
  constructor() {
    this.settingsKey = 'videomind_settings';
    this.loadSettings();
    this.applyTheme();
  }

  loadSettings() {
    const defaultSettings = {
      theme: 'dark',
      defaultSummaryStyle: 'quick',
      expertMode: false,
      voiceSpeed: 1.0,
      customApiKey: ''
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
  }

  getSetting(key) {
    return this.settings[key];
  }
}

window.authManager = new AuthManager();
