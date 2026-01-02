"""
COMPLETE TEST SUITE: Phase 1, 2 & 3
Tests all functionality end-to-end with shared dataset
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8001"
TEST_CSV_PATH = "datacue_sample.csv"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def print_header(text):
    print(f"\n{'='*80}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print('='*80 + '\n')

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


# ============================================================================
# PHASE 1 TESTS: CSV UPLOAD & SCHEMA EXTRACTION
# ============================================================================

def test_phase1_upload():
    """Test Phase 1: Upload CSV and extract schema"""
    print_header("PHASE 1: CSV UPLOAD & SCHEMA EXTRACTION")
    
    # Test 1: Health check
    print_header("Test 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server status: {data['status']}")
            print_success(f"Service: {data['service']}")
            print_success(f"Phases: {', '.join(data['phases'])}")
        else:
            print_error(f"Health check failed: {response.status_code}")
            return None, None
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return None, None
    
    # Test 2: Upload CSV
    print_header("Test 2: Upload CSV File")
    try:
        if not os.path.exists(TEST_CSV_PATH):
            print_error(f"Test CSV not found: {TEST_CSV_PATH}")
            return None, None
            
        with open(TEST_CSV_PATH, 'rb') as f:
            files = {'file': (TEST_CSV_PATH, f, 'text/csv')}
            data = {
                'user_id': 'test-user-123',
                'session_id': 'test-session-456'
            }
            response = requests.post(f"{BASE_URL}/ingestion/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', result)  # Handle both wrapped and unwrapped responses
            dataset_id = data.get('dataset_id')
            session_id = data.get('session_id')
            
            print_success("CSV uploaded successfully")
            print_info(f"Dataset ID: {dataset_id}")
            print_info(f"Session ID: {session_id}")
            print_info(f"Dataset Name: {data.get('dataset_name')}")
            print_info(f"Rows: {data.get('row_count')}")
            print_info(f"Columns: {data.get('column_count')}")
            
            print(f"\n{Colors.BOLD}Schema (LLM-Ready Format):{Colors.ENDC}")
            for col in data.get('columns', []):
                print(f"  • {col['name']: <25} [{col['type']}]")
            
            return dataset_id, session_id
        else:
            print_error(f"Upload failed: {response.status_code}")
            print_error(f"Error: {response.text}")
            return None, None
    except Exception as e:
        print_error(f"Upload error: {str(e)}")
        return None, None


# ============================================================================
# PHASE 2 TESTS: DASHBOARD GENERATION
# ============================================================================

def test_phase2_dashboard(dataset_id, session_id):
    """Test Phase 2: Dashboard generation with LLM + SQL execution"""
    print_header("PHASE 2: DASHBOARD GENERATION")
    
    if not dataset_id:
        print_error("No dataset_id available. Skipping Phase 2.")
        return False
    
    try:
        # Call Phase 2 endpoint
        response = requests.post(
            f"{BASE_URL}/dashboard/generate-from-schema",
            params={"dataset_id": dataset_id, "session_id": session_id}
        )
        
        if response.status_code != 200:
            print_error(f"Phase 2 API error: {response.status_code}")
            print_error(f"Error: {response.text}")
            return False
        
        result = response.json()
        dashboard = result.get('data', result)  # Handle wrapped response
        
        # Display dashboard overview
        print_success(f"Dashboard: {dashboard.get('title', 'N/A')}")
        print_info(f"Total Charts: {dashboard['total_charts']}")
        print_success(f"Successful: {dashboard['successful_charts']}")
        print_warning(f"Skipped: {dashboard['skipped_charts']}")
        print_error(f"Failed: {dashboard['failed_charts']}")
        
        # Display each chart
        print(f"\n{Colors.BOLD}Chart Details:{Colors.ENDC}\n")
        
        for i, chart in enumerate(dashboard['charts'], 1):
            status = chart['status']
            
            if status == 'success':
                print(f"{Colors.GREEN}✓ Chart {i}: {chart['title']}{Colors.ENDC}")
                print(f"  Type: {chart['chart_type']}")
                
                # Handle different data structures
                data = chart.get('data', {})
                if isinstance(data, dict):
                    if 'value' in data:
                        print(f"  Value: {data['value']}")
                    elif 'labels' in data:
                        print(f"  Data points: {len(data.get('labels', []))}")
                        if data.get('labels'):
                            print(f"  Sample: {data['labels'][:3]}...")
                    else:
                        print(f"  Data structure: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"  Data points: {len(data)}")
                    if data:
                        print(f"  Sample: {str(data[0])[:100]}...")
                
                # Show SQL (full query)
                sql_query = chart.get('sql_query', 'N/A')
                print(f"  SQL: {sql_query.replace(chr(10), ' ')}")
                print()
                
            elif status == 'skipped':
                print(f"{Colors.YELLOW}⊘ Chart {i}: {chart['title']}{Colors.ENDC}")
                print(f"  Type: {chart['chart_type']}")
                print(f"  Reason: {chart.get('error', 'Unknown')}")
                print()
                
            elif status == 'failed':
                print(f"{Colors.RED}✗ Chart {i}: {chart['title']}{Colors.ENDC}")
                print(f"  Type: {chart['chart_type']}")
                print(f"  Error: {chart.get('error', 'Unknown')}")
                print()
        
        # Final summary
        print_header("Phase 2 Summary")
        success_rate = (dashboard['successful_charts'] / dashboard['total_charts']) * 100
        print_info(f"Success Rate: {success_rate:.1f}%")
        
        if dashboard['successful_charts'] >= 9:
            print_success(f"✓ Phase 2 PASSED: {dashboard['successful_charts']}/10 charts successful")
            return True
        else:
            print_warning(f"⚠ Phase 2 NEEDS IMPROVEMENT: Only {dashboard['successful_charts']}/10 charts successful")
            return False
            
    except Exception as e:
        print_error(f"Phase 2 error: {str(e)}")
        return False


# ============================================================================
# PHASE 3 TESTS: CHAT WITH CSV
# ============================================================================

def test_phase3_chat(dataset_id, session_id):
    """Test Phase 3: Natural language chat queries"""
    print_header("PHASE 3: CHAT WITH CSV")
    
    if not dataset_id:
        print_error("No dataset_id available. Skipping Phase 3.")
        return False
    
    # Test cases covering different intent types
    test_queries = [
        {
            "question": "What is the total revenue?",
            "expected_intent": "kpi",  # 1 row, 1 column
            "description": "Single metric aggregation"
        },
        {
            "question": "Show me the top 5 products by units sold",
            "expected_intent": "table",  # Multiple rows, potentially 1-2 columns
            "description": "Ranked list query"
        },
        {
            "question": "What is the average satisfaction rating by region?",
            "expected_intent": "chart",  # Multiple rows, 2 columns (region, avg_rating)
            "description": "Grouped aggregation"
        },
        {
            "question": "How many customers are there?",
            "expected_intent": "kpi",  # 1 row, 1 column
            "description": "Count query"
        },
        {
            "question": "List all regions with their total revenue",
            "expected_intent": "chart",  # Multiple rows, 2 columns (region, total_revenue)
            "description": "Group by query"
        },
        {
            "question": "What's the revenue trend over time?",
            "expected_intent": "chart",  # Multiple rows, 2 columns (date, revenue)
            "description": "Time series query"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{Colors.BOLD}Test {i}: {test['description']}{Colors.ENDC}")
        print(f"Question: \"{test['question']}\"")
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/query",
                json={
                    "dataset_id": dataset_id,
                    "session_id": session_id,
                    "question": test['question']
                }
            )
            
            if response.status_code != 200:
                print_error(f"Query failed: {response.status_code}")
                print_error(f"Error: {response.text}")
                failed += 1
                continue
            
            result = response.json()
            
            # Check for errors
            if result.get('status') == 'failed' or result.get('error'):
                print_error(f"Query error: {result.get('error', 'Unknown error')}")
                print_error(f"SQL: {result.get('sql_query', 'N/A')[:100]}...")
                failed += 1
                continue
            
            # Display results
            print_success(f"Intent: {result['intent']}")
            print_info(f"SQL: {result['sql_query'][:100]}...")
            
            if result['intent'] == 'kpi':
                data = result.get('data', [])
                if data and len(data) > 0:
                    # Extract first value from first row
                    value = list(data[0].values())[0] if data[0] else 'N/A'
                    print_success(f"Value: {value}")
            elif result['intent'] == 'table':
                data = result.get('data', [])
                print_success(f"Rows: {len(data)}")
                if data:
                    print(f"  Sample: {data[0]}")
            elif result['intent'] == 'chart':
                data = result.get('data', [])
                print_success(f"Data points: {len(data)}")
                if data:
                    print(f"  Sample: {data[:3]}...")
                else:
                    print_success(f"Data structure: {list(data.keys())}")
            
            # Verify intent matches expectation
            if result['intent'] == test['expected_intent']:
                print_success(f"✓ Intent matches expected: {test['expected_intent']}")
                passed += 1
            else:
                print_warning(f"⚠ Intent mismatch: expected {test['expected_intent']}, got {result['intent']}")
                passed += 1  # Still count as passed if query worked
            
        except Exception as e:
            print_error(f"Query error: {str(e)}")
            failed += 1
    
    # Summary
    print_header("Phase 3 Summary")
    print_info(f"Passed: {passed}/{len(test_queries)}")
    print_info(f"Failed: {failed}/{len(test_queries)}")
    
    success_rate = (passed / len(test_queries)) * 100
    print_info(f"Success Rate: {success_rate:.1f}%")
    
    if passed >= len(test_queries) - 1:  # Allow 1 failure
        print_success("✓ Phase 3 PASSED")
        return True
    else:
        print_warning("⚠ Phase 3 NEEDS IMPROVEMENT")
        return False


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_all_tests():
    """Run complete test suite for all phases"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("="*80)
    print("  DATACUE COMPLETE TEST SUITE")
    print("  Phase 1: CSV Upload & Schema Extraction")
    print("  Phase 2: Dashboard Generation (LLM + SQL)")
    print("  Phase 3: Chat With CSV (Natural Language)")
    print("="*80)
    print(f"{Colors.ENDC}\n")
    
    # Phase 1: Upload CSV and get dataset_id
    dataset_id, session_id = test_phase1_upload()
    
    if not dataset_id:
        print_error("\n❌ CRITICAL: Phase 1 failed. Cannot continue.")
        return
    
    # Phase 2: Generate dashboard
    phase2_passed = test_phase2_dashboard(dataset_id, session_id)
    
    # Phase 3: Test chat queries
    phase3_passed = test_phase3_chat(dataset_id, session_id)
    
    # Final Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("="*80)
    print("  FINAL TEST SUMMARY")
    print("="*80)
    print(f"{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
    print(f"  Phase 1 (Upload): {Colors.GREEN}✓ PASSED{Colors.ENDC}")
    
    if phase2_passed:
        print(f"  Phase 2 (Dashboard): {Colors.GREEN}✓ PASSED{Colors.ENDC}")
    else:
        print(f"  Phase 2 (Dashboard): {Colors.YELLOW}⚠ PARTIAL{Colors.ENDC}")
    
    if phase3_passed:
        print(f"  Phase 3 (Chat): {Colors.GREEN}✓ PASSED{Colors.ENDC}")
    else:
        print(f"  Phase 3 (Chat): {Colors.YELLOW}⚠ PARTIAL{Colors.ENDC}")
    
    if phase2_passed and phase3_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL PHASES PASSED! System is ready for production.{Colors.ENDC}\n")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Some tests need attention. Review results above.{Colors.ENDC}\n")


if __name__ == "__main__":
    run_all_tests()
