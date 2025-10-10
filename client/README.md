# DataCue Frontend

React-based frontend for the DataCue AI-powered data analytics platform.

## Features

### 🏠 Home Page

- Overview of all available features
- Quick navigation to different agents
- Getting started guide

### 📤 File Upload (Ingestion Agent)

- Drag-and-drop CSV/Excel file upload
- Automatic data cleaning and type detection
- Metadata extraction and preview
- List all uploaded datasets

### 📊 Dashboard Generator

- Auto-generated interactive visualizations
- 13+ chart types (bar, line, scatter, pie, heatmap, etc.)
- AI-powered chart recommendations
- Quality scoring and data profiling
- Exportable dashboards

### 💬 Knowledge Q&A

- Natural language questions about your data
- Statistical analysis and insights
- Correlation discovery
- Anomaly detection
- Chat-based interface

### 🤖 Prediction Agent

- AutoML with 21 algorithms
- Model training with cross-validation
- Real-time predictions
- Model explainability (SHAP)
- Model versioning and metadata

### 🚀 Orchestrator Pipeline

- End-to-end workflow automation
- Select and configure pipeline steps
- Multi-agent coordination
- Comprehensive results reporting

## Tech Stack

- **React 19.1.1** - UI framework
- **React Router DOM 7.2.0** - Navigation
- **Vite 7.1.7** - Build tool & dev server
- **Tailwind CSS 4.1.14** - Styling
- **@tailwindcss/vite 4.1.14** - Tailwind integration

## Project Structure

```
src/
├── api/              # API client modules
│   ├── ingestion.js
│   ├── dashboard.js
│   ├── knowledge.js
│   ├── prediction.js
│   └── orchestrator.js
├── components/       # Reusable UI components
│   ├── Navbar.jsx
│   ├── Sidebar.jsx
│   ├── FileUploader.jsx
│   ├── Loader.jsx
│   ├── DashboardView.jsx
│   ├── KnowledgeChat.jsx
│   └── PredictionPanel.jsx
├── pages/           # Page components
│   ├── Home.jsx
│   ├── UploadPage.jsx
│   ├── DashboardPage.jsx
│   ├── KnowledgePage.jsx
│   ├── PredictionPage.jsx
│   └── OrchestratorPage.jsx
├── App.jsx          # Main app with routing
├── main.jsx         # Entry point
└── index.css        # Global styles
```

## Setup

### Prerequisites

- Node.js 18+ and npm
- DataCue backend running on `http://localhost:8000`

### Installation

1. **Install dependencies**:

   ```bash
   npm install
   ```

2. **Configure environment**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your backend URL:

   ```
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. **Start development server**:

   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`

### Production Build

```bash
npm run build
npm run preview  # Preview production build
```

## Usage Workflow

### 1. Upload Data

1. Navigate to **Upload** page
2. Drag and drop or select CSV/Excel file
3. Optionally specify sheet name (for Excel)
4. Click "Upload File"
5. Note the **Dataset ID** from the success message

### 2. Generate Dashboard

1. Go to **Dashboard** page
2. Enter the Dataset ID from step 1
3. Select desired chart types
4. Click "Generate Dashboard"
5. View auto-generated visualizations and insights

### 3. Ask Questions

1. Navigate to **Knowledge** page
2. Enter Dataset ID and click "Analyze"
3. Ask natural language questions in the chat
4. Get AI-powered answers with confidence scores

### 4. Train and Predict

1. Go to **Prediction** page
2. **Train Tab**: Upload training data, specify target column and task type
3. Click "Train Model with AutoML"
4. **Predict Tab**: Select trained model, input features as JSON
5. View predictions with probabilities and explanations

### 5. Run Full Pipeline

1. Navigate to **Orchestrator** page
2. Upload your data file
3. Select which agents to run
4. Configure prediction settings (if enabled)
5. Click "Run Full Pipeline"
6. View aggregated results from all agents

## API Integration

All API calls are handled through modules in `src/api/`:

```javascript
// Example: Upload a file
import { uploadFile } from "./api/ingestion";
const result = await uploadFile(file, sheetName);

// Example: Generate dashboard
import { generateDashboard } from "./api/dashboard";
const dashboard = await generateDashboard(payload);

// Example: Ask question
import { askQuestion } from "./api/knowledge";
const answer = await askQuestion("What are the key trends?");
```

The base URL is configured via `VITE_API_BASE_URL` environment variable and defaults to `http://localhost:8000`.

## Component Documentation

### FileUploader

Reusable drag-and-drop file upload component.

```jsx
<FileUploader onUpload={setFile} accept=".csv,.xlsx,.xls" />
```

### DashboardView

Displays generated dashboard with charts and quality metrics.

```jsx
<DashboardView dashboard={dashboardData} />
```

### KnowledgeChat

Chat interface for Q&A with the Knowledge Agent.

```jsx
<KnowledgeChat onAskQuestion={handleAskQuestion} />
```

### PredictionPanel

Model selection and prediction interface.

```jsx
<PredictionPanel models={trainedModels} />
```

## Styling

Tailwind CSS is configured with custom gradient themes:

- **Blue-Purple gradients**: Dashboard and orchestrator features
- **Green accents**: Knowledge and analysis features
- **Orange accents**: Prediction and ML features
- **Responsive design**: Mobile-first with breakpoints at `md` and `lg`

## Development

### Running Tests

```bash
npm run lint  # Run ESLint
```

### Code Style

- Use functional components with hooks
- Follow React best practices
- Keep components focused and reusable
- Use Tailwind utility classes for styling

## Troubleshooting

### CORS Errors

If you see CORS errors, ensure the backend is configured to allow requests from `http://localhost:5173`. Check backend CORS middleware settings.

### API Connection Issues

1. Verify backend is running: `curl http://localhost:8000/docs`
2. Check `.env` file has correct `VITE_API_BASE_URL`
3. Restart dev server after changing `.env`

### Build Errors

1. Clear node_modules: `rm -rf node_modules package-lock.json`
2. Reinstall: `npm install`
3. Clear Vite cache: `rm -rf node_modules/.vite`

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

Part of the DataCue project.
