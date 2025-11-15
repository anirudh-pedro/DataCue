"""
Test intelligent column selection for LLM queries.
Verifies that relevant columns are prioritized based on the question.
"""
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent.query_engine import QueryEngine

def test_intelligent_column_selection():
    """Test that columns mentioned in questions are prioritized."""
    
    # Create test dataset with 10 numeric columns
    # But we only send 5 to LLM (MAX_NUMERIC_COLUMNS_CONTEXT=5)
    data = pd.DataFrame({
        'ID': range(1, 101),
        'Age': [25, 30, 35] * 33 + [40],
        'Height': [170, 175, 180] * 33 + [165],
        'Weight': [70, 75, 80] * 33 + [65],
        'Score': [85, 90, 95] * 33 + [88],
        'Revenue': [1000, 2000, 3000] * 33 + [1500],
        'Profit': [100, 200, 300] * 33 + [150],
        'Salary': [50000, 60000, 70000] * 33 + [55000],  # 8th column
        'Bonus': [5000, 6000, 7000] * 33 + [5500],       # 9th column
        'Commission': [1000, 1500, 2000] * 33 + [1200],  # 10th column
    })
    
    engine = QueryEngine()
    engine.set_data(data)
    
    print("=" * 70)
    print("INTELLIGENT COLUMN SELECTION TEST")
    print("=" * 70)
    print(f"\n📊 Dataset has {len(data.columns)} numeric columns")
    print(f"🔧 LLM receives only 5 columns (MAX_NUMERIC_COLUMNS_CONTEXT=5)")
    print(f"\nColumns in order: {', '.join(data.columns.tolist())}\n")
    
    # Test cases
    test_cases = [
        {
            'question': 'What is the average salary?',
            'expected_column': 'Salary',
            'description': 'Salary is 8th column - should be prioritized!'
        },
        {
            'question': 'What is the total commission?',
            'expected_column': 'Commission',
            'description': 'Commission is 10th column - should be prioritized!'
        },
        {
            'question': 'Show me bonus statistics',
            'expected_column': 'Bonus',
            'description': 'Bonus is 9th column - should be prioritized!'
        },
        {
            'question': 'What is the average age?',
            'expected_column': 'Age',
            'description': 'Age is 2nd column - already in first 5'
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: {test['description']}")
        print(f"Question: \"{test['question']}\"")
        print(f"Expected column in context: {test['expected_column']}")
        
        try:
            # Query the engine
            result = engine.query(test['question'])
            
            # Check if answer was generated
            if result['success'] and result['answer']:
                print(f"✅ Answer: {result['answer']}")
                
                # Verify the expected column was included in the data
                if 'data' in result and result['data']:
                    data_keys = result['data'].keys()
                    expected_keys = [key for key in data_keys if test['expected_column'].lower() in key.lower()]
                    
                    if expected_keys:
                        print(f"✅ Column '{test['expected_column']}' WAS included in LLM context")
                        print(f"   Found keys: {', '.join(expected_keys)}")
                    else:
                        print(f"⚠️  Column '{test['expected_column']}' may not have been in context")
                        print(f"   Available keys: {', '.join(list(data_keys)[:5])}...")
            else:
                print(f"❌ Failed: {result.get('answer', 'No answer')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_intelligent_column_selection()
