"""
Example Usage: Prediction Agent
Demonstrates automated machine learning with the Prediction Agent.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.prediction_agent import PredictionAgent


def example_classification():
    """
    Example 1: Binary Classification - Customer Churn Prediction
    """
    print("=" * 80)
    print("EXAMPLE 1: Binary Classification - Customer Churn Prediction")
    print("=" * 80)
    
    # Generate synthetic churn data
    np.random.seed(42)
    n_samples = 1000
    
    data = pd.DataFrame({
        'age': np.random.randint(18, 70, n_samples),
        'income': np.random.randint(20000, 150000, n_samples),
        'account_balance': np.random.randint(0, 50000, n_samples),
        'tenure_months': np.random.randint(1, 120, n_samples),
        'num_products': np.random.randint(1, 5, n_samples),
        'has_credit_card': np.random.choice([0, 1], n_samples),
        'is_active_member': np.random.choice([0, 1], n_samples),
        'customer_complaints': np.random.randint(0, 10, n_samples)
    })
    
    # Create churn based on some logic (for realistic data)
    churn_probability = (
        (data['age'] < 30) * 0.2 +
        (data['tenure_months'] < 12) * 0.3 +
        (data['customer_complaints'] > 5) * 0.4 +
        (data['is_active_member'] == 0) * 0.3
    )
    data['churned'] = (np.random.random(n_samples) < churn_probability).astype(int)
    
    # Initialize Prediction Agent
    agent = PredictionAgent(models_dir="models")
    
    # Run AutoML
    result = agent.auto_ml(
        data=data,
        target_column='churned',
        problem_type='classification',  # Explicitly specify
        test_size=0.2,
        feature_engineering=True,
        explain_model=True,
        save_model=True
    )
    
    # Display results
    if result['status'] == 'success':
        print(f"\n✅ AutoML Completed Successfully!")
        print(f"\nBest Model: {result['best_model']['name']}")
        print(f"Accuracy: {result['best_model']['metrics']['accuracy']:.3f}")
        print(f"F1 Score: {result['best_model']['metrics']['f1_score']:.3f}")
        print(f"ROC AUC: {result['best_model']['metrics']['roc_auc']:.3f}")
        
        # Model comparison
        print("\n📊 Model Comparison:")
        comparison_df = pd.DataFrame(result['model_comparison'])
        print(comparison_df.to_string(index=False))
        
        # Feature importance
        if 'explainability' in result and 'feature_importance' in result['explainability']:
            print("\n💡 Top 5 Important Features:")
            imp = result['explainability']['feature_importance']
            for i, (feat, score) in enumerate(zip(imp['features'][:5], imp['importances'][:5])):
                print(f"   {i+1}. {feat}: {score:.4f}")
        
        # Recommendations
        print("\n🎯 Recommendations:")
        for rec in result['recommendations']['next_steps'][:3]:
            print(f"   - {rec}")
        
        print(f"\n💾 Model saved to: {result['best_model']['model_path']}")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
    
    print("\n")
    return agent, result


def example_regression():
    """
    Example 2: Regression - House Price Prediction
    """
    print("=" * 80)
    print("EXAMPLE 2: Regression - House Price Prediction")
    print("=" * 80)
    
    # Generate synthetic house price data
    np.random.seed(42)
    n_samples = 800
    
    data = pd.DataFrame({
        'square_feet': np.random.randint(800, 5000, n_samples),
        'bedrooms': np.random.randint(1, 6, n_samples),
        'bathrooms': np.random.randint(1, 4, n_samples),
        'age_years': np.random.randint(0, 50, n_samples),
        'lot_size': np.random.randint(1000, 20000, n_samples),
        'garage_spaces': np.random.randint(0, 3, n_samples),
        'has_pool': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'neighborhood_rating': np.random.randint(1, 11, n_samples)
    })
    
    # Create price based on realistic relationships
    data['price'] = (
        data['square_feet'] * 150 +
        data['bedrooms'] * 20000 +
        data['bathrooms'] * 15000 -
        data['age_years'] * 1000 +
        data['lot_size'] * 5 +
        data['has_pool'] * 30000 +
        data['neighborhood_rating'] * 10000 +
        np.random.normal(0, 20000, n_samples)
    )
    
    # Initialize agent
    agent = PredictionAgent(models_dir="models")
    
    # Run AutoML
    result = agent.auto_ml(
        data=data,
        target_column='price',
        problem_type='regression',
        test_size=0.2,
        feature_engineering=False,  # Skip to keep simple
        explain_model=True,
        save_model=True
    )
    
    # Display results
    if result['status'] == 'success':
        print(f"\n✅ AutoML Completed Successfully!")
        print(f"\nBest Model: {result['best_model']['name']}")
        print(f"R² Score: {result['best_model']['metrics']['r2_score']:.3f}")
        print(f"RMSE: ${result['best_model']['metrics']['rmse']:,.2f}")
        print(f"MAE: ${result['best_model']['metrics']['mae']:,.2f}")
        
        # Model comparison
        print("\n📊 Model Comparison:")
        comparison_df = pd.DataFrame(result['model_comparison'])
        print(comparison_df.to_string(index=False))
        
        # Feature importance
        if 'explainability' in result and 'feature_importance' in result['explainability']:
            print("\n💡 Top Features Affecting Price:")
            imp = result['explainability']['feature_importance']
            for i, (feat, score) in enumerate(zip(imp['features'][:5], imp['importances'][:5])):
                print(f"   {i+1}. {feat}: {score:.4f}")
        
        print(f"\n💾 Model saved to: {result['best_model']['model_path']}")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
    
    print("\n")
    return agent, result


def example_with_sklearn_data():
    """
    Example 3: Using scikit-learn's built-in datasets
    """
    print("=" * 80)
    print("EXAMPLE 3: Iris Classification (Classic ML Dataset)")
    print("=" * 80)
    
    from sklearn.datasets import load_iris
    
    # Load iris dataset
    iris = load_iris()
    data = pd.DataFrame(iris.data, columns=iris.feature_names)
    data['species'] = iris.target
    
    # Initialize agent
    agent = PredictionAgent(models_dir="models")
    
    # Run AutoML (auto-detect problem type)
    result = agent.auto_ml(
        data=data,
        target_column='species',
        problem_type=None,  # Auto-detect
        test_size=0.3,
        feature_engineering=False,
        explain_model=True,
        save_model=False  # Don't save this example
    )
    
    if result['status'] == 'success':
        print(f"\n✅ Problem Type Detected: {result['problem_type'].upper()}")
        print(f"Best Model: {result['best_model']['name']}")
        print(f"Accuracy: {result['best_model']['metrics']['accuracy']:.3f}")
        
        print("\n📊 All Models Performance:")
        comparison_df = pd.DataFrame(result['model_comparison'])
        print(comparison_df[['Model', 'Accuracy', 'F1 Score']].to_string(index=False))
        
        # Make predictions on new data
        print("\n🔮 Making Predictions on New Samples:")
        new_samples = data.sample(3).drop(columns=['species'])
        predictions = agent.predict(data=new_samples)
        
        print(f"Predictions: {predictions['predictions']}")
        print(f"Probabilities:\n{np.array(predictions['probabilities'])}")
    
    print("\n")
    return agent, result


def example_datetime_features():
    """
    Example 4: Dataset with DateTime Features
    """
    print("=" * 80)
    print("EXAMPLE 4: Sales Prediction with DateTime Features")
    print("=" * 80)
    
    # Generate synthetic sales data with dates
    np.random.seed(42)
    n_samples = 500
    
    # Create date range
    dates = pd.date_range(start='2023-01-01', periods=n_samples, freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'temperature': np.random.randint(50, 95, n_samples),
        'marketing_spend': np.random.randint(1000, 10000, n_samples),
        'competitor_price': np.random.randint(50, 150, n_samples),
        'inventory_level': np.random.randint(100, 1000, n_samples)
    })
    
    # Create sales with seasonal patterns
    day_of_week = data['date'].dt.dayofweek
    month = data['date'].dt.month
    
    data['sales'] = (
        1000 +  # Base sales
        (day_of_week == 5) * 500 +  # Weekend boost (Saturday)
        (day_of_week == 6) * 600 +  # Weekend boost (Sunday)
        (month == 12) * 800 +  # December boost
        data['marketing_spend'] * 0.5 +
        (100 - data['competitor_price']) * 10 +
        np.random.normal(0, 200, n_samples)
    )
    
    # Initialize agent
    agent = PredictionAgent(models_dir="models")
    
    # Run AutoML with feature engineering
    result = agent.auto_ml(
        data=data,
        target_column='sales',
        problem_type='regression',
        feature_engineering=True,  # Will extract datetime features!
        explain_model=True,
        save_model=False
    )
    
    if result['status'] == 'success':
        print(f"\n✅ AutoML Completed!")
        print(f"Features Created: {result['dataset_info']['n_features']} (including datetime features)")
        print(f"\nBest Model: {result['best_model']['name']}")
        print(f"R² Score: {result['best_model']['metrics']['r2_score']:.3f}")
        
        # Check if datetime features were created
        print("\n📅 Engineered DateTime Features:")
        datetime_features = [f for f in result['dataset_info']['feature_names'] 
                           if 'date_' in f or 'day' in f or 'month' in f]
        for feat in datetime_features[:8]:
            print(f"   - {feat}")
    
    print("\n")
    return agent, result


def main():
    """Run all examples"""
    print("\n" + "🤖" * 40)
    print("PREDICTION AGENT - EXAMPLE DEMONSTRATIONS")
    print("🤖" * 40 + "\n")
    
    # Example 1: Classification
    agent1, result1 = example_classification()
    
    # Example 2: Regression
    agent2, result2 = example_regression()
    
    # Example 3: sklearn datasets
    agent3, result3 = example_with_sklearn_data()
    
    # Example 4: DateTime features
    agent4, result4 = example_datetime_features()
    
    print("=" * 80)
    print("✅ All Examples Completed Successfully!")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Try with your own dataset")
    print("2. Explore saved models in the 'models/' directory")
    print("3. Integrate with File Ingestion Agent for data cleaning")
    print("4. Use Knowledge Agent for insights before prediction")
    print("\n")


if __name__ == "__main__":
    main()
