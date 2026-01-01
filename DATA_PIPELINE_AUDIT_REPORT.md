# DataCue Data Pipeline Audit Report

**Date:** January 1, 2026  
**Auditor:** Principal Full-Stack Engineer  
**Focus:** End-to-end data integrity verification

---

## Executive Summary

**CRITICAL FINDINGS: Data loss detected in query result transformation layer**

✅ **PASSED:** File upload, data storage, aggregation queries  
❌ **FAILED:** Selection queries, data type preservation in results  
⚠️ **ISSUES:** 6 critical data loss points, 4 data transformation inconsistencies

---

## Test Results

### Test 1: File Upload & Storage ✅ PASSED

```
Input: 5 rows × 5 columns (name, age, salary, department, join_date)
- Strings: name, department
- Integers: age
- Floats: salary (50000.50, 45000.00, 60000.75, 52000.25, 55000.00)
- Dates: join_date

Result: Successfully stored in PostgreSQL
- Dataset ID: e72d59a9c9834f2e84069daa2fb6496f
- Session ID: e72d59a9c9834f2e84069daa2fb6496f
```

### Test 2: Aggregation Query ✅ PASSED

```
Query: "What is the total salary?"
Expected: 262,001.50
Received: 262,001.50
Difference: 0.00 ✅

Conclusion: Numeric aggregation preserves float precision
```

### Test 3: Selection Queries ❌ FAILED

```
3.1: String Query
Query: "Show me all unique departments"
Expected: ['Engineering', 'Sales', 'Marketing']
Received: Empty result (result_type: "text")

3.2: Float Precision Query
Query: "What is Alice's salary?"
Expected: 50000.50
Received: null/undefined

Conclusion: Non-aggregation queries lose data in result transformation
```

---

## Data Flow Analysis

### Pipeline Overview

```
CSV File
   ↓
[1] Frontend Upload (FormData)
   ↓
[2] Backend Ingestion Router
   ↓
[3] File Ingestion Agent
   ↓
[4] Data Cleaner (standardize, fill nulls, dedupe)
   ↓
[5] PostgreSQL Storage (DatasetRow.data JSON)
   ↓
[6] Query Retrieval (get_all_rows)
   ↓
[7] Pandas DataFrame Reconstruction
   ↓
[8] LLM Query Generation
   ↓
[9] Query Validation
   ↓
[10] Query Execution (eval in namespace)
   ↓
[11] Result Detection & Formatting
   ↓
[12] Frontend Rendering
```

---

## Critical Data Loss Points

### 🔴 ISSUE #1: Result Detector Type Misclassification

**Location:** `backend/agents/chat_agent/result_detector.py`

**Problem:** When query returns DataFrame, type detection fails for certain patterns

**Code:**

```python
def _detect_dataframe_type(self, df: pd.DataFrame, query: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    # Single cell result → KPI
    if len(df) == 1 and len(df.columns) == 1:
        value = df.iloc[0, 0]
        if isinstance(value, (int, float)):
            return self._format_kpi(value, query)
    # ...continues but may return wrong type
```

**Impact:** Query "Show me all unique departments" returns text instead of table  
**Data Loss:** ❌ Entire result set lost

---

### 🔴 ISSUE #2: Missing Result Data in Response

**Location:** `backend/agents/chat_agent/result_detector.py` (lines 200+)

**Problem:** Result transformation methods may not include actual data

**Evidence from test:**

```
Result type: text
Departments found: undefined
Values: (empty)
```

**Root Cause:** `_format_table()` or detection logic returns wrong structure  
**Data Loss:** ❌ Complete data payload missing

---

### 🔴 ISSUE #3: DataFrame-to-Dict Conversion Issues

**Location:** `backend/services/dataset_service.py:get_all_rows()`

**Code:**

```python
def get_all_rows(self, session_id: str, dataset_id: Optional[str] = None, limit: int = 10000):
    rows = db.query(DatasetRow).filter(...).order_by(DatasetRow.row_index).limit(limit).all()
    return [row.data for row in rows]  # Returns list of dicts
```

