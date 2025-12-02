# MongoDB-Backed Natural Language Querying

## Overview

This feature enables natural language question answering directly against your uploaded CSV data using:

- **MongoDB** for storing dataset rows
- **Groq LLM** for translating questions into MongoDB aggregation pipelines
- **Automatic query execution** and result formatting

## Architecture

```
User Question → Groq LLM → MongoDB Pipeline → Execute → Results
     ↓              ↓             ↓              ↓          ↓
  "How many    [{"$group":   Collection     Raw Data    Formatted
   rows?"       ...}]       Query                      Answer
```

### Flow

1. **CSV Upload** → Rows stored in MongoDB with sanitized column names
2. **User asks question** → Sent to Groq with dataset context (schema, samples)
3. **Groq generates** → MongoDB aggregation pipeline in JSON
4. **Backend executes** → Pipeline against stored rows
5. **Results returned** → Structured data + natural language summary

## Setup

### 1. Environment Variables

Add to your `.env` file:

```env
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017/datacue

# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Optional: LLM Configuration
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500
```

### 2. Install Dependencies

Dependencies already included in `requirements.txt`:

- `pymongo==4.15.0`
- `groq` (for LLM calls)

### 3. Start MongoDB

**Using Docker:**

```bash
docker run -d -p 27017:27017 --name datacue-mongo mongo:latest
```

**Or use MongoDB Atlas** (cloud):

```env
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/datacue
```

## API Endpoints

### Upload CSV with Session

**POST** `/ingestion/upload`

```bash
curl -X POST http://localhost:8000/ingestion/upload \
  -F "file=@dataset.csv" \
  -F "session_id=my_session_123"
```

**Response:**

```json
{
  "success": true,
  "dataset_name": "dataset",
  "gridfs_id": "...",
  "mongo_storage": {
    "enabled": true,
    "session_id": "my_session_123",
    "dataset_id": "uuid-here",
    "rows_stored": 150
  }
}
```

### Ask Question via MongoDB

**POST** `/knowledge/ask-mongo`

```bash
curl -X POST http://localhost:8000/knowledge/ask-mongo \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session_123",
    "question": "What is the average age?"
  }'
```

**Response:**

```json
{
  "success": true,
  "method": "mongo_llm",
  "question": "What is the average age?",
  "answer": "The average age across all records is 32.5 years",
  "pipeline": [
    {
      "$group": {
        "_id": null,
        "avg_age": { "$avg": "$age" }
      }
    }
  ],
  "data": [{ "avg_age": 32.5 }]
}
```

## Services

### DatasetService (`services/dataset_service.py`)

Handles MongoDB storage and querying:

**Key Methods:**

- `store_dataset()` - Store CSV rows with sanitized columns
- `get_session_dataset()` - Retrieve dataset metadata
- `get_sample_rows()` - Get sample data for context
- `run_pipeline()` - Execute MongoDB aggregation
- `clear_session_data()` - Clean up session data

**Column Sanitization:**

- Removes special characters (`$`, `.`, etc.)
- Prefixes numbers with `col_`
- Converts to lowercase
- Maintains original→sanitized mapping

### MongoQueryService (`services/mongo_query_service.py`)

Translates natural language to MongoDB queries:

**Key Methods:**

- `ask()` - Main entry point for questions
- `_build_prompt()` - Creates context-rich prompt for Groq
- `_call_groq()` - Invokes LLM to generate pipeline
- `_prepend_security_filters()` - Ensures query isolation per session

**Security Features:**

- Automatic session/dataset filters
- Blocks dangerous operators (`$where`, `$function`, `$merge`, `$out`)
- Limits result size (max 50 raw rows)
- Field name validation

## Example Questions

### Simple Queries

- "How many rows are in the dataset?"
- "What are all the column names?"
- "Show me the first 10 rows"

### Aggregations

- "What is the average salary?"
- "Count records by department"
- "Sum total sales by region"

### Filtering

- "Show employees with age > 30"
- "Find all records from 2024"
- "List unique categories"

### Complex

- "What's the top 5 products by revenue?"
- "Show monthly trends in sales"
- "Group by category and calculate average price"

## Testing

### Automated Test

```bash
cd backend
python test_mongo_query.py
```

Tests:

1. CSV upload with session
2. Multiple question types
3. Error handling

### Manual Testing

1. **Start backend:**

   ```bash
   cd backend
   python main.py
   ```

