# DataCue Frontend - Component Architecture

## 📐 Component Hierarchy

```
App.jsx (BrowserRouter)
│
├── Navbar.jsx (Top navigation)
│   └── React Router <Link> components
│
├── Sidebar.jsx (Left navigation)
│   └── React Router <Link> components with icons
│
└── <Routes>
    │
    ├── Route: "/" → Home.jsx
    │   ├── Feature cards grid
    │   ├── Quick stats dashboard
    │   └── Getting started steps
    │
    ├── Route: "/upload" → UploadPage.jsx
    │   ├── <FileUploader />
    │   ├── Dataset name input
    │   ├── Upload button
    │   ├── <Loader /> (conditional)
    │   └── Dataset list viewer
    │
    ├── Route: "/dashboard" → DashboardPage.jsx
    │   ├── Configuration panel
    │   │   ├── Dataset ID input
    │   │   └── Chart type checkboxes
    │   ├── Generate button
    │   ├── <Loader /> (conditional)
    │   └── <DashboardView dashboard={data} />
    │       ├── Quality score bar
    │       ├── Charts grid
    │       └── Metadata stats
    │
    ├── Route: "/knowledge" → KnowledgePage.jsx
    │   ├── Analysis setup panel
    │   │   ├── Dataset ID input
    │   │   └── Analyze button
    │   ├── <Loader /> (conditional)
    │   ├── Dataset summary cards
    │   └── <KnowledgeChat onAskQuestion={handler} />
    │       ├── Message history
    │       ├── User/assistant bubbles
    │       └── Input form
    │
    ├── Route: "/prediction" → PredictionPage.jsx
    │   ├── Tab switcher (Train/Predict)
    │   ├── Train Tab:
    │   │   ├── <FileUploader />
    │   │   ├── Dataset name input
    │   │   ├── Configuration form
    │   │   ├── Train button
    │   │   └── <Loader /> (conditional)
    │   ├── Predict Tab:
    │   │   ├── <PredictionPanel models={models} />
    │   │   │   ├── Model dropdown
    │   │   │   ├── Features JSON textarea
    │   │   │   ├── Predict button
    │   │   │   └── Results display
    │   │   └── Models list viewer
    │   └── Training results display
    │
    └── Route: "/orchestrator" → OrchestratorPage.jsx
        ├── <FileUploader />
        ├── Pipeline step checkboxes
        ├── Prediction settings (conditional)
        ├── Run Pipeline button
        ├── <Loader /> (conditional)
        ├── Progress tracker
        └── Results aggregation display
```

## 🔄 Data Flow Patterns

### Pattern 1: File Upload Flow

```
User selects file
    ↓
FileUploader component captures file
    ↓
Parent page receives file via onUpload callback
    ↓
Parent stores file in state (useState)
    ↓
User clicks upload button
    ↓
Page calls API function (e.g., uploadFile(file))
    ↓
API makes fetch() request to backend
    ↓
Response received and stored in state
    ↓
UI updates to show results
```

### Pattern 2: Dashboard Generation Flow

```
User enters dataset ID
    ↓
Page stores ID in state
    ↓
User selects chart types
    ↓
Page updates chartTypes state
    ↓
User clicks generate
    ↓
Page calls generateDashboard(payload)
    ↓
Shows <Loader /> while waiting
    ↓
Response received with dashboard data
    ↓
Passes data to <DashboardView dashboard={data} />
    ↓
DashboardView renders charts and metrics
```

### Pattern 3: Chat Interface Flow

```
User types question in KnowledgeChat
    ↓
Component adds user message to local state
    ↓
Calls parent's onAskQuestion callback
    ↓
Parent calls askQuestion API
    ↓
Shows loading animation
    ↓
Response received with answer
    ↓
Parent returns answer to component
    ↓
Component adds assistant message to state
    ↓
Chat updates with new message
```

### Pattern 4: Orchestrator Pipeline Flow

```
User uploads file + configures pipeline
    ↓
Page builds FormData with all settings
    ↓
Calls runPipeline(formData)
    ↓
Shows <Loader /> + progress tracker
    ↓
Backend runs multiple agents sequentially
    ↓
Response received with aggregated results
    ↓
Page displays results by agent type
    ↓
User can view raw JSON or formatted results
```

## 🗂️ State Management

### Page-level State (useState)

Each page manages its own state:

**UploadPage**:

- `file` - Selected file object
- `sheetName` - Excel sheet name
- `uploadStatus` - Success/error message
- `isUploading` - Loading flag
- `datasets` - List of uploaded datasets

**DashboardPage**:

- `datasetId` - Selected dataset
- `chartTypes` - Array of selected chart types
- `dashboard` - Generated dashboard data
- `isGenerating` - Loading flag
- `error` - Error message

**KnowledgePage**:

- `datasetId` - Dataset to analyze
- `isAnalyzed` - Analysis completion flag
- `isAnalyzing` - Loading flag
- `summary` - Analysis summary
- `error` - Error message

**PredictionPage**:

- `activeTab` - 'train' or 'predict'
- `file` - Training data file
- `datasetName` - Dataset identifier
- `targetColumn` - ML target
- `taskType` - classification/regression/clustering
- `models` - List of trained models
- `isTraining` - Training in progress
- `trainingResult` - Training output