**Problem:** When reconstructed to DataFrame, column ordering may not be preserved  
**Impact:** Minimal - pandas handles dict lists well  
**Data Loss:** ⚠️ Potential column order shuffling

---

### 🔴 ISSUE #4: Query Result Serialization Gap

**Location:** `backend/agents/chat_agent/chat_agent.py:ask()`

**Code Flow:**

```python
# Step 4: Detect result type
detected = self.result_detector.detect(result=exec_result["raw_result"], ...)

# Step 5: Format response
return {
    "status": "success",
    "result": detected["data"],  # ← May be incomplete
    "result_type": detected["type"],
    "chart_config": detected.get("config", {}),
}
```

**Problem:** `detected["data"]` structure varies by type but frontend expects consistent format  
**Data Loss:** ❌ Data exists in DataFrame but not in response JSON

---

### 🟡 ISSUE #5: Data Cleaning Mutations (Non-Reversible)

**Location:** `backend/agents/file_ingestion_agent/data_cleaner.py`

**Mutations Applied:**

1. **Column Names:** Lowercased, special chars removed, spaces → underscores

   ```python
   # Original: "Employee Name" → "employee_name"
   # Original: "Salary ($)" → "salary"
   ```

   **Impact:** Frontend must use cleaned names, original metadata lost

2. **Missing Values:** Filled with median (numeric), mode (categorical), 'Unknown' (fallback)

   ```python
   if pd.api.types.is_numeric_dtype(df[col]):
       df[col].fillna(df[col].median(), inplace=True)
   ```

   **Impact:** ⚠️ Cannot distinguish between actual vs imputed values

3. **Duplicate Rows:** Silently removed

   ```python
   df = df.drop_duplicates()
   ```

   **Impact:** ⚠️ User not informed of removed rows

4. **Data Type Coercion:** Auto-converts strings to numeric/datetime when possible
   ```python
   converted_numeric = pd.to_numeric(df[col], errors='coerce')
   ```
   **Impact:** ⚠️ May incorrectly convert data (e.g., "1234" as product ID → integer)

---

### 🟡 ISSUE #6: Float Precision in JSON Storage

**Location:** `backend/services/dataset_service.py:store_dataset()`

**Code:**

```python
for col in dataframe.columns:
    value = row[col]
    if pd.isna(value):
        row_data[col] = None
    elif hasattr(value, 'item'):  # numpy type
        row_data[col] = value.item()  # ← Converts to Python native
```

**Test Result:** ✅ Precision preserved (50000.50 stored correctly)  
**Status:** Working correctly with PostgreSQL JSONB

---

## Data Transformation Inconsistencies

### 1. Column Naming Divergence

**Source → Stored → Frontend:**

```
CSV:          "Employee Name", "Salary ($)"
Cleaned:      "employee_name", "salary"
Frontend:     Must query with cleaned names (no mapping back)
```

**Issue:** Original column names irretrievable  
**Recommendation:** Store original_columns mapping in metadata

---

### 2. Multiple Data Representations

**Same dataset exists in 3 forms:**

| Format         | Location                               | Purpose         | Sync Status     |
| -------------- | -------------------------------------- | --------------- | --------------- |
| CSV Raw        | `uploads/` folder                      | Original file   | Not cleaned     |
| DataFrame dict | PostgreSQL `dataset_rows.data`         | Query execution | Cleaned ✅      |
| Plotly figures | MongoDB `chat_sessions.dashboard_data` | Visualization   | Pre-computed ❌ |

**Risk:** Frontend may render different data depending on source

---

### 3. Result Format Variation

**Backend returns inconsistent structures:**

```javascript
// Aggregation query
{ status: "success", result: { value: 262001.5 }, result_type: "kpi" }

// Table query (expected)
{ status: "success", result: [{...}, {...}], result_type: "table" }

// Table query (actual - BROKEN)
{ status: "success", result: undefined, result_type: "text" }
```

**Frontend normalizeAnswer()** tries to handle this but is fragile

---

### 4. Chart Data Duplication

