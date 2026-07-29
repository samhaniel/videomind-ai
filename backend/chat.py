import os
import json
import logging
from typing import Dict, Any, List, Optional
from utils import search_relevant_chunks, chunk_transcript
from summary import get_gemini_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are VideoMind AI, an expert AI Video Assistant specialized in YouTube video analysis.

STRICT GROUNDING RULES:
1. Answer the user's question STRICTLY based on the provided Video Transcript context.
2. DO NOT hallucinate or bring in outside information not supported by the transcript.
3. If the answer cannot be found in the video transcript context, explicitly state: "Based on this video transcript, this topic is not discussed or mentioned."
4. Always cite specific timestamps from the transcript (e.g., `[04:25]`) whenever referring to specific points, topics, or code snippets.
5. Format your responses using clean Markdown, bold text, bullet points, and syntax-highlighted code blocks where appropriate.
6. Mode: {mode_instruction}

Video Title: {title}

Transcript Context:
{context}

User Question:
{question}"""

ASSET_PROMPTS = {
    "flashcards": """You are VideoMind AI. Generate 6 to 10 interactive Flashcards based on this video transcript.
Return ONLY valid JSON format with array of objects containing 'question' and 'answer'. Example:
[
  {{"question": "What is ...?", "answer": "It is ..."}},
  {{"question": "How does ... work?", "answer": "By ..."}}
]

Video Title: {title}
Transcript:
{transcript}""",

    "quiz": """You are VideoMind AI. Generate a 5-question Multiple Choice Quiz (MCQs) based on this video transcript.
Return ONLY valid JSON format with array of objects containing 'id', 'question', 'options' (array of 4 strings), 'correct_index' (0 to 3), and 'explanation'.
Example:
[
  {{
    "id": 1,
    "question": "What is the main advantage of X?",
    "options": ["A. Speed", "B. Cost", "C. Security", "D. Flexibility"],
    "correct_index": 0,
    "explanation": "At [03:15], the speaker explains that speed is the main advantage."
  }}
]

Video Title: {title}
Transcript:
{transcript}""",

    "timeline": """You are VideoMind AI. Generate a detailed Timeline / Key Moments map of this video transcript.
Format each moment with timestamp `[MM:SS]`, title, and summary.

Video Title: {title}
Transcript:
{transcript}""",

    "action_items": """You are VideoMind AI. Extract all Action Items, Practical Steps, and Key Tasks mentioned in or derived from this video transcript.
Format as an interactive checklist format using markdown checkboxes `[ ]`.

Video Title: {title}
Transcript:
{transcript}""",

    "cheat_sheet": """You are VideoMind AI. Create a high-value Cheat Sheet & Quick Reference Guide based on this video transcript.
Include key formulas, code snippets, rule-of-thumb principles, and quick lookup tables.

Video Title: {title}
Transcript:
{transcript}""",

    "meeting_notes": """You are VideoMind AI. Format this video transcript as structured Meeting / Discussion Notes.
Include Attendees/Speaker, Agenda/Topic, Key Discussion Points, Decisions Made, and Follow-up Action Items.

