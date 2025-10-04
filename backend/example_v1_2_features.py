"""
Knowledge Agent v1.2.0 - Complete Feature Demonstration

This example demonstrates ALL features including the latest additions:

✅ v1.0.0 - Core Features:
   - Data profiling
   - AI insights (Groq LLM)
   - Natural language Q&A
   - Recommendations
   - Report generation

✅ v1.1.0 - Enhanced Features:
   - Conversation memory
   - Confidence scoring
   - Interactive visualizations

✅ v1.2.0 - NEW High-Priority Features:
   - User feedback system (thumbs up/down, star ratings)
   - Advanced anomaly detection with alerts
   - PNG/PDF/SVG export for visualizations

IMPORTANT: Set GROQ_API_KEY in your .env file before running!
"""

import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from agents.knowledge_agent import (
    KnowledgeAgent,
    FeedbackSystem,
    AnomalyDetector,
    VisualizationGenerator,
    ConversationManager,
    ConfidenceScorer,
    AlertSeverity
)

# Load environment variables from .env file
load_dotenv()

# Get Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def create_sample_data_with_anomalies():
    """Create sample dataset with intentional anomalies"""
    np.random.seed(42)
    
    # Normal data
    dates = pd.date_range('2024-01-01', periods=400, freq='D')
    
    df = pd.DataFrame({
        'date': np.random.choice(dates[:350], 350),  # Missing last 50 days
        'revenue': np.random.normal(50000, 10000, 350),
        'quantity': np.random.randint(100, 500, 350),
        'customer_age': np.random.randint(18, 70, 350),
        'category': np.random.choice(['Electronics', 'Fashion', 'Home', 'Books'], 350, p=[0.4, 0.3, 0.2, 0.1]),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 350),
        'satisfaction': np.random.uniform(3.0, 5.0, 350)
    })
    
    # Add anomalies intentionally
    # 1. Extreme outliers in revenue
    df.loc[df.sample(n=10).index, 'revenue'] = np.random.uniform(200000, 300000, 10)
    df.loc[df.sample(n=5).index, 'revenue'] = np.random.uniform(-5000, 0, 5)  # Negative values
    
    # 2. Add rare category
    df.loc[df.sample(n=2).index, 'category'] = 'Automotive'  # Very rare
    
    # 3. Missing values
    df.loc[df.sample(frac=0.08).index, 'satisfaction'] = np.nan
    
    # 4. Extreme customer ages
    df.loc[df.sample(n=3).index, 'customer_age'] = np.random.randint(100, 120, 3)
    
    return df


def demo_1_feedback_system():
    """Demo 1: User Feedback System"""
    print("\n" + "="*70)
    print("👍 DEMO 1: USER FEEDBACK SYSTEM")
    print("="*70 + "\n")
    
    # Initialize feedback system
    feedback = FeedbackSystem(feedback_file='user_feedback.json')
    
    print("📝 Simulating user feedback on insights...\n")
    
    # Simulate feedback on various insights
    insights = [
        ("ins_001", "Strong correlation (0.85) between revenue and quantity", "correlation"),
        ("ins_002", "North region shows 25% higher revenue than average", "regional_analysis"),
        ("ins_003", "Customer age peaks at 35-45 age group", "demographic"),
        ("ins_004", "Revenue shows upward trend in Q2", "trend"),
        ("ins_005", "Electronics category dominates with 40% of sales", "category_analysis")
    ]
    
    # User gives feedback
    feedback.thumbs_up("ins_001", insights[0][1], category=insights[0][2])
    print("✅ User: Thumbs up on correlation insight")
    
    feedback.rate_stars("ins_002", insights[1][1], stars=5, category=insights[1][2], comment="Very actionable!")
    print("⭐ User: 5 stars on regional analysis - 'Very actionable!'")
    
    feedback.rate_stars("ins_003", insights[2][1], stars=3, category=insights[2][2], comment="Somewhat useful")
    print("⭐ User: 3 stars on demographic insight - 'Somewhat useful'")
    
    feedback.thumbs_down("ins_004", insights[3][1], category=insights[3][2], comment="Not relevant to my business")
    print("👎 User: Thumbs down on trend - 'Not relevant'")
    
    feedback.rate_stars("ins_005", insights[4][1], stars=4, category=insights[4][2])
    print("⭐ User: 4 stars on category analysis\n")
    
    # Get feedback summary
    summary = feedback.get_feedback_summary()
    print("📊 Feedback Summary:")
    print(f"  • Total feedback: {summary['total_feedback']}")
    print(f"  • Average rating: {summary['average_rating']:.2f}")
    print(f"  • Approval rate: {summary['approval_rate']:.1%}")
    print(f"  • Most active category: {summary['most_active_category'][0]}")
    
    # Get top-rated insights
    print("\n🏆 Top Rated Insights:")
    top = feedback.get_top_rated_insights(n=3, min_ratings=1)
    for i, insight in enumerate(top, 1):
        print(f"  {i}. {insight['insight_text'][:50]}...")
        print(f"     Rating: {insight['average_rating']:.2f} ({insight['total_ratings']} ratings)")
    
    # Get recommendations for improvement
    print("\n💡 Recommendations for Improvement:")
    recs = feedback.get_recommendations_for_improvement()
    for rec in recs:
        print(f"  • {rec}")
    
    print("\n💾 Feedback saved to: user_feedback.json\n")


