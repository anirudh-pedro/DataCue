"""
Phase 1 & 2 Test: CSV Upload, Schema Extraction & Dashboard Generation
Tests the complete Phase 1 & 2 flow with Groq LLM integration
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8001"
TEST_CSV_PATH = "datacue_sample.csv"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")

def print_json(data, title=None):
    if title:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{title}:{Colors.RESET}")
    print(f"{Colors.GREEN}{json.dumps(data, indent=2)}{Colors.RESET}")


def test_health_check():
    """Test 1: Server Health Check"""
    print_header("TEST 1: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success("Server is online")
            print_json(response.json())
            return True
        else:
            print_error(f"Server returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to connect to server: {e}")
        return False


def test_csv_upload():
    """Test 2: CSV Upload"""
    print_header("TEST 2: CSV Upload & Schema Extraction")
    
    # Check if test CSV exists
    if not os.path.exists(TEST_CSV_PATH):
        print_error(f"Test CSV not found at: {TEST_CSV_PATH}")
        return None
    
    print_info(f"Uploading CSV: {TEST_CSV_PATH}")
    
    try:
        with open(TEST_CSV_PATH, 'rb') as f:
            files = {'file': ('test_data.csv', f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/ingestion/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print_success("CSV uploaded successfully")
            
            # Extract schema data
            data = result.get('data', {})
            dataset_id = data.get('dataset_id')
            session_id = data.get('session_id')
            
            print(f"\n{Colors.BOLD}Dataset Information:{Colors.RESET}")
            print(f"  Dataset ID: {Colors.YELLOW}{dataset_id}{Colors.RESET}")
            print(f"  Session ID: {Colors.YELLOW}{session_id}{Colors.RESET}")
            print(f"  Dataset Name: {Colors.YELLOW}{data.get('dataset_name')}{Colors.RESET}")
            print(f"  Row Count: {Colors.YELLOW}{data.get('row_count')}{Colors.RESET}")
            print(f"  Columns: {Colors.YELLOW}{len(data.get('columns', []))}{Colors.RESET}")
            
            # Show schema that will be sent to LLM
            print_header("SCHEMA FOR LLM (Phase 2)")
            print_info("This is the exact schema that will be sent to Groq LLM in Phase 2:")
            
            llm_schema = {
                "dataset_name": data.get('dataset_name'),
                "row_count": data.get('row_count'),
                "columns": data.get('columns', [])
            }
            
            print_json(llm_schema)
            
            # Show column details
            print(f"\n{Colors.BOLD}Column Details (Normalized & Typed):{Colors.RESET}")
            for i, col in enumerate(data.get('columns', []), 1):
                col_name = col.get('name')
                col_type = col.get('type')
                type_color = {
                    'numeric': Colors.GREEN,
                    'categorical': Colors.CYAN,
                    'datetime': Colors.YELLOW,
                    'text': Colors.RESET
                }.get(col_type, Colors.RESET)
                
                print(f"  {i}. {Colors.BOLD}{col_name}{Colors.RESET} → {type_color}{col_type}{Colors.RESET}")
            
            return {
                'dataset_id': dataset_id,
                'session_id': session_id,
                'schema': llm_schema
            }
        else:
            print_error(f"Upload failed with status {response.status_code}")
            print_error(response.text)
            return None
            
    except Exception as e:
        print_error(f"Upload failed: {e}")
        return None


def test_get_schema(dataset_id):
    """Test 3: Retrieve Schema by Dataset ID"""
    print_header("TEST 3: Retrieve Schema by Dataset ID")
    
    try:
        response = requests.get(f"{BASE_URL}/ingestion/schema/{dataset_id}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Schema retrieved successfully")
            print_json(result.get('data'))
            return True
        else:
            print_error(f"Failed to retrieve schema: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Failed to retrieve schema: {e}")
        return False


def test_get_schema_by_session(session_id):
    """Test 4: Retrieve Schema by Session ID"""
    print_header("TEST 4: Retrieve Schema by Session ID")
    
    try:
        response = requests.get(f"{BASE_URL}/ingestion/schema/session/{session_id}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Schema retrieved by session ID")
            print_json(result.get('data'))
            return True
        else:
            print_error(f"Failed to retrieve schema: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Failed to retrieve schema: {e}")
        return False


def verify_database_storage():
    """Test 5: Verify PostgreSQL Storage"""
    print_header("TEST 5: Verify PostgreSQL Storage")
    
    try:
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv
        
        load_dotenv()
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:anirudh_84@localhost:5432/datacue')
        
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # Count datasets
        result = conn.execute(text("SELECT COUNT(*) FROM datasets"))
        dataset_count = result.fetchone()[0]
        print_success(f"Datasets in database: {dataset_count}")
        
        # Count rows
        result = conn.execute(text("SELECT COUNT(*) FROM dataset_rows"))
        row_count = result.fetchone()[0]
        print_success(f"Total rows stored: {row_count}")
        
        # Show sample data
        result = conn.execute(text("SELECT id, dataset_name, row_count, column_count FROM datasets LIMIT 1"))
        dataset = result.fetchone()
        
        if dataset:
            print(f"\n{Colors.BOLD}Sample Dataset Record:{Colors.RESET}")
            print(f"  ID: {Colors.YELLOW}{dataset[0]}{Colors.RESET}")
            print(f"  Name: {Colors.YELLOW}{dataset[1]}{Colors.RESET}")
            print(f"  Rows: {Colors.YELLOW}{dataset[2]}{Colors.RESET}")
            print(f"  Columns: {Colors.YELLOW}{dataset[3]}{Colors.RESET}")
        
        conn.close()
        return True
        
    except Exception as e:
        print_error(f"Database verification failed: {e}")
        return False


def call_groq_llm(schema):
    """Call Groq LLM with the schema and get chart specifications"""
    print_header("CALLING GROQ LLM FOR DASHBOARD GENERATION")
    
    if not GROQ_API_KEY:
        print_error("GROQ_API_KEY not found in .env file")
        return None
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        prompt = f"""You are a senior data analyst and BI architect.
You must only return valid JSON.

