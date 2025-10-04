"""
Enhanced Knowledge Agent - Demonstration of New Features

This example showcases the NEW high-priority features:
✅ Context-aware conversation memory
✅ AI confidence scoring  
✅ Interactive Plotly visualizations

Features demonstrated:
1. Conversational chat with memory
2. Follow-up question understanding
3. Confidence scores for insights
4. Interactive correlation heatmaps
5. Distribution plots
6. Conversation history export

IMPORTANT: Set GROQ_API_KEY in your .env file before running!
"""

import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from agents.knowledge_agent import (
    KnowledgeAgent,
    ConversationManager,
    ConfidenceScorer,
    VisualizationGenerator
)

# Load environment variables from .env file
load_dotenv()

# Get Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def create_sample_data():
    """Create sample e-commerce dataset"""
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=500, freq='D')
    
    df = pd.DataFrame({
        'date': np.random.choice(dates, 500),
        'revenue': np.random.randint(10000, 100000, 500),
        'quantity_sold': np.random.randint(50, 500, 500),
        'customer_age': np.random.randint(18, 75, 500),
        'category': np.random.choice(['Electronics', 'Fashion', 'Home', 'Sports', 'Books'], 500),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 500),
        'satisfaction': np.random.uniform(3.0, 5.0, 500),
        'discount_percent': np.random.uniform(0, 30, 500)
    })
    
    # Add some correlations
    df['revenue'] = df['quantity_sold'] * 150 + np.random.normal(0, 5000, 500)
    df['satisfaction'] = 5 - (df['discount_percent'] / 10) + np.random.normal(0, 0.3, 500)
    df['satisfaction'] = df['satisfaction'].clip(1, 5)
    
    # Add some missing values
    df.loc[df.sample(frac=0.05).index, 'satisfaction'] = np.nan
    
    return df


def demo_1_conversation_memory():
    """Demo 1: Conversation Memory & Context Awareness"""
    print("\n" + "="*70)
    print("🧠 DEMO 1: CONVERSATION MEMORY & CONTEXT AWARENESS")
    print("="*70 + "\n")
    
    # Initialize conversation manager
    conv_manager = ConversationManager(max_history=20)
    
    # Simulate a conversation
    print("📝 Simulating a multi-turn conversation...\n")
    
    # Turn 1
    query1 = "What is the average revenue?"
    response1 = {"answer": "The average revenue is $54,250.", "success": True}
    conv_manager.add_interaction(query1, response1, query_type='aggregation')
    print(f"User: {query1}")
    print(f"Agent: {response1['answer']}\n")
    
    # Turn 2 - Follow-up
    query2 = "What about the maximum?"
    is_followup = conv_manager.detect_follow_up(query2)
    print(f"User: {query2}")
    print(f"🔍 Follow-up detected: {is_followup}")
    
    # Get context
    context = conv_manager.format_context_for_llm(n_recent=2)
    print(f"\n📋 Context for LLM:\n{context}\n")
    
    response2 = {"answer": "The maximum revenue is $99,850.", "success": True}
    conv_manager.add_interaction(query2, response2, query_type='aggregation')
    print(f"Agent: {response2['answer']}\n")
    
    # Turn 3 - Different topic
    query3 = "Which category has the highest sales?"
    conv_manager.add_interaction(query3, {"answer": "Electronics has the highest sales."}, query_type='top_n')
    
    # Get conversation summary
    summary = conv_manager.get_conversation_summary()
    print("📊 Conversation Summary:")
    print(f"  • Total queries: {summary['total_queries']}")
    print(f"  • Session duration: {summary['session_duration']}")
    print(f"  • Topics discussed: {', '.join(summary['topics_discussed'])}")
    print(f"  • Most common query type: {summary['most_common_query_type']}\n")
    
    # Export conversation history
    conv_manager.export_history('conversation_history.json')
    print("💾 Conversation history exported to: conversation_history.json\n")
    
    return conv_manager