**Location:** Dashboard generation

**Problem:** Charts contain both:

- `figure`: Plotly JSON with full data
- `data`: Raw data array (redundant)

**Example:**

```json
{
  "chart_id": "xyz",
  "figure": { "data": [{"x": [...], "y": [...]}] },
  "data": [{"x": 1, "y": 2}, ...]  // ← Duplicated
}
```

**Impact:** 2x storage usage, potential inconsistency

---

## Data Integrity Verification Matrix

| Stage            | Input     | Output    | Data Loss?            | Type Loss?        |
| ---------------- | --------- | --------- | --------------------- | ----------------- |
| File Upload      | CSV 5×5   | bytes     | ✅ None               | N/A               |
| CSV Parsing      | bytes     | DataFrame | ✅ None               | ✅ Preserved      |
| Data Cleaning    | DataFrame | DataFrame | ⚠️ Duplicates removed | ⚠️ Coerced        |
| PostgreSQL Store | DataFrame | JSON rows | ✅ None               | ✅ Preserved      |
| Row Retrieval    | JSON rows | DataFrame | ✅ None               | ✅ Preserved      |
| Query Execution  | DataFrame | Mixed     | ✅ None               | ✅ Preserved      |
| Result Detection | Mixed     | Dict      | ❌ **DATA LOST**      | ❌ **TYPE WRONG** |
| Frontend Display | Dict      | React     | ❌ Cannot render      | N/A               |

**Critical failure point:** Result Detection (step 11)

---

## Root Cause Analysis

### Why Selection Queries Fail

**Hypothesis:** LLM generates valid pandas code, but result format not handled

**Evidence:**

1. Aggregation works (returns scalar)
2. Selection fails (returns DataFrame/list)
3. Result detector checks for DataFrame but may misclassify

**Likely Code Path:**

```python
# LLM generates: df['department'].unique()
# Execution returns: numpy array ['Engineering', 'Sales', 'Marketing']
# Result detector: Doesn't recognize numpy array as table
# Returns: {"type": "text", "data": {"value": str(array)}}
# Frontend: Shows stringified array, not actual data
```

---

## Specific Code Issues Found

### Issue: Result Detector Missing Format Handler

**File:** `backend/agents/chat_agent/result_detector.py:detect()`

```python
def detect(self, result: Union[pd.DataFrame, pd.Series, int, float, str], ...):
    # Handles: int, float, str, pd.Series, pd.DataFrame
    # Missing: numpy array, list, dict

    # When query returns df['col'].unique():
    # Result is numpy.ndarray
    # Falls through to fallback:
    return {"type": "text", "data": {"value": str(result)}, "config": {}}
```

**Fix Required:** Add numpy array and list handling

---

### Issue: Format Methods Don't Return Data Properly

**File:** `backend/agents/chat_agent/result_detector.py:_format_table()`

**Current (line ~200+):**

```python
def _format_table(self, df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "type": "table",
        "data": df.to_dict('records'),  # Should work but verify keys
        "config": {...}
    }
```

**Verify:** This should return data correctly, but tests show empty results

---

## Data Pipeline Vulnerabilities

### Vulnerability #1: Unsafe Query Execution

```python
# File: chat_agent.py:_execute_query()
namespace = {'df': df, 'pd': pd, '__builtins__': safe_builtins}
result = eval(query, namespace)  # ← Code injection possible
```

**Risk:** Even with validation, LLM can be tricked  
**Example bypass:** `df.__class__.__bases__[0].__subclasses__()`

---

### Vulnerability #2: No Row Count Limits in Queries

```python
# User query: "Show me all data"
# LLM generates: df
# Execution returns: Entire DataFrame (could be 1M+ rows)
# Sent to frontend: JSON payload explodes
```

**Missing:** Result size validation before returning

---

### Vulnerability #3: Unconstrained Memory Usage

```python
# dataset_service.py:get_all_rows()
def get_all_rows(self, session_id: str, ..., limit: int = 10000):
    rows = db.query(DatasetRow).filter(...).limit(limit).all()
    return [row.data for row in rows]
```

