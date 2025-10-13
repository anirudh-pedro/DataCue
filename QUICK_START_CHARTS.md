# Quick Start: DataCue with Live Chart Streaming

## What's New

✨ **Real-time chart streaming during file upload**
✨ **Chat-based visual queries with automatic chart generation**
✨ **Interactive Plotly visualizations in chat bubbles**

## Start the Application

### 1. Backend (Terminal 1)

```powershell
cd "c:\Users\HP\Desktop\machine learning\DataCue\backend"
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend (Terminal 2)

```powershell
cd "c:\Users\HP\Desktop\machine learning\DataCue\client"
npm run dev
```

### 3. Open Browser

Navigate to: **http://localhost:5173**

## Try It Out

### Upload Flow (Live Charts)

1. **Click upload button** (📎 icon) in chat
2. **Select a CSV file** (e.g., `backend/data/sentiment140_csv.csv`)
3. **Watch the magic**:
   - Status updates appear in real-time
   - Charts stream into the chat as they're generated
   - "Analysis complete" message when done

### Chat Queries (Visual Answers)

Ask these questions after upload completes:

**Numeric Aggregations:**

```
What's the average value?
Total count of records?
Sum of all values?
```

→ Returns text + metric indicator chart

**Top N Queries:**

```
Top 5 categories
Highest 10 products by revenue
Bottom 3 regions by sales
```

→ Returns text + bar chart

**Distributions:**

```
Show distribution of prices
How are ages distributed?
```

→ Returns histogram (if configured)

## Expected Behavior

### During Upload

You'll see messages like:

- 📁 Upload received. Preparing analysis…
- 🔍 Reading CSV and validating columns…
- 📊 Generating summary statistics…
- **Chart appears** (first bar chart)
- **Chart appears** (second histogram)
- **Chart appears** (third correlation heatmap)
- ✅ Analysis complete — visualizations ready!

### During Chat

**User:** "Top 5 products"

**Assistant:**

- Text bubble: "The top 5 products are Product A (150), Product B (120)..."
- Chart bubble: Interactive bar chart showing the top 5

## Troubleshooting

### Backend not reloading?

Stop uvicorn (Ctrl+C) and restart:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Charts not showing?

1. Check browser console (F12) for errors
2. Verify `react-plotly.js` is installed:
   ```powershell
   cd client
   npm list react-plotly.js
   ```
3. Hard refresh browser (Ctrl+Shift+R)

### "Please upload a dataset" error?

You need to upload a file first before asking questions.

### CORS errors?

Backend should have CORS enabled for `http://localhost:5173`. If not, check `backend/main.py` includes:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Advanced Usage

### Fullscreen Charts

- **Hover over chart** → Click maximize icon (⛶)
- **Click background** to close

### Download Charts

- **Hover over chart** → Click download icon (⬇)
- Saves as PNG

### Multiple Charts per Question

Some queries return multiple visualizations:

```
Compare sales by region and month
```

→ Text + grouped bar + time series

## File Structure

```
DataCue/
├── backend/
│   ├── services/
│   │   ├── orchestrator_service.py  # Emits chart_ready events
│   │   └── knowledge_service.py     # ask_visual method
│   └── routers/
│       └── knowledge_router.py      # /ask-visual endpoint
├── client/
│   ├── src/
│   │   ├── components/
│   │   │   └── ChartMessage.jsx     # Renders Plotly charts
│   │   └── pages/
│   │       └── ChatPage.jsx         # Handles SSE + visual queries
│   └── package.json                 # react-plotly.js dependency
└── CHART_STREAMING_GUIDE.md         # Full documentation
```

## Next Steps

1. **Test with your own data**: Upload any CSV and explore
2. **Try different questions**: See what generates charts automatically
3. **Check insights**: Charts include key metrics below the visualization
4. **Experiment with fullscreen**: Perfect for presentations

---

**Questions?** Check `CHART_STREAMING_GUIDE.md` for complete technical docs.
