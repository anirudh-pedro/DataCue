"""
Test MongoDB-backed Groq query flow end-to-end.

This script tests:
1. Upload CSV with session_id
2. Verify rows stored in MongoDB
3. Ask natural language questions
4. Verify Groq generates valid MongoDB queries
5. Verify results are returned correctly
"""

import json
import sys
import time
from pathlib import Path

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TEST_CSV = Path(__file__).parent / "data" / "datacue_sample_dataset.csv"
SESSION_ID = f"test_session_{int(time.time())}"


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_result(success: bool, message: str):
    """Print a formatted result."""
    status = "✓" if success else "✗"
    print(f"{status} {message}")


def test_upload_dataset():
    """Test 1: Upload CSV with session_id."""
    print_section("TEST 1: Upload Dataset with Session ID")
    
    if not TEST_CSV.exists():
        print_result(False, f"Test CSV not found: {TEST_CSV}")
        return None
    
    with open(TEST_CSV, "rb") as f:
        files = {"file": (TEST_CSV.name, f, "text/csv")}
        data = {"session_id": SESSION_ID}
        
        try:
            response = requests.post(
                f"{BASE_URL}/ingestion/upload",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print_result(True, "Dataset uploaded successfully")
                
                # Check MongoDB storage info
                mongo_storage = result.get("mongo_storage", {})
                if mongo_storage.get("enabled"):
                    print_result(True, f"Rows stored in MongoDB: {mongo_storage.get('rows_stored')}")
                    print_result(True, f"Session ID: {mongo_storage.get('session_id')}")
                    print_result(True, f"Dataset ID: {mongo_storage.get('dataset_id')}")
                    return result
                else:
                    print_result(False, f"MongoDB storage not enabled: {mongo_storage.get('error')}")
                    return None
            else:
                print_result(False, f"Upload failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            print_result(False, "Cannot connect to backend. Is the server running on port 8000?")
            return None
        except Exception as e:
            print_result(False, f"Upload error: {e}")
            return None


def test_ask_mongo_questions(upload_result):
    """Test 2: Ask questions using MongoDB backend."""
    print_section("TEST 2: Ask Questions via Groq + MongoDB")
    
    if not upload_result:
        print_result(False, "Skipping - no upload result")
        return
    
    # Define test questions
    questions = [
        "How many rows are in the dataset?",
        "What are the column names?",
        "Show me the first 5 rows",
        "What is the average of all numeric columns?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}: {question}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/knowledge/ask-mongo",
                json={
                    "session_id": SESSION_ID,
                    "question": question
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    print_result(True, "Query executed successfully")
                    print(f"   Answer: {result.get('answer')}")
                    print(f"   Method: {result.get('method')}")
                    
                    # Show pipeline (first 2 stages only for brevity)
                    pipeline = result.get("pipeline", [])
                    if pipeline:
                        print(f"   Pipeline preview: {json.dumps(pipeline[:2], indent=4)}")
                    
                    # Show data count
                    data = result.get("data", [])
                    print(f"   Results: {len(data)} record(s)")
                    
                    # Show first result if available
                    if data:
                        print(f"   First result: {json.dumps(data[0], indent=4)}")
                else:
                    print_result(False, f"Query failed: {result.get('error')}")
            else:
                print_result(False, f"Request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print_result(False, f"Question error: {e}")


def test_error_handling():
    """Test 3: Error handling for invalid requests."""
    print_section("TEST 3: Error Handling")
    
    # Test with non-existent session
    print("\n--- Test: Non-existent session")
    try:
        response = requests.post(
            f"{BASE_URL}/knowledge/ask-mongo",
            json={
                "session_id": "non_existent_session_12345",
                "question": "How many rows?"
            },
            timeout=10
        )
        
        if response.status_code == 400:
            result = response.json()
            print_result(True, f"Correctly returned 400: {result.get('detail')}")
        else:
            print_result(False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        print_result(False, f"Error test failed: {e}")


def main():
    """Run all tests."""
    print_section("MongoDB-Backed Groq Query System Test")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test CSV: {TEST_CSV}")
    print(f"Session ID: {SESSION_ID}")
    
    # Test 1: Upload
    upload_result = test_upload_dataset()
    
    if not upload_result:
        print("\n❌ Upload failed. Ensure:")
        print("  1. Backend server is running (python main.py)")
        print("  2. MONGO_URI is set in .env")
        print("  3. GROQ_API_KEY is set in .env")
        print("  4. MongoDB is accessible")
        sys.exit(1)
    
    # Test 2: Questions
    test_ask_mongo_questions(upload_result)
    
    # Test 3: Error handling
    test_error_handling()
    
    print_section("Test Summary")
    print("✓ All tests completed")
    print(f"\nSession ID for manual testing: {SESSION_ID}")
    print("\nYou can now test in the browser or use curl:")
    print(f"""
    curl -X POST {BASE_URL}/knowledge/ask-mongo \\
      -H "Content-Type: application/json" \\
      -d '{{"session_id": "{SESSION_ID}", "question": "What is the total count?"}}'
    """)


if __name__ == "__main__":
    main()
