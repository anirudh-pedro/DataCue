"""
Test "first N" and "last N" row-level queries.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent.query_engine import QueryEngine

def test_first_n_queries():
    """Test queries about first/last N rows."""
    
    # Create test dataset matching your example
    data = pd.DataFrame({
        'customer_id': range(1, 151),
        'age': [25, 30, 35, 40, 45] * 30,
        'gender': ['Male', 'Female'] * 75,
        'product_category': ['Electronics', 'Clothing', 'Food'] * 50,
        'units_sold': [1, 2, 3, 4, 5] * 30,
        'revenue': [
            125.69, 250.00, 375.50, 500.75, 625.99,
            750.25, 875.50, 1000.00, 1250.00, 1500.00,
            # ... and so on, with varying values
        ] + [round(200 + i * 50.5, 2) for i in range(140)],
        'satisfaction_rating': [4.5, 3.8, 4.2, 4.9, 3.5] * 30,
        'date_purchased': pd.date_range('2024-01-01', periods=150, freq='D'),
        'region': ['North', 'South', 'East', 'West'] * 37 + ['North', 'South']
    })
    
    engine = QueryEngine()
    engine.set_data(data)
    
    print("=" * 70)
    print("FIRST/LAST N QUERIES TEST")
    print("=" * 70)
    print(f"\n📊 Dataset: {len(data)} rows, {len(data.columns)} columns")
    print(f"First 10 revenue values: {data['revenue'].head(10).tolist()}")
    print(f"Expected average: {data['revenue'].head(10).mean():.2f}\n")
    
    test_cases = [
        "calculate the average for first 10 revenue?",
        "what is the sum of first 5 revenue?",
        "show me the first 10 revenue values",
        "what is the average of last 10 revenue?",
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: {question}")
        
        result = engine.query(question)
        
        if result['success']:
            print(f"✅ Answer: {result['answer']}")
            if 'data' in result:
                print(f"📊 Data provided: {list(result['data'].keys())[:5]}")
        else:
            print(f"❌ Failed: {result.get('answer', 'No answer')}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_first_n_queries()
