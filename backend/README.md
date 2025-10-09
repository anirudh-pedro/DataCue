# DataCue Backend – Four-Agent AI Analytics Platform

This backend powers the DataCue platform: a modular analytics stack with **File Ingestion**, **Dashboard Generation**, **Knowledge (Conversational) Analytics**, and **Prediction (ML) Agents**.

---

## 🚀 Capabilities at a Glance

| Agent                        | Key Skills                                                                           | Primary Modules                                                                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **1. File Ingestion**        | Multi-format ingestion, cleaning, rich metadata extraction                           | `ingestion_agent.py`, `data_cleaner.py`, `metadata_extractor.py`                                                                         |
| **2. Dashboard Generator**   | Auto chart recommendations (13 types), layouting, AI narratives, exports             | `chart_recommender.py`, `layout_manager.py`, `insight_generator.py`                                                                      |
| **3. Knowledge Agent**       | Natural-language Q&A, anomaly detection, recommendations, Groq-powered narratives    | `knowledge_agent.py`, `query_engine.py`, `recommendation_engine.py`                                                                      |
| **4. Prediction Agent v2.0** | AutoML across 21 models, hyperparameter tuning, ensembles, SHAP, monitoring, FastAPI | `prediction_agent.py`, `model_selector.py`, `cross_validator.py`, `hyperparameter_tuner.py`, `model_monitor.py`, `api/prediction_api.py` |

Supporting docs live under `backend/ARCHITECTURE_DIAGRAM.md`, `V2_ENHANCEMENTS.md`, and `COMPLETE_BUILD_SUMMARY.md`.

---

## 🧱 Project Structure

```
backend/
├── agents/
│   ├── file_ingestion_agent/
│   ├── dashboard_generator_agent/
│   ├── knowledge_agent/
│   └── prediction_agent/
├── core/
│   └── config.py               # Centralised .env loading and settings helper
├── ARCHITECTURE_DIAGRAM.md     # Platform architecture overview
├── COMPLETE_BUILD_SUMMARY.md   # Change log & statistics
├── requirements.txt            # Consolidated dependencies
└── tests/
        └── test_bootstrap.py       # Smoke tests to ensure modules import
```

---

## 🛠️ Prerequisites

- **Python 3.11+**
- **pip** (latest)
- **Visual C++ Build Tools** (Windows) – required for Prophet / statsmodels compilation
- (Optional) **cmdstanpy** backend for Prophet → install by running `python -m prophet.models.install` after dependency install

---

## ⚙️ Setup

```bash
git clone https://github.com/anirudh-pedro/DataCue.git
cd DataCue/backend

python -m venv .venv
.venv\Scripts\activate  # PowerShell (Windows)

pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variables

The backend loads `backend/.env` automatically via `core.config.get_settings()`.

Required keys:

| Variable       | Purpose                                                                                             |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `GROQ_API_KEY` | Enables Groq LLM narratives inside the Knowledge Agent (auto-populated from `groq_api` if present). |
| `MONGO_URI`    | Connection string for future persistence integrations (currently optional).                         |

The default `.env` file contains example values – replace them with your own secrets before deploying.

---

## ▶️ Running the Prediction API (Agent 4)

1. **Activate the virtual environment** and ensure dependencies are installed.
2. **Start the FastAPI service**:

```bash
uvicorn agents.prediction_agent.api.prediction_api:app --host 0.0.0.0 --port 8000 --reload
```

3. **Upload a dataset**:

```bash
curl -F "file=@data/my_dataset.csv" http://localhost:8000/datasets/upload
```

4. **Train a model**:

```bash
curl -X POST http://localhost:8000/train \
    -H "Content-Type: application/json" \
    -d '{
                "dataset_name": "my_dataset",
                "target_column": "label",
                "problem_type": "classification",
                "tune_hyperparameters": true,
                "create_ensemble": true
            }'
```

5. **Predict / Explain / Monitor** using `/predict`, `/explain`, `/models`, `/health` endpoints.

Datasets are persisted to `./data`, and models to `./saved_models` (directories are auto-created).

---

## 📚 Examples & Usage

- `agents/prediction_agent/example_v2_enhanced_features.py` – showcases cross-validation, tuning, ensembles, time series, and monitoring.
- `agents/knowledge_agent/example_usage.ipynb` (coming soon) – explore conversational analytics.
- Dashboard agent README includes configuration details for chart customization and exports.

---

## ✅ Smoke Tests

Run the bundled bootstrap checks:

```bash
pip install -r requirements-dev.txt
pytest
```

These tests confirm the critical agents import correctly and that environment configuration is wired up.

---

## 📦 Key Dependencies

- Core analytics: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `statsmodels`, `prophet`
- Explainability & monitoring: `shap`, `optuna`, `imbalanced-learn`, `tqdm`
- API layer: `fastapi`, `uvicorn`, `python-dotenv`
- Visualization & docs: `plotly`, `matplotlib`, `reportlab`
- LLM integration: `groq`

All pinned versions are listed in `requirements.txt`. Use `agents/prediction_agent/requirements_prediction.txt` when deploying the prediction service independently.

---

## 🤝 Contributing

1. Fork the repo & create a feature branch
2. Ensure tests (`pytest`) pass locally
3. Submit a PR with a summary of changes

---

## 📄 License

MIT © DataCue Team

---

## 🙌 Acknowledgements

Built with Python, FastAPI, scikit-learn, XGBoost, Prophet, and the Groq LLM ecosystem.