**Issue:** Loads all rows into memory at once  
**Impact:** 10K rows × 50 cols = 500K dict entries in RAM

---

## Frontend Data Handling Issues

### Issue: Multiple localStorage Keys (Stale Data Risk)

**File:** `client/src/pages/ChatPage.jsx`

```javascript
localStorage.getItem("sessionId");
localStorage.getItem("chatSessionId"); // Duplicate
localStorage.getItem("sessionUserId");
localStorage.getItem("chatSessionUserId"); // Duplicate
```

**Risk:** Keys get out of sync, user loads wrong session's data

---

### Issue: normalizeAnswer() Cannot Handle All Types

**File:** `client/src/pages/ChatPage.jsx:normaliseAnswer()`

```javascript
const normaliseAnswer = (payload) => {
  if (payload.error) return payload.error;
  if (payload.answer) return payload.answer;
  if (payload.response) return payload.response;
  // ...tries many fields, may miss actual data
  return `Here is what I received:\n\`\`\`json\n${JSON.stringify(
    payload
  )}\n\`\`\``;
};
```

**Impact:** When result structure unexpected, shows raw JSON dump

---

## Recommendations (Priority Order)

### 🔴 CRITICAL (Fix Immediately)

1. **Fix Result Detector Type Handling**

   - Add numpy array detection
   - Add list detection
   - Ensure all DataFrame types formatted correctly

2. **Add Result Size Limits**

   ```python
   MAX_RESULT_ROWS = 1000
   if isinstance(result, pd.DataFrame) and len(result) > MAX_RESULT_ROWS:
       result = result.head(MAX_RESULT_ROWS)
       # Add truncation warning
   ```

3. **Consolidate localStorage Keys**
   - Use only `sessionId` and `datasetId`
   - Remove all duplicate keys

---

### 🟡 HIGH PRIORITY (Fix This Week)

4. **Store Original Column Names**

   ```python
   metadata = {
       "columns": [...],
       "original_column_names": {"employee_name": "Employee Name", ...}
   }
   ```

5. **Add Data Mutation Tracking**

   ```python
   cleaning_stats = {
       "duplicates_removed": 5,
       "missing_values_filled": 12,
       "columns_renamed": 3,
       "original_row_count": 100,
       "final_row_count": 95
   }
   ```

6. **Implement Result Schema Validation**
   ```python
   # Ensure all responses match
   class QueryResult(BaseModel):
       status: str
       result: Union[List[Dict], Dict, float, int, str]
       result_type: str
       insight: Optional[str]
   ```

---

### 🟢 MEDIUM PRIORITY (Fix This Month)

7. **Add Streaming for Large Results**
8. **Implement Query Result Caching**
9. **Add Data Lineage Tracking**
10. **Create Data Validation Tests**

---

## Test Coverage Gaps

**Missing Tests:**

- [ ] Multi-column selection queries
- [ ] Date range filtering
- [ ] String pattern matching
- [ ] NULL value handling in queries
- [ ] Large dataset (10K+ rows) queries
- [ ] Concurrent query execution
- [ ] Dashboard data staleness
- [ ] Frontend chart rendering with empty data

---

## Conclusion

**Overall Pipeline Status:** ⚠️ **PARTIALLY FUNCTIONAL**

**Working:**

- ✅ File upload and parsing
- ✅ Data cleaning and standardization
- ✅ PostgreSQL storage
- ✅ Aggregation queries
- ✅ Float precision preservation

**Broken:**

- ❌ Non-aggregation query results
- ❌ DataFrame result transformation
- ❌ String value retrieval
- ❌ Complex selection queries

**Critical Path to Fix:**

1. Debug `result_detector.py:detect()` for all return types
2. Add comprehensive logging in result transformation
3. Add unit tests for each query result type
4. Verify frontend can render all result types

**Estimated Fix Time:** 4-6 hours  
**Risk Level:** HIGH - Production deployment blocked

---

**Audit Completed:** January 1, 2026  
**Next Review:** After critical fixes implemented
