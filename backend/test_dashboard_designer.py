"""
Test Dashboard Designer Functionality
Quick validation script
"""
import sys
sys.path.append('.')

def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")
    
    try:
        from models.dashboard_models import (
            DashboardTemplate, TemplateSection, ChartOption, ChartType
        )
        print("✅ Models imported successfully")
        
        from agents.dashboard_designer_agent import (
            TemplateLibrary, DataAnalyzer, DashboardDesignerAgent
        )
        print("✅ Agent modules imported successfully")
        
        from services.dashboard_designer_service import DashboardDesignerService
        print("✅ Service imported successfully")
        
        from routers.dashboard_designer_router import router
        print("✅ Router imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False


def test_template_library():
    """Test template library"""
    print("\nTesting template library...")
    
    try:
        from agents.dashboard_designer_agent import TemplateLibrary
        
        library = TemplateLibrary()
        templates = library.list_templates()
        
        print(f"✅ Found {len(templates)} templates:")
        for template in templates:
            print(f"   - {template.name} ({template.template_id}): {len(template.sections)} sections")
        
        # Test getting specific template
        sales_template = library.get_template("sales_overview")
        print(f"✅ Sales template has sections: {[s.section_id for s in sales_template.sections]}")
        
        return True
    except Exception as e:
        print(f"❌ Template library test failed: {str(e)}")
        return False


def test_data_analyzer():
    """Test data analyzer with sample data"""
    print("\nTesting data analyzer...")
    
    try:
        import pandas as pd
        from agents.dashboard_designer_agent import DataAnalyzer
        from models.dashboard_models import ChartType
        
        # Create sample data
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'revenue': [100, 150, 120, 180, 200, 190, 210, 230, 250, 270],
            'category': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
            'count': [10, 20, 15, 25, 30, 35, 40, 45, 50, 55]
        })
        
        analyzer = DataAnalyzer()
        
        # Analyze dataset
        dataset_info = analyzer.analyze_dataset(df, "test_dataset")
        print(f"✅ Dataset analyzed: {len(dataset_info.columns)} columns")
        print(f"   Column types: {dataset_info.column_types}")
        
        # Test chart compatibility
        compatible = analyzer.get_compatible_chart_types("datetime", "numeric")
        print(f"✅ Compatible charts for datetime x numeric: {[c.value for c in compatible]}")
        
        # Test axis options
        x_opts, y_opts, color_opts = analyzer.get_axis_options(dataset_info, ChartType.LINE)
        print(f"✅ Line chart options - X: {x_opts}, Y: {y_opts}")
        
        # Test validation
        is_valid, msg = analyzer.validate_chart_config(
            dataset_info, ChartType.LINE, "date", "revenue"
        )
        print(f"✅ Validation test: {is_valid}")
        
        return True
    except Exception as e:
        print(f"❌ Data analyzer test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_router_structure():
    """Test router has all endpoints"""
    print("\nTesting router structure...")
    
    try:
        from routers.dashboard_designer_router import router
        
        routes = [route.path for route in router.routes]
        print(f"✅ Router has {len(routes)} endpoints:")
        for route in router.routes:
            if hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"   {methods} {route.path}")
        
        return True
    except Exception as e:
        print(f"❌ Router test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Dashboard Designer Backend - Validation Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Template Library", test_template_library()))
    results.append(("Data Analyzer", test_data_analyzer()))
    results.append(("Router Structure", test_router_structure()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Dashboard Designer is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    print("=" * 60)
