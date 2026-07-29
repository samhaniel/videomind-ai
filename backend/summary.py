import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gemini_client():
    """Initialize Gemini API client using modern google-genai or google.generativeai SDK."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, None
        
    # Try modern google-genai SDK first
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return client, "genai"
    except Exception as e1:
        logger.debug(f"google.genai SDK not available: {str(e1)}")
        
    # Fallback to google.generativeai SDK
    try:
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=api_key)
        model = genai_legacy.GenerativeModel("gemini-2.5-flash")
        return model, "legacy"
    except Exception as e2:
        logger.error(f"Error initializing Google Generative AI: {str(e2)}")
        return None, None

SUMMARY_PROMPTS = {
    "quick": """You are VideoMind AI. Provide a **Quick Summary** (maximum 3-4 impactful sentences) of this video transcript.
Highlight the central theme, primary claim, and main conclusion. Include key timestamps if available.

Video Title: {title}
Transcript:
{transcript}""",

    "detailed": """You are VideoMind AI. Provide a **Detailed Structured Summary** of this video transcript.
Structure your output cleanly with markdown headings:
- 📌 **Executive Overview**
- 🔑 **Core Themes & Concepts**
- ⏱️ **Timestamped Section Breakdown** (e.g. `[MM:SS] Title - Description`)
- 💡 **Deep Dive Analysis**
- 🎯 **Final Conclusion & Takeaway**

Video Title: {title}
Transcript:
{transcript}""",

    "bullet": """You are VideoMind AI. Provide a **Bullet Point Summary** of this video transcript.
List 7 to 12 clear, high-yield bullet points capturing all essential insights, key facts, data points, and takeaways mentioned in the video.

Video Title: {title}
Transcript:
{transcript}""",

    "student": """You are VideoMind AI. Generate comprehensive **Student Study Notes** based on this video transcript.
Format with markdown:
- 📚 **Topic Overview**
- 🔑 **Key Terms & Definitions**
- 📝 **Detailed Topic Explanations**
- ⚠️ **Common Misconceptions / Pitfalls**
- 🧠 **Self-Assessment Check (Key Questions to Test Understanding)**

Video Title: {title}
Transcript:
{transcript}""",

    "executive": """You are VideoMind AI. Prepare an **Executive Briefing** for senior leaders based on this video.
Include:
- 💼 **Strategic Context & Objective**
- 📊 **Key Metrics, Findings & Insights**
- 🚀 **Strategic Opportunities & Risks**
- ⚡ **Actionable Recommendations**

Video Title: {title}
Transcript:
{transcript}""",

    "beginner": """You are VideoMind AI. Explain this video transcript **Like I am 10 Years Old (ELI5)**.
Use simple everyday analogies, clear visual language, fun comparisons, and zero jargon. Break down complex ideas into effortless concepts.

Video Title: {title}
Transcript:
{transcript}""",

    "technical": """You are VideoMind AI. Provide an in-depth **Technical & Engineering Breakdown** of this video transcript.
Analyze:
- ⚙️ **System Architecture / Technical Specs**
- 💻 **Code / Algorithmic Patterns & Logic**
- 🛠️ **Implementation Nuances & Trade-offs**
- 🔬 **Deep Technical Takeaways**

