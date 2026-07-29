import os
import json
import logging
from typing import Dict, Any, List, Optional
from utils import search_relevant_chunks
from summary import get_gemini_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATES = {
    "quick": "You are VideoMind AI. Provide a **Quick Summary** (3-4 sentences) based strictly on the spoken video transcript:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "detailed": "You are VideoMind AI. Provide a **Detailed Structured Summary** of this video transcript with section headings and timestamps `[MM:SS]`:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "bullet": "You are VideoMind AI. Provide a **Bullet Point Summary** (8-12 high-impact key points) of this spoken video content:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "takeaways": "You are VideoMind AI. List the top 10 **Key Takeaways & Lessons** from this video transcript:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "timeline": "You are VideoMind AI. Generate a **Timestamped Timeline & Chapter Breakdown** (`[MM:SS] Topic`):\n\nTitle: {title}\nTranscript:\n{transcript}",
    "topics": "You are VideoMind AI. Identify and explain all **Important Topics & Core Themes** discussed in this video:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "definitions": "You are VideoMind AI. Extract all **Important Definitions, Jargon, and Terminology** explained in this video:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "action": "You are VideoMind AI. Extract all **Action Points, Practical Tasks, and Key Steps** mentioned in this video transcript:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "notes": "You are VideoMind AI. Generate comprehensive **Learning & Study Notes** from this video transcript:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "faqs": "You are VideoMind AI. Create a **Frequently Asked Questions (FAQs)** guide with answers based on this video:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "interview": "You are VideoMind AI. Generate 8 **Interview Questions & Answers** based on the technical/conceptual knowledge shared in this video:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "quotes": "You are VideoMind AI. Extract the most **Important Quotes & Statements** spoken in this video with timestamps:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "technical": "You are VideoMind AI. Provide an in-depth **Technical & Architectural Breakdown** of this video transcript:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "beginner": "You are VideoMind AI. Provide a clear **Beginner Explanation** of this video transcript without complex jargon:\n\nTitle: {title}\nTranscript:\n{transcript}",
    "eli5": "You are VideoMind AI. **Explain Like I'm 10 (ELI5)** using fun analogies and simple stories:\n\nTitle: {title}\nTranscript:\n{transcript}"
}

CHAT_STRICT_PROMPT = """You are VideoMind AI, a specialized Video Intelligence Assistant.

STRICT GROUNDING RULES:
1. Answer the user's question ONLY using the provided Video Transcript context.
2. If the information is not mentioned in the transcript, you MUST reply: "I couldn't find this information in the analyzed video."
3. DO NOT hallucinate, invent details, or use outside knowledge.
4. Cite specific timestamps (e.g. `[03:15]`) whenever referring to specific points in the transcript.

Video Title: {title}

Transcript Context:
{context}

User Question:
{question}"""

class ChatService:
    @staticmethod
    def generate_analysis(title: str, transcript_text: str, style: str = "quick") -> Dict[str, Any]:
        """Generate requested analysis style using Gemini 2.5 Flash with fallback."""
        style_key = style.lower().strip()
        template = PROMPT_TEMPLATES.get(style_key, PROMPT_TEMPLATES["quick"])
        
        prompt = template.format(title=title, transcript=transcript_text[:40000])
        client, sdk_type = get_gemini_client()
        
        if client:
            try:
                if sdk_type == "genai":
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    if res and res.text:
                        return {"success": True, "style": style_key, "content": res.text.strip(), "source": "gemini-ai"}
                elif sdk_type == "legacy":
                    res = client.generate_content(prompt)
                    if res and res.text:
                        return {"success": True, "style": style_key, "content": res.text.strip(), "source": "gemini-ai"}
            except Exception as e:
                logger.error(f"Gemini error generating analysis style {style_key}: {str(e)}")

        # Fallback content generator
        from summary import build_algorithmic_summary
        fallback = build_algorithmic_summary(title, transcript_text, style_key)
        return {"success": True, "style": style_key, "content": fallback, "source": "videomind-engine"}

    @staticmethod
    def answer_question(title: str, chunks: List[Dict[str, Any]], question: str) -> Dict[str, Any]:
        """Strict grounded Q&A strictly from analyzed video transcript."""
        relevant_chunks = search_relevant_chunks(question, chunks, top_k=5)
        
        context_text = "\n\n".join([f"[{c['timestamp_formatted']}] {c['text']}" for c in relevant_chunks])
        if not context_text:
            return {
                "success": True,
                "answer": "I couldn't find this information in the analyzed video.",
                "relevant_timestamps": []
            }
            
        prompt = CHAT_STRICT_PROMPT.format(title=title, context=context_text[:35000], question=question)
        client, sdk_type = get_gemini_client()
        
        if client:
            try:
                if sdk_type == "genai":
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    if res and res.text:
                        return {
                            "success": True,
                            "answer": res.text.strip(),
                            "relevant_timestamps": [c['timestamp_formatted'] for c in relevant_chunks],
                            "source": "gemini-rag"
                        }
                elif sdk_type == "legacy":
                    res = client.generate_content(prompt)
                    if res and res.text:
                        return {
                            "success": True,
                            "answer": res.text.strip(),
                            "relevant_timestamps": [c['timestamp_formatted'] for c in relevant_chunks],
                            "source": "gemini-rag"
                        }
            except Exception as e:
                logger.error(f"Gemini error in Q&A: {str(e)}")

        from chat import generate_fallback_answer
        fallback_ans = generate_fallback_answer(question, title, relevant_chunks)
        return {
            "success": True,
            "answer": fallback_ans,
            "relevant_timestamps": [c['timestamp_formatted'] for c in relevant_chunks],
            "source": "videomind-grounded"
        }

chat_service = ChatService()
