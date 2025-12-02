# Quick Start: MongoDB Query Feature

## Setup (5 minutes)

### 1. Configure Environment

Add to `backend/.env`:

```env
MONGO_URI=mongodb://localhost:27017/datacue
GROQ_API_KEY=your_groq_api_key_here
```

### 2. Start MongoDB

**Option A - Docker (Recommended):**

```bash
docker run -d -p 27017:27017 --name datacue-mongo mongo:latest
```

**Option B - Local MongoDB:**

- Download from https://www.mongodb.com/try/download/community
- Start service: `mongod`

**Option C - MongoDB Atlas (Cloud):**

- Create free cluster at https://cloud.mongodb.com
- Get connection string and update `MONGO_URI`

### 3. Start Backend

```bash
cd backend
python main.py
```

Look for: `MongoQueryService initialized with Groq` in logs

## Usage

### Step 1: Upload CSV

```bash
curl -X POST http://localhost:8000/ingestion/upload \
  -F "file=@data/datacue_sample_dataset.csv" \
  -F "session_id=my_session"
```

✓ Check response for `"mongo_storage": {"enabled": true}`

### Step 2: Ask Questions

```bash
curl -X POST http://localhost:8000/knowledge/ask-mongo \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "question": "How many rows are in the dataset?"
  }'
```

### Step 3: Try More Questions

```bash
# Count rows
"How many rows are there?"

# Show data
"Show me the first 5 rows"

# Aggregations
"What is the average of all numeric columns?"

# Filtering
"Show records where age > 30"

# Grouping
"Count records by category"
```

## Verify It's Working

Run the test script:

```bash
cd backend
python test_mongo_query.py
```

Expected output:

```
✓ Dataset uploaded successfully
✓ Rows stored in MongoDB: 150
✓ Query executed successfully
```

## Troubleshooting

| Issue                                | Solution                                           |
| ------------------------------------ | -------------------------------------------------- |
| "MongoDB not configured"             | Check `MONGO_URI` in `.env` and MongoDB is running |
| "No dataset found"                   | Upload CSV first with `session_id`                 |
| "Groq did not return valid pipeline" | Verify `GROQ_API_KEY` is correct                   |
| Connection refused                   | Ensure backend is running on port 8000             |

## Next Steps

1. Read full documentation: `MONGO_QUERY_GUIDE.md`
2. Test with your own datasets
3. Integrate with frontend chat interface
4. Explore complex aggregation queries

## Architecture Summary

```
CSV Upload → MongoDB Storage (sanitized columns)
                     ↓
User Question → Groq LLM (generates Mongo pipeline)
                     ↓
Execute Pipeline → MongoDB Collection
                     ↓
Results → Formatted Answer + Data
```

**Key Benefits:**

- No need to load entire dataset into memory
- Fast queries via MongoDB indexes
- Natural language interface
- Structured results with context
