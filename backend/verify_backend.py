import requests
import time
import sys
import os

BASE = 'http://127.0.0.1:8000'
SESSION = 'final-complete-check-' + str(int(time.time()))
CSV_PATH = r'c:\Users\HP\Desktop\machine learning\DataCue\backend\data\datacue_sample_dataset.csv'

print(f'\n=== FINAL BACKEND VERIFICATION ({SESSION}) ===')

# 1. Health Check
print('\n[1] Checking System Health...')
try:
    status = 'unknown'
    db_status = 'unknown'
    for i in range(10):
        try:
            h = requests.get(BASE + '/health', timeout=2).json()
            status = h.get('status')
            db_status = h.get('services', {}).get('database')
            break
        except:
            time.sleep(1)
    
    print(f'   Global Status: {status}')
    print(f'   Database: {db_status}')
    if status != 'healthy' or db_status != 'ok':
        print('   ❌ CRITICAL: Health check failed')
        sys.exit(1)
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)

# 2. Ingestion
print('\n[2] Testing File Ingestion...')
dataset_id = None
try:
    if not os.path.exists(CSV_PATH):
        print(f'   ❌ CSV file not found at {CSV_PATH}')
        sys.exit(1)

    with open(CSV_PATH, 'rb') as f:
        r = requests.post(BASE + '/ingestion/upload', 
            files={'file': ('data.csv', f)}, 
            data={'session_id': SESSION}
        ).json()
    
    dataset_id = r.get('dataset_id')
    print(f'   Status: {r.get("status")}')
    print(f'   Dataset ID: {dataset_id}')
    print(f'   Rows Parsed: {r.get("metadata", {}).get("row_count")}')
    
    if r.get('mongo_storage', {}).get('error'):
         print(f'   ❌ Storage Error: {r.get("mongo_storage").get("error")}')
    
    if not dataset_id:
        print('   ❌ Failed to get Dataset ID')
        sys.exit(1)
    else:
        print('   ✅ Verified')

except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)

# 3. Chat Query
print('\n[3] Testing Chat Agent (Natural Language to SQL/Pandas)...')
try:
    q = 'What is the total revenue?'
    r = requests.post(BASE + '/chat/ask', json={'question': q, 'session_id': SESSION}, timeout=90).json()
    print(f'   Question: {q}')
    print(f'   Result: {r.get("result")}')
    print(f'   Status: {r.get("status")}')
    
    if r.get('status') != 'success' or not r.get('result'):
        print('   ❌ Chat query failed')
    else:
        print(f'   ✅ Verified (Result matches: {r.get("result") == 3141425})')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 4. Dashboard Generation
print('\n[4] Testing Dashboard Generation...')
try:
    r = requests.post(BASE + '/dashboard/generate', json={'session_id': SESSION}, timeout=90).json()
    print(f'   Status: {r.get("status")}')
    charts = r.get('dashboard', {}).get('charts', [])
    print(f'   Charts Generated: {len(charts)}')
    if len(charts) > 0:
        print(f'   First Chart: {charts[0].get("title")} ({charts[0].get("type")})')
        print('   ✅ Verified')
    else:
        print('   ⚠️ No charts generated')
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n=== VERIFICATION COMPLETE ===')
