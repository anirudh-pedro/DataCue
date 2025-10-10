# DataCue - Quick Start Guide

Complete AI-powered data analytics platform with React frontend and FastAPI backend.

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend**:

   ```bash
   cd backend
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Start backend server**:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at: `http://localhost:8000`
   API docs at: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend**:

   ```bash
   cd client
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure environment**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   ```
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **Start development server**:

   ```bash
   npm run dev
   ```

   Frontend will be available at: `http://localhost:5173`

## 📋 Features Overview

### 1. File Ingestion Agent 📤

- Upload CSV/Excel files
- Automatic data cleaning
- Type detection
- Metadata extraction

**API Endpoint**: `POST /ingestion/upload`

### 2. Dashboard Generator Agent 📊

- Auto-generated visualizations
- 13+ chart types
- Quality scoring
- AI insights

**API Endpoint**: `POST /dashboard/generate`

### 3. Knowledge Agent 💬

- Natural language Q&A
- Statistical analysis
- Correlation discovery
- Anomaly detection

**API Endpoints**:

- `POST /knowledge/analyze`
- `POST /knowledge/ask`

### 4. Prediction Agent 🤖

- AutoML with 21 algorithms
- Model training
- Predictions with explainability
- Model versioning

**API Endpoints**:

- `POST /prediction/train`
- `POST /prediction/predict`

### 5. Orchestrator Pipeline 🚀

- End-to-end automation
- Multi-agent coordination
- Comprehensive reporting

**API Endpoint**: `POST /orchestrator/pipeline`

## 🔄 Complete Workflow Example

### Step 1: Upload Data

```bash
curl -X POST "http://localhost:8000/ingestion/upload" \
  -F "file=@data.csv"
```

Response:

```json
{
  "dataset_id": "abc123",
  "row_count": 1000,
  "column_count": 15
}
```

### Step 2: Generate Dashboard

```bash
curl -X POST "http://localhost:8000/dashboard/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "abc123",
    "options": {
      "chart_types": ["bar", "line", "scatter"],
      "max_charts": 8
    }
  }'
```

### Step 3: Ask Questions

```bash
curl -X POST "http://localhost:8000/knowledge/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key trends in this data?"
  }'
```

### Step 4: Train Model

```bash
curl -X POST "http://localhost:8000/prediction/train" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "abc123",
    "target_column": "churn",
    "task_type": "classification"
  }'
```

### Step 5: Run Full Pipeline

```bash
curl -X POST "http://localhost:8000/orchestrator/pipeline" \
  -F "file=@data.csv" \
  -F "target_column=churn" \
  -F "run_ingestion=true" \
  -F "run_dashboard=true" \
  -F "run_knowledge=true" \
  -F "run_prediction=true"
```

## 🛠️ Tech Stack

### Backend

- **FastAPI** - High-performance web framework
- **Pandas** - Data manipulation
- **Scikit-learn** - Machine learning
- **XGBoost, LightGBM** - Advanced ML algorithms
- **Plotly** - Interactive visualizations

### Frontend

- **React 19** - UI framework
- **React Router** - Navigation
- **Tailwind CSS 4** - Styling
- **Vite 7** - Build tool

## 📁 Project Structure

```
DataCue/
├── backend/
│   ├── agents/              # AI agents
│   │   ├── file_ingestion_agent/
│   │   ├── dashboard_generator_agent/
│   │   ├── knowledge_agent/
│   │   └── prediction_agent/
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   ├── core/                # Configuration
│   └── main.py              # FastAPI app
├── client/
│   └── src/
│       ├── api/             # API clients
│       ├── components/      # Reusable components
│       └── pages/           # Page components
└── QUICK_START.md           # This file
```

## 🔒 Security Notes

- Default backend allows all CORS origins for development
- For production, configure CORS in `backend/main.py`
- Use environment variables for sensitive configuration
- Implement authentication before public deployment

## 🐛 Troubleshooting

### Backend Issues

**Port 8000 already in use**:

```bash
# Find and kill the process
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux
```

**Module not found errors**:

```bash
pip install -r requirements.txt --upgrade
```

### Frontend Issues

**CORS errors**:

- Ensure backend is running
- Check CORS settings in `backend/main.py`
- Verify `.env` has correct `VITE_API_BASE_URL`

**Build errors**:

```bash
rm -rf node_modules package-lock.json
npm install
```

## 📊 Sample Data

Sample CSV located at: `backend/data/sample.csv`

Try it with the orchestrator:

```bash
curl -X POST "http://localhost:8000/orchestrator/pipeline" \
  -F "file=@backend/data/sample.csv" \
  -F "target_column=target" \
  -F "run_ingestion=true" \
  -F "run_dashboard=true"
```

## 📚 Documentation

- **Backend API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Backend README**: `backend/README.md`
- **Frontend README**: `client/README.md`
- **Architecture**: `backend/ARCHITECTURE_DIAGRAM.md`

## 🎯 Next Steps

1. **Explore the UI**: Open `http://localhost:5173` and try each page
2. **Read the Docs**: Check `/docs` endpoints for detailed API info
3. **Production Setup**: Review `backend/docs/security/` for hardening
4. **Custom Models**: Add your own algorithms to Prediction Agent
5. **Advanced Features**: Explore Knowledge Agent's recommendation engine

## 📞 Support

For issues or questions:

1. Check troubleshooting section above
2. Review API docs at `/docs` endpoint
3. Examine backend logs in terminal
4. Check browser console for frontend errors

---

**Built with ❤️ using FastAPI, React, and AI**
