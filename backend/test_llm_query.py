"""Quick test of LLM-powered query engine"""

import pandas as pd
from agents.knowledge_agent.query_engine import QueryEngine

# Create sample dataset
data = pd.DataFrame({
    'customer_id': range(1, 101),
    'age': [25, 30, 35, 40, 45] * 20,
    'gender': ['Male', 'Female', 'Male', 'Female', 'Other'] * 20,
    'purchase_amount': [100, 200, 150, 300, 250] * 20,
    'satisfaction_rating': [4.5, 4.0, 3.5, 5.0, 4.2] * 20
})

# Initialize query engine
engine = QueryEngine()
engine.set_data(data)

# Test questions
questions = [
    "How many males are there?",
    "What is the average purchase amount?",
    "How many total customers?",
    "What are the columns in the dataset?"
]

print("=" * 60)
print("LLM-POWERED QUERY ENGINE TEST")
print("=" * 60)

for question in questions:
    print(f"\nQ: {question}")
    result = engine.query(question, use_cache=False)
    print(f"A: {result['answer']}")
    print(f"Type: {result.get('query_type', 'unknown')}")
    print("-" * 60)
