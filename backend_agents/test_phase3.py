"""
Phase 3 Test Suite: Chat With CSV
Tests natural language query interface
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8001"
TEST_CSV_PATH = "datacue_sample.csv"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def test_health_check():
    """Test 1: Verify server is running"""
    print_header("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server status: {data.get('status')}")
            print_success(f"Service: {data.get('service')}")
            print_success(f"Phases: {data.get('phases')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False


def upload_test_csv():
    """Upload test CSV and return dataset_id and session_id"""
    print_header("Setup: Upload Test CSV")
    
    try:
        with open(TEST_CSV_PATH, 'rb') as f:
            files = {'file': (TEST_CSV_PATH, f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/ingestion/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            dataset_id = data['data']['dataset_id']
            session_id = data['data']['session_id']
            print_success(f"CSV uploaded successfully")
            print_info(f"Dataset ID: {dataset_id}")
            print_info(f"Session ID: {session_id}")
            print_info(f"Rows: {data['data']['row_count']}, Columns: {data['data']['column_count']}")
            return dataset_id, session_id
        else:
            print_error(f"Upload failed: {response.status_code}")
            return None, None
    except Exception as e:
        print_error(f"Upload error: {str(e)}")
        return None, None


def test_chat_query(dataset_id, session_id, question, test_num, expected_intent=None):
    """Test a chat query"""
    print_header(f"Test {test_num}: {question}")
    
    try:
        payload = {
            "dataset_id": dataset_id,
            "session_id": session_id,
            "question": question,
            "include_explanation": True
        }
        
        response = requests.post(f"{BASE_URL}/chat/query", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'success':
                print_success(f"Query executed successfully")
                print_info(f"Intent: {data['intent']}")
                print_info(f"Result Type: {data['result_type']}")
                
                # Display SQL query
                print(f"\n{Colors.YELLOW}SQL Query:{Colors.END}")
                print(f"{Colors.YELLOW}{data['sql_query']}{Colors.END}")
                
                # Display result based on type
                print(f"\n{Colors.BLUE}Result:{Colors.END}")
                if data['result_type'] == 'single_value':
                    value = data['data']['value']
                    print(f"{Colors.GREEN}{Colors.BOLD}{value}{Colors.END}")
                
                elif data['result_type'] == 'single_row':
                    for key, value in data['data'].items():
                        print(f"  {key}: {value}")
                
                elif data['result_type'] == 'rows' or data['result_type'] == 'grouped_numeric':
                    result_data = data['data']
                    if isinstance(result_data, list):
                        print(f"  Returned {len(result_data)} rows")
                        # Show first 5 rows
                        for i, row in enumerate(result_data[:5]):
                            print(f"  {i+1}. {row}")
                        if len(result_data) > 5:
                            print(f"  ... and {len(result_data)-5} more rows")
                
                # Display explanation
                if data['explanation']:
                    print(f"\n{Colors.CYAN}Explanation:{Colors.END}")
                    print(f"{Colors.CYAN}{data['explanation']}{Colors.END}")
                
                # Validate expected intent
                if expected_intent and data['intent'] != expected_intent:
                    print_error(f"Intent mismatch: expected '{expected_intent}', got '{data['intent']}'")
                
                return True
            else:
                print_error(f"Query failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print_error(f"API error: {response.status_code}")
            if response.text:
                print_error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print_error(f"Query error: {str(e)}")
        return False


def run_all_tests():
    """Run comprehensive Phase 3 test suite"""
    print(f"\n{Colors.BOLD}{Colors.UNDERLINE}PHASE 3 TEST SUITE: CHAT WITH CSV{Colors.END}")
    print(f"{Colors.BOLD}Testing natural language query interface{Colors.END}\n")
    
    # Test 1: Health check
    if not test_health_check():
        print_error("Server not ready. Exiting tests.")
        return
    
    # Setup: Upload test CSV
    dataset_id, session_id = upload_test_csv()
    if not dataset_id:
        print_error("Failed to upload CSV. Exiting tests.")
        return
    
    # Test suite with various question types
    test_cases = [
        {
            "question": "What is the total revenue?",
            "test_num": 2,
            "expected_intent": "kpi"
        },
        {
            "question": "Show me the average satisfaction rating",
            "test_num": 3,
            "expected_intent": "kpi"
        },
        {
            "question": "What are the top 5 products by revenue?",
            "test_num": 4,
            "expected_intent": "table"
        },
        {
            "question": "Show me all customers from the North region",
            "test_num": 5,
            "expected_intent": "table"
        },
        {
            "question": "What is the revenue by region?",
            "test_num": 6,
            "expected_intent": "chart"
        },
        {
            "question": "Average units sold by product",
            "test_num": 7,
            "expected_intent": "chart"
        },
        {
            "question": "How many unique customers are there?",
            "test_num": 8,
            "expected_intent": "kpi"
        },
        {
            "question": "What is the average age of customers?",
            "test_num": 9,
            "expected_intent": "kpi"
        },
        {
            "question": "Show me revenue breakdown by gender",
            "test_num": 10,
            "expected_intent": "chart"
        },
        {
            "question": "Which region has the highest average satisfaction?",
            "test_num": 11,
            "expected_intent": "table"
        }
    ]
    
    # Run all test cases
    results = []
    for test_case in test_cases:
        result = test_chat_query(
            dataset_id,
            session_id,
            test_case["question"],
            test_case["test_num"],
            test_case.get("expected_intent")
        )
        results.append(result)
    
    # Summary
    print_header("TEST SUMMARY")
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed_tests}")
    if failed_tests > 0:
        print_error(f"Failed: {failed_tests}")
    
    success_rate = (passed_tests / total_tests) * 100
    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Phase 3 acceptance criteria met: {success_rate:.0f}% success rate{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Phase 3 needs improvement: {success_rate:.0f}% success rate{Colors.END}")
    
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}\n")


if __name__ == "__main__":
    run_all_tests()
