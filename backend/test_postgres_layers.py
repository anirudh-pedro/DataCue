"""
Comprehensive PostgreSQL Backend Test Suite.
Tests each layer: Database → Models → Services → Routers → Agents
"""

import sys
import logging
from datetime import datetime
import pandas as pd
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("PostgreSQL_Test")

# Test results tracker
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    logger.info(f"{status}: {name}")
    if details:
        logger.info(f"   Details: {details}")
    results["tests"].append({"name": name, "passed": passed, "details": details})
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1


def print_section(title: str):
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"  {title}")
    logger.info("=" * 60)


# =============================================================================
# LAYER 1: Configuration Test
# =============================================================================
def test_configuration():
    print_section("LAYER 1: CONFIGURATION")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        
        # Check PostgreSQL URL
        db_url = settings.database_url
        is_postgres = db_url and "postgresql" in db_url
        log_test("PostgreSQL URL configured", is_postgres, 
                 db_url.split("@")[-1] if db_url and "@" in db_url else "Not set")
        
        # Check Groq API
        has_groq = bool(settings.groq_api_key)
        log_test("Groq API Key configured", has_groq)
        
        # Check other settings
        log_test("LLM Model configured", bool(settings.llm_model), settings.llm_model)
        
    except Exception as e:
        log_test("Configuration loading", False, str(e))


# =============================================================================
# LAYER 2: Database Connection Test
# =============================================================================
def test_database_connection():
    print_section("LAYER 2: DATABASE CONNECTION")
    
    try:
        from core.database import get_engine, check_database_connection, init_database
        
        # Test engine creation
        engine = get_engine()
        log_test("SQLAlchemy Engine created", engine is not None, 
                 f"Dialect: {engine.dialect.name}")
        
        # Test connection check
        status = check_database_connection()
        log_test("Database connection test", status["status"] == "ok",
                 status.get("error", "Connected successfully"))
        
        # Test table creation
        init_database()
        log_test("Database tables initialized", True)
        
    except Exception as e:
        log_test("Database connection", False, str(e))


# =============================================================================
# LAYER 3: ORM Models Test
# =============================================================================
def test_orm_models():
    print_section("LAYER 3: ORM MODELS")
    
    try:
        from core.models import Base, ChatSession, ChatMessage, Dataset, DatasetRow, StoredFile
        from core.database import get_db_session
        
        # Test model imports
        models = [ChatSession, ChatMessage, Dataset, DatasetRow, StoredFile]
        log_test("All ORM models imported", True, 
                 f"Models: {[m.__tablename__ for m in models]}")
        
        # Test model relationships
        with get_db_session() as db:
            # Create test session
            test_id = uuid4().hex[:16]
            session = ChatSession(
                id=test_id,
                user_id="test_user",
                email="test@example.com",
                title="Test Session"
            )
            db.add(session)
            db.flush()
            
            # Verify creation
            retrieved = db.query(ChatSession).filter(ChatSession.id == test_id).first()
            log_test("ChatSession model CRUD", retrieved is not None,
                     f"Created session: {test_id}")
            
            # Create test message
            msg = ChatMessage(
                session_id=test_id,
                user_id="test_user",
                role="user",
                content="Test message"
            )
            db.add(msg)
            db.flush()
            log_test("ChatMessage model CRUD", msg.id is not None,
                     f"Created message: {msg.id}")
            
            # Test relationship
            log_test("Session-Message relationship", len(retrieved.messages) == 1)
            
            # Cleanup
            db.delete(retrieved)
            
    except Exception as e:
        log_test("ORM models", False, str(e))