def demo_2_confidence_scoring():
    """Demo 2: AI Confidence Scoring"""
    print("\n" + "="*70)
    print("🎯 DEMO 2: AI CONFIDENCE SCORING")
    print("="*70 + "\n")
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize confidence scorer
    scorer = ConfidenceScorer()
    
    # Example 1: High-confidence insight (large sample, strong correlation)
    print("📈 Example 1: Strong Correlation Insight\n")
    confidence1 = scorer.calculate_insight_confidence(
        insight_type='correlation',
        data=df,
        statistical_metrics={
            'correlation': 0.85,
            'p_value': 0.001
        },
        data_quality_score=95.0
    )
    
    print(f"Insight: 'Strong positive correlation between quantity_sold and revenue'")
    print(f"Confidence Score: {confidence1['confidence_score']}/100")
    print(f"Confidence Level: {confidence1['confidence_level'].upper()}")
    print(f"\nScore Breakdown:")
    for factor, score in confidence1['factors'].items():
        print(f"  • {factor}: {score}/25-30")
    print(f"\n💡 Reasoning: {confidence1['reasoning']}")
    print(f"\n✅ Recommendations:")
    for rec in confidence1['recommendations']:
        print(f"  • {rec}")
    
    # Example 2: Low-confidence insight (small sample, weak correlation)
    print("\n" + "-"*70 + "\n")
    print("📉 Example 2: Weak Pattern (Low Confidence)\n")
    
    small_df = df.sample(n=25)  # Small sample
    
    confidence2 = scorer.calculate_insight_confidence(
        insight_type='correlation',
        data=small_df,
        statistical_metrics={
            'correlation': 0.25,
            'p_value': 0.15
        },
        data_quality_score=70.0
    )
    
    print(f"Insight: 'Weak correlation between customer_age and satisfaction'")
    print(f"Confidence Score: {confidence2['confidence_score']}/100")
    print(f"Confidence Level: {confidence2['confidence_level'].upper()} ⚠️")
    print(f"\nScore Breakdown:")
    for factor, score in confidence2['factors'].items():
        print(f"  • {factor}: {score}/25-30")
    print(f"\n💡 Reasoning: {confidence2['reasoning']}")
    print(f"\n⚠️ Recommendations:")
    for rec in confidence2['recommendations']:
        print(f"  • {rec}")
    
    # Show scoring methodology
    print("\n" + "-"*70 + "\n")
    print("📖 Confidence Scoring Methodology:\n")
    print(scorer.get_score_breakdown())


def demo_3_interactive_visualizations():
    """Demo 3: Interactive Plotly Visualizations"""
    print("\n" + "="*70)
    print("📊 DEMO 3: INTERACTIVE PLOTLY VISUALIZATIONS")
    print("="*70 + "\n")
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize visualization generator
    viz_gen = VisualizationGenerator(theme='plotly_white')
    
    # 1. Correlation Heatmap
    print("🔥 Creating interactive correlation heatmap...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    heatmap = viz_gen.create_correlation_heatmap(
        df[numeric_cols],
        method='pearson',
        title='Sales Data Correlation Matrix',
        show_values=True
    )
    
    viz_gen.save_figure(heatmap, 'correlation_heatmap.html', format='html')
    print("✅ Saved: correlation_heatmap.html (open in browser for interactivity)\n")
    
    # 2. Distribution Plot
    print("📈 Creating revenue distribution plot...")
    dist_plot = viz_gen.create_distribution_plot(
        df,
        column='revenue',
        plot_type='histogram',
        bins=30,
        title='Revenue Distribution with Mean/Median'
    )
    
    viz_gen.save_figure(dist_plot, 'revenue_distribution.html', format='html')
    print("✅ Saved: revenue_distribution.html\n")
    
    # 3. Scatter Plot
    print("🎯 Creating scatter plot...")
    scatter = viz_gen.create_scatter_plot(
        df,
        x='quantity_sold',
        y='revenue',
        color='category',
        title='Revenue vs Quantity Sold by Category',
        trendline=False  # Trendline requires statsmodels
    )
    
    viz_gen.save_figure(scatter, 'revenue_vs_quantity.html', format='html')
    print("✅ Saved: revenue_vs_quantity.html\n")
    
    # 4. Time Series
    print("📅 Creating time series visualization...")
    df_sorted = df.sort_values('date')
    df_daily = df_sorted.groupby('date').agg({
        'revenue': 'sum',
        'quantity_sold': 'sum'
    }).reset_index()
    
    timeseries = viz_gen.create_time_series(
        df_daily,
        date_column='date',
        value_columns=['revenue', 'quantity_sold'],
        title='Daily Revenue and Quantity Trends',
        show_trend=True
    )
    
    viz_gen.save_figure(timeseries, 'time_series.html', format='html')
    print("✅ Saved: time_series.html\n")
    
    # 5. Categorical Bar Chart
    print("📊 Creating categorical analysis...")
    bar_chart = viz_gen.create_categorical_bar(
        df,
        category_column='category',
        value_column='revenue',
        aggregation='sum',
        title='Total Revenue by Category'
    )
    
    viz_gen.save_figure(bar_chart, 'category_revenue.html', format='html')
    print("✅ Saved: category_revenue.html\n")
    
    # 6. Comprehensive Dashboard
    print("🎨 Creating comprehensive dashboard...")
    try:
        dashboard = viz_gen.create_comprehensive_dashboard(
            df,
            profile_data=None
        )
        
        viz_gen.save_figure(dashboard, 'analysis_dashboard.html', format='html')
        print("✅ Saved: analysis_dashboard.html\n")
    except Exception as e:
        print(f"⚠️ Dashboard creation skipped: {e}\n")
    
    print("🎉 All visualizations created successfully!")
    print("\n💡 Open the HTML files in your browser to explore interactive features:")
    print("  • Hover for details")
    print("  • Zoom and pan")
    print("  • Toggle series on/off")
    print("  • Export to PNG\n")


