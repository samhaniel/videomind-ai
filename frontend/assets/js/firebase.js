/**
 * VideoMind AI - Firebase & Local Storage Data Manager
 */

class FirebaseManager {
  constructor() {
    this.storageKey = 'videomind_local_history';
    this.favoritesKey = 'videomind_favorites';
    this.userKey = 'videomind_user_id';
    this.initUser();
  }

  initUser() {
    let uid = localStorage.getItem(this.userKey);
    if (!uid) {
      uid = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem(this.userKey, uid);
    }
    this.userId = uid;
  }

  getUserId() {
    return this.userId;
  }

  saveVideoToHistory(videoData) {
    let history = this.getLocalHistory();
    history = history.filter(item => item.video_id !== videoData.video_id);
    history.unshift({
      video_id: videoData.video_id,
      title: videoData.metadata?.title || 'YouTube Video',
      author: videoData.metadata?.author || 'Creator',
      thumbnail_url: videoData.metadata?.thumbnail_url || '',
      url: videoData.metadata?.url || '',
      duration: videoData.duration || '00:00',
      timestamp: Date.now()
    });

    if (history.length > 50) history = history.slice(0, 50);
    localStorage.setItem(this.storageKey, JSON.stringify(history));
  }

  getLocalHistory() {
    try {
      return JSON.parse(localStorage.getItem(this.storageKey)) || [];
    } catch (e) {
      return [];
    }
  }

  clearHistory() {
    localStorage.removeItem(this.storageKey);
  }

  deleteHistoryItem(videoId) {
    let history = this.getLocalHistory();
    history = history.filter(item => item.video_id !== videoId);
    localStorage.setItem(this.storageKey, JSON.stringify(history));
  }

  toggleFavorite(videoId) {
    let favs = this.getFavorites();
    if (favs.includes(videoId)) {
      favs = favs.filter(id => id !== videoId);
    } else {
      favs.push(videoId);
    }
    localStorage.setItem(this.favoritesKey, JSON.stringify(favs));
    return favs.includes(videoId);
  }

  getFavorites() {
    try {
      return JSON.parse(localStorage.getItem(this.favoritesKey)) || [];
    } catch (e) {
      return [];
    }
  }
}

window.firebaseManager = new FirebaseManager();
