"""
Test full dataset mode - comparing summary vs full data approaches.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent.query_engine import QueryEngine
from core.config import get_settings

def test_full_dataset_enabled():
    """Test with full dataset mode enabled."""
    
    # Reload settings to get new .env values
    import importlib
    import core.config
    importlib.reload(core.config)
    from core.config import get_settings
    
    settings = get_settings()
    
    print("=" * 70)
    print("FULL DATASET MODE - ENABLED")
    print("=" * 70)
    
    print(f"\n⚙️  Current Configuration:")
    print(f"   INCLUDE_SAMPLE_DATA: {settings.include_sample_data}")
    print(f"   MAX_FULL_DATASET_ROWS: {settings.max_full_dataset_rows}")
    print(f"   MAX_SAMPLE_ROWS: {settings.max_sample_rows}")
    
    # Create realistic test dataset
    data = pd.DataFrame({
        'customer_id': range(1, 21),
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 
                 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack',
                 'Kate', 'Liam', 'Mia', 'Noah', 'Olivia',
                 'Peter', 'Quinn', 'Rachel', 'Sam', 'Tina'],
        'age': [25, 30, 35, 40, 45, 50, 28, 33, 38, 42,
                27, 31, 36, 41, 46, 29, 34, 39, 43, 48],
        'gender': ['Male', 'Female'] * 10,
        'region': ['North', 'South', 'East', 'West'] * 5,
        'product': ['A', 'B', 'C', 'D', 'E'] * 4,
        'units_sold': [10, 20, 30, 15, 25, 5, 40, 35, 50, 12, 
                       18, 22, 28, 33, 45, 8, 16, 38, 42, 55],
        'unit_price': [10.0, 15.0, 20.0, 12.0, 18.0] * 4,
        'revenue': [100, 300, 600, 180, 450, 50, 800, 525, 1000, 144,
                    180, 330, 560, 396, 810, 80, 320, 684, 840, 990],
        'purchase_date': pd.date_range('2024-01-01', periods=20, freq='D')
    })
    
    engine = QueryEngine()
    engine.set_data(data)
    
    print(f"\n📊 Test Dataset: {len(data)} rows × {len(data.columns)} columns")
    print(f"   Full dataset will be sent to LLM!")
    
    # Test queries that benefit from full data access
    test_cases = [
        {
            'question': 'Who is the customer with the highest revenue?',
            'why': 'Needs to see actual customer names and revenue'
        },
        {
            'question': 'Show me all customers from the North region',
            'why': 'Needs to filter by region and return names'
        },
        {
            'question': 'What is the revenue of customer Charlie?',
            'why': 'Needs to look up specific customer'
        },
        {
            'question': 'Which customers bought product E?',
            'why': 'Needs to filter and return customer list'
        },
        {
            'question': 'units_sold who has crossed the profit margin? profit margin is 200',
            'why': 'Your original question - with full context'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: {test['question']}")
        print(f"Why full data helps: {test['why']}")
        print("─" * 70)
        
        result = engine.query(test['question'])
        
        if result['success']:
            print(f"✅ Answer: {result['answer']}")
        else:
            print(f"❌ Failed: {result.get('answer', 'No answer')}")
    
    print("\n" + "=" * 70)
    print("BENEFITS OF FULL DATASET MODE")
    print("=" * 70)
    print("✅ LLM can see actual row-level data")
    print("✅ Can answer questions about specific customers/records")
    print("✅ Better for small-medium datasets (<100 rows)")
    print("✅ More accurate for complex filtering queries")
    print("\n⚠️  NOTE: For datasets >1000 rows, may hit token limits")
    print("=" * 70)

if __name__ == "__main__":
    test_full_dataset_enabled()
