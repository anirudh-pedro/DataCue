"""
Knowledge Agent - Main Orchestrator
Coordinates all Phase 4 modules to provide comprehensive data understanding and insights.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from .data_profiler import DataProfiler
from .insight_generator import InsightGenerator
from .query_engine import QueryEngine
from .recommendation_engine import RecommendationEngine
from .report_generator import ReportGenerator
from core.config import get_settings


class KnowledgeAgent:
    """
    Main orchestrator for the Knowledge Agent (Phase 4).
    
    Transforms cleaned datasets into actionable insights by:
    1. Profiling data comprehensively
    2. Generating AI-powered insights
    3. Answering natural language questions
    4. Recommending next analytical steps
    5. Creating comprehensive EDA reports
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialize the Knowledge Agent.
        
        Args:
            groq_api_key: Optional Groq API key for LLM-powered features
        """
        settings = get_settings()
        resolved_api_key = groq_api_key or settings.groq_api_key

        self.profiler = DataProfiler()
        self.insight_generator = InsightGenerator(api_key=resolved_api_key)
        self.query_engine = QueryEngine()
        self.recommendation_engine = RecommendationEngine()
        self.report_generator = ReportGenerator()
        
        # State
        self.data = None
        self.profile_data = None
        self.insights = None
        self.recommendations = None
        self.analysis_complete = False
    
    def set_groq_api_key(self, api_key: str):
        """
        Set or update the Groq API key for LLM features.
        
        Args:
            api_key: Groq API key
        """
        self.insight_generator.set_api_key(api_key)
    
    def analyze_dataset(
        self,
        data: pd.DataFrame,
        generate_insights: bool = True,
        generate_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete analysis of the dataset.
        
        Args:
            data: Input DataFrame (should be cleaned)
            generate_insights: Whether to generate AI insights
            generate_recommendations: Whether to generate recommendations
            
        Returns:
            Complete analysis results dictionary
        """
        print("🔍 Starting Knowledge Agent Analysis...")
        
        # Store data
        self.data = data.copy()
        
        # Step 1: Profile the dataset
        print("📊 Step 1/4: Profiling dataset...")
        self.profile_data = self.profiler.profile_dataset(data)
        
        # Step 2: Generate insights
        insights_result = None
        if generate_insights:
            print("💡 Step 2/4: Generating insights...")
            self.insights = self.insight_generator.generate_insights(
                self.profile_data,
                data
            )
        else:
            self.insights = {}
            print("⏭️  Step 2/4: Skipping insights generation...")
        
        # Step 3: Generate recommendations
        if generate_recommendations:
            print("🎯 Step 3/4: Generating recommendations...")
            self.recommendations = self.recommendation_engine.generate_recommendations(
                self.profile_data,
                data,
                self.insights
            )
        else:
            self.recommendations = {}
            print("⏭️  Step 3/4: Skipping recommendations...")
        
        # Step 4: Set up query engine
        print("🔧 Step 4/4: Initializing query engine...")
        self.query_engine.set_data(data, self.profile_data)
        
        self.analysis_complete = True
        print("✅ Analysis complete!\n")
        
        # Return comprehensive results
        return {
            'status': 'success',
            'analysis_timestamp': datetime.now().isoformat(),
            'profile': self.profile_data,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'summary': self.get_summary()
        }
    
    def ask_question(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Answer a natural language question about the data.
        
        Args:
            question: Natural language question
            use_cache: Whether to use cached results
            
        Returns:
            Answer dictionary with response and metadata
        """
        if not self.analysis_complete:
            return {
                'success': False,
                'error': 'Please run analyze_dataset() first.'
            }
        
        # Use query engine for structured questions
        query_result = self.query_engine.query(question, use_cache=use_cache)
        
        # If query engine can't answer, try LLM
        if not query_result.get('success', False) and self.insight_generator.groq_client:
            llm_answer = self.insight_generator.answer_question(
                question,
                self.profile_data,
                self.data
            )
            return {
                'success': True,
                'answer': llm_answer,
                'method': 'llm',
                'question': question
            }
        
        return query_result
    
    def generate_report(
        self,
        format: str = 'markdown',
        filepath: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive EDA report.
        
        Args:
            format: 'markdown' or 'html'
            filepath: Optional path to save the report
            
        Returns:
            Report content as string
        """
        if not self.analysis_complete:
            return "Error: Please run analyze_dataset() first."
        
        report = self.report_generator.generate_report(
            data=self.data,
            profile_data=self.profile_data,
            insights=self.insights,
            recommendations=self.recommendations,
            format=format
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Report saved to: {filepath}")
        
        return report
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a quick summary of the analysis.
        
        Returns:
            Summary dictionary
        """
        if not self.profile_data:
            return {'error': 'No analysis performed yet'}
        
        basic = self.profile_data['basic_info']
        quality = self.profile_data['data_quality']
        correlations = self.profile_data['correlations']
        
        return {
            'dataset_size': f"{basic['num_rows']:,} rows × {basic['num_columns']} columns",
            'memory_usage': f"{basic['memory_usage_mb']:.2f} MB",
            'quality_score': f"{quality['overall_quality_score']:.1f}/100 ({quality['quality_grade']})",
            'missing_data': f"{basic['total_missing_values']:,} values ({basic['missing_percentage']:.2f}%)",
            'duplicates': f"{basic['duplicate_rows']:,} rows",
            'strong_correlations': correlations.get('num_strong_correlations', 0),
            'column_types': basic['column_types'],
            'analysis_complete': self.analysis_complete
        }
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get the complete data profile"""
        return self.profile_data
    
    def get_insights(self) -> Optional[Dict[str, Any]]:
        """Get all generated insights"""
        return self.insights
    
    def get_recommendations(self) -> Optional[Dict[str, Any]]:
        """Get all recommendations"""
        return self.recommendations
    
    def get_key_findings(self, limit: int = 10) -> List[str]:
        """
        Get top key findings from the analysis.
        
        Args:
            limit: Maximum number of findings to return
            
        Returns:
            List of key findings
        """
        if not self.insights:
            return []
        
        findings = self.insights.get('key_findings', [])
        return findings[:limit]
    
    def get_visualization_recommendations(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recommended visualizations.
        
        Args:
            priority: Filter by priority ('high', 'medium', 'low')
            
        Returns:
            List of visualization recommendations
        """
        if not self.recommendations:
            return []
        
        viz_recs = self.recommendations.get('visualization', [])
        
        if priority:
            viz_recs = [v for v in viz_recs if v.get('priority') == priority]
        
        return viz_recs
    
    def get_modeling_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get ML modeling recommendations.
        
        Returns:
            List of modeling recommendations
        """
        if not self.recommendations:
            return []
        
        return self.recommendations.get('modeling', [])
    
    def get_next_steps(self) -> List[Dict[str, str]]:
        """
        Get recommended next steps.
        
        Returns:
            List of next steps
        """
        if not self.recommendations:
            return []
        
        return self.recommendations.get('next_steps', [])
    
    def export_insights(self, filepath: str, format: str = 'json'):
        """
        Export insights to a file.
        
        Args:
            filepath: Path to save insights
            format: 'json' or 'pickle'
        """
        if not self.insights:
            raise ValueError("No insights available. Run analyze_dataset() first.")
        
        if format == 'json':
            import json
            with open(filepath, 'w') as f:
                # Convert numpy types for JSON serialization
                json_safe_insights = self._make_json_safe(self.insights)
                json.dump(json_safe_insights, f, indent=2)
        elif format == 'pickle':
            import pickle
            with open(filepath, 'wb') as f:
                pickle.dump(self.insights, f)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"💾 Insights exported to: {filepath}")
    
    def _make_json_safe(self, obj):
        """Convert numpy/pandas types to JSON-safe types"""
        if isinstance(obj, dict):
            return {k: self._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get query cache statistics"""
        return self.query_engine.get_cache_stats()
    
    def clear_cache(self):
        """Clear the query cache"""
        self.query_engine.clear_cache()
    
    def __repr__(self) -> str:
        """String representation"""
        if self.analysis_complete:
            summary = self.get_summary()
            return f"""KnowledgeAgent(
    status='analyzed',
    dataset={summary['dataset_size']},
    quality={summary['quality_score']},
    correlations={summary['strong_correlations']}
)"""
        else:
            return "KnowledgeAgent(status='not_analyzed')"