def demo_2_anomaly_detection():
    """Demo 2: Advanced Anomaly Detection with Alerts"""
    print("\n" + "="*70)
    print("🚨 DEMO 2: ADVANCED ANOMALY DETECTION & ALERTS")
    print("="*70 + "\n")
    
    # Create data with anomalies
    df = create_sample_data_with_anomalies()
    print(f"📊 Dataset: {df.shape[0]} rows × {df.shape[1]} columns\n")
    
    # Initialize detector
    detector = AnomalyDetector(alert_threshold=0.05)
    
    print("🔍 Running comprehensive anomaly detection...\n")
    
    # Detect all anomalies
    results = detector.detect_all_anomalies(df)
    
    # Display results
    print(f"📈 Detection Summary:")
    print(f"  • Total anomalies found: {results['total_anomalies']}")
    print(f"  • Total alerts generated: {results['summary']['total_alerts']}")
    print(f"  • Critical alerts: {results['summary']['critical_alerts']}")
    print(f"  • Methods used: {', '.join(results['summary']['methods_used'])}\n")
    
    # Show Z-score anomalies
    if 'zscore' in results['anomalies_by_method']:
        zscore = results['anomalies_by_method']['zscore']
        print(f"📊 Z-score Anomalies ({len(zscore['anomalies'])} columns):")
        for anom in zscore['anomalies'][:3]:
            print(f"  • {anom['column']}: {anom['n_anomalies']} outliers ({anom['percentage']}%)")
            print(f"    Severity: {anom['severity'].upper()}")
    
    # Show categorical anomalies
    if 'categorical' in results['anomalies_by_method']:
        cat = results['anomalies_by_method']['categorical']
        print(f"\n📑 Categorical Anomalies ({len(cat['anomalies'])} issues):")
        for anom in cat['anomalies'][:2]:
            print(f"  • {anom['column']}: {anom['description']}")
    
    # Show temporal anomalies
    if 'temporal' in results['anomalies_by_method']:
        temp = results['anomalies_by_method']['temporal']
        print(f"\n⏰ Temporal Anomalies ({len(temp['anomalies'])} issues):")
        for anom in temp['anomalies']:
            print(f"  • {anom['column']}: {anom['description']}")
    
    # Display critical alerts
    critical = detector.get_critical_alerts()
    if critical:
        print(f"\n🚨 CRITICAL ALERTS ({len(critical)}):")
        for alert in critical[:3]:
            print(f"  🔴 [{alert['severity'].upper()}] {alert['message']}")
            print(f"     Type: {alert['type']}, ID: {alert['id']}")
    
    # Alert summary
    alert_summary = detector.get_alert_summary()
    print(f"\n📋 Alert Summary:")
    print(f"  • Total: {alert_summary['total_alerts']}")
    print(f"  • By severity: {alert_summary['by_severity']}")
    print(f"  • Unacknowledged: {alert_summary['unacknowledged']}")


def demo_3_export_visualizations():
    """Demo 3: Export Visualizations to Multiple Formats"""
    print("\n" + "="*70)
    print("💾 DEMO 3: EXPORT VISUALIZATIONS (PNG/PDF/SVG)")
    print("="*70 + "\n")
    
    # Create data
    df = create_sample_data_with_anomalies()
    
    # Initialize viz generator
    viz = VisualizationGenerator(theme='plotly_white')
    
    print("📊 Creating visualizations...\n")
    
    # Create correlation heatmap
    heatmap = viz.create_correlation_heatmap(
        df.select_dtypes(include=[np.number]),
        title='Correlation Matrix - Sales Data'
    )
    
    # Export to multiple formats
    print("💾 Exporting correlation heatmap to:")
    
    # 1. HTML (interactive)
    viz.save_figure(heatmap, 'exports/heatmap.html', format='html')
    print("  ✅ HTML (interactive): exports/heatmap.html")
    
    # 2. PNG (static, high quality)
    viz.save_figure(heatmap, 'exports/heatmap.png', format='png', width=1600, height=1200, scale=2)
    print("  ✅ PNG (high-res): exports/heatmap.png")
    
    # 3. PDF (print-ready) - requires kaleido
    print("  ⏳ PDF: exports/heatmap.pdf", end=" ")
    viz.save_figure(heatmap, 'exports/heatmap.pdf', format='pdf', width=1200, height=800)
    print("(fallback to HTML if kaleido not installed)")
    
    # 4. SVG (vector graphics)
    print("  ⏳ SVG: exports/heatmap.svg", end=" ")
    viz.save_figure(heatmap, 'exports/heatmap.svg', format='svg')
    print("(fallback to HTML if kaleido not installed)")
    
    # Create distribution plot
    print("\n📈 Creating distribution plot...")
    dist_plot = viz.create_distribution_plot(df, 'revenue', plot_type='histogram')
    viz.save_figure(dist_plot, 'exports/distribution.html')
    viz.save_figure(dist_plot, 'exports/distribution.png', format='png')
    print("  ✅ Saved to exports/distribution.html and .png")
    
    print("\n💡 Note: Install 'kaleido' for PNG/PDF/SVG export:")
    print("   pip install kaleido\n")