2. **Upload dataset:**

   ```bash
   curl -X POST http://localhost:8000/ingestion/upload \
     -F "file=@data/datacue_sample_dataset.csv" \
     -F "session_id=test_123"
   ```

3. **Ask questions:**
   ```bash
   curl -X POST http://localhost:8000/knowledge/ask-mongo \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test_123", "question": "How many rows?"}'
   ```

## MongoDB Collections

### `session_dataset_rows`

Stores actual data rows:

```json
{
  "session_id": "abc123",
  "dataset_id": "uuid",
  "row_index": 0,
  "col_name": "John",
  "col_age": 30,
  "col_salary": 50000
}
```

**Indexes:**

- `(session_id, dataset_id)`
- `(dataset_id)`

### `session_datasets_meta`

Stores dataset metadata:

```json
{
  "session_id": "abc123",
  "dataset_id": "uuid",
  "dataset_name": "employees",
  "row_count": 150,
  "column_map": {
    "Name": "col_name",
    "Age": "col_age",
    "Salary": "col_salary"
  },
  "metadata": {...}
}
```

**Indexes:**

- `(session_id)` - unique

## Groq Prompt Engineering

The system provides Groq with:

1. **Schema** - Column names (original + sanitized) and data types
2. **Sample data** - 5 example documents
3. **Constraints** - Security rules, operators allowed
4. **Dataset info** - Row count, name
5. **User question** - Natural language query

Example prompt excerpt:

```
You are analyzing a MongoDB collection named `session_dataset_rows`.

AVAILABLE COLUMNS (use "field" name, NOT "original"):
[
  {"original": "Employee Name", "field": "col_employee_name", "data_type": "string"},
  {"original": "Salary", "field": "col_salary", "data_type": "number"}
]

SAMPLE DOCUMENTS:
[
  {"session_id": "...", "col_employee_name": "John", "col_salary": 50000},
  ...
]

USER QUESTION: What is the average salary?

Return JSON:
{
  "pipeline": [...],
  "summary": "..."
}
```

## Troubleshooting

### "MongoDB not configured"

- Ensure `MONGO_URI` is set in `.env`
- Verify MongoDB is running and accessible

### "No dataset found for this session"

- Upload CSV first with matching `session_id`
- Check upload response for `mongo_storage.enabled: true`

### "Groq did not return valid pipeline"

- Check `GROQ_API_KEY` is valid
- Try simpler questions first
- Check backend logs for Groq response

### Query execution fails

- Groq might generate invalid syntax
- Try rephrasing question
- Check logs for MongoDB error details

## Best Practices

### For Users

- Use specific, clear questions
- Reference actual column names when possible
- Start with simple queries, then increase complexity

### For Developers

- Monitor Groq token usage
- Implement caching for repeated questions
- Add query result pagination for large datasets
- Consider query timeout limits

## Integration with Frontend

### React/Vue Example

```javascript
// Upload with session
const uploadDataset = async (file, sessionId) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);

  const response = await fetch("/ingestion/upload", {
    method: "POST",
    body: formData,
  });

  return await response.json();
};

// Ask question
const askQuestion = async (sessionId, question) => {
  const response = await fetch("/knowledge/ask-mongo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });

  return await response.json();
};

// Usage
const session = "user_session_" + Date.now();
await uploadDataset(file, session);
const result = await askQuestion(session, "What's the total count?");
console.log(result.answer, result.data);
```

## Future Enhancements

- [ ] Query result caching
- [ ] Chart generation from results
- [ ] Query history per session
- [ ] Multi-dataset joins
- [ ] Streaming results for large queries
- [ ] Query optimization suggestions
- [ ] Natural language query builder UI

## Performance Considerations

- **Column sanitization**: One-time cost during upload
- **Groq latency**: ~1-3 seconds per question
- **MongoDB query**: Depends on dataset size and pipeline complexity
- **Result serialization**: BSON→JSON conversion overhead

**Optimization tips:**

- Index frequently queried fields
- Limit sample rows in prompt (default: 5)
- Use `$limit` in pipelines
- Consider result pagination

## Security

- Session isolation enforced automatically
- Dangerous MongoDB operators blocked
- Field name validation prevents injection
- API rate limiting recommended
- Session expiry/cleanup for storage management

---

**Version:** 1.0.0  
**Last Updated:** December 2024  
**Maintainer:** DataCue Team