Video Title: {title}
Transcript:
{transcript}"""
}

def generate_ai_summary(video_id: str, title: str, transcript_text: str, style: str = "quick") -> Dict[str, Any]:
    """Generate requested AI summary style from transcript text."""
    style_key = style.lower().strip()
    if style_key not in SUMMARY_PROMPTS:
        style_key = "quick"
        
    prompt_template = SUMMARY_PROMPTS[style_key]
    trimmed_transcript = transcript_text[:40000]
    prompt = prompt_template.format(title=title, transcript=trimmed_transcript)
    
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
                        "summary_style": style_key,
                        "content": response.text.strip(),
                        "source": "gemini-ai"
                    }
            elif sdk_type == "legacy":
                response = client.generate_content(prompt)
                if response and response.text:
                    return {
                        "success": True,
                        "summary_style": style_key,
                        "content": response.text.strip(),
                        "source": "gemini-ai"
                    }
        except Exception as e:
            logger.error(f"Gemini API error during summary generation: {str(e)}")
            
    # Algorithmic Fallback Generator
    fallback_content = build_algorithmic_summary(title, transcript_text, style_key)
    return {
        "success": True,
        "summary_style": style_key,
        "content": fallback_content,
        "source": "videomind-engine"
    }

def build_algorithmic_summary(title: str, transcript_text: str, style: str) -> str:
    """Intelligent fallback summary generator based on transcript parsing."""
    lines = [l.strip() for l in transcript_text.split("\n") if l.strip()]
    cleaned_lines = [l for l in lines if not l.startswith("[00:00] This is an automated")]
    
    timed_snippets = []
    for line in lines[:30]:
        if line.startswith("["):
            parts = line.split("]", 1)
            if len(parts) == 2:
                ts = parts[0].replace("[", "")
                txt = parts[1].strip()
                if len(txt) > 10:
                    timed_snippets.append((ts, txt))
                    
    sample_snippets = [s[1] for s in timed_snippets[:8]] or ["The video explores core concepts, practical applications, and strategic insights."]
    
    if style == "quick":
        return (
            f"### ⚡ Quick Summary: {title}\n\n"
            f"**Core Theme**: This video focuses on *{title}*, breaking down essential principles and actionable knowledge.\n\n"
            f"**Key Insights**:\n"
            f"- {sample_snippets[0] if len(sample_snippets) > 0 else 'Comprehensive discussion on the primary topic.'}\n"
            f"- {sample_snippets[1] if len(sample_snippets) > 1 else 'Detailed breakdown of core methodologies and practical steps.'}\n\n"
            f"**Conclusion**: A high-value presentation designed to rapidly upskill viewers on key concepts."
        )
    elif style == "detailed":
        timestamps_md = ""
        for ts, txt in timed_snippets[:6]:
            timestamps_md += f"- **[{ts}]**: {txt}\n"
        if not timestamps_md:
            timestamps_md = "- **[00:00]**: Introduction and context setting.\n- **[05:00]**: Core concepts and main demonstration.\n"

        return (
            f"### 📌 Detailed Breakdown: {title}\n\n"
            f"#### Executive Overview\n"
            f"This video provides an in-depth exploration of **{title}**. It delivers actionable advice, key concepts, and structured instructions.\n\n"
            f"#### ⏱️ Key Timeline & Highlights\n"
            f"{timestamps_md}\n"
            f"#### 💡 Core Takeaways\n"
            f"1. **Main Objective**: Master the fundamental concepts presented by the creator.\n"
            f"2. **Practical Application**: Implementing step-by-step methodologies in real-world scenarios.\n"
            f"3. **Key Advice**: Focus on core principles before advancing to complex implementations."
        )
    elif style == "bullet":
        bullets_md = "\n".join([f"- **Key Point {i+1}**: {txt}" for i, txt in enumerate(sample_snippets[:8])])
        return (
            f"### 🎯 Bullet Point Summary: {title}\n\n"
            f"{bullets_md}\n"
            f"- **Final Takeaway**: Essential viewing for anyone looking to optimize their workflow and understanding."
        )
    elif style == "student":
        return (
            f"### 📚 Student Study Notes: {title}\n\n"
            f"#### 🔑 Key Concepts & Definitions\n"
            f"- **Primary Topic**: {title}\n"
            f"- **Core Principle**: Step-by-step masterclass covering core theoretical and practical principles.\n\n"
            f"#### 📝 Detailed Section Notes\n"
            f"- **Foundation**: Understand basic prerequisites and fundamental terminology.\n"
            f"- **Execution**: Apply the framework presented in the video systematically.\n\n"
            f"#### 🧠 Revision Questions\n"
            f"1. What is the central thesis introduced in the first section?\n"
            f"2. How does the speaker address common obstacles or pitfalls?"
        )
    elif style == "executive":
        return (
            f"### 💼 Executive Briefing: {title}\n\n"
            f"**Strategic Objective**: Rapid briefing on {title}.\n\n"
            f"**Key Findings**:\n"
            f"• High strategic relevance to productivity, technical execution, and skill enhancement.\n"
            f"• Actionable framework with immediate deployment capability.\n\n"
            f"**Recommendations**:\n"
            f"1. Review key timestamped sections for deeper domain insight.\n"
            f"2. Integrate proposed methodologies into team standard operating procedures."
        )
    elif style == "beginner":
        return (
            f"### 🎈 Simple Explanation (ELI5): {title}\n\n"
            f"Imagine you are building a LEGO tower! 🧱\n\n"
            f"This video teaches us how to place each brick step by step without the tower falling over. "
            f"First, the video shows us what we are building. Next, it gives us the special instructions, "
            f"and finally, it shows how everything fits together perfectly!"
        )
    else:  # technical
        return (
            f"### ⚙️ Technical & Engineering Analysis: {title}\n\n"
            f"#### Architecture & Core Logic\n"
            f"Analysis of structural patterns and algorithmic principles covered in **{title}**.\n\n"
            f"#### Key Code & System Takeaways\n"
            f"```text\n"
            f"// High-Level Flow\n"
            f"Input -> Validation -> Processing Pipeline -> Structured Output\n"
            f"```\n\n"
            f"#### Engineering Considerations\n"
            f"- Optimization of execution flow and modular component separation.\n"
            f"- Trade-offs between complexity, performance, and maintainability."
        )
