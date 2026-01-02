"""
Comprehensive Test Suite for Enhanced Dashboard Agent
Tests all layers: prompts, planning, validation, chart building, insights
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from agents.dashboard_agent import EnhancedDashboardAgent
from agents.dashboard_agent.structured_prompts import (
    build_dashboard_planner_prompt,
    build_sql_generation_prompt,
    build_insights_prompt,
    validate_sql_safety,
    validate_columns_exist,
    extract_json_from_response
)

# ANSI color codes for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(80)}{Colors.END}")
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

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_section(text):
    """Print section header"""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}{text}{Colors.END}")

# ============================================================================
# TEST DATA LOADING
# ============================================================================

def load_test_data():
    """Load test CSV data"""
    print_section("Loading Test Data")
    
    csv_path = Path(__file__).parent / "data" / "datacue_sample_dataset.csv"
    
    if not csv_path.exists():
        print_error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    print_success(f"Loaded CSV: {csv_path.name}")
    print_info(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print_info(f"Columns: {', '.join(df.columns.tolist())}")
    
    # Generate metadata
    metadata = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": []
    }
    
    for col in df.columns:
        dtype = df[col].dtype
        if dtype in ['int64', 'float64']:
            col_type = 'numeric'
        elif dtype == 'object':
            col_type = 'categorical'
        elif dtype == 'datetime64[ns]':
            col_type = 'datetime'
        else:
            col_type = 'string'
        
        metadata["columns"].append({
            "name": col,
            "type": col_type,
            "unique_count": int(df[col].nunique()),
            "null_count": int(df[col].isnull().sum())
        })
    
    data = df.to_dict('records')
    
    return df, metadata, data

# ============================================================================
# LAYER 1: STRUCTURED PROMPTS TESTING
# ============================================================================

def test_prompt_generation(metadata):
    """Test prompt generation"""
    print_section("LAYER 1: Testing Structured Prompts Generation")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Dashboard Planner Prompt
    tests_total += 1
    try:
        prompt = build_dashboard_planner_prompt(metadata)
        assert len(prompt) > 100, "Prompt too short"
        assert "DATASET SCHEMA" in prompt, "Missing schema section"
        assert "INSTRUCTIONS" in prompt, "Missing instructions"
        assert "RETURN FORMAT" in prompt, "Missing format section"
        print_success("Dashboard Planner Prompt generated correctly")
        print_info(f"Prompt length: {len(prompt)} characters")
        tests_passed += 1
    except Exception as e:
        print_error(f"Dashboard Planner Prompt failed: {e}")
    
    # Test 2: SQL Generation Prompt
    tests_total += 1
    try:
        sql_prompt = build_sql_generation_prompt(
            table_name="uploaded_data",
            dimensions=["Region"],
            metrics=["AVG(Revenue)"],
            chart_type="bar"
        )
        assert len(sql_prompt) > 50, "SQL prompt too short"
        assert "RULES" in sql_prompt, "Missing rules section"
        assert "uploaded_data" in sql_prompt, "Table name missing"
        print_success("SQL Generation Prompt generated correctly")
        tests_passed += 1
    except Exception as e:
        print_error(f"SQL Generation Prompt failed: {e}")
    
    # Test 3: Insights Prompt
    tests_total += 1
    try:
        insights_prompt = build_insights_prompt(metadata, [])
        assert len(insights_prompt) > 50, "Insights prompt too short"
        assert "DATASET INFO" in insights_prompt, "Missing dataset info"
        print_success("Insights Prompt generated correctly")
        tests_passed += 1
    except Exception as e:
        print_error(f"Insights Prompt failed: {e}")
    
    print_info(f"\nLayer 1 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total

# ============================================================================
# LAYER 2: SQL SAFETY VALIDATION
# ============================================================================

def test_sql_safety():
    """Test SQL safety validation"""
    print_section("LAYER 2: Testing SQL Safety Validation")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Valid SELECT query
    tests_total += 1
    try:
        sql = "SELECT region, AVG(revenue) FROM uploaded_data GROUP BY region"
        result = validate_sql_safety(sql)
        assert result["safe"] == True, "Valid query marked as unsafe"
        print_success("Valid SELECT query passed validation")
        tests_passed += 1
    except Exception as e:
        print_error(f"Valid SELECT test failed: {e}")
    
    # Test 2: DROP keyword blocked
    tests_total += 1
    try:
        sql = "DROP TABLE uploaded_data"
        result = validate_sql_safety(sql)
        assert result["safe"] == False, "DROP query not blocked"
        print_success("DROP keyword correctly blocked")
        tests_passed += 1
    except Exception as e:
        print_error(f"DROP blocking test failed: {e}")
    
    # Test 3: DELETE keyword blocked
    tests_total += 1
    try:
        sql = "DELETE FROM uploaded_data WHERE id = 1"
        result = validate_sql_safety(sql)
        assert result["safe"] == False, "DELETE query not blocked"
        print_success("DELETE keyword correctly blocked")
        tests_passed += 1
    except Exception as e:
        print_error(f"DELETE blocking test failed: {e}")
    
    # Test 4: UPDATE keyword blocked
    tests_total += 1
    try:
        sql = "UPDATE uploaded_data SET revenue = 0"
        result = validate_sql_safety(sql)
        assert result["safe"] == False, "UPDATE query not blocked"
        print_success("UPDATE keyword correctly blocked")
        tests_passed += 1
    except Exception as e:
        print_error(f"UPDATE blocking test failed: {e}")
    
    # Test 5: Multiple statements blocked
    tests_total += 1
    try:
        sql = "SELECT * FROM table1; DROP TABLE table2;"
        result = validate_sql_safety(sql)
        assert result["safe"] == False, "Multiple statements not blocked"
        print_success("Multiple statements correctly blocked")
        tests_passed += 1
    except Exception as e:
        print_error(f"Multiple statements test failed: {e}")
    
    # Test 6: Non-SELECT query blocked
    tests_total += 1
    try:
        sql = "CREATE TABLE test (id INT)"
        result = validate_sql_safety(sql)
        assert result["safe"] == False, "Non-SELECT query not blocked"
        print_success("Non-SELECT query correctly blocked")
        tests_passed += 1
    except Exception as e:
        print_error(f"Non-SELECT test failed: {e}")
    
    print_info(f"\nLayer 2 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total

# ============================================================================
# LAYER 3: JSON EXTRACTION
# ============================================================================

def test_json_extraction():
    """Test JSON extraction from LLM responses"""
    print_section("LAYER 3: Testing JSON Extraction")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Plain JSON
    tests_total += 1
    try:
        text = '{"key": "value", "number": 42}'
        result = extract_json_from_response(text)
        assert result["key"] == "value", "JSON not parsed correctly"
        print_success("Plain JSON extracted correctly")
        tests_passed += 1
    except Exception as e:
        print_error(f"Plain JSON test failed: {e}")
    
    # Test 2: JSON in markdown code block
    tests_total += 1
    try:
        text = '```json\n{"key": "value"}\n```'
        result = extract_json_from_response(text)
        assert result["key"] == "value", "Markdown JSON not parsed"
        print_success("Markdown code block JSON extracted correctly")
        tests_passed += 1
    except Exception as e:
        print_error(f"Markdown JSON test failed: {e}")
    
    # Test 3: JSON with surrounding text
    tests_total += 1
    try:
        text = 'Here is the result:\n{"key": "value"}\nEnd of result'
        result = extract_json_from_response(text)
        assert result["key"] == "value", "JSON with text not parsed"
        print_success("JSON with surrounding text extracted correctly")
        tests_passed += 1
    except Exception as e:
        print_error(f"JSON with text test failed: {e}")
    
    # Test 4: Array JSON
    tests_total += 1
    try:
        text = '[{"id": 1}, {"id": 2}]'
        result = extract_json_from_response(text)
        assert len(result) == 2, "Array JSON not parsed"
        print_success("Array JSON extracted correctly")
        tests_passed += 1
    except Exception as e:
        print_error(f"Array JSON test failed: {e}")
    
    print_info(f"\nLayer 3 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total

# ============================================================================
# LAYER 4: DASHBOARD PLANNING
# ============================================================================

def test_dashboard_planning(agent, metadata):
    """Test dashboard planning phase"""
    print_section("LAYER 4: Testing Dashboard Planning")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Basic dashboard plan
    tests_total += 1
    try:
        plan = agent._plan_dashboard(metadata, None)
        assert "charts" in plan, "No charts in plan"
        assert len(plan["charts"]) >= agent.min_charts, f"Too few charts: {len(plan['charts'])}"
        assert len(plan["charts"]) <= agent.max_charts, f"Too many charts: {len(plan['charts'])}"
        print_success(f"Dashboard plan generated with {len(plan['charts'])} charts")
        
        # Validate chart structure
        for i, chart in enumerate(plan["charts"]):
            required_fields = ["chart_id", "title", "chart_type", "description", "dimensions", "metrics"]
            for field in required_fields:
                assert field in chart, f"Chart {i} missing field: {field}"
        
        print_success("All charts have required fields")
        tests_passed += 1
    except Exception as e:
        print_error(f"Dashboard planning failed: {e}")
        # Show fallback plan
        print_warning("Using fallback plan for remaining tests")
        plan = agent._fallback_dashboard_plan(metadata)
    
    # Test 2: Plan with user prompt
    tests_total += 1
    try:
        custom_plan = agent._plan_dashboard(metadata, "Focus on revenue analysis by region")
        assert "charts" in custom_plan, "No charts in custom plan"
        print_success("Custom dashboard plan generated with user prompt")
        tests_passed += 1
    except Exception as e:
        print_error(f"Custom dashboard planning failed: {e}")
    
    # Test 3: Chart types validation
    tests_total += 1
    try:
        valid_types = {"bar", "line", "pie", "histogram", "scatter", "box", "area"}
        for chart in plan["charts"]:
            chart_type = chart.get("chart_type", "").lower()
            assert chart_type in valid_types, f"Invalid chart type: {chart_type}"
        print_success("All chart types are valid")
        tests_passed += 1
    except Exception as e:
        print_error(f"Chart type validation failed: {e}")
    
    print_info(f"\nLayer 4 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total, plan

# ============================================================================
# LAYER 5: CHART BUILDING
# ============================================================================

def test_chart_building(agent, plan, df, metadata):
    """Test chart building from specifications"""
    print_section("LAYER 5: Testing Chart Building")
    
    tests_passed = 0
    tests_total = 0
    
    successful_charts = []
    
    for i, chart_spec in enumerate(plan["charts"][:5]):  # Test first 5 charts
        tests_total += 1
        chart_title = chart_spec.get("title", f"Chart {i+1}")
        
        try:
            chart = agent._build_chart_from_spec(chart_spec, df, metadata)
            
            if chart:
                # Validate chart structure
                assert "figure" in chart, "Chart missing figure"
                assert "data" in chart["figure"], "Figure missing data"
                assert "layout" in chart["figure"], "Figure missing layout"
                assert len(chart["figure"]["data"]) > 0, "Figure has no data traces"
                
                print_success(f"Chart '{chart_title}' built successfully")
                successful_charts.append(chart)
                tests_passed += 1
            else:
                print_warning(f"Chart '{chart_title}' returned None (data validation failed)")
        
        except Exception as e:
            print_error(f"Chart '{chart_title}' failed: {e}")
    
    # Test specific chart types
    print_info(f"\n{len(successful_charts)} charts built successfully")
    
    # Validate chart types distribution
    chart_types = [c.get("type") for c in successful_charts]
    print_info(f"Chart types: {', '.join(set(chart_types))}")
    
    print_info(f"\nLayer 5 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total, successful_charts

# ============================================================================
# LAYER 6: INSIGHTS GENERATION
# ============================================================================

def test_insights_generation(agent, metadata, charts, df):
    """Test insights generation"""
    print_section("LAYER 6: Testing Insights Generation")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Generate insights
    tests_total += 1
    try:
        insights = agent._generate_insights(metadata, charts, df)
        assert isinstance(insights, list), "Insights not a list"
        assert len(insights) > 0, "No insights generated"
        print_success(f"Generated {len(insights)} insights")
        
        for i, insight in enumerate(insights, 1):
            print_info(f"  {i}. {insight[:100]}...")
        
        tests_passed += 1
    except Exception as e:
        print_error(f"Insights generation failed: {e}")
    
    print_info(f"\nLayer 6 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total

# ============================================================================
# LAYER 7: END-TO-END DASHBOARD GENERATION
# ============================================================================

def test_end_to_end_generation(agent, metadata, data):
    """Test complete end-to-end dashboard generation"""
    print_section("LAYER 7: Testing End-to-End Dashboard Generation")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Generate complete dashboard
    tests_total += 1
    try:
        print_info("Starting complete dashboard generation...")
        result = agent.generate_dashboard(metadata, data)
        
        # Validate response structure
        assert result["status"] == "success", f"Status not success: {result.get('status')}"
        assert "dashboard" in result, "No dashboard in result"
        assert "insights" in result, "No insights in result"
        
        dashboard = result["dashboard"]
        assert "dashboard_id" in dashboard, "No dashboard_id"
        assert "title" in dashboard, "No title"
        assert "charts" in dashboard, "No charts"
        
        charts = dashboard["charts"]
        print_success(f"Dashboard generated successfully")
        print_info(f"  Dashboard ID: {dashboard['dashboard_id']}")
        print_info(f"  Title: {dashboard['title']}")
        print_info(f"  Description: {dashboard.get('description', 'N/A')}")
        print_info(f"  Charts: {len(charts)}")
        print_info(f"  Insights: {len(result['insights'])}")
        
        # Validate each chart
        for chart in charts:
            assert "id" in chart, "Chart missing id"
            assert "type" in chart, "Chart missing type"
            assert "title" in chart, "Chart missing title"
            assert "figure" in chart, "Chart missing figure"
        
        print_success(f"All {len(charts)} charts validated successfully")
        tests_passed += 1
        
        return tests_passed, tests_total, result
    
    except Exception as e:
        print_error(f"End-to-end generation failed: {e}")
        import traceback
        traceback.print_exc()
        return tests_passed, tests_total, None

# ============================================================================
# LAYER 8: EXPORT VALIDATION
# ============================================================================

def test_export_validation(result):
    """Test that dashboard can be exported/serialized"""
    print_section("LAYER 8: Testing Dashboard Export/Serialization")
    
    tests_passed = 0
    tests_total = 0
    
    if not result:
        print_warning("Skipping export tests (no dashboard result)")
        return 0, 0
    
    # Test 1: JSON serialization
    tests_total += 1
    try:
        json_str = json.dumps(result, indent=2)
        assert len(json_str) > 100, "JSON too short"
        
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed["status"] == result["status"], "Serialization changed data"
        
        print_success("Dashboard JSON serialization successful")
        print_info(f"  JSON size: {len(json_str):,} bytes")
        tests_passed += 1
    except Exception as e:
        print_error(f"JSON serialization failed: {e}")
    
    # Test 2: Save to file
    tests_total += 1
    try:
        output_path = Path(__file__).parent / "test_dashboard_output.json"
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print_success(f"Dashboard saved to: {output_path.name}")
        tests_passed += 1
    except Exception as e:
        print_error(f"File save failed: {e}")
    
    print_info(f"\nLayer 8 Results: {tests_passed}/{tests_total} tests passed")
    return tests_passed, tests_total

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print_header("ENHANCED DASHBOARD AGENT - COMPREHENSIVE TEST SUITE")
    
    print_info("Initializing Enhanced Dashboard Agent...")
    try:
        agent = EnhancedDashboardAgent()
        print_success("Agent initialized successfully")
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        return
    
    # Load test data
    df, metadata, data = load_test_data()
    
    # Run all test layers
    total_passed = 0
    total_tests = 0
    
    # Layer 1: Structured Prompts
    passed, total = test_prompt_generation(metadata)
    total_passed += passed
    total_tests += total
    
    # Layer 2: SQL Safety
    passed, total = test_sql_safety()
    total_passed += passed
    total_tests += total
    
    # Layer 3: JSON Extraction
    passed, total = test_json_extraction()
    total_passed += passed
    total_tests += total
    
    # Layer 4: Dashboard Planning
    passed, total, plan = test_dashboard_planning(agent, metadata)
    total_passed += passed
    total_tests += total
    
    # Layer 5: Chart Building
    passed, total, charts = test_chart_building(agent, plan, df, metadata)
    total_passed += passed
    total_tests += total
    
    # Layer 6: Insights Generation
    passed, total = test_insights_generation(agent, metadata, charts, df)
    total_passed += passed
    total_tests += total
    
    # Layer 7: End-to-End Generation
    passed, total, result = test_end_to_end_generation(agent, metadata, data)
    total_passed += passed
    total_tests += total
    
    # Layer 8: Export Validation
    passed, total = test_export_validation(result)
    total_passed += passed
    total_tests += total
    
    # Final Results
    print_header("FINAL TEST RESULTS")
    
    percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{Colors.BOLD}Total Tests: {total_tests}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed: {total_passed}{Colors.END}")
    print(f"{Colors.RED}{Colors.BOLD}Failed: {total_tests - total_passed}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}Success Rate: {percentage:.1f}%{Colors.END}\n")
    
    if percentage >= 90:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT! All critical tests passed!{Colors.END}")
    elif percentage >= 75:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ GOOD! Most tests passed, some issues to review.{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ NEEDS WORK! Multiple failures detected.{Colors.END}")
    
    print(f"\n{Colors.CYAN}Check test_dashboard_output.json for generated dashboard{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

if __name__ == "__main__":
    main()
