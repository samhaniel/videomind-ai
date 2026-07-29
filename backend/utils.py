import re
import math
from typing import List, Dict, Any

def extract_youtube_id(url: str) -> str:
    """Extract 11-character YouTube video ID from various URL formats."""
    if not url:
        return ""
    
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|shorts\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    return ""

def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS or HH:MM:SS format."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def parse_timestamp_to_seconds(ts_str: str) -> float:
    """Parse MM:SS or HH:MM:SS string to seconds."""
    parts = ts_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    return 0.0

def chunk_transcript(transcript_items: List[Dict[str, Any]], chunk_size: int = 1500, overlap: int = 200) -> List[Dict[str, Any]]:
    """Group transcript items into overlapping chunks with timestamp metadata."""
    if not transcript_items:
        return []
        
    chunks = []
    current_chunk_text = []
    current_length = 0
    start_time = transcript_items[0].get("start", 0)
    
    for item in transcript_items:
        text = item.get("text", "").strip()
        if not text:
            continue
            
        current_chunk_text.append(text)
        current_length += len(text)
        
        if current_length >= chunk_size:
            chunk_full_text = " ".join(current_chunk_text)
            chunks.append({
                "text": chunk_full_text,
                "start_time": start_time,
                "end_time": item.get("start", 0) + item.get("duration", 0),
                "timestamp_formatted": format_timestamp(start_time)
            })
            
            # Carry over overlap
            overlap_items = []
            accumulated = 0
            for prev_item in reversed(current_chunk_text):
                accumulated += len(prev_item)
                overlap_items.insert(0, prev_item)
                if accumulated >= overlap:
                    break
            
            current_chunk_text = overlap_items
            current_length = sum(len(t) for t in current_chunk_text)
            start_time = item.get("start", 0)
            
    if current_chunk_text:
        chunk_full_text = " ".join(current_chunk_text)
        last_item = transcript_items[-1]
        chunks.append({
            "text": chunk_full_text,
            "start_time": start_time,
            "end_time": last_item.get("start", 0) + last_item.get("duration", 0),
            "timestamp_formatted": format_timestamp(start_time)
        })
        
    return chunks

def search_relevant_chunks(query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform keyword/semantic relevance scoring between query and transcript chunks."""
    if not chunks:
        return []
        
    query_words = set(re.findall(r'\w+', query.lower()))
    if not query_words:
        return chunks[:top_k]
        
    scored_chunks = []
    for chunk in chunks:
        chunk_words = re.findall(r'\w+', chunk["text"].lower())
        word_counts = {}
        for word in chunk_words:
            word_counts[word] = word_counts.get(word, 0) + 1
            
        score = 0.0
        for qw in query_words:
            if qw in word_counts:
                # TF score component
                tf = word_counts[qw] / len(chunk_words)
                score += (tf + 1.0) * (len(qw) ** 0.5)
                
        scored_chunks.append((score, chunk))
        
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Filter out chunks with 0 score if we have non-zero results, else take top_k
    non_zero = [c for s, c in scored_chunks if s > 0]
    if non_zero:
        return non_zero[:top_k]
    return [c for s, c in scored_chunks[:top_k]]
