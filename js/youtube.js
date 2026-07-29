/**
 * VideoMind AI - YouTube URL Parser & Embedded Player Helper
 */

class YouTubeHelper {
  static extractVideoId(url) {
    if (!url) return null;
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|shorts\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  }

  static getEmbedUrl(videoId, startSeconds = 0) {
    return `https://www.youtube.com/embed/${videoId}?autoplay=1&enablejsapi=1&start=${Math.floor(startSeconds)}`;
  }

  static parseTimestampToSeconds(tsStr) {
    if (!tsStr) return 0;
    const parts = tsStr.replace('[', '').replace(']', '').trim().split(':');
    try {
      if (parts.length === 3) {
        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseFloat(parts[2]);
      } else if (parts.length === 2) {
        return parseInt(parts[0]) * 60 + parseFloat(parts[1]);
      } else if (parts.length === 1) {
        return parseFloat(parts[0]);
      }
    } catch (e) {
      console.warn('Timestamp parse error', e);
    }
    return 0;
  }

  static seekIframeToTimestamp(iframeId, tsStr) {
    const iframe = document.getElementById(iframeId);
    if (!iframe) return;
    const seconds = this.parseTimestampToSeconds(tsStr);
    
    // Send postMessage to YouTube iframe API
    try {
      iframe.contentWindow.postMessage(JSON.stringify({
        event: 'command',
        func: 'seekTo',
        args: [seconds, true]
      }), '*');
    } catch (e) {
      console.warn('Could not postMessage seekTo iframe', e);
    }
  }
}

window.YouTubeHelper = YouTubeHelper;
