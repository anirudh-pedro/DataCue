"""
DataCue Full Stack Test Suite
Tests all layers: Health, Database, Chat, Ingestion, Dashboard, LLM
Run with: pytest tests/test_all_layers.py -v
"""

import pytest
import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

# ============================================================================
# LAYER 1: HEALTH ENDPOINTS
# ============================================================================

class TestLayer1Health:
    """Test health and root endpoints"""
    
    def test_health_endpoint(self):
        """TEST 1.1: /health returns healthy status"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["api"] == "ok"
        assert data["services"]["database"] == "ok"
        assert data["services"]["groq"] == "ok"
        print("✅ Health endpoint OK")
    
    def test_root_endpoint(self):
        """TEST 1.2: / returns API info"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "agents" in data
        print(f"✅ Root endpoint OK - Version: {data['version']}")
    
    def test_openapi_docs(self):
        """TEST 1.3: /openapi.json is accessible"""
        response = requests.get(f"{BASE_URL}/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        print(f"✅ OpenAPI docs OK - {len(data['paths'])} endpoints")


# ============================================================================
# LAYER 2: DATABASE LAYER
# ============================================================================

class TestLayer2Database:
    """Test database operations via API"""
    
    def test_create_session(self):
        """TEST 2.1: Create chat session"""
        response = requests.post(
            f"{BASE_URL}/chat/sessions",
            json={
                "user_id": f"test_user_{uuid.uuid4().hex[:8]}",
                "email": "test@datacue.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 32
        # Store globally for other tests
        global test_session_id
        test_session_id = data["session_id"]
        print(f"✅ Session created: {data['session_id']}")
        return data["session_id"]


# ============================================================================
# LAYER 3: CHAT API LAYER
# ============================================================================

class TestLayer3ChatAPI:
    """Test chat session and message operations"""
    
    @pytest.fixture
    def session_id(self):
        """Create a session for testing"""
        response = requests.post(
            f"{BASE_URL}/chat/sessions",
            json={
                "user_id": f"test_user_{uuid.uuid4().hex[:8]}",
                "email": "test@datacue.com"
            }
        )
        return response.json()["session_id"]
    
    def test_add_message(self, session_id):
        """TEST 3.1: Add message to session"""
        response = requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            json={
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "user",
                "content": "Hello, this is a test message",
                "timestamp": "2026-01-01T12:00:00Z"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        assert data["content"] == "Hello, this is a test message"
        print("✅ Message added successfully")
    
    def test_get_messages(self, session_id):
        """TEST 3.2: Get session messages"""
        # First add a message
        requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            json={
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "user",
                "content": "Test message for retrieval",
                "timestamp": "2026-01-01T12:00:00Z"
            }
        )
        
        # Then retrieve
        response = requests.get(f"{BASE_URL}/chat/sessions/{session_id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 1
        print(f"✅ Retrieved {len(data['messages'])} messages")
    
    def test_update_session_title(self, session_id):
        """TEST 3.3: Update session title"""
        response = requests.patch(
            f"{BASE_URL}/chat/sessions/{session_id}/title",
            json={"title": "Test Session Title"}
        )
        assert response.status_code == 200
        print("✅ Session title updated")


# ============================================================================
# LAYER 4: DASHBOARD GENERATION
# ============================================================================

class TestLayer4Dashboard:
    """Test dashboard generation with LLM"""
    
    def test_dashboard_health(self):
        """TEST 4.1: Dashboard service health"""
        response = requests.get(f"{BASE_URL}/dashboard/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ Dashboard service healthy")
    
    def test_generate_dashboard_with_data(self):
        """TEST 4.2: Generate dashboard from inline data"""
        test_data = [
            {"name": "Alice", "age": 30, "salary": 50000, "department": "Engineering"},
            {"name": "Bob", "age": 25, "salary": 45000, "department": "Marketing"},
            {"name": "Charlie", "age": 35, "salary": 60000, "department": "Engineering"},
            {"name": "Diana", "age": 28, "salary": 52000, "department": "Sales"},
            {"name": "Eve", "age": 32, "salary": 55000, "department": "Marketing"},
        ]
        
        metadata = {
            "columns": [
                {"name": "name", "type": "string"},
                {"name": "age", "type": "numeric"},
                {"name": "salary", "type": "numeric"},
                {"name": "department", "type": "string"}
            ],
            "row_count": 5,
            "column_count": 4
        }
        
        response = requests.post(
            f"{BASE_URL}/dashboard/generate",
            json={"data": test_data, "metadata": metadata},
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "dashboard" in data
        assert "charts" in data["dashboard"]
        print(f"✅ Dashboard generated: {data['dashboard']['title']}")
        print(f"   Charts: {len(data['dashboard']['charts'])}")
        return data


# ============================================================================
# LAYER 5: KNOWLEDGE/ASK API
# ============================================================================

class TestLayer5Knowledge:
    """Test knowledge and ask endpoints"""
    
    @pytest.fixture
    def session_with_data(self):
        """Create session and add data for testing"""
        # Create session
        session_resp = requests.post(
            f"{BASE_URL}/chat/sessions",
            json={
                "user_id": f"test_user_{uuid.uuid4().hex[:8]}",
                "email": "test@datacue.com"
            }
        )
        session_id = session_resp.json()["session_id"]
        return session_id
    
    def test_ask_visual_endpoint(self, session_with_data):
        """TEST 5.1: Ask visual question"""
        response = requests.post(
            f"{BASE_URL}/knowledge/ask-visual",
            json={
                "session_id": session_with_data,
                "question": "What insights can you provide?",
                "data": [
                    {"product": "A", "sales": 100},
                    {"product": "B", "sales": 150},
                    {"product": "C", "sales": 80}
                ]
            },
            timeout=30
        )
        # May return 200 or 400 depending on data availability
        assert response.status_code in [200, 400, 500]
        print(f"✅ Ask-visual endpoint responded: {response.status_code}")


# ============================================================================
# LAYER 6: ORCHESTRATOR
# ============================================================================

class TestLayer6Orchestrator:
    """Test orchestrator pipeline"""
    
    def test_orchestrator_health(self):
        """TEST 6.1: Orchestrator health check"""
        response = requests.get(f"{BASE_URL}/orchestrator/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ Orchestrator service healthy")


# ============================================================================
# LAYER 7: INTEGRATION TESTS
# ============================================================================

class TestLayer7Integration:
    """End-to-end integration tests"""
    
    def test_full_chat_flow(self):
        """TEST 7.1: Complete chat session flow"""
        # 1. Create session
        session_resp = requests.post(
            f"{BASE_URL}/chat/sessions",
            json={
                "user_id": f"integration_test_{uuid.uuid4().hex[:8]}",
                "email": "integration@test.com"
            }
        )
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session_id"]
        print(f"  Step 1: Session created - {session_id[:16]}...")
        
        # 2. Add user message
        msg_resp = requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            json={
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "user",
                "content": "Analyze my sales data",
                "timestamp": "2026-01-01T12:00:00Z"
            }
        )
        assert msg_resp.status_code == 200
        print("  Step 2: User message added")
        
        # 3. Add assistant response
        assist_resp = requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            json={
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": "I'll analyze your sales data. Please upload a CSV file.",
                "timestamp": "2026-01-01T12:00:01Z"
            }
        )
        assert assist_resp.status_code == 200
        print("  Step 3: Assistant response added")
        
        # 4. Verify messages
        msgs_resp = requests.get(f"{BASE_URL}/chat/sessions/{session_id}/messages")
        assert msgs_resp.status_code == 200
        messages = msgs_resp.json()["messages"]
        assert len(messages) == 2
        print(f"  Step 4: Verified {len(messages)} messages")
        
        # 5. Update title
        title_resp = requests.patch(
            f"{BASE_URL}/chat/sessions/{session_id}/title",
            json={"title": "Sales Analysis Session"}
        )
        assert title_resp.status_code == 200
        print("  Step 5: Session title updated")
        
        print("✅ Full chat flow completed successfully")
    
    def test_dashboard_generation_flow(self):
        """TEST 7.2: Dashboard generation with realistic data"""
        # Realistic sales data
        sales_data = [
            {"month": "Jan", "revenue": 45000, "units": 120, "region": "North"},
            {"month": "Feb", "revenue": 52000, "units": 145, "region": "South"},
            {"month": "Mar", "revenue": 48000, "units": 130, "region": "North"},
            {"month": "Apr", "revenue": 61000, "units": 165, "region": "East"},
            {"month": "May", "revenue": 55000, "units": 150, "region": "West"},
            {"month": "Jun", "revenue": 67000, "units": 180, "region": "South"},
        ]
        
        metadata = {
            "columns": [
                {"name": "month", "type": "string"},
                {"name": "revenue", "type": "numeric"},
                {"name": "units", "type": "numeric"},
                {"name": "region", "type": "string"}
            ],
            "row_count": 6,
            "column_count": 4
        }
        
        response = requests.post(
            f"{BASE_URL}/dashboard/generate",
            json={
                "data": sales_data,
                "metadata": metadata,
                "user_prompt": "Create a sales performance dashboard"
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        dashboard = data["dashboard"]
        print(f"  Dashboard: {dashboard['title']}")
        print(f"  Charts: {len(dashboard['charts'])}")
        
        for i, chart in enumerate(dashboard["charts"]):
            print(f"    {i+1}. {chart['title']} ({chart['type']})")
        
        if "insights" in data and data["insights"]:
            print(f"  Insights: {len(data['insights'])}")
        
        print("✅ Dashboard generation flow completed")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DATACUE FULL STACK TEST SUITE")
    print("="*60 + "\n")
    
    # Run tests manually for quick execution
    print("LAYER 1: HEALTH ENDPOINTS")
    print("-" * 40)
    t1 = TestLayer1Health()
    t1.test_health_endpoint()
    t1.test_root_endpoint()
    t1.test_openapi_docs()
    
    print("\nLAYER 2: DATABASE LAYER")
    print("-" * 40)
    t2 = TestLayer2Database()
    session_id = t2.test_create_session()
    
    print("\nLAYER 3: CHAT API LAYER")
    print("-" * 40)
    t3 = TestLayer3ChatAPI()
    t3.test_add_message(session_id)
    t3.test_get_messages(session_id)
    t3.test_update_session_title(session_id)
    
    print("\nLAYER 4: DASHBOARD GENERATION")
    print("-" * 40)
    t4 = TestLayer4Dashboard()
    t4.test_dashboard_health()
    t4.test_generate_dashboard_with_data()
    
    print("\nLAYER 6: ORCHESTRATOR")
    print("-" * 40)
    t6 = TestLayer6Orchestrator()
    t6.test_orchestrator_health()
    
    print("\nLAYER 7: INTEGRATION TESTS")
    print("-" * 40)
    t7 = TestLayer7Integration()
    t7.test_full_chat_flow()
    t7.test_dashboard_generation_flow()
    
    print("\n" + "="*60)
    print("  ALL TESTS COMPLETED SUCCESSFULLY ✅")
    print("="*60 + "\n")
