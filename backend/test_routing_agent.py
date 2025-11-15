"""
Test the Routing Agent for query classification.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent.routing_agent import RoutingAgent
from agents.knowledge_agent.query_engine import QueryEngine

def test_routing_agent():
    """Test that the routing agent correctly classifies queries."""
    
    # Create test dataset
    data = pd.DataFrame({
        'customer_id': range(1, 21),
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'] * 4,
        'age': [25, 30, 35, 40, 45] * 4,
        'revenue': [100, 200, 300, 400, 500] * 4,
        'region': ['North', 'South', 'East', 'West'] * 5
    })
    
    router = RoutingAgent()
    engine = QueryEngine()
    engine.set_data(data)
    
    print("=" * 70)
    print("ROUTING AGENT TEST")
    print("=" * 70)
    print(f"\n📊 Dataset columns: {', '.join(data.columns.tolist())}\n")
    
    # Test cases
    test_cases = [
        {
            'question': 'Show me the top 10 revenue',
            'expected_tool': 'TOP_N',
            'expected_args': {'column': 'revenue', 'n': 10}
        },
        {
            'question': 'What is the average age?',
            'expected_tool': 'AVERAGE',
            'expected_args': {'column': 'age'}
        },
        {
            'question': 'How many customers from North?',
            'expected_tool': 'COUNT',
            'expected_args': {'column': 'region', 'value': 'North'}
        },
        {
            'question': 'Give me a summary',
            'expected_tool': 'SUMMARY',
            'expected_args': {}
        },
        {
            'question': 'Plot revenue vs age',
            'expected_tool': 'CHART',
            'expected_args': {'x_column': 'age', 'y_column': 'revenue'}
        },
        {
            'question': 'What is the total revenue?',
            'expected_tool': 'SUM',
            'expected_args': {'column': 'revenue'}
        },
        {
            'question': 'Show me customers',
            'expected_tool': 'CUSTOM_QUERY',  # Vague, goes to general LLM
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: \"{test['question']}\"")
        print("─" * 70)
        
        # Route the question
        routing_result = router.route(test['question'], data.columns.tolist())
        
        if routing_result.get('needs_clarification'):
            print(f"⚠️  NEEDS CLARIFICATION")
            print(f"   Message: {routing_result.get('message')}")
        else:
            tool = routing_result.get('tool')
            args = routing_result.get('arguments', {})
            
            print(f"🎯 Routed to: {tool}")
            print(f"📝 Arguments: {args}")
            
            # Check if routing is correct
            if tool == test.get('expected_tool'):
                print(f"✅ CORRECT TOOL!")
            else:
                print(f"⚠️  Expected: {test.get('expected_tool')}, Got: {tool}")
            
            # Execute the tool
            print(f"\n🔄 Executing tool...")
            result = router.execute_tool(tool, args, engine)
            
            if result.get('success'):
                answer = result.get('answer', '')
                # Truncate long answers
                if len(answer) > 100:
                    answer = answer[:100] + "..."
                print(f"✅ Result: {answer}")
            else:
                print(f"❌ Failed: {result.get('answer')}")
    
    print("\n" + "=" * 70)
    print("ROUTING AGENT BENEFITS")
    print("=" * 70)
    print("✅ Reliable intent classification")
    print("✅ Structured tool selection")
    print("✅ Parameter extraction")
    print("✅ Handles ambiguous queries gracefully")
    print("✅ Fallback to general LLM for complex questions")
    print("=" * 70)

if __name__ == "__main__":
    test_routing_agent()
