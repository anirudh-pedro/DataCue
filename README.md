# DataCue - AI-Powered Data Analysis Platform

## Overview

DataCue is a comprehensive data analysis platform that combines data ingestion, visualization, natural language querying, and machine learning predictions. Upload CSV files and interact with your data using conversational AI powered by Groq LLM.

## Quick Start

### Backend Setup

1. **Install Dependencies**

```bash
cd backend
pip install -r requirements.txt
```

2. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your credentials:
# - GROQ_API_KEY (required)
# - MONGO_URI (optional, defaults to in-memory)
```

3. **Start Server**

```bash
python main.py
```

Server runs on `http://localhost:8000`

### Frontend Setup

1. **Install Dependencies**

```bash
cd client
npm install
```

2. **Configure Environment**

```bash
cp .env.example .env
# Edit .env if backend URL differs from default
```

3. **Start Development Server**

```bash
npm run dev
```

Client runs on `http://localhost:5173`

## Core Features

### 📊 Data Ingestion

- CSV file upload with automatic schema detection
- Data validation and type inference
- Session-based data management

### 📈 Dashboard Generation

- Automatic visualization creation
- Multiple chart types (bar, line, scatter, pie, etc.)
- Interactive chart customization
- Export to PNG/PDF

### 💬 Natural Language Querying

Ask questions about your data in plain English:

- "How many rows are in this dataset?"
- "What's the average salary by department?"
- "Show me the top 5 customers by revenue"

Powered by MongoDB aggregation and Groq LLM for intelligent query translation.

### 🤖 Machine Learning

- Automated model training
- Regression and classification support
- Feature importance analysis
- Model performance metrics

## Architecture

- **Backend**: Python FastAPI with MongoDB
- **Frontend**: React 19 + Vite + Tailwind CSS
- **AI/ML**: Groq LLM (llama-3.3-70b-versatile)
- **Database**: MongoDB (optional, falls back to in-memory)

## Documentation

Comprehensive guides available in `backend/docs/guides/`:

- MongoDB Query Setup & Usage
- Dynamic Configuration
- LLM Query Engine

## Environment Variables

### Backend (.env)

```env
GROQ_API_KEY=your_groq_api_key
MONGO_URI=mongodb://localhost:27017/datacue  # optional
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

See `.env.example` for full configuration options.

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_EMAIL_SERVICE_URL=http://localhost:4000
```

## Project Structure

```
DataCue/
├── backend/
│   ├── agents/          # Specialized AI agents
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   ├── core/            # Configuration
│   ├── data/            # Sample datasets
│   └── docs/            # Documentation
│
├── client/
│   ├── src/
│   │   ├── pages/       # React pages
│   │   ├── components/  # Reusable UI components
│   │   └── utils/       # Helper functions
│   └── docs/            # Frontend documentation
│
└── README.md
```

## API Endpoints

- **POST** `/ingestion/upload` - Upload CSV file
- **POST** `/knowledge/ask-mongo` - Natural language query
- **POST** `/dashboard/generate` - Create visualizations
- **POST** `/prediction/train` - Train ML model
- **POST** `/prediction/predict` - Make predictions

## Requirements

### Backend

- Python 3.11+
- MongoDB (optional)
- Groq API key (free tier available)

### Frontend

- Node.js 18+
- Modern browser (Chrome, Firefox, Safari, Edge)

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Building for Production

```bash
# Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd client
npm run build
```

## License

This project is for educational and development purposes.

## Support

For questions or issues, refer to the documentation in `backend/docs/guides/` or create an issue in the repository.
