# DataCue - AI-Powered Analytics Platform

Transform CSV/Excel data into interactive dashboards with natural language queries. No SQL or coding required.

## ✨ Features

- 🤖 **Natural Language Queries** - Ask questions in plain English
- 📊 **Auto Dashboards** - AI-generated visualizations with 8+ chart types
- 🔐 **Secure** - Firebase authentication with JWT tokens
- ⚡ **Fast** - Async FastAPI with PostgreSQL caching

## 🛠️ Tech Stack

**Backend:** FastAPI • PostgreSQL • Groq & Gemini LLMs • Firebase Auth  
**Frontend:** React 19 • TailwindCSS • Plotly • Vite

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Node.js 18+
- [Groq API Key](https://console.groq.com)
- [Gemini API Key](https://makersuite.google.com/app/apikey)
- Firebase Admin Service Account

### Backend Setup

```bash
# 1. Navigate to backend
cd backend_agents

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Create database
createdb datacue  # or use existing PostgreSQL

# 6. Start server
python main.py
# Server runs on http://localhost:8001
```

### Frontend Setup

```bash
# 1. Navigate to client
cd client

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with Firebase config

# 4. Start dev server
npm run dev
# Client runs on http://localhost:5173
```

## 📚 Usage

1. **Sign Up** - Create account with email OTP verification
2. **Upload Data** - CSV/Excel files with auto schema detection
3. **Generate Dashboard** - AI creates visualizations automatically
4. **Chat** - Ask questions like "What's the total revenue?" or "Show top 10 customers"

## 🔧 Environment Variables

Create `.env` files from `.env.example` templates:

**Backend (.env):**

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/datacue
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-admin.json
```

**Frontend (.env):**

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_FIREBASE_API_KEY=your_key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## 📖 API Documentation

Visit `http://localhost:8001/docs` for interactive Swagger UI

## 🤝 Contributing

Feel free to fork and adapt for your own use.

## 📄 License

Open source for educational purposes.

---

**Built with Python, FastAPI, PostgreSQL, React, and AI**