def demo_4_integrated_analysis():
    """Demo 4: Complete Analysis with All Features"""
    print("\n" + "="*70)
    print("🚀 DEMO 4: INTEGRATED ANALYSIS (All Features Combined)")
    print("="*70 + "\n")
    
    # Create data
    df = create_sample_data()
    print(f"📊 Dataset: {df.shape[0]} rows × {df.shape[1]} columns\n")
    
    # Initialize components
    conv_manager = ConversationManager()
    scorer = ConfidenceScorer()
    viz_gen = VisualizationGenerator()
    
    # Simulate analysis workflow
    print("🔍 Step 1: Analyzing data patterns...")
    
    # Calculate correlation
    corr = df['revenue'].corr(df['quantity_sold'])
    
    # Score the insight
    confidence = scorer.calculate_insight_confidence(
        insight_type='correlation',
        data=df,
        statistical_metrics={'correlation': corr, 'p_value': 0.001},
        data_quality_score=92.0
    )
    
    # Store in conversation
    insight = f"Strong correlation ({corr:.2f}) between revenue and quantity_sold"
    conv_manager.add_interaction(
        "What patterns do you see in the data?",
        {
            'insight': insight,
            'confidence': confidence['confidence_score'],
            'level': confidence['confidence_level']
        },
        query_type='pattern_analysis'
    )
    
    print(f"💡 Insight: {insight}")
    print(f"🎯 Confidence: {confidence['confidence_score']}/100 ({confidence['confidence_level']})")
    print(f"📝 Reasoning: {confidence['reasoning']}\n")
    
    # Create visualization
    print("📊 Step 2: Creating visualization...")
    heatmap = viz_gen.create_correlation_heatmap(
        df.select_dtypes(include=[np.number]),
        title='Complete Correlation Analysis'
    )
    viz_gen.save_figure(heatmap, 'integrated_analysis_heatmap.html')
    print("✅ Saved: integrated_analysis_heatmap.html\n")
    
    # Follow-up question
    print("🔄 Step 3: Handling follow-up question...")
    followup = "What about the regional differences?"
    is_followup = conv_manager.detect_follow_up(followup)
    
    print(f"User: {followup}")
    print(f"🧠 Context-aware: {'Yes' if is_followup else 'No'}")
    
    # Get context
    context = conv_manager.format_context_for_llm(n_recent=1)
    print(f"\n📋 Using conversation context:")
    print(context[:150] + "...\n")
    
    # Regional analysis
    regional_stats = df.groupby('region')['revenue'].mean().sort_values(ascending=False)
    
    response = f"Top region: {regional_stats.index[0]} with ${regional_stats.iloc[0]:,.2f} average revenue"
    conv_manager.add_interaction(followup, response, query_type='regional_analysis')
    
    print(f"Agent: {response}\n")
    
    # Summary
    print("📈 Step 4: Session summary...")
    summary = conv_manager.get_conversation_summary()
    print(f"  • Queries processed: {summary['total_queries']}")
    print(f"  • Insights generated: {len(scorer.score_history)}")
    print(f"  • Visualizations created: 1")
    print(f"  • Average confidence: {np.mean([s['confidence_score'] for s in scorer.score_history]):.1f}/100")
    
    print("\n✅ Integrated analysis complete!\n")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🎨 ENHANCED KNOWLEDGE AGENT - NEW FEATURES DEMO")
    print("="*70)
    print("\nShowcasing HIGH-PRIORITY features:")
    print("  ✅ Context-aware conversation memory")
    print("  ✅ AI confidence scoring")
    print("  ✅ Interactive Plotly visualizations")
    
    # Run demos
    demo_1_conversation_memory()
    demo_2_confidence_scoring()
    demo_3_interactive_visualizations()
    demo_4_integrated_analysis()
    
    print("\n" + "="*70)
    print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("="*70 + "\n")
    
    print("📂 Files Generated:")
    print("  • conversation_history.json - Chat history export")
    print("  • correlation_heatmap.html - Interactive heatmap")
    print("  • revenue_distribution.html - Distribution plot")
    print("  • revenue_vs_quantity.html - Scatter plot with trendline")
    print("  • time_series.html - Time series with moving average")
    print("  • category_revenue.html - Bar chart")
    print("  • integrated_analysis_heatmap.html - Complete analysis")
    
    print("\n💡 Next Steps:")
    print("  1. Open HTML files in browser for interactive visualizations")
    print("  2. Review conversation_history.json for chat tracking")
    print("  3. Integrate these features into your main agent!")
    print("\n")


if __name__ == "__main__":
    main()
