"""
Test user-provided parameter queries (e.g., "profit margin is 200").
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent.query_engine import QueryEngine

def test_user_provided_parameters():
    """Test queries where users provide parameters like thresholds."""
    
    # Create test dataset matching the user's scenario
    data = pd.DataFrame({
        'customer_id': range(1, 21),
        'age': [25, 30, 35, 40, 45] * 4,
        'gender': ['Male', 'Female'] * 10,
        'region': ['North', 'South', 'East', 'West'] * 5,
        'product': ['A', 'B', 'C', 'D', 'E'] * 4,
        'units_sold': [10, 20, 30, 15, 25, 5, 40, 35, 50, 12, 
                       18, 22, 28, 33, 45, 8, 16, 38, 42, 55],
        'unit_price': [10.0, 15.0, 20.0, 12.0, 18.0] * 4,
        'satisfaction_rating': [4.5, 3.8, 4.2, 4.9, 3.5] * 4,
        'revenue': [100, 300, 600, 180, 450, 50, 800, 525, 1000, 144,
                    180, 330, 560, 396, 810, 80, 320, 684, 840, 990],
        'purchase_date': pd.date_range('2024-01-01', periods=20, freq='D')
    })
    
    engine = QueryEngine()
    engine.set_data(data)
    
    print("=" * 70)
    print("USER-PROVIDED PARAMETER TEST")
    print("=" * 70)
    print(f"\n📊 Dataset: {len(data)} rows")
    print(f"Revenue range: ${data['revenue'].min()} - ${data['revenue'].max()}")
    print(f"Units sold range: {data['units_sold'].min()} - {data['units_sold'].max()}")
    
    # Count how many records have revenue > 200
    actual_count = len(data[data['revenue'] > 200])
    actual_units = data[data['revenue'] > 200]['units_sold'].tolist()
    
    print(f"\n✓ Actual records with revenue > 200: {actual_count}")
    print(f"✓ Their units_sold: {actual_units}\n")
    
    test_cases = [
        {
            'question': 'units_sold who has crossed the profit margin?',
            'description': 'First ask without providing margin (should say data not available)'
        },
        {
            'question': 'profit margin is 200',
            'description': 'User provides the profit margin value'
        },
        {
            'question': 'units_sold who has crossed the profit margin? profit margin is 200',
            'description': 'Combined question with parameter'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: {test['description']}")
        print(f"Question: \"{test['question']}\"")
        
        result = engine.query(test['question'])
        
        if result['success']:
            print(f"\n✅ Answer: {result['answer']}")
            
            if 'data' in result and result['data']:
                data_keys = [k for k in result['data'].keys() if 'margin' in k or 'exceeding' in k]
                if data_keys:
                    print(f"\n📊 Computed data:")
                    for key in data_keys:
                        print(f"   {key}: {result['data'][key]}")
        else:
            print(f"❌ Failed: {result.get('answer', 'No answer')}")
    
    print("\n" + "=" * 70)
    print("EXPECTED BEHAVIOR:")
    print("=" * 70)
    print("1st query: Should say 'data not available' (no margin provided)")
    print("2nd query: Should acknowledge margin = 200")
    print("3rd query: Should calculate and return units_sold where revenue > 200")
    print(f"           Expected units: {actual_units}")
    print("=" * 70)

if __name__ == "__main__":
    test_user_provided_parameters()