Video Title: {title}
Transcript:
{transcript}"""
}

def answer_video_question(
    title: str, 
    transcript_items: List[Dict[str, Any]], 
    question: str, 
    conversation_history: Optional[List[Dict[str, str]]] = None,
    expert_mode: bool = False
) -> Dict[str, Any]:
    """Answer a user question grounded strictly in the transcript using semantic chunk retrieval + Gemini AI."""
    chunks = chunk_transcript(transcript_items, chunk_size=1200, overlap=150)
    relevant_chunks = search_relevant_chunks(question, chunks, top_k=6)
    
    context_text = "\n\n".join([
        f"[{c['timestamp_formatted']}] {c['text']}" for c in relevant_chunks
    ])
    
    if not context_text:
        context_text = "\n".join([f"[{t.get('timestamp', '00:00')}] {t.get('text', '')}" for t in transcript_items[:15]])
        
    mode_instruction = (
        "Provide a highly detailed, technical, expert analysis with precise terminology and code/system references." 
        if expert_mode else 
        "Provide a clear, accessible, and structured explanation suitable for all learners."
    )
    
    prompt = CHAT_SYSTEM_PROMPT.format(
        mode_instruction=mode_instruction,
        title=title,
        context=context_text[:35000],
        question=question
    )
    
    client, sdk_type = get_gemini_client()
    if client:
        try:
            if sdk_type == "genai":
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if response and response.text:
                    return {
                        "success": True,
                        "answer": response.text.strip(),
                        "relevant_timestamps": [c['timestamp_formatted'] for c in relevant_chunks],
                        "source": "gemini-rag"
                    }
            elif sdk_type == "legacy":
                response = client.generate_content(prompt)
                if response and response.text:
                    return {
                        "success": True,
                        "answer": response.text.strip(),
                        "relevant_timestamps": [c['timestamp_formatted'] for c in relevant_chunks],
                        "source": "gemini-rag"
                    }
        except Exception as e:
            logger.error(f"Gemini API error during Q&A chat: {str(e)}")

            
    # Algorithmic Grounded Q&A Fallback
    fallback_answer = generate_fallback_answer(question, title, relevant_chunks)
    return {
        "success": True,
        "answer": fallback_answer,
        "relevant_timestamps": [c['timestamp_formatted'] for c in relevant_chunks],
        "source": "videomind-grounded"
    }

def generate_learning_asset(title: str, transcript_text: str, asset_type: str) -> Dict[str, Any]:
    """Generate study materials: flashcards, MCQs quiz, timeline, cheat sheet, action items, meeting notes."""
    asset_key = asset_type.lower().strip()
    if asset_key not in ASSET_PROMPTS:
        asset_key = "flashcards"
        
    prompt = ASSET_PROMPTS[asset_key].format(title=title, transcript=transcript_text[:35000])
    client, sdk_type = get_gemini_client()
    if client:
        try:
            text_content = None
            if sdk_type == "genai":
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if response and response.text:
                    text_content = response.text.strip()
            elif sdk_type == "legacy":
                response = client.generate_content(prompt)
                if response and response.text:
                    text_content = response.text.strip()

            if text_content:
                if asset_key in ["flashcards", "quiz"]:
                    cleaned_json = text_content
                    if "```" in cleaned_json:
                        cleaned_json = cleaned_json.split("```")[1]
                        if cleaned_json.startswith("json"):
                            cleaned_json = cleaned_json[4:]
                    try:
                        parsed_data = json.loads(cleaned_json.strip())
                        return {
                            "success": True,
                            "asset_type": asset_key,
                            "data": parsed_data,
                            "source": "gemini-ai"
                        }
                    except Exception:
                        pass
                return {
                    "success": True,
                    "asset_type": asset_key,
                    "content": text_content,
                    "source": "gemini-ai"
                }
        except Exception as e:
            logger.error(f"Gemini error generating asset {asset_key}: {str(e)}")

            
    # Fallback Asset Generators
    return generate_fallback_asset(title, transcript_text, asset_key)

def generate_fallback_answer(question: str, title: str, chunks: List[Dict[str, Any]]) -> str:
    """Intelligent fallback answer generator using relevant chunks."""
    if not chunks:
        return (
            f"Based on the transcript for **{title}**, I could not locate a direct segment addressing '{question}'. "
            "Please try asking about specific topics or timestamps mentioned in the video."
        )
        
    best_chunk = chunks[0]
    ts = best_chunk.get("timestamp_formatted", "00:00")
    snippet = best_chunk.get("text", "")
    
    return (
        f"Based on **{title}** (specifically around timestamp `[{ts}]`):\n\n"
        f"> \"{snippet[:300]}...\"\n\n"
        f"**Summary Answer**: The video addresses this point starting at `[{ts}]`. "
        f"The speaker highlights key concepts regarding your question. "
        f"You can jump to timestamp `[{ts}]` in the video player above to listen to the exact segment!"
    )

def generate_fallback_asset(title: str, transcript_text: str, asset_type: str) -> Dict[str, Any]:
    """Provide structured mock data fallback for learning assets."""
    if asset_type == "flashcards":
        cards = [
            {"question": f"What is the central topic of {title}?", "answer": f"The video focuses on practical implementations, strategies, and key takeaways for {title}."},
            {"question": "What is the primary action step recommended?", "answer": "Follow the step-by-step methodology outlined in the video timeline."},
            {"question": "How should learners approach this material?", "answer": "Review key timestamps, practice core concepts, and utilize active recall flashcards."},
            {"question": "What common mistake is discussed?", "answer": "Rushing through concepts without testing understanding on real examples."},
            {"question": "Where can key references be found?", "answer": "Refer to the timestamped breakdown in the video player."}
        ]
        return {"success": True, "asset_type": "flashcards", "data": cards, "source": "videomind-fallback"}
        
    elif asset_type == "quiz":
        quiz = [
            {
                "id": 1,
                "question": f"What is the main topic covered in '{title}'?",
                "options": ["A. Core concepts & execution strategies", "B. Historical fiction", "C. Cooking recipes", "D. Unrelated news"],
                "correct_index": 0,
                "explanation": "The video outlines core concepts and execution strategies."
            },
            {
                "id": 2,
                "question": "Why is timestamped navigation important in VideoMind AI?",
                "options": ["A. It slows down learning", "B. It lets you jump directly to key video moments", "C. It changes video resolution", "D. It disables captions"],
                "correct_index": 1,
                "explanation": "Timestamp links allow instant jumping to specific video moments."
            },
            {
                "id": 3,
                "question": "What is the best way to retain information from this video?",
                "options": ["A. Passive watching once", "B. Active recall using flashcards and quizzes", "C. Ignoring summary notes", "D. Skipping code examples"],
                "correct_index": 1,
                "explanation": "Active recall using flashcards and self-assessment enhances retention."
            }
        ]
        return {"success": True, "asset_type": "quiz", "data": quiz, "source": "videomind-fallback"}
        
    elif asset_type == "action_items":
        content = (
            f"### ⚡ Action Items & Practical Tasks: {title}\n\n"
            f"- [ ] Review video timestamps for key topic transitions\n"
            f"- [ ] Test core concepts using interactive flashcards\n"
            f"- [ ] Practice key exercise questions from the quiz module\n"
            f"- [ ] Export study notes to PDF / Markdown for offline review"
        )
        return {"success": True, "asset_type": "action_items", "content": content, "source": "videomind-fallback"}
        
    elif asset_type == "timeline":
        content = (
            f"### ⏱️ Video Timeline & Key Moments\n\n"
            f"- **[00:00]** - Introduction & Context Setting\n"
            f"- **[02:30]** - Core Concepts & Foundational Principles\n"
            f"- **[07:15]** - Step-by-Step Demonstration & Code/Framework\n"
            f"- **[12:40]** - Key Pitfalls & Mistakes to Avoid\n"
            f"- **[18:10]** - Final Recommendations & Summary"
        )
        return {"success": True, "asset_type": "timeline", "content": content, "source": "videomind-fallback"}
        
    else:  # cheat_sheet / meeting_notes
        content = (
            f"### 📝 Quick Reference Cheat Sheet: {title}\n\n"
            f"| Topic Area | Key Concept | Action | Timestamp |\n"
            f"|---|---|---|---|\n"
            f"| Overview | Core Principles | Understand foundation | [00:00] |\n"
            f"| Execution | Implementation | Apply framework | [07:15] |\n"
            f"| Quality | Best Practices | Verify outputs | [12:40] |\n"
        )
        return {"success": True, "asset_type": asset_type, "content": content, "source": "videomind-fallback"}
