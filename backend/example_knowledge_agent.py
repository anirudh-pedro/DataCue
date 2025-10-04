"""
Knowledge Agent - Example Usage
Demonstrates how to use the Knowledge Agent for data analysis and insights.

IMPORTANT: Set your Groq API key before running!
Set GROQ_API_KEY in your .env file or as an environment variable.
"""

import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from agents.knowledge_agent import KnowledgeAgent

# Load environment variables
load_dotenv()

# Set to True to use LLM features (requires API key)
USE_LLM = True  # LLM features enabled

# Get Groq API key from environment variable
# Set this in your .env file: GROQ_API_KEY=your_actual_key_here
GROQ_API_KEY = os.getenv("GROQ_API_KEY", None)


def create_sample_data():
    """Create sample dataset for demonstration"""
    np.random.seed(42)
    
    dates = pd.date_range('2023-01-01', periods=365, freq='D')
    
    df = pd.DataFrame({
        'date': dates,
        'revenue': np.random.randint(10000, 50000, 365) + np.sin(np.arange(365) * 2 * np.pi / 365) * 5000,
        'quantity': np.random.randint(50, 300, 365),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 365),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 365),
        'customer_age': np.random.randint(18, 70, 365),
        'satisfaction_score': np.random.uniform(1, 5, 365)
    })
    
    # Add some missing values
    df.loc[df.sample(frac=0.05).index, 'satisfaction_score'] = np.nan
    
    # Add some outliers
    df.loc[df.sample(frac=0.02).index, 'revenue'] = df['revenue'].max() * 2
    
    return df


def example_1_basic_analysis():
    """Example 1: Basic dataset analysis"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Analysis")
    print("="*60 + "\n")
    
    # Create sample data
    df = create_sample_data()
    print(f"Created sample dataset: {df.shape[0]} rows × {df.shape[1]} columns\n")
    
    # Initialize agent
    if USE_LLM:
        agent = KnowledgeAgent(groq_api_key=GROQ_API_KEY)
        print("✅ Agent initialized with LLM support\n")
    else:
        agent = KnowledgeAgent()
        print("ℹ️  Agent initialized without LLM (set USE_LLM=True for AI insights)\n")
    
    # Analyze dataset
    print("🔍 Analyzing dataset...")
    results = agent.analyze_dataset(df)
    
    # Print summary
    print("\n📊 Analysis Summary:")
    summary = agent.get_summary()
    for key, value in summary.items():
        if key != 'column_types' and key != 'analysis_complete':
            print(f"  • {key}: {value}")
    
    print("\n✅ Analysis complete!")
    return agent


def example_2_key_findings(agent):
    """Example 2: Get key findings"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Key Findings")
    print("="*60 + "\n")
    
    findings = agent.get_key_findings(limit=5)
    
    print("💡 Top 5 Key Findings:")
    for i, finding in enumerate(findings, 1):
        print(f"  {i}. {finding}")


def example_3_ask_questions(agent):
    """Example 3: Ask questions about the data"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Question Answering")
    print("="*60 + "\n")
    
    questions = [
        "What are the top 3 categories by revenue?",
        "Which region has the highest average revenue?",
        "What is the distribution of customer age?",
    ]
    
    for question in questions:
        print(f"❓ {question}")
        answer = agent.ask_question(question)
        if answer.get('success'):
            print(f"💬 {answer['answer']}\n")
        else:
            print(f"⚠️  Could not answer: {answer.get('error', 'Unknown error')}\n")


def example_4_recommendations(agent):
    """Example 4: Get recommendations"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Recommendations")
    print("="*60 + "\n")
    
    # Visualization recommendations
    print("📊 Top Visualization Recommendations:")
    viz_recs = agent.get_visualization_recommendations(priority='high')
    for i, rec in enumerate(viz_recs[:3], 1):
        print(f"  {i}. {rec['title']}")
        print(f"     Type: {rec['type']}")
        print(f"     {rec['description']}\n")
    
    # Modeling recommendations
    print("🤖 Modeling Recommendations:")
    model_recs = agent.get_modeling_recommendations()
    for i, rec in enumerate(model_recs[:2], 1):
        print(f"  {i}. {rec['task'].upper()}")
        print(f"     Target: {rec.get('target', 'N/A')}")
        print(f"     Models: {', '.join(rec.get('recommended_models', [])[:3])}\n")
    
    # Next steps
    print("🎯 Recommended Next Steps:")
    steps = agent.get_next_steps()
    for step in steps[:3]:
        print(f"  • {step['step']}")
        print(f"    {step['description']}\n")


def example_5_generate_report(agent):
    """Example 5: Generate EDA report"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Report Generation")
    print("="*60 + "\n")
    
    # Generate Markdown report
    print("📝 Generating Markdown report...")
    md_report = agent.generate_report(format='markdown')
    print(f"✅ Markdown report generated ({len(md_report)} characters)")
    
    # Save to file
    md_filepath = "example_eda_report.md"
    agent.generate_report(format='markdown', filepath=md_filepath)
    print(f"💾 Saved to: {md_filepath}")
    
    # Generate HTML report
    print("\n🌐 Generating HTML report...")
    html_filepath = "example_eda_report.html"
    agent.generate_report(format='html', filepath=html_filepath)
    print(f"💾 Saved to: {html_filepath}")
    
    print("\n✅ Reports generated successfully!")


def example_6_export_insights(agent):
    """Example 6: Export insights"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Export Insights")
    print("="*60 + "\n")
    
    # Export as JSON
    json_filepath = "example_insights.json"
    agent.export_insights(json_filepath, format='json')
    print(f"💾 Insights exported to: {json_filepath}")
    
    # Show cache stats
    print("\n📈 Query Cache Statistics:")
    cache_stats = agent.get_cache_stats()
    print(f"  Cached queries: {cache_stats['cached_queries']}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print(" KNOWLEDGE AGENT - EXAMPLE USAGE")
    print("="*60)
    
    if not USE_LLM:
        print("\n⚠️  NOTE: Running without LLM support")
        print("   To enable AI-powered insights:")
        print("   1. Set USE_LLM = True")
        print("   2. Set GROQ_API_KEY = 'your_actual_key'")
        print("   3. Get free API key from https://console.groq.com")
    
    # Run examples
    agent = example_1_basic_analysis()
    example_2_key_findings(agent)
    example_3_ask_questions(agent)
    example_4_recommendations(agent)
    example_5_generate_report(agent)
    example_6_export_insights(agent)
    
    print("\n" + "="*60)
    print(" ALL EXAMPLES COMPLETED SUCCESSFULLY! ")
    print("="*60 + "\n")
    
    print("📚 Next Steps:")
    print("  • Review generated reports (example_eda_report.md/html)")
    print("  • Check exported insights (example_insights.json)")
    print("  • Try with your own dataset!")
    print("  • Enable LLM for AI-powered insights")
    print("\n")


if __name__ == "__main__":
    main()
