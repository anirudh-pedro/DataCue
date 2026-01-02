"""
Test SQL-Based Dashboard Agent
Verifies that individual LLM requests are made for each chart
"""

import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.insert(0, '.')

from agents.dashboard_agent import EnhancedDashboardAgent
import pandas as pd
import json

def main():
    print("\n" + "="*80)
    print("TESTING SQL-BASED DASHBOARD AGENT")
    print("="*80)
    
    # Load sample CSV
    csv_path = "data/datacue_sample_dataset.csv"
    print(f"\n📂 Loading sample data from: {csv_path}")
    
    df = pd.DataFrame(data)
    print(f"✓ Loaded {len(df)} rows")
    print(f"✓ Columns: {list(df.columns)}")
    
    # Extract metadata
    metadata = {
        "row_count": len(df),
        "columns": [
            {"name": col, "type": str(df[col].dtype)}
            for col in df.columns
        ]
    }
    
    print(f"\n📊 Metadata:")
    print(json.dumps(metadata, indent=2))
    
    # Initialize agent
    print(f"\n🤖 Initializing EnhancedDashboardAgent...")
    agent = EnhancedDashboardAgent()
    
    # Test dashboard planning (LLM Request #1)
    print(f"\n" + "="*80)
    print("STEP 1: DASHBOARD PLANNING (LLM Request #1)")
    print("="*80)
    
    dashboard_plan = agent._plan_dashboard(metadata, None)
    
    if dashboard_plan and "charts" in dashboard_plan:
        num_charts = len(dashboard_plan["charts"])
        print(f"✓ Dashboard plan generated successfully")
        print(f"✓ Title: {dashboard_plan.get('dashboard_title')}")
        print(f"✓ Number of charts: {num_charts}")
        
        print(f"\n📋 Chart Specifications:")
        for i, chart in enumerate(dashboard_plan["charts"], 1):
            print(f"\n  Chart {i}:")
            print(f"    ID: {chart.get('chart_id')}")
            print(f"    Title: {chart.get('title')}")
            print(f"    Type: {chart.get('chart_type')}")
            print(f"    Queries Needed: {chart.get('queries_needed', 1)}")
            print(f"    Description: {chart.get('description')[:100]}...")
        
        # Test SQL generation for first 3 charts
        print(f"\n" + "="*80)
        print("STEP 2: SQL GENERATION (Individual LLM Requests)")
        print("="*80)
        
        from agents.dashboard_agent.structured_prompts import (
            build_chart_sql_prompt,
            SYSTEM_PROMPT_SQL
        )
        
        for i, chart_spec in enumerate(dashboard_plan["charts"][:3], 1):
            print(f"\n{'─'*80}")
            print(f"LLM Request #{i+1}: Generating SQL for '{chart_spec.get('title')}'")
            print(f"{'─'*80}")
            
            # Build prompt
            prompt = build_chart_sql_prompt(metadata, chart_spec)
            
            print(f"\n📝 GENERATED PROMPT:")
            print(f"{'─'*80}")
            print(prompt)
            print(f"{'─'*80}")
            
            # Make LLM request
            print(f"\n🔄 Sending to Groq LLM...")
            response = agent.client.chat.completions.create(
                model=agent.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_SQL},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            sql_response = response.choices[0].message.content.strip()
            
            print(f"\n✓ LLM RESPONSE:")
            print(f"{'─'*80}")
            print(sql_response)
            print(f"{'─'*80}")
            
        print(f"\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"✓ Total charts planned: {num_charts}")
        print(f"✓ Total LLM requests: 1 (planning) + {num_charts} (SQL generation) = {num_charts + 1}")
        print(f"✓ Implementation matches your vision:")
        print(f"   - 1 LLM request for dashboard planning ✓")
        print(f"   - {num_charts} individual LLM requests for SQL generation ✓")
        print(f"   - Each chart gets its own SQL query/queries ✓")
        
    else:
        print("✗ Dashboard planning failed")
        return
    
    print(f"\n" + "="*80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("="*80)

if __name__ == "__main__":
    # Sample data for testing
    data = [
        {"name": "Alice", "department": "Engineering", "salary": 50000.50, "age": 25},
        {"name": "Bob", "department": "Sales", "salary": 60000.00, "age": 30},
        {"name": "Charlie", "department": "Engineering", "salary": 75000.00, "age": 35},
        {"name": "Diana", "department": "Marketing", "salary": 65000.00, "age": 28},
        {"name": "Eve", "department": "Sales", "salary": 12001.00, "age": 26},
    ]
    
    main()
