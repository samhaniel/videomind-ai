# ⚡ VideoMind AI — Next-Gen YouTube Video Intelligence

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Backend-Flask%20%7C%20FastAPI-green.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI Engine-Google%20Gemini-orange.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Deployment](https://img.shields.io/badge/Deploy-Render%20Ready-purple.svg?logo=render&logoColor=white)](https://render.com/)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

> Turn any long YouTube video or lecture into grounded Q&A, interactive study notes, 3D flip flashcards, and MCQ quizzes within seconds using Google Gemini AI.

---

## 🌟 Key Features

* **🎥 Automatic Transcript Extraction:** Paste any YouTube video link and extract transcripts with automatic language detection and timestamp mapping.
* **💬 Strict Grounded AI Chat:** Ask questions about the video and get precise answers grounded strictly in the transcript with zero AI hallucinations.
* **📊 18+ Comprehensive Analysis Formats:**
  * Quick Summary & Executive Brief
  * Detailed Chapter Breakdown
  * Timelines & Key Events
  * Bulleted Takeaways & Action Points
  * Definitions, Technical Terms & FAQs
  * Explain Like I'm 5 (ELI5)
* **🎴 Interactive 3D Flashcards & Quizzes:** Auto-generate 3D flipping flashcards and interactive multiple-choice quizzes to master video content.
* **📄 One-Click Export:** Download summaries and Q&A transcripts in **PDF**, **Markdown**, **JSON**, or **TXT** formats.
* **🎨 Premium Glassmorphism UI:** Built with dark mode, modern typography, responsive micro-animations, and smooth user experience.

---

## 🏗️ Tech Stack

* **Backend:** Python 3.11+, Flask, FastAPI, `youtube-transcript-api`, `google-genai` / `google-generativeai`, `firebase-admin`
* **Frontend:** Vanilla HTML5, Modern CSS3 (Glassmorphism & CSS Variables), JavaScript (ES6+)
* **Database / Services:** Firebase Firestore & Auth, Google Gemini API

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
Ensure you have **Python 3.10+** and **Git** installed on your system.

### 2. Clone Repository
```bash
git clone https://github.com/samhaniel/videomind-ai.git
cd videomind-ai
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (or inside `backend/.env`) based on `.env.example`:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
PORT=5000
DEBUG=True
SECRET_KEY=videomind-secret-key-2026
```

### 5. Launch Application
```bash
python backend/app.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🌐 Deploy to Render (Hosting Guide)

This repository includes pre-configured `Procfile`, `runtime.txt`, and `requirements.txt` for one-click hosting on **Render**:

1. Log in to [Render.com](https://render.com) using your GitHub account.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your repository: `samhaniel/videomind-ai`.
4. Configure the service:
   * **Environment:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn --chdir backend app:app`
5. Add your `GEMINI_API_KEY` under **Environment Variables**.
6. Click **Create Web Service**.

---

## 📂 Project Structure

```
videomind-ai/
├── backend/
│   ├── app.py                # Main Flask Server & Route Handler
│   ├── routes.py             # API Endpoints
│   ├── chat_service.py       # Grounded RAG Chat Engine
│   ├── summary.py            # Gemini Summarization Service
│   ├── transcript_service.py # YouTube Transcript Extractor
│   ├── firebase_service.py   # Firebase Database & Auth
│   └── test_verification.py  # Automated Test Suite
├── frontend/
│   ├── index.html            # Landing Page
│   ├── chat.html             # AI Studio & Chatbot
│   ├── history.html          # History & Saved Notes
│   ├── settings.html         # User Settings & API Keys
│   └── assets/               # CSS Styles & JavaScript Modules
├── Procfile                  # Production Deployment Command
├── requirements.txt          # Python Dependencies
├── runtime.txt             # Python Runtime Specification
└── README.md                 # Project Documentation
```

---

## 🧪 Running Tests

To run the automated verification suite for transcript extraction, video processing, and Gemini AI integration:

```bash
python backend/test_verification.py
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

Developed by **[Sam Haniel](https://github.com/samhaniel)**.
