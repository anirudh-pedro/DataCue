# DataCue - AI-Powered Conversational Analytics Platform

[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20PostgreSQL%20%7C%20React%20%7C%20Firebase-blue)]()
[![Python](https://img.shields.io/badge/Python-3.12+-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

## 🚀 Overview

DataCue is a **production-ready full-stack analytics platform** that transforms CSV/Excel datasets into interactive dashboards with **natural language querying**. Upload your data and ask questions in plain English—no SQL or coding required.

### Key Features

- 🤖 **AI-Powered SQL Generation** - Convert natural language to optimized PostgreSQL queries using Groq & Gemini LLMs
- 📊 **Auto-Generated Dashboards** - Intelligent chart recommendations with 8+ Plotly visualization types
- 💬 **Conversational Interface** - Chat with your data using natural language
- 🔐 **Enterprise Security** - Firebase Authentication, JWT tokens, rate limiting (30 req/min)
- ⚡ **High Performance** - Async FastAPI, PostgreSQL connection pooling, strategic caching
- 📱 **Modern UI** - React 19 + TailwindCSS with responsive design

---

## 🏗️ Architecture

### Tech Stack

**Backend:**

- **Framework:** FastAPI 0.115.0 (async/await patterns)
- **Database:** PostgreSQL 16+ with SQLAlchemy ORM
- **AI/LLM:** Groq (llama-3.3-70b) + Gemini (dual-model fallback)
- **Auth:** Firebase Admin SDK + JWT token verification
- **Rate Limiting:** SlowAPI (30 req/min per user)
- **Data Processing:** Pandas 2.2.3

**Frontend:**

- **Framework:** React 19 + Vite 7
- **Styling:** TailwindCSS 4.1
- **Visualizations:** Plotly.js (8 chart types)
- **Routing:** React Router DOM 7
- **Auth:** Firebase Client SDK

**Infrastructure:**

- PostgreSQL database with JSONB columns for flexible schema
- Connection pooling (10 base + 20 overflow)
- Session-based architecture with message persistence
- RESTful API with 15+ endpoints

---

## 📋 Prerequisites

### Backend Requirements

- **Python:** 3.11 or higher
- **PostgreSQL:** 16+ (running locally or remote)
- **API Keys:**
  - [Groq API Key](https://console.groq.com) (free tier available)
  - [Google Gemini API Key](https://makersuite.google.com/app/apikey)
  - Firebase Admin Service Account JSON

### Frontend Requirements

- **Node.js:** 18+ and npm
- **Modern Browser:** Chrome, Firefox, Safari, or Edge

---

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend directory**

```bash
cd backend_agents
```

2. **Create virtual environment (recommended)**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**

```sql
-- Create database
CREATE DATABASE datacue;

-- Or use existing PostgreSQL instance
```

5. **Configure environment variables**

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials:
# - DATABASE_URL (PostgreSQL connection string)
# - GROQ_API_KEY (required)
# - GEMINI_API_KEY (required)
# - FIREBASE_SERVICE_ACCOUNT_PATH (path to Firebase JSON)
# - SMTP credentials (for OTP email authentication)
```

6. **Start the server**

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Server runs on `http://localhost:8001`

API documentation available at `http://localhost:8001/docs`

---

### Frontend Setup

1. **Navigate to client directory**

```bash
cd client
```

2. **Install dependencies**

```bash
npm install
```

3. **Configure environment variables**

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your Firebase config:
# - VITE_API_BASE_URL (backend URL)
# - VITE_FIREBASE_API_KEY
# - VITE_FIREBASE_AUTH_DOMAIN
# - etc. (get from Firebase Console)
```

4. **Start development server**

```bash
npm run dev
```

Client runs on `http://localhost:5173`

---

## 💡 Usage Guide

### 1. **Sign Up / Login**

- Create an account using email OTP verification
- Secure Firebase Authentication with session management

### 2. **Upload Your Dataset**

- Supports CSV and Excel files
- Automatic schema detection and type inference
- Data validation and quality scoring

### 3. **Generate Dashboard**

- Click "Generate Dashboard" to create auto-visualizations
- AI analyzes correlations and recommends optimal chart types
- Instant KPI cards and insights

### 4. **Chat with Your Data**

- Ask questions in natural language:
  - "What's the total revenue?"
  - "Show top 10 customers by sales"
  - "Average satisfaction by region"
- AI converts questions to SQL and returns formatted results
- Supports tables, charts, and single-value KPIs

---

## 🎯 Core Features

### 📤 Data Ingestion

- **File Upload:** CSV, Excel (.xlsx, .xls)
- **Schema Detection:** Automatic column type inference (numeric, datetime, categorical)
- **Data Validation:** Quality scoring and anomaly detection
- **Multi-User Support:** User-specific datasets with Firebase UID isolation

### 📊 Dashboard Generation

- **Auto-Visualization:** AI-powered chart type recommendation based on data characteristics
- **Chart Types:** 8+ Plotly charts (Line, Bar, Scatter, Heatmap, Histogram, Box, Pie, Donut)
- **KPI Cards:** Automatic metric extraction with trend indicators
- **Insights Panel:** AI-generated insights from correlation analysis
- **Responsive Layout:** Smart grid system adapting to screen sizes

### 💬 Natural Language Querying (Chat)

- **SQL Generation:** LLM converts questions to PostgreSQL queries
- **Dual-Model Fallback:** Groq primary, Gemini backup for reliability
- **Intelligent Caching:** Reduces API calls for repeated queries
- **Result Formatting:** Auto-detects intent (KPI, table, chart) from query results
- **Session Persistence:** Message history saved to PostgreSQL
- **Rate Limiting:** 30 requests/minute per authenticated user

### 🔐 Security & Authentication

- **Firebase Auth:** Email/password with OTP verification
- **JWT Tokens:** Secure API authentication
- **Dataset Ownership:** Row-level security (users can only access their own data)
- **Input Validation:** Pydantic models for request/response validation
- **SQL Injection Protection:** Parameterized queries, read-only validation
- **Rate Limiting:** SlowAPI integration with per-user/IP limits

### ⚡ Performance Optimizations

- **Async Operations:** FastAPI with `async/await` patterns
- **Connection Pooling:** PostgreSQL pool (10 base + 20 overflow)
- **Query Caching:** SQL query result caching
- **Indexed Columns:** dataset_id, session_id, owner_uid indexes
- **JSONB Storage:** Flexible schema with fast JSON queries
- **Timeout Protection:** 20s timeout for LLM calls

---

## 📁 Project Structure

```
DataCue/
├── backend_agents/              # Backend API
│   ├── main.py                  # Main FastAPI application (2600+ lines)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment template
│   └── test_safeguards.py       # Security tests
│
├── client/                      # Frontend React app
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx     # Main chat interface
│   │   │   ├── Login.jsx        # Authentication
│   │   │   ├── VerifyOtp.jsx    # OTP verification
│   │   │   └── Profile.jsx      # User profile
│   │   ├── components/
│   │   │   ├── analytics/       # Dashboard components
│   │   │   │   ├── AnalyticsDashboard.jsx
│   │   │   │   ├── PowerBIDashboard.jsx
│   │   │   │   ├── KpiCard.jsx
│   │   │   │   └── ...
│   │   │   ├── charts/          # Plotly chart wrappers
│   │   │   │   ├── LineChart.jsx
│   │   │   │   ├── BarChart.jsx
│   │   │   │   ├── ScatterPlot.jsx
│   │   │   │   └── ...
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── ErrorBoundary.jsx
│   │   ├── context/
│   │   │   ├── AuthContext.jsx  # Firebase auth state
│   │   │   └── ChatContext.jsx  # Chat state management
│   │   ├── lib/
│   │   │   └── api.js           # API client with auth
│   │   └── utils/
│   │       └── sessionManager.js # Session handling
│   ├── package.json
│   └── .env.example
│
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## 🔌 API Endpoints

### Authentication

- `POST /auth/verify-token` - Verify Firebase JWT token
- `GET /auth/me` - Get current user info

### Data Ingestion

- `POST /ingestion/upload` - Upload CSV/Excel file
- `GET /ingestion/schema/{dataset_id}` - Get dataset schema
- `GET /ingestion/health` - Health check

### Dashboard Generation

- `POST /dashboard/generate-from-schema` - Generate visualizations
- `GET /dashboard/{dataset_id}` - Retrieve dashboard

### Chat / Querying

- `POST /chat/sessions` - Create new chat session
- `GET /chat/sessions/{session_id}` - Get session details
- `POST /chat/sessions/{session_id}/messages` - Send message
- `GET /chat/sessions/{session_id}/messages` - Get message history
- `PUT /chat/sessions/{session_id}/title` - Update session title
- `POST /chat/query` - Execute natural language query

### Email / OTP

- `POST /email/send-otp` - Send OTP to email
- `POST /email/verify-otp` - Verify OTP code

Full API documentation: `http://localhost:8001/docs` (Swagger UI)

---

## 🔧 Environment Variables

### Backend (.env)

```env
# PostgreSQL Database
DATABASE_URL=postgresql://username:password@localhost:5432/datacue

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=True

# Firebase Admin SDK
FIREBASE_SERVICE_ACCOUNT_PATH=./your-firebase-adminsdk.json
FIREBASE_PROJECT_ID=your-project-id

# LLM API Keys
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Email/OTP (for authentication)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

### Frontend (.env)

```env
# Backend API
VITE_API_BASE_URL=http://localhost:8001

# Firebase Configuration
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-bucket.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

**⚠️ IMPORTANT:** Never commit `.env` files to version control. Use `.env.example` templates instead.

---

## 🧪 Testing & Development

### Running the Backend

```bash
cd backend_agents
python main.py
# Or with uvicorn for more control
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### Running the Frontend

```bash
cd client
npm run dev
```

### Testing Security Safeguards

```bash
cd backend_agents
python test_safeguards.py
```

### Building for Production

**Backend:**

```bash
cd backend_agents
pip install -r requirements.txt
# Configure production .env
# Use production PostgreSQL database
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

**Frontend:**

```bash
cd client
npm run build
# Serve dist/ folder with nginx, Vercel, or Netlify
```

---

## 🛡️ Security Best Practices

1. **Never commit `.env` files** - Always use `.env.example` templates
2. **Rotate API keys regularly** - Especially after accidental exposure
3. **Use Firebase Service Account JSON** - Store securely, never commit
4. **Enable CORS properly** - Set `ALLOWED_ORIGINS` in production
5. **Use HTTPS in production** - Never send JWT tokens over HTTP
6. **Set strong database passwords** - Use environment-specific credentials
7. **Monitor rate limits** - Adjust based on usage patterns
8. **Review Firebase rules** - Ensure proper data access controls

---

## 🐛 Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'slowapi'"**

```bash
pip install -r requirements.txt
```

**"Connection refused" to PostgreSQL**

```bash
# Ensure PostgreSQL is running
sudo service postgresql start  # Linux
brew services start postgresql  # macOS
# Check DATABASE_URL in .env
```

**"Firebase initialization failed"**

- Verify FIREBASE_SERVICE_ACCOUNT_PATH points to correct JSON file
- Check Firebase project ID matches your console
- Ensure service account has proper permissions

### Frontend Issues

**"Failed to fetch" / CORS errors**

- Check VITE_API_BASE_URL matches backend address
- Verify backend CORS settings allow frontend origin
- Ensure both servers are running

**Firebase auth not working**

- Verify all Firebase config variables in `.env`
- Check Firebase Console > Authentication is enabled
- Ensure email/password provider is activated

---

## 📊 Performance Metrics

- **Query Response Time:** < 2s for most natural language queries
- **Dashboard Generation:** 5-15s for typical datasets (< 10K rows)
- **File Upload:** Supports files up to 50MB
- **Concurrent Users:** Handles 30+ requests/minute per user
- **Database Performance:** PostgreSQL JSONB queries ~50-200ms

---

## 🤝 Contributing

This is a portfolio/educational project. Feel free to fork and adapt for your own use.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available for educational purposes.

---

## 🙏 Acknowledgments

- **Groq** - Fast LLM inference (llama-3.3-70b-versatile)
- **Google Gemini** - Fallback LLM provider
- **Firebase** - Authentication and user management
- **FastAPI** - Modern Python web framework
- **React** - UI framework
- **Plotly** - Interactive visualizations
- **PostgreSQL** - Robust relational database

---

## 📧 Contact & Support

For questions, issues, or feedback:

- Create an issue on GitHub
- Check API documentation at `/docs` endpoint
- Review code comments in `main.py` for implementation details

---

**Built with ❤️ using Python, FastAPI, PostgreSQL, React, and AI**