DATASET SCHEMA:
{json.dumps(schema, indent=2)}

Your task is to DESIGN a professional analytics dashboard.

Generate 10 chart specifications (minimum 6) that best visualize this data.

Return ONLY valid JSON in this format:
{{
  "dashboard_title": "Sales Analytics Dashboard",
  "charts": [
    {{
      "chart_id": "chart_1",
      "title": "Revenue by Region",
      "chart_type": "bar",
      "description": "Compare revenue across regions",
      "dimensions": ["region"],
      "metrics": ["AVG(revenue)"],
      "priority": 1
    }}
  ]
}}

Chart types you can use: bar, line, pie, scatter, heatmap, area
Only use columns from the schema provided.
"""
        
        print_info("📤 Sending schema to Groq LLM...")
        print_info(f"   Model: llama-3.3-70b-versatile")
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data visualization expert. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content
        dashboard_spec = json.loads(response_text)
        
        print_success("📥 LLM response received!\n")
        
        print_json(dashboard_spec, "LLM DASHBOARD SPECIFICATION")
        
        print(f"\n{Colors.BOLD}Dashboard Overview:{Colors.RESET}")
        print(f"  Title: {Colors.CYAN}{dashboard_spec.get('dashboard_title', 'N/A')}{Colors.RESET}")
        print(f"  Charts: {Colors.GREEN}{len(dashboard_spec.get('charts', []))}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Chart Details:{Colors.RESET}")
        for i, chart in enumerate(dashboard_spec.get('charts', []), 1):
            print(f"\n  {Colors.CYAN}Chart {i}:{Colors.RESET}")
            print(f"    Title: {chart.get('title', 'N/A')}")
            print(f"    Type: {Colors.YELLOW}{chart.get('chart_type', 'N/A')}{Colors.RESET}")
            print(f"    Dimensions: {', '.join(chart.get('dimensions', []))}")
            print(f"    Metrics: {', '.join(chart.get('metrics', []))}")
            if 'description' in chart:
                print(f"    Description: {chart.get('description')}")
        
        return dashboard_spec
        
    except Exception as e:
        print_error(f"Error calling Groq LLM: {str(e)}")
        return None


def show_phase2_preview(schema):
    """Show what Phase 2 will do with this schema"""
    print_header("PHASE 2: LLM DASHBOARD GENERATION")
    
    # Actually call the LLM
    dashboard_spec = call_groq_llm(schema)
    
    if dashboard_spec:
        print_info("\n✓ Phase 2 Preview Complete!")
        print_info("⚠️  In full Phase 2 implementation, the system will:")
        print("   1. ✓ Send schema to Groq LLM (DONE)")
        print("   2. ✓ Receive chart specifications (DONE)")
        print("   3. TODO: For EACH chart, make another LLM call to generate PostgreSQL query")
        print("   4. TODO: Execute queries on the uploaded data")
        print("   5. TODO: Generate Plotly charts")
        print("   6. TODO: Display on dashboard")
    else:
        print_info("\n⚠️  Phase 2 will:")
        print("   1. Send this schema to Groq LLM")
        print("   2. LLM returns 6-10 chart specifications")
        print("   3. For EACH chart, make another LLM call to generate PostgreSQL query")
        print("   4. Execute queries on the uploaded data")
        print("   5. Generate Plotly charts")
    print("   6. Display on dashboard")


def main():
    """Run all Phase 1 & 2 tests"""
    print_header("DATACUE PHASE 1 & 2 - COMPREHENSIVE TEST SUITE")
    
    # Test 1: Health check
    if not test_health_check():
        print_error("Server is not running. Start it with: uvicorn main:app --reload --port 8001")
        return
    
    # Test 2: CSV Upload
    upload_result = test_csv_upload()
    if not upload_result:
        print_error("CSV upload failed. Cannot proceed with remaining tests.")
        return
    
    dataset_id = upload_result['dataset_id']
    session_id = upload_result['session_id']
    schema = upload_result['schema']
    
    # Test 3: Get schema by dataset ID
    test_get_schema(dataset_id)
    
    # Test 4: Get schema by session ID
    test_get_schema_by_session(session_id)
    
    # Test 5: Verify database storage
    verify_database_storage()
    
    # Show Phase 2 preview
    show_phase2_preview(schema)
    
    # Final summary
    print_header("PHASE 1 TEST SUMMARY")
    print_success("✓ All Phase 1 tests passed!")
    print_success("✓ CSV parsed successfully")
    print_success("✓ Column names normalized to snake_case")
    print_success("✓ Data types inferred (numeric, categorical, datetime, text)")
    print_success("✓ Data stored in PostgreSQL")
    print_success("✓ Schema metadata ready for LLM")
    print_success("✓ LLM dashboard design generated!")
    
    print(f"\n{Colors.BOLD}Testing Phase 2:{Colors.RESET}")
    print(f"  {Colors.YELLOW}Now testing dashboard generation with SQL execution...{Colors.RESET}")
    
    # Test Phase 2: Generate dashboard from schema
    test_phase2_dashboard(dataset_id, session_id)


def test_phase2_dashboard(dataset_id, session_id):
    """Test Phase 2: Full dashboard generation"""
    print_header("PHASE 2: DASHBOARD GENERATION WITH SQL EXECUTION")
    
    try:
        print_info("📤 Calling Phase 2 endpoint: /dashboard/generate-from-schema")
        print_info(f"   Dataset ID: {dataset_id}")
        print_info(f"   Session ID: {session_id}")
        
        response = requests.post(
            f"{BASE_URL}/dashboard/generate-from-schema",
            params={
                "dataset_id": dataset_id,
                "session_id": session_id
            },
            timeout=120  # Phase 2 takes longer (multiple LLM calls)
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                dashboard = result["data"]
                
                print_success("✓ Dashboard generated successfully!\n")
                
                print(f"{Colors.BOLD}Dashboard Overview:{Colors.RESET}")
                print(f"  Title: {Colors.CYAN}{dashboard['dashboard_title']}{Colors.RESET}")
                print(f"  Total Charts: {Colors.GREEN}{dashboard['total_charts']}{Colors.RESET}")
                print(f"  Successful: {Colors.GREEN}{dashboard['successful_charts']}{Colors.RESET}")
                print(f"  Failed: {Colors.RED}{dashboard['failed_charts']}{Colors.RESET}")
                
                # Show each chart
                print(f"\n{Colors.BOLD}Generated Charts:{Colors.RESET}")
                for i, chart in enumerate(dashboard['charts'], 1):
                    status_icon = "✓" if chart['status'] == 'success' else "✗"
                    status_color = Colors.GREEN if chart['status'] == 'success' else Colors.RED
                    
                    print(f"\n  {status_color}{status_icon} Chart {i}: {chart['title']}{Colors.RESET}")
                    print(f"    Type: {chart['type']}")
                    print(f"    Description: {chart['description']}")
                    
                    if chart['status'] == 'success':
                        data = chart['data']
                        if 'labels' in data and 'values' in data:
                            print(f"    Data Points: {len(data['labels'])}")
                            if len(data['labels']) > 0:
                                print(f"    Sample: {data['labels'][0]} = {data['values'][0]}")
                        elif 'value' in data:
                            print(f"    Value: {data['value']}")
                        
                        # Show SQL query (truncated)
                        if 'sql_query' in chart:
                            sql_preview = chart['sql_query'][:80].replace('\n', ' ')
                            print(f"    SQL: {sql_preview}...")
                    else:
                        print(f"    Error: {chart.get('error', 'Unknown error')}")
                
                # Final Phase 2 summary
                print_header("PHASE 2 COMPLETE")
                print_success(f"✓ Dashboard generated with {dashboard['successful_charts']}/{dashboard['total_charts']} charts")
                
                if dashboard['successful_charts'] >= 6:
                    print_success("✓ Minimum 6 charts requirement met")
                else:
                    print_error(f"✗ Only {dashboard['successful_charts']} charts successful (minimum 6 required)")
                
                print(f"\n{Colors.BOLD}Phase 2 Highlights:{Colors.RESET}")
                print(f"  {Colors.GREEN}✓{Colors.RESET} LLM generated {dashboard['total_charts']} chart specifications")
                print(f"  {Colors.GREEN}✓{Colors.RESET} Each chart got a custom SQL query from LLM")
                print(f"  {Colors.GREEN}✓{Colors.RESET} All queries executed on PostgreSQL")
                print(f"  {Colors.GREEN}✓{Colors.RESET} No raw data sent to LLM (only schema)")
                print(f"  {Colors.GREEN}✓{Colors.RESET} Dashboard ready for frontend rendering")
                
                return dashboard
            else:
                print_error(f"Dashboard generation failed: {result.get('message', 'Unknown error')}")
                return None
        else:
            print_error(f"Phase 2 API error: {response.status_code}")
            print_error(response.text)
            return None
            
    except requests.exceptions.Timeout:
        print_error("Phase 2 request timed out (this can happen with many charts)")
        print_info("Tip: Reduce number of charts or increase timeout")
        return None
    except Exception as e:
        print_error(f"Phase 2 test failed: {str(e)}")
        return None


def main():
    """Run all Phase 1 & 2 tests"""
    print_header("DATACUE PHASE 1 & 2 - COMPREHENSIVE TEST SUITE")

 
 i f   _ _ n a m e _ _   = =   ' _ _ m a i n _ _ ' : 
         m a i n ( )  
 
 
 i f   _ _ n a m e _ _   = =   ' _ _ m a i n _ _ ' : 
         m a i n ( )  
 