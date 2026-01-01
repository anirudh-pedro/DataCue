import requests
import json
import time
import os
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"
DATA_FILE = r"c:\Users\HP\Desktop\machine learning\DataCue\backend\data\datacue_sample_dataset.csv"
SESSION_ID = f"manual_test_{int(time.time())}"

def print_result(step_name, response, error=None):
    print(f"\n{'='*20} {step_name} {'='*20}")
    if error:
        print(f"❌ FAILED: {error}")
        return

    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("Response Body:")
        print(json.dumps(data, indent=2))
        
        # Check specific logical success conditions
        if response.status_code == 200:
            status = data.get("status")
            if status == "success" or status == "healthy":
                 print("✅ SUCCESS")
            else:
                 print(f"⚠️ STATUS: {status}")
    except json.JSONDecodeError:
        print("Response Text (Not JSON):")
        print(response.text)

def run_tests():
    print(f"Targeting Server: {BASE_URL}")
    print(f"Test Session ID: {SESSION_ID}")
    
    # 1. Health Check
    try:
        print("\n[1] Testing Health Endpoint...")
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print_result("Health Check", resp)
    except Exception as e:
        print(f"❌ Could not connect to server: {e}")
        return

    # 2. Ingestion
    if not os.path.exists(DATA_FILE):
        print(f"\n❌ Data file not found at: {DATA_FILE}")
        return

    try:
        print("\n[2] Testing File Ingestion...")
        with open(DATA_FILE, "rb") as f:
            files = {"file": ("manual_test_data.csv", f)}
            data = {"session_id": SESSION_ID}
            resp = requests.post(f"{BASE_URL}/ingestion/upload", files=files, data=data, timeout=30)
            print_result("Ingestion", resp)
            
            if resp.status_code == 200:
                json_resp = resp.json()
                if not json_resp.get("dataset_id"):
                    print("❌ No dataset_id returned! Aborting subsequent tests.")
                    return
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        return

    # 3. Chat Query
    try:
        print("\n[3] Testing Chat Query...")
        payload = {
            "session_id": SESSION_ID,
            "question": "What is the total revenue?"
        }
        resp = requests.post(f"{BASE_URL}/chat/ask", json=payload, timeout=60)
        print_result("Chat Query", resp)
    except Exception as e:
        print(f"❌ Chat query failed: {e}")

    # 4. Dashboard Generation
    try:
        print("\n[4] Testing Dashboard Generation...")
        payload = {
            "session_id": SESSION_ID
        }
        resp = requests.post(f"{BASE_URL}/dashboard/generate", json=payload, timeout=90)
        print_result("Dashboard Generation", resp)
    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}")

if __name__ == "__main__":
    run_tests()
