# MongoDB Query Feature - Verification Checklist

## Pre-Deployment Checklist

### Environment Setup

- [ ] `MONGO_URI` is set in `.env`
- [ ] `GROQ_API_KEY` is set in `.env`
- [ ] MongoDB is accessible (test connection)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)

### Service Initialization

- [ ] Backend starts without errors
- [ ] Logs show: `DatasetService initialized with MongoDB`
- [ ] Logs show: `MongoQueryService initialized with Groq`
- [ ] No errors about missing configuration

### MongoDB Collections

- [ ] `session_dataset_rows` collection exists (after first upload)
- [ ] `session_datasets_meta` collection exists (after first upload)
- [ ] Indexes created successfully
  - `session_dataset_rows`: `(session_id, dataset_id)`
  - `session_datasets_meta`: `(session_id)` - unique

### API Endpoints

- [ ] `POST /ingestion/upload` accepts `session_id` parameter
- [ ] `POST /knowledge/ask-mongo` endpoint available
- [ ] OpenAPI docs show new endpoints at `http://localhost:8000/docs`

## Functional Testing

### Upload Flow

- [ ] Upload CSV without session_id (auto-generates)
- [ ] Upload CSV with custom session_id
- [ ] Response contains `mongo_storage.enabled: true`
- [ ] Response shows correct `rows_stored` count
- [ ] Verify rows in MongoDB: `db.session_dataset_rows.countDocuments()`

### Column Sanitization

- [ ] Special characters removed (`$`, `.`, etc.)
- [ ] Numbers prefixed with `col_`
- [ ] Spaces converted to underscores
- [ ] Original→sanitized mapping in metadata
- [ ] All field names lowercase

### Query Execution

- [ ] Simple count query works: "How many rows?"
- [ ] Sample query works: "Show me first 5 rows"
- [ ] Aggregation works: "What is the average?"
- [ ] Filtering works: "Show records where age > 30"
- [ ] Grouping works: "Count by category"

### Response Structure

- [ ] Response contains `success: true`
- [ ] Response has `answer` (natural language)
- [ ] Response has `pipeline` (MongoDB stages)
- [ ] Response has `data` (query results)
- [ ] Response has `method: "mongo_llm"`

### Error Handling

- [ ] Non-existent session returns 400
- [ ] Invalid question handled gracefully
- [ ] MongoDB connection error caught
- [ ] Groq API error handled
- [ ] Pipeline execution error returns error message

### Security

- [ ] Queries limited to session's data only
- [ ] Cannot query other sessions' data
- [ ] Dangerous operators blocked ($where, $function)
- [ ] Result limits enforced (max 50 raw rows)

## Performance Testing

### Upload Performance

- [ ] 100 rows: < 2 seconds
- [ ] 1,000 rows: < 5 seconds
- [ ] 10,000 rows: < 30 seconds

### Query Performance

- [ ] Simple count: < 1 second total
- [ ] Aggregation: < 2 seconds total
- [ ] Complex query: < 5 seconds total
- [ ] Groq response: 1-3 seconds
- [ ] MongoDB execution: < 100ms

### Concurrent Users

- [ ] Multiple sessions don't interfere
- [ ] Session isolation maintained
- [ ] No data leakage between sessions

## Integration Testing

### With Existing Features

- [ ] GridFS storage still works
- [ ] Knowledge agent still functions
- [ ] Dashboard generation unaffected
- [ ] Prediction service unaffected
- [ ] OTP/auth still works

### Backward Compatibility

- [ ] Old uploads without session_id work
- [ ] Existing endpoints unchanged
- [ ] No breaking changes to responses

## Documentation

- [ ] `MONGO_QUERY_GUIDE.md` complete
- [ ] `MONGO_QUERY_QUICKSTART.md` accurate
- [ ] `IMPLEMENTATION_SUMMARY_MONGO_QUERY.md` comprehensive
- [ ] Code comments clear
- [ ] API docs in OpenAPI/Swagger

## Testing Scripts

- [ ] `test_mongo_query.py` runs successfully
- [ ] All test sections pass
- [ ] Example curl commands work
- [ ] Manual test instructions accurate

## Deployment Readiness

### Production Environment

- [ ] MongoDB production instance configured
- [ ] Groq API key has sufficient quota
- [ ] Environment variables set in production
- [ ] Firewall rules allow MongoDB access
- [ ] SSL/TLS enabled for MongoDB connection

### Monitoring

- [ ] Log MongoDB connection status
- [ ] Log Groq API calls and errors
- [ ] Monitor query execution times
- [ ] Track storage usage
- [ ] Alert on service failures

### Scaling Considerations

- [ ] MongoDB indexes optimized
- [ ] Connection pooling configured
- [ ] Query timeout limits set
- [ ] Rate limiting on endpoints
- [ ] Consider Groq API rate limits

## User Acceptance

### End-User Testing

- [ ] Non-technical users can upload CSV
- [ ] Questions in plain English work
- [ ] Results are understandable
- [ ] Error messages are helpful
- [ ] Response times acceptable

### Frontend Integration

- [ ] Upload form sends session_id
- [ ] Chat interface calls `/ask-mongo`
- [ ] Results displayed properly
- [ ] Loading states shown
- [ ] Errors handled gracefully

## Sign-Off

### Technical Review

- [ ] Code reviewed by team
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Error handling comprehensive
- [ ] Logging adequate

### Business Review

- [ ] Feature meets requirements
- [ ] User experience validated
- [ ] Documentation complete
- [ ] Support team trained

---

## Test Results

**Date:** ******\_******  
**Tester:** ******\_******  
**Environment:** ******\_******

**Overall Status:**

- [ ] ✅ All checks passed - Ready for production
- [ ] ⚠️ Minor issues - Deploy with caution
- [ ] ❌ Blocking issues - Do not deploy

**Notes:**

---

---

---

**Approved by:** ******\_******  
**Date:** ******\_******
