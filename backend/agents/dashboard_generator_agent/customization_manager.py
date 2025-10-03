"""
Dashboard Customization Manager
Handles user preferences for dashboard personalization
"""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardCustomizer:
    """
    Manages user customization preferences for dashboards
    Supports hiding charts, reordering, changing chart types, and persisting preferences
    """
    
    def __init__(self, storage_backend: Optional[str] = None):
        """
        Initialize customization manager
        
        Args:
            storage_backend: Path to JSON file for persistence (optional)
        """
        self.storage_backend = storage_backend
        self.preferences = {}
    
    def apply_user_preferences(
        self,
        dashboard_config: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user customization preferences to dashboard configuration
        
        Args:
            dashboard_config: Original dashboard configuration
            user_preferences: User customization settings
            
        Returns:
            Modified dashboard configuration
        """
        try:
            modified_config = dashboard_config.copy()
            
            # Apply chart visibility
            if 'hidden_charts' in user_preferences:
                modified_config['charts'] = self._filter_hidden_charts(
                    modified_config['charts'],
                    user_preferences['hidden_charts']
                )
            
            # Apply chart reordering
            if 'chart_order' in user_preferences:
                modified_config['charts'] = self._reorder_charts(
                    modified_config['charts'],
                    user_preferences['chart_order']
                )
            
            # Apply chart type changes
            if 'chart_type_overrides' in user_preferences:
                modified_config['charts'] = self._apply_chart_type_overrides(
                    modified_config['charts'],
                    user_preferences['chart_type_overrides']
                )
            
            # Apply filter visibility
            if 'hidden_filters' in user_preferences:
                modified_config['filters'] = self._filter_hidden_filters(
                    modified_config['filters'],
                    user_preferences['hidden_filters']
                )
            
            # Apply layout preferences
            if 'layout_preferences' in user_preferences:
                modified_config['layout'] = self._apply_layout_preferences(
                    modified_config['layout'],
                    user_preferences['layout_preferences']
                )
            
            # Add customization metadata
            modified_config['customization'] = {
                "applied": True,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_preferences.get('user_id', 'anonymous'),
                "preferences_version": user_preferences.get('version', '1.0')
            }
            
            return modified_config
            
        except Exception as e:
            logger.error(f"Error applying user preferences: {str(e)}")
            return dashboard_config  # Return original on error
    
    def _filter_hidden_charts(
        self,
        charts: List[Dict[str, Any]],
        hidden_chart_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Remove hidden charts from configuration
        """
        return [chart for chart in charts if chart['id'] not in hidden_chart_ids]
    
    def _reorder_charts(
        self,
        charts: List[Dict[str, Any]],
        chart_order: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Reorder charts based on user preference
        """
        # Create lookup dict
        chart_dict = {chart['id']: chart for chart in charts}
        
        # Reorder based on preference
        reordered = []
        for chart_id in chart_order:
            if chart_id in chart_dict:
                reordered.append(chart_dict[chart_id])
        
        # Add any charts not in order list (in case new charts were added)
        for chart in charts:
            if chart['id'] not in chart_order:
                reordered.append(chart)
        
        return reordered
    
    def _apply_chart_type_overrides(
        self,
        charts: List[Dict[str, Any]],
        type_overrides: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Change chart types based on user preference
        
        type_overrides format: {chart_id: new_chart_type}
        """
        modified_charts = []
        
        for chart in charts:
            if chart['id'] in type_overrides:
                new_type = type_overrides[chart['id']]
                chart_copy = chart.copy()
                chart_copy['type'] = new_type
                chart_copy['customized'] = True
                chart_copy['original_type'] = chart['type']
                modified_charts.append(chart_copy)
            else:
                modified_charts.append(chart)
        
        return modified_charts
    
    def _filter_hidden_filters(
        self,
        filters: List[Dict[str, Any]],
        hidden_filter_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Remove hidden filters from configuration
        """
        return [f for f in filters if f['id'] not in hidden_filter_ids]
    
    def _apply_layout_preferences(
        self,
        layout: Dict[str, Any],
        layout_prefs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply layout customizations
        """
        modified_layout = layout.copy()
        
        # Apply grid column override
        if 'grid_columns' in layout_prefs:
            modified_layout['grid_columns'] = layout_prefs['grid_columns']
        
        # Apply sidebar visibility
        if 'hide_sidebar' in layout_prefs:
            modified_layout['has_sidebar'] = not layout_prefs['hide_sidebar']
        
        # Apply theme
        if 'theme' in layout_prefs:
            modified_layout['theme'] = layout_prefs['theme']
        
        return modified_layout
    
    def save_preferences(
        self,
        dashboard_id: str,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Save user preferences to storage backend
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.storage_backend:
                logger.warning("No storage backend configured")
                return False
            
            # Create preference entry
            pref_entry = {
                "dashboard_id": dashboard_id,
                "user_id": user_id,
                "preferences": preferences,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Load existing preferences
            try:
                with open(self.storage_backend, 'r') as f:
                    all_prefs = json.load(f)
            except FileNotFoundError:
                all_prefs = []
            
            # Update or append
            key = f"{user_id}_{dashboard_id}"
            updated = False
            for i, pref in enumerate(all_prefs):
                if pref['user_id'] == user_id and pref['dashboard_id'] == dashboard_id:
                    all_prefs[i] = pref_entry
                    updated = True
                    break
            
            if not updated:
                all_prefs.append(pref_entry)
            
            # Save back
            with open(self.storage_backend, 'w') as f:
                json.dump(all_prefs, f, indent=2)
            
            logger.info(f"Saved preferences for user {user_id}, dashboard {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving preferences: {str(e)}")
            return False
    
    def load_preferences(
        self,
        dashboard_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load user preferences from storage backend
        
        Returns:
            User preferences dict or None if not found
        """
        try:
            if not self.storage_backend:
                return None
            
            with open(self.storage_backend, 'r') as f:
                all_prefs = json.load(f)
            
            for pref in all_prefs:
                if pref['user_id'] == user_id and pref['dashboard_id'] == dashboard_id:
                    return pref['preferences']
            
            return None
            
        except FileNotFoundError:
            logger.warning(f"Preferences file not found: {self.storage_backend}")
            return None
        except Exception as e:
            logger.error(f"Error loading preferences: {str(e)}")
            return None
    
    def create_preference_template(
        self,
        dashboard_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a preference template based on current dashboard configuration
        Users can modify this template to customize their dashboard
        
        Returns:
            Preference template with all available customization options
        """
        return {
            "version": "1.0",
            "user_id": "user_id_here",
            "hidden_charts": [],  # Add chart IDs to hide
            "chart_order": [chart['id'] for chart in dashboard_config.get('charts', [])],
            "chart_type_overrides": {},  # {chart_id: new_type}
            "hidden_filters": [],  # Add filter IDs to hide
            "layout_preferences": {
                "grid_columns": 12,
                "hide_sidebar": False,
                "theme": "light"  # "light", "dark", "auto"
            },
            "available_chart_types": [
                "histogram", "bar", "line", "scatter", "pie", 
                "box_plot", "heatmap", "grouped_bar", "time_series"
            ],
            "available_charts": [
                {
                    "id": chart['id'],
                    "title": chart['title'],
                    "type": chart['type']
                }
                for chart in dashboard_config.get('charts', [])
            ],
            "available_filters": [
                {
                    "id": f['id'],
                    "label": f['label'],
                    "column": f['column']
                }
                for f in dashboard_config.get('filters', [])
            ]
        }
    
    def validate_preferences(
        self,
        preferences: Dict[str, Any],
        dashboard_config: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Validate user preferences against dashboard configuration
        
        Returns:
            Dictionary of validation errors by category
        """
        errors = {
            "invalid_chart_ids": [],
            "invalid_filter_ids": [],
            "invalid_chart_types": [],
            "warnings": []
        }
        
        valid_chart_ids = {chart['id'] for chart in dashboard_config.get('charts', [])}
        valid_filter_ids = {f['id'] for f in dashboard_config.get('filters', [])}
        valid_chart_types = {
            "histogram", "bar", "line", "scatter", "pie",
            "box_plot", "heatmap", "grouped_bar", "time_series"
        }
        
        # Validate hidden charts
        for chart_id in preferences.get('hidden_charts', []):
            if chart_id not in valid_chart_ids:
                errors['invalid_chart_ids'].append(chart_id)
        
        # Validate chart order
        for chart_id in preferences.get('chart_order', []):
            if chart_id not in valid_chart_ids:
                errors['invalid_chart_ids'].append(chart_id)
        
        # Validate chart type overrides
        for chart_id, new_type in preferences.get('chart_type_overrides', {}).items():
            if chart_id not in valid_chart_ids:
                errors['invalid_chart_ids'].append(chart_id)
            if new_type not in valid_chart_types:
                errors['invalid_chart_types'].append(new_type)
        
        # Validate hidden filters
        for filter_id in preferences.get('hidden_filters', []):
            if filter_id not in valid_filter_ids:
                errors['invalid_filter_ids'].append(filter_id)
        
        # Warning: hiding all charts
        if len(preferences.get('hidden_charts', [])) == len(valid_chart_ids):
            errors['warnings'].append("All charts are hidden")
        
        return errors