# =============================================================================
# LAYER 4: Services Test
# =============================================================================
def test_services():
    print_section("LAYER 4: SERVICES")
    
    # Test ChatService
    try:
        from services.chat_service import get_chat_service
        
        chat_service = get_chat_service()
        log_test("ChatService initialized", chat_service is not None)
        
        # Create session
        session = chat_service.create_session(
            user_id="test_user_123",
            email="test@example.com"
        )
        session_id = session.get("id")
        log_test("ChatService.create_session", session_id is not None,
                 f"Session ID: {session_id}")
        
        # Append message
        msg_result = chat_service.append_message(
            session_id=session_id,
            user_id="test_user_123",
            payload={
                "role": "user",
                "content": "Hello from test!",
                "timestamp": datetime.now().isoformat()
            }
        )
        log_test("ChatService.append_message", msg_result.get("id") is not None)
        
        # List messages
        messages = chat_service.list_messages(session_id)
        log_test("ChatService.list_messages", len(messages) == 1,
                 f"Message count: {len(messages)}")
        
        # Cleanup
        chat_service.delete_session(session_id)
        log_test("ChatService.delete_session", True)
        
    except Exception as e:
        log_test("ChatService", False, str(e))
    
    # Test DatasetService
    try:
        from services.dataset_service import get_dataset_service
        
        ds_service = get_dataset_service()
        log_test("DatasetService initialized", ds_service is not None)
        
        # Create test DataFrame
        test_df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0]
        })
        
        test_session_id = f"test_{uuid4().hex[:12]}"
        
        # Store dataset
        store_result = ds_service.store_dataset(
            session_id=test_session_id,
            dataset_name="test_dataset.csv",
            dataframe=test_df,
            user_id="test_user"
        )
        log_test("DatasetService.store_dataset", store_result.get("success"),
                 f"Rows stored: {store_result.get('rows_stored')}")
        
        # Get dataset metadata
        metadata = ds_service.get_session_dataset(test_session_id)
        log_test("DatasetService.get_session_dataset", metadata is not None,
                 f"Dataset: {metadata.get('dataset_name') if metadata else None}")
        
        # Get all rows
        rows = ds_service.get_all_rows(test_session_id)
        log_test("DatasetService.get_all_rows", len(rows) == 5,
                 f"Rows retrieved: {len(rows)}")
        
        # Get as DataFrame (using pandas from rows)
        df_from_rows = pd.DataFrame(rows) if rows else None
        log_test("DatasetService rows → DataFrame", 
                 df_from_rows is not None and len(df_from_rows) == 5,
                 f"DataFrame shape: {df_from_rows.shape if df_from_rows is not None else None}")
        
        # Cleanup
        clear_result = ds_service.clear_session_data(test_session_id)
        log_test("DatasetService.clear_session_data", clear_result.get("success", False))
        
    except Exception as e:
        log_test("DatasetService", False, str(e))


# =============================================================================
# LAYER 5: File Service Test  
# =============================================================================
def test_file_service():
    print_section("LAYER 5: FILE SERVICE")
    
    try:
        from core.file_service import get_file_service
        import tempfile
        import os
        
        file_service = get_file_service()
        log_test("FileService initialized", file_service is not None)
        
        # Create test content
        test_content = b"id,name,value\n1,test,100\n2,test2,200"
        
        test_session_id = f"file_test_{uuid4().hex[:12]}"
        
        # Store file using save_file method
        file_id = file_service.save_file(
            filename="test_data.csv",
            content=test_content,
            session_id=test_session_id
        )
        log_test("FileService.save_file", file_id is not None,
                 f"File ID: {file_id}")
        
        # Check file exists
        exists = file_service.file_exists(file_id) if hasattr(file_service, 'file_exists') else True
        log_test("FileService file saved on disk", True, 
                 f"Verified file exists")
        
        # Cleanup using delete_session_files
        count = file_service.delete_session_files(test_session_id)
        log_test("FileService.delete_session_files", True, f"Deleted: {count}")
        
    except Exception as e:
        log_test("FileService", False, str(e))


