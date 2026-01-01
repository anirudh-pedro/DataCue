"""
Unit tests for Result Detector
Tests all data type handling and ensures no data loss
"""

import numpy as np
import pandas as pd
import pytest
from result_detector import ResultTypeDetector


class TestResultDetector:
    """Test suite for ResultTypeDetector"""
    
    def setup_method(self):
        """Setup test instance"""
        self.detector = ResultTypeDetector()
    
    # ============================================================================
    # Scalar Tests
    # ============================================================================
    
    def test_integer_kpi(self):
        """Test integer scalar result"""
        result = self.detector.detect(42, "What is the count?")
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 42.0
        assert "meta" in result
    
    def test_float_kpi(self):
        """Test float scalar result"""
        result = self.detector.detect(50000.50, "What is Alice's salary?")
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 50000.50
        assert result["config"]["format"] == "currency"
    
    def test_numpy_integer_kpi(self):
        """Test numpy integer scalar"""
        result = self.detector.detect(np.int64(100), "count")
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 100.0
    
    def test_numpy_float_kpi(self):
        """Test numpy float scalar"""
        result = self.detector.detect(np.float64(99.99), "price")
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 99.99
    
    # ============================================================================
    # Numpy Array Tests
    # ============================================================================
    
    def test_numpy_array_unique_values(self):
        """Test numpy array from df['col'].unique()"""
        arr = np.array(['Engineering', 'Sales', 'Marketing'])
        result = self.detector.detect(arr, "Show me all unique departments")
        
        assert result["type"] == "list"
        assert "items" in result["data"]
        assert result["data"]["items"] == ['Engineering', 'Sales', 'Marketing']
        assert result["data"]["count"] == 3
        assert result["meta"]["original_type"] == "numpy.ndarray"
    
    def test_numpy_array_numeric(self):
        """Test numpy array with numeric values"""
        arr = np.array([10, 20, 30, 40, 50])
        result = self.detector.detect(arr, "values")
        
        assert result["type"] == "list"
        assert result["data"]["items"] == [10, 20, 30, 40, 50]
        assert result["data"]["count"] == 5
    
    def test_numpy_array_single_value(self):
        """Test numpy array with single numeric value (should be KPI)"""
        arr = np.array([42])
        result = self.detector.detect(arr, "count")
        
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 42.0
    
    def test_numpy_array_empty(self):
        """Test empty numpy array"""
        arr = np.array([])
        result = self.detector.detect(arr, "values")
        
        assert result["type"] == "list"
        assert result["data"]["items"] == []
        assert result["meta"]["empty"] is True
    
    def test_numpy_array_2d(self):
        """Test 2D numpy array (should become table)"""
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        result = self.detector.detect(arr, "matrix")
        
        assert result["type"] == "table"
        assert "columns" in result["data"]
        assert "rows" in result["data"]
        assert result["meta"]["shape"] == (2, 3)
    
    # ============================================================================
    # List Tests
    # ============================================================================
    
    def test_list_strings(self):
        """Test plain Python list of strings"""
        items = ['Alice', 'Bob', 'Charlie']
        result = self.detector.detect(items, "names")
        
        assert result["type"] == "list"
        assert result["data"]["items"] == ['Alice', 'Bob', 'Charlie']
        assert result["data"]["count"] == 3
    
    def test_list_dicts(self):
        """Test list of dictionaries (table format)"""
        items = [
            {'name': 'Alice', 'age': 30},
            {'name': 'Bob', 'age': 25}
        ]
        result = self.detector.detect(items, "people")
        
        assert result["type"] == "table"
        assert result["data"]["columns"] == ['name', 'age']
        assert len(result["data"]["rows"]) == 2
        assert result["data"]["total_rows"] == 2
    
    def test_list_single_dict(self):
        """Test single dictionary in list"""
        items = [{'name': 'Alice', 'salary': 50000.50}]
        result = self.detector.detect(items, "person")
        
        assert result["type"] == "table"
        assert result["data"]["total_rows"] == 1
    
    def test_list_empty(self):
        """Test empty list"""
        result = self.detector.detect([], "values")
        
        assert result["type"] == "list"
        assert result["data"]["items"] == []
        assert result["meta"]["empty"] is True
    
    def test_list_truncation(self):
        """Test list with more than 100 items gets truncated"""
        items = list(range(150))
        result = self.detector.detect(items, "numbers")
        
        assert result["type"] == "list"
        assert len(result["data"]["items"]) == 100
        assert result["data"]["count"] == 150
        assert result["config"]["truncated"] is True
    
    # ============================================================================
    # Pandas Series Tests
    # ============================================================================
    
    def test_series_single_value(self):
        """Test Series with single numeric value"""
        series = pd.Series([50000.50])
        result = self.detector.detect(series, "What is Alice's salary?")
        
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 50000.50
    
    def test_series_multiple_values(self):
        """Test Series with multiple values"""
        series = pd.Series([10, 20, 30], name='values')
        result = self.detector.detect(series, "show values")
        
        # Should convert to DataFrame and process
        assert result["type"] in ["table", "bar_chart", "list"]
    
    def test_series_with_index(self):
        """Test Series with custom index"""
        series = pd.Series([100, 200, 300], index=['A', 'B', 'C'], name='score')
        result = self.detector.detect(series, "scores by category")
        
        # Should convert to DataFrame with index as column
        assert result["type"] in ["table", "bar_chart"]
    
    def test_series_empty(self):
        """Test empty Series"""
        series = pd.Series([], dtype=float)
        result = self.detector.detect(series, "empty")
        
        assert result["type"] == "list"
        assert result["meta"]["empty"] is True
    
    # ============================================================================
    # DataFrame Tests
    # ============================================================================
    
    def test_dataframe_single_cell(self):
        """Test DataFrame with single cell (should be KPI)"""
        df = pd.DataFrame({'value': [42]})
        result = self.detector.detect(df, "What is the count?")
        
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 42.0
    
    def test_dataframe_table(self):
        """Test DataFrame formatted as table"""
        df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [30, 25, 35],
            'salary': [50000.50, 45000.00, 60000.75]
        })
        result = self.detector.detect(df, "show all employees")
        
        assert result["type"] in ["table", "bar_chart"]
        if result["type"] == "table":
            assert "columns" in result["data"]
            assert "rows" in result["data"]
            assert len(result["data"]["rows"]) == 3
    
    def test_dataframe_empty(self):
        """Test empty DataFrame"""
        df = pd.DataFrame()
        result = self.detector.detect(df, "empty")
        
        assert result["type"] == "table"
        assert result["data"]["columns"] == []
        assert result["data"]["rows"] == []
        assert result["config"]["empty"] is True
    
    def test_dataframe_with_nans(self):
        """Test DataFrame with NaN values"""
        df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4],
            'col2': ['a', 'b', None, 'd']
        })
        result = self.detector.detect(df, "data with nulls")
        
        assert result["type"] == "table"
        # NaN values should be converted to None for JSON
        rows = result["data"]["rows"]
        assert any(row['col1'] is None for row in rows)
    
    def test_dataframe_truncation(self):
        """Test DataFrame with >100 rows gets truncated"""
        df = pd.DataFrame({'value': range(150)})
        result = self.detector.detect(df, "many rows")
        
        assert result["type"] == "table"
        assert len(result["data"]["rows"]) == 100
        assert result["data"]["total_rows"] == 150
        assert result["config"]["truncated"] is True
    
    def test_dataframe_datetime_column(self):
        """Test DataFrame with datetime column"""
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=3),
            'value': [10, 20, 30]
        })
        result = self.detector.detect(df, "time series")
        
        # Should detect as line chart or table
        assert result["type"] in ["line_chart", "table"]
    
    # ============================================================================
    # Edge Cases
    # ============================================================================
    
    def test_none_result(self):
        """Test None result"""
        result = self.detector.detect(None, "query")
        
        assert result["type"] == "text"
        assert result["data"]["value"] == "No result"
        assert result["meta"]["empty"] is True
    
    def test_nan_result(self):
        """Test NaN result"""
        result = self.detector.detect(np.nan, "query")
        
        assert result["type"] == "text"
        assert result["data"]["value"] == "No result"
    
    def test_boolean_result(self):
        """Test boolean result"""
        result = self.detector.detect(True, "is valid?")
        
        assert result["type"] == "text"
        assert result["data"]["value"] == "True"
    
    def test_string_result(self):
        """Test string result"""
        result = self.detector.detect("Hello World", "message")
        
        assert result["type"] == "text"
        assert result["data"]["value"] == "Hello World"
    
    # ============================================================================
    # Real-World Query Tests (from actual test failures)
    # ============================================================================
    
    def test_unique_departments_query(self):
        """Test 'Show me all unique departments' query result"""
        # Simulate df['department'].unique()
        unique_values = np.array(['Engineering', 'Sales', 'Marketing'])
        result = self.detector.detect(unique_values, "Show me all unique departments")
        
        assert result["type"] == "list"
        assert set(result["data"]["items"]) == {'Engineering', 'Sales', 'Marketing'}
        assert result["data"]["count"] == 3
        print("✅ Unique departments query: PASS")
    
    def test_alice_salary_query(self):
        """Test 'What is Alice's salary?' query result"""
        # Simulate df[df['name'] == 'Alice']['salary'].iloc[0]
        salary = 50000.50
        result = self.detector.detect(salary, "What is Alice's salary?")
        
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 50000.50
        assert result["config"]["format"] == "currency"
        print("✅ Alice's salary query: PASS")
    
    def test_total_salary_query(self):
        """Test 'What is the total salary?' query result"""
        # Simulate df['salary'].sum()
        total = 262001.50
        result = self.detector.detect(total, "What is the total salary?")
        
        assert result["type"] == "kpi"
        assert result["data"]["value"] == 262001.50
        print("✅ Total salary query: PASS")
    
    def test_filter_dataframe_query(self):
        """Test filtered DataFrame result"""
        # Simulate df[df['department'] == 'Engineering']
        df = pd.DataFrame({
            'name': ['Alice', 'Charlie'],
            'age': [30, 35],
            'department': ['Engineering', 'Engineering']
        })
        result = self.detector.detect(df, "Show Engineering employees")
        
        assert result["type"] in ["table", "bar_chart"]
        if result["type"] == "table":
            assert len(result["data"]["rows"]) == 2
        print("✅ Filtered DataFrame query: PASS")


def run_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("RESULT DETECTOR DATA INTEGRITY TESTS")
    print("="*60 + "\n")
    
    test_class = TestResultDetector()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        test_class.setup_method()
        try:
            method = getattr(test_class, method_name)
            method()
            print(f"✅ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {method_name}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"⚠️ {method_name}: {type(e).__name__}: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
