"""Quick API test script"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("=== Testing Health Endpoint ===")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_ingestion():
    print("\n=== Testing Ingestion Upload ===")
    csv_path = r"C:\Users\HP\Desktop\machine learning\DataCue\backend\data\datacue_sample_dataset.csv"
    try:
        with open(csv_path, 'rb') as f:
            files = {'file': ('datacue_sample_dataset.csv', f, 'text/csv')}
            data = {'session_id': 'test-session-123'}
            resp = requests.post(
                f"{BASE_URL}/ingestion/upload", 
                files=files, 
                data=data, 
                timeout=30
            )
            print(f"Status: {resp.status_code}")
            result = resp.json()
            print(f"Full response: {json.dumps(result, indent=2, default=str)[:2000]}")
            if resp.status_code == 200:
                print(f"\nSuccess: {result.get('success', False)}")
                meta = result.get('metadata', {})
                print(f"Rows: {meta.get('row_count', 0)}")
                print(f"Columns: {meta.get('column_count', 0)}")
            return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_dashboard():
    print("\n=== Testing Dashboard Generate ===")
    try:
        payload = {
            "session_id": "test-session-123"
        }
        resp = requests.post(
            f"{BASE_URL}/dashboard/generate",
            json=payload,
            timeout=60
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            print(f"Response keys: {list(result.keys())}")
            print(f"Status field: {result.get('status')}")
            
            # If error, print message
            if result.get('status') == 'error':
                print(f"Error message: {result.get('message')}")
                return
            
            # Check for dashboard structure
            dashboard = result.get('dashboard', {})
            if dashboard:
                charts = dashboard.get('charts', [])
                print(f"Dashboard title: {dashboard.get('title')}")
                print(f"Charts generated: {len(charts)}")
                for i, chart in enumerate(charts[:3]):
                    print(f"  Chart {i+1}: {chart.get('chart_type')} - {chart.get('title', 'No title')}")
            else:
                # Fallback to old structure
                charts = result.get('charts', [])
                print(f"Charts generated: {len(charts)}")
                for i, chart in enumerate(charts[:3]):
                    print(f"  Chart {i+1}: {chart.get('chart_type')} - {chart.get('title', 'No title')}")
            
            # Print insights
            insights = result.get('insights', [])
            if insights:
                print(f"Insights: {len(insights)}")
                for insight in insights[:2]:
                    print(f"  - {insight[:100]}...")
        else:
            print(f"Error: {resp.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_chat_ask():
    print("\n=== Testing Chat Ask ===")
    questions = [
        "What is the total revenue?",
        "Show the average age by region",
        "How many customers are there?"
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        try:
            payload = {
                "question": question,
                "session_id": "test-session-123"
            }
            resp = requests.post(
                f"{BASE_URL}/chat/ask",
                json=payload,
                timeout=60
            )
            if resp.status_code == 200:
                result = resp.json()
                status = result.get('status')
                if status == 'success':
                    print(f"  ✓ Type: {result.get('result_type')}")
                    print(f"  ✓ Query: {result.get('query_used', 'N/A')}")
                    print(f"  ✓ Result: {str(result.get('result'))[:100]}")
                else:
                    print(f"  ✗ Error: {result.get('message')}")
            else:
                print(f"  ✗ HTTP {resp.status_code}: {resp.json().get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")

if __name__ == "__main__":
    print("DataCue API Test\n" + "="*40)
    
    if test_health():
        ingestion_result = test_ingestion()
        if ingestion_result:
            test_dashboard()
            test_chat_ask()
    else:
        print("\nServer not running. Start with:")
        print("  uvicorn main:app --reload --port 8000")