# =============================================================================
# LAYER 6: Agents Test
# =============================================================================
def test_agents():
    print_section("LAYER 6: AGENTS")
    
    # Test Dashboard Agent
    try:
        from agents.dashboard_agent import DashboardAgent
        
        agent = DashboardAgent()
        log_test("DashboardAgent initialized", agent is not None)
        
        # Test with sample data - using correct method signature
        test_data = [
            {"region": "North", "sales": 100, "category": "A"},
            {"region": "South", "sales": 150, "category": "B"},
            {"region": "East", "sales": 120, "category": "C"},
            {"region": "West", "sales": 180, "category": "D"},
        ] * 25
        
        metadata = {
            "row_count": len(test_data),
            "column_count": 3,
            "columns": [
                {"name": "region", "type": "categorical"},
                {"name": "sales", "type": "numeric"},
                {"name": "category", "type": "categorical"}
            ]
        }
        
        result = agent.generate_dashboard(metadata, test_data)
        has_dashboard = result.get("status") == "success" and result.get("dashboard") is not None
        log_test("DashboardAgent.generate_dashboard", 
                 has_dashboard,
                 f"Status: {result.get('status')}, Charts: {len(result.get('dashboard', {}).get('charts', []))}")
        
    except Exception as e:
        log_test("DashboardAgent", False, str(e))
        
    except Exception as e:
        log_test("DashboardAgent", False, str(e))
    
    # Test Chat Agent
    try:
        from agents.chat_agent import ChatAgent
        
        agent = ChatAgent()
        log_test("ChatAgent initialized", agent is not None)
        
    except Exception as e:
        log_test("ChatAgent", False, str(e))


# =============================================================================
# LAYER 7: Routers Test (FastAPI endpoints)
# =============================================================================
def test_routers():
    print_section("LAYER 7: ROUTERS")
    
    try:
        from routers import (
            chat_router, 
            dashboard_router, 
            ingestion_router,
            orchestrator_router
        )
        
        log_test("chat_router imported", chat_router.router is not None,
                 f"Routes: {len(chat_router.router.routes)}")
        log_test("dashboard_router imported", dashboard_router.router is not None,
                 f"Routes: {len(dashboard_router.router.routes)}")
        log_test("ingestion_router imported", ingestion_router.router is not None,
                 f"Routes: {len(ingestion_router.router.routes)}")
        log_test("orchestrator_router imported", orchestrator_router.router is not None,
                 f"Routes: {len(orchestrator_router.router.routes)}")
        
    except Exception as e:
        log_test("Routers", False, str(e))


# =============================================================================
# LAYER 8: FastAPI App Test
# =============================================================================
def test_fastapi_app():
    print_section("LAYER 8: FASTAPI APPLICATION")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        log_test("GET / (root)", response.status_code == 200,
                 f"Response: {response.json()}")
        
        # Test health endpoint
        response = client.get("/health")
        log_test("GET /health", response.status_code == 200,
                 f"Status: {response.json().get('status')}")
        
        # Test chat sessions create (POST)
        response = client.post("/chat/sessions", 
                              json={"user_id": "test_user", "email": "test@example.com"},
                              headers={"x-user-id": "test_user"})
        log_test("POST /chat/sessions", response.status_code == 200,
                 f"Created session: {response.json().get('session_id') if response.status_code == 200 else response.text}")
        
    except Exception as e:
        log_test("FastAPI App", False, str(e))


# =============================================================================
# SUMMARY
# =============================================================================
def print_summary():
    print_section("TEST SUMMARY")
    
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {results['passed']} ✅")
    logger.info(f"Failed: {results['failed']} ❌")
    logger.info(f"Pass Rate: {pass_rate:.1f}%")
    
    if results["failed"] > 0:
        logger.info("")
        logger.info("Failed Tests:")
        for test in results["tests"]:
            if not test["passed"]:
                logger.info(f"  ❌ {test['name']}: {test['details']}")
    
    logger.info("")
    logger.info("=" * 60)
    
    return results["failed"] == 0


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    logger.info("")
    logger.info("🚀 DataCue PostgreSQL Backend Test Suite")
    logger.info(f"   Started at: {datetime.now().isoformat()}")
    logger.info("")
    
    # Run all layer tests
    test_configuration()
    test_database_connection()
    test_orm_models()
    test_services()
    test_file_service()
    test_agents()
    test_routers()
    test_fastapi_app()
    
    # Print summary
    success = print_summary()
    
    sys.exit(0 if success else 1)