**OrchestratorPage**:

- `file` - Input data file
- `targetColumn` - ML target (if prediction enabled)
- `taskType` - ML task type
- `enabledSteps` - Object with step flags
- `isRunning` - Pipeline execution flag
- `result` - Aggregated pipeline results
- `error` - Error message

### Component-level State

**KnowledgeChat**:

- `messages` - Chat history array
- `input` - Current input value
- `isLoading` - Waiting for response

**PredictionPanel**:

- `selectedModel` - Chosen model ID
- `features` - JSON feature string
- `prediction` - Prediction result
- `isLoading` - Prediction in progress

## 🎨 Styling Architecture

### Tailwind Utility Classes

All styling uses Tailwind CSS utilities:

```jsx
// Layout
<div className="flex items-center justify-between">
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">

// Spacing
<div className="p-6 mb-4 space-y-3">

// Colors
<div className="bg-white text-gray-900">
<div className="bg-blue-50 text-blue-800">

// Borders & Shadows
<div className="border border-gray-200 rounded-lg shadow">

// Typography
<h1 className="text-3xl font-bold">
<p className="text-sm text-gray-600">

// States
<button className="hover:bg-blue-700 disabled:opacity-50">

// Responsive
<div className="hidden md:block">
```

### Color Semantics

- **Gray**: Neutral UI elements, text
- **Blue**: Primary actions, ingestion
- **Purple**: Dashboard features
- **Green**: Knowledge/analysis features
- **Orange**: ML/prediction features
- **Red**: Errors, orchestrator accent

### Gradient Patterns

```css
/* Primary gradient (Navbar, buttons) */
from-blue-600 to-purple-600

/* Orchestrator gradient */
from-blue-600 via-purple-600 to-orange-600

/* Success states */
bg-green-50 border-green-200

/* Error states */
bg-red-50 border-red-200
```

## 📡 API Communication Layer

### Base Configuration

All API modules import from a common pattern:

```javascript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
```

### Request Patterns

**JSON Payloads**:

```javascript
const response = await fetch(`${API_BASE_URL}/endpoint`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
```

**File Uploads (FormData)**:

```javascript
const formData = new FormData();
formData.append("file", file);
const response = await fetch(`${API_BASE_URL}/endpoint`, {
  method: "POST",
  body: formData, // No Content-Type header!
});
```

### Error Handling

```javascript
if (!response.ok) {
  const error = await response.json();
  throw new Error(error.detail || "Request failed");
}
return await response.json();
```

## 🔌 Router Configuration

### Routes Table

| Path            | Component        | Purpose                        |
| --------------- | ---------------- | ------------------------------ |
| `/`             | Home             | Landing page, feature overview |
| `/upload`       | UploadPage       | File ingestion interface       |
| `/dashboard`    | DashboardPage    | Visualization generator        |
| `/knowledge`    | KnowledgePage    | Q&A and analysis               |
| `/prediction`   | PredictionPage   | ML training and prediction     |
| `/orchestrator` | OrchestratorPage | Pipeline orchestration         |

### Navigation Components

- **Navbar**: Horizontal links at top
- **Sidebar**: Vertical menu with icons
- Both use `<Link to="/path">` from react-router-dom

## 🧩 Component Reusability

### Highly Reusable

- `<FileUploader />` - Used in Upload, Prediction, Orchestrator
- `<Loader />` - Used across all pages
- `<Navbar />` - Single instance in App
- `<Sidebar />` - Single instance in App

### Context-Specific

- `<DashboardView />` - Only in DashboardPage
- `<KnowledgeChat />` - Only in KnowledgePage
- `<PredictionPanel />` - Only in PredictionPage

### Customization via Props

```jsx
// FileUploader accepts different file types
<FileUploader accept=".csv,.xlsx" />
<FileUploader accept=".json" />

// Loader shows custom messages
<Loader message="Processing your file..." />
<Loader message="Training models..." />
```

## 📱 Responsive Breakpoints

Tailwind breakpoints used:

- **Default** (0px): Mobile layout
- **md:** (768px): Tablet layout
- **lg:** (1024px): Desktop layout

Example responsive patterns:

```jsx
// Grid columns
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// Visibility
<div className="hidden md:block">

// Spacing
<div className="px-4 md:px-6 lg:px-8">
```

## 🎯 Key Design Decisions

1. **Component Composition**: Pages compose smaller components rather than monolithic structures
2. **State Colocation**: State lives closest to where it's used
3. **Prop Drilling Avoidance**: Callbacks passed max 1 level deep
4. **Loading States**: Every async operation has a loading indicator
5. **Error Boundaries**: Each page handles its own errors
6. **Responsive First**: Mobile-friendly base with desktop enhancements
7. **Semantic HTML**: Proper use of headings, lists, forms
8. **Accessibility**: Labels, ARIA attributes where needed

## 🚀 Performance Considerations

- **Code Splitting**: React Router lazy loading ready
- **Build Optimization**: Vite automatically chunks
- **Asset Optimization**: Images/icons as emojis (no downloads)
- **CSS Purging**: Tailwind removes unused styles in production
- **Bundle Size**: 277KB JS (82KB gzipped) - reasonable for feature set

---

**Last Updated**: Implementation completed with all components, pages, and routing functional.
