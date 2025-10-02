# DataCue - AI-Powered Data Analysis Platform

Backend service for DataCue, an intelligent data ingestion and analysis system.

## Features

### File Ingestion Agent

- **File Support**: CSV, Excel (.xlsx, .xls) with multi-sheet support
- **Data Cleaning**: Automatic standardization, missing value handling, duplicate removal
- **Advanced Metadata Extraction**:
  - Chart recommendations per column
  - Time series detection
  - High cardinality detection
  - Smart column role classification
  - Data quality scoring (0-100)
  - Correlation analysis
  - Dataset-level insights

## Project Structure

```
backend/
├── agents/
│   └── file_ingestion_agent/
│       ├── ingestion_agent.py      # Main file processing agent
│       ├── data_cleaner.py         # Data cleaning logic
│       └── metadata_extractor.py   # Metadata & advanced features
├── requirements.txt                 # Python dependencies
└── test_agent.py                   # Quick verification test
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/DataCue.git
cd DataCue/backend
```

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from agents.file_ingestion_agent import FileIngestionAgent

# Initialize agent
agent = FileIngestionAgent()

# Ingest a file
result = agent.ingest_file('data.csv')

# Access results
if result['status'] == 'success':
    data = result['data']                    # Cleaned data
    metadata = result['metadata']            # Complete metadata
    preview = result['data_preview']         # First 10 rows
```

### Advanced Features

```python
# Data quality score
quality = metadata['data_quality_score']
print(f"Quality: {quality['overall_score']}/100 ({quality['rating']})")

# Chart recommendations
for col in metadata['columns']:
    print(f"{col['name']}: {col['chart_recommendations']}")
    print(f"  Role: {col['suggested_role']['role']}")
    print(f"  Time Series: {col['is_time_series']['is_time_series']}")

# Correlation analysis
for cor in metadata['correlation_matrix']['strong_correlations']:
    print(f"{cor['column1']} ↔ {cor['column2']}: {cor['correlation']}")
```

### Multi-Sheet Excel Support

```python
# List all sheets
sheets = agent.get_excel_sheets('workbook.xlsx')

# Process specific sheet
result = agent.ingest_file('workbook.xlsx', sheet_name='Sales')

# Process all sheets
all_results = agent.ingest_excel_all_sheets('workbook.xlsx')
```

## Testing

Run the verification test:

```bash
python test_agent.py
```

## Features Overview

### Data Cleaning

- Column name standardization
- Missing value handling (median/mode/forward fill)
- Duplicate removal
- Data type inference
- Empty row/column removal

### Metadata Extraction

- **Column Analysis**: Name, type, nulls, unique values
- **Numeric Stats**: Min, max, mean, median, std, quartiles
- **Categorical Stats**: Top values, frequencies
- **Datetime Stats**: Date ranges
- **Quality Metrics**: Completeness, uniqueness, validity

### Advanced Features

- **Chart Recommendations**: Auto-suggest appropriate visualizations
- **Time Series Detection**: Identify temporal columns
- **Column Roles**: Classify as measure, dimension, identifier, etc.
- **Data Quality Score**: 0-100 rating with component breakdown
- **Correlation Matrix**: Detect relationships between numeric columns
- **Smart Insights**: Dataset-level recommendations

## Dependencies

- pandas >= 2.3.2
- numpy >= 2.3.3
- openpyxl >= 3.1.2
- fastapi >= 0.116.1
- uvicorn >= 0.35.0
- python-multipart >= 0.0.20

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

- [ ] Dashboard Generator Agent
- [ ] Knowledge Agent (AI-powered querying)
- [ ] FastAPI REST endpoints
- [ ] MongoDB integration
- [ ] React frontend
- [ ] Export to PDF/Excel/HTML

## Authors

DataCue Team

## Acknowledgments

Built with Python, FastAPI, and modern data science libraries.