def demo_4_integrated_workflow():
    """Demo 4: Complete Workflow with All Features"""
    print("\n" + "="*70)
    print("🎯 DEMO 4: INTEGRATED WORKFLOW (All Features)")
    print("="*70 + "\n")
    
    # Create data
    df = create_sample_data_with_anomalies()
    
    # Initialize all components
    feedback = FeedbackSystem()
    detector = AnomalyDetector()
    scorer = ConfidenceScorer()
    viz = VisualizationGenerator()
    
    print("🔍 Step 1: Detect Anomalies...")
    results = detector.detect_all_anomalies(df)
    print(f"   Found {results['total_anomalies']} anomalies\n")
    
    print("📊 Step 2: Generate Insights with Confidence Scores...")
    
    # Example insight
    insight_text = f"Detected {results['total_anomalies']} anomalies including outliers and distribution issues"
    confidence = scorer.calculate_insight_confidence(
        insight_type='outlier',
        data=df,
        statistical_metrics={'n_outliers': results['total_anomalies'], 'total_points': len(df)},
        data_quality_score=85.0
    )
    
    print(f"   💡 Insight: {insight_text}")
    print(f"   🎯 Confidence: {confidence['confidence_score']}/100 ({confidence['confidence_level']})")
    print(f"   📝 {confidence['reasoning']}\n")
    
    print("👍 Step 3: Collect User Feedback...")
    fb = feedback.rate_stars(
        'ins_anom_001',
        insight_text,
        stars=5,
        category='anomaly_detection',
        comment="Very helpful! Found critical issues in my data."
    )
    print(f"   ⭐ User gave 5 stars: '{fb['comment']}'\n")
    
    print("📊 Step 4: Create & Export Visualization...")
    heatmap = viz.create_correlation_heatmap(df.select_dtypes(include=[np.number]))
    viz.save_figure(heatmap, 'exports/integrated_heatmap.html')
    viz.save_figure(heatmap, 'exports/integrated_heatmap.png', format='png')
    print("   ✅ Saved to exports/integrated_heatmap.html and .png\n")
    
    print("🚨 Step 5: Review Critical Alerts...")
    critical_alerts = detector.get_critical_alerts()
    if critical_alerts:
        for alert in critical_alerts[:2]:
            print(f"   🔴 [{alert['severity'].upper()}] {alert['message']}")
    else:
        print("   ✅ No critical alerts - data looks good!\n")
    
    print("\n📈 Workflow Summary:")
    print(f"  • Anomalies detected: {results['total_anomalies']}")
    print(f"  • Alerts generated: {len(detector.alerts)}")
    print(f"  • Confidence score: {confidence['confidence_score']}/100")
    print(f"  • User rating: {fb['rating']} stars")
    print(f"  • Visualizations exported: 2 formats")
    
    print("\n✅ Complete workflow executed successfully!\n")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print(" KNOWLEDGE AGENT v1.2.0 - COMPLETE FEATURE DEMO")
    print("="*70)
    print("\nNEW Features Demonstrated:")
    print("  ✅ User feedback system (thumbs up/down, star ratings)")
    print("  ✅ Advanced anomaly detection with alerts")
    print("  ✅ Multi-format visualization export (PNG/PDF/SVG)")
    
    # Run demos
    demo_1_feedback_system()
    demo_2_anomaly_detection()
    demo_3_export_visualizations()
    demo_4_integrated_workflow()
    
    print("\n" + "="*70)
    print(" ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("="*70 + "\n")
    
    print("📂 Generated Files:")
    print("  • user_feedback.json - User feedback history")
    print("  • exports/heatmap.html - Interactive heatmap")
    print("  • exports/heatmap.png - High-res PNG")
    print("  • exports/heatmap.pdf - PDF (if kaleido installed)")
    print("  • exports/heatmap.svg - SVG vector (if kaleido installed)")
    print("  • exports/distribution.html - Distribution plot")
    print("  • exports/distribution.png - Distribution PNG")
    print("  • exports/integrated_heatmap.html - Workflow result")
    print("  • exports/integrated_heatmap.png - Workflow PNG")
    
    print("\n💡 Next Steps:")
    print("  1. Install kaleido for full export support: pip install kaleido")
    print("  2. Review user_feedback.json for feedback patterns")
    print("  3. Check exports/ folder for all visualizations")
    print("  4. Integrate these features into your main application!")
    print("\n")


if __name__ == "__main__":
    main()
