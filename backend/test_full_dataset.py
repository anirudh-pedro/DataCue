"""
Test sending full dataset to LLM for small datasets.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent.query_engine import QueryEngine
from core.config import get_settings

def test_full_dataset_mode():
    """Test that small datasets can be sent entirely to LLM."""
    
    settings = get_settings()
    
    print("=" * 70)
    print("FULL DATASET MODE TEST")
    print("=" * 70)
    
    print(f"\n⚙️  Configuration:")
    print(f"   INCLUDE_SAMPLE_DATA: {settings.include_sample_data}")
    print(f"   MAX_FULL_DATASET_ROWS: {settings.max_full_dataset_rows}")
    print(f"   MAX_SAMPLE_ROWS: {settings.max_sample_rows}")
    
    # Test 1: Small dataset (will send full data)
    print(f"\n{'─' * 70}")
    print("Test 1: Small Dataset (10 rows)")
    print("─" * 70)
    
    small_data = pd.DataFrame({
        'customer_id': range(1, 11),
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 
                 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack'],
        'age': [25, 30, 35, 40, 45, 50, 28, 33, 38, 42],
        'revenue': [1000, 1500, 2000, 2500, 3000, 3500, 1200, 1800, 2200, 2800]
    })
    
    engine = QueryEngine()
    engine.set_data(small_data)
    
    print(f"Dataset size: {len(small_data)} rows")
    print(f"Expected behavior: Send ALL {len(small_data)} rows to LLM")
    print(f"(Because {len(small_data)} <= MAX_FULL_DATASET_ROWS={settings.max_full_dataset_rows})")
    
    result = engine.query("Who is the customer with the highest revenue?")
    
    if result['success']:
        print(f"\n✅ Answer: {result['answer']}")
        print(f"\n   Expected: Should correctly identify 'Frank' or customer_id 6")
        print(f"   (Revenue = 3500)")
    
    # Test 2: Large dataset (will send only summary)
    print(f"\n{'─' * 70}")
    print("Test 2: Large Dataset (100 rows)")
    print("─" * 70)
    
    large_data = pd.DataFrame({
        'customer_id': range(1, 101),
        'revenue': [100 + i * 50 for i in range(100)]
    })
    
    engine2 = QueryEngine()
    engine2.set_data(large_data)
    
    print(f"Dataset size: {len(large_data)} rows")
    print(f"Expected behavior: Send only SUMMARY (not full data)")
    print(f"(Because {len(large_data)} > MAX_FULL_DATASET_ROWS={settings.max_full_dataset_rows})")
    
    result2 = engine2.query("What is the maximum revenue?")
    
    if result2['success']:
        print(f"\n✅ Answer: {result2['answer']}")
        print(f"   Expected: Should use summary stats (max=5050)")
    
    # Test 3: How to enable full data for all datasets
    print(f"\n{'─' * 70}")
    print("Test 3: How to Enable Full Data Mode")
    print("─" * 70)
    
    print("\nTo send sample data for ALL datasets, add to .env:")
    print("   INCLUDE_SAMPLE_DATA=true")
    print("\nTo send FULL dataset for larger datasets, add to .env:")
    print("   MAX_FULL_DATASET_ROWS=500")
    print("\n⚠️  WARNING: This increases token usage and API costs!")
    print("   Only use for datasets you're sure will fit in context.")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print("✅ Keep default settings for most use cases")
    print("✅ Current approach is FASTER and CHEAPER")
    print("✅ LLM gets exactly what it needs via computed statistics")
    print("❌ Sending full Excel rarely improves accuracy")
    print("=" * 70)

if __name__ == "__main__":
    test_full_dataset_mode()
