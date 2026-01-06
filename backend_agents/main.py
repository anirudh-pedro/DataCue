"""
DataCue Backend - Phase 1 & 2: CSV Upload, Schema Extraction & Dashboard Generation (All-in-One)
Complete implementation in a single file
"""

import os
import re
import uuid
import json
import smtplib
import asyncio
import functools
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import Dict, List, Any, Tuple, Generator, Optional
from email.mime.text import MIMEText
from email.utils import formatdate
from pydantic import BaseModel

from fastapi import FastAPI, APIRouter, UploadFile, File, Depends, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Index, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

load_dotenv()

# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

def get_rate_limit_key(request: Request) -> str:
    """
    Rate limit key resolver:
    - Authenticated users: Firebase uid from header
    - Unauthenticated: Client IP
    """
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
        try:
            # Decode token to get uid (lightweight verification)
            decoded = firebase_auth.verify_id_token(token)
            return f"user:{decoded['uid']}"
        except:
            pass  # Fall back to IP
    
    # Fallback to IP-based limiting
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[],  # No global limits, applied per-endpoint
    storage_uri="memory://",  # In-memory store (MVP)
)


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/datacue_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Dataset(Base):
    """Stores dataset metadata (schema only, no raw data)"""
    __tablename__ = "datasets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_name = Column(String(255), nullable=False)
    owner_uid = Column(String(255), nullable=False, index=True)  # Firebase UID - NEVER trust client
    session_id = Column(String(36), nullable=False, index=True)
    
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    columns = Column(JSON, nullable=False)  # Schema array
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_datasets_owner_uid', 'owner_uid'),
        Index('idx_datasets_session_id', 'session_id'),
        Index('idx_datasets_created_at', 'created_at'),
    )


class DatasetRow(Base):
    """Stores actual CSV rows in PostgreSQL"""
    __tablename__ = "dataset_rows"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Entire row as JSON
    row_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_datasetrows_dataset_id', 'dataset_id'),
        Index('idx_datasetrows_session_id', 'session_id'),
        Index('idx_datasetrows_row_number', 'dataset_id', 'row_number'),
    )


class ChatSession(Base):
    """Stores chat session metadata"""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True)
    owner_uid = Column(String(255), nullable=False, index=True)  # Firebase UID
    dataset_id = Column(String(36), nullable=True)
    title = Column(String(500), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_chatsessions_owner_uid', 'owner_uid'),
        Index('idx_chatsessions_created_at', 'created_at'),
    )


class ChatMessage(Base):
    """Stores individual chat messages"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    chart = Column(JSON, nullable=True)  # Chart data if present
    message_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed to avoid SQLAlchemy conflict)
    timestamp = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_chatmessages_session_id', 'session_id'),
        Index('idx_chatmessages_created_at', 'created_at'),
    )


# ============================================================================
# LLM TIMEOUT & RETRY UTILITIES
# ============================================================================

class LLMTimeoutError(Exception):
    """Raised when LLM call exceeds timeout"""
    pass


class LLMRetryableError(Exception):
    """Raised when LLM call fails with retryable error (5xx, timeout)"""
    pass


def timeout_wrapper(timeout_seconds: int = 20):
    """
    Decorator to add timeout to async or sync LLM calls.
    
    Args:
        timeout_seconds: Maximum time to wait (default 20s)
    
    Raises:
        LLMTimeoutError: If call exceeds timeout
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise LLMTimeoutError(f"LLM call timed out after {timeout_seconds}s")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.to_thread(func, *args, **kwargs),
                            timeout=timeout_seconds
                        )
                    )
                except asyncio.TimeoutError:
                    raise LLMTimeoutError(f"LLM call timed out after {timeout_seconds}s")
                finally:
                    loop.close()
            else:
                # Already in an async context, just call the function directly
                # (timeout will be handled at a higher level)
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def retry_on_transient_errors(max_retries: int = 1, backoff_seconds: float = 1.0):
    """
    Decorator to retry LLM calls on transient failures.
    
    Args:
        max_retries: Maximum retry attempts (default 1)
        backoff_seconds: Initial backoff delay (default 1s)
    
    Retries on:
        - LLMTimeoutError
        - Exceptions with 5xx status codes
        - Connection errors
    
    Does NOT retry on:
        - 4xx client errors (invalid request)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except LLMTimeoutError as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_seconds * (2 ** attempt)
                        print(f"⚠️ LLM timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        asyncio.run(asyncio.sleep(wait_time))
                        continue
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Check for retryable errors (5xx, connection issues)
                    is_retryable = (
                        '500' in error_msg or '502' in error_msg or '503' in error_msg or '504' in error_msg or
                        'timeout' in error_msg or 'connection' in error_msg or 'network' in error_msg
                    )
                    
                    # Don't retry on client errors (4xx)
                    is_client_error = any(code in error_msg for code in ['400', '401', '403', '404', '429'])
                    
                    if is_retryable and not is_client_error and attempt < max_retries:
                        last_exception = e
                        wait_time = backoff_seconds * (2 ** attempt)
                        print(f"⚠️ Transient LLM error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        asyncio.run(asyncio.sleep(wait_time))
                        continue
                    
                    # Non-retryable error, raise immediately
                    raise
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    
    return decorator


# ============================================================================
# FIREBASE AUTHENTICATION
# ============================================================================

# Initialize Firebase Admin SDK
try:
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    # Option 1: Use service account JSON file (easiest for development)
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if service_account_path and os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        print("✓ Firebase Admin initialized from JSON file")
    
    # Option 2: Use environment variables (better for production)
    elif firebase_project_id and os.getenv("FIREBASE_PRIVATE_KEY"):
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": firebase_project_id,
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        })
        firebase_admin.initialize_app(cred)
        print("✓ Firebase Admin initialized from environment variables")
    else:
        print("⚠️ Firebase Admin not configured - auth will be disabled")
        print("   Download service account JSON from Firebase Console or set environment variables")
except Exception as e:
    print(f"⚠️ Firebase Admin init failed (auth will be disabled): {e}")


async def get_current_user(authorization: str = Header(None)) -> Optional[str]:
    """
    Verify Firebase ID token and return user ID.
    Returns None if auth fails (for backward compatibility during migration).
    """
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "").strip()
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token.get("uid")
    except Exception as e:
        print(f"⚠️ Auth verification failed: {e}")
        return None


# Optional: Strict auth that raises error
async def require_auth(authorization: str = Header(None)) -> str:
    """Require valid Firebase token, raise 401 if missing/invalid"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        token = authorization.replace("Bearer ", "").strip()
        decoded_token = firebase_auth.verify_id_token(token)
        user_id = decoded_token.get("uid")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# Authorization Helper - Enforce Ownership
def check_dataset_ownership(dataset_id: str, uid: str, db: Session) -> Dataset:
    """
    Verify dataset belongs to authenticated user.
    Returns dataset if authorized, raises 403 if not, 404 if missing.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.owner_uid != uid:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: You don't own this dataset"
        )
    
    return dataset


def check_session_ownership(session_id: str, uid: str, db: Session) -> ChatSession:
    """
    Verify chat session belongs to authenticated user.
    Returns session if authorized, raises 403 if not, 404 if missing.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.owner_uid != uid:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: You don't own this session"
        )
    
    return session


# ============================================================================
# CSV PARSER WITH TYPE INFERENCE
# ============================================================================

def normalize_column_name(col: str) -> str:
    """
    Normalize column name to snake_case
    Examples: "Customer ID" -> "customer_id", "PurchaseDate" -> "purchase_date"
    Special handling for ID patterns to avoid "customer_i_d" bug
    """
    # First, handle common ID patterns BEFORE snake_case conversion
    # This prevents "CustomerID" -> "customer_i_d" bug
    col = re.sub(r'ID\b', 'Id', col)  # CustomerID -> CustomerId
    col = re.sub(r'Id\b', 'Id', col)  # Normalize all Id patterns
    
    # Remove special chars
    col = re.sub(r'[^\w\s]', '', col)
    
    # Spaces to underscores
    col = col.replace(' ', '_')
    
    # camelCase to snake_case
    col = re.sub(r'(?<!^)(?=[A-Z])', '_', col)
    
    # Lowercase everything
    col = col.lower()
    
    # Remove consecutive underscores
    col = re.sub(r'_+', '_', col)
    
    # Strip leading/trailing underscores
    col = col.strip('_')
    
    return col


def infer_column_type(series: pd.Series) -> str:
    """
    Infer data type: numeric, categorical, datetime, or text
    Rules:
    - numeric: int, float
    - datetime: dates, timestamps
    - categorical: low cardinality strings (< 50% unique values)
    - text: high cardinality strings (>= 50% unique values)
    """
    # Check for datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    
    if series.dtype == 'object':
        try:
            pd.to_datetime(series.dropna().head(100))
            return "datetime"
        except:
            pass
    
    # Check for numeric
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    
    if series.dtype == 'object':
        try:
            pd.to_numeric(series.dropna().head(100))
            return "numeric"
        except:
            pass
    
    # Check cardinality for categorical vs text
    if series.dtype == 'object' or series.dtype.name == 'category':
        non_null = series.dropna()
        if len(non_null) == 0:
            return "text"
        
        unique_ratio = len(non_null.unique()) / len(non_null)
        return "categorical" if unique_ratio < 0.5 else "text"
    
    return "text"


def parse_csv(file_content: bytes) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Parse CSV file and extract schema metadata
    Returns: (DataFrame with normalized columns, schema metadata)
    """
    # Read CSV
    try:
        df = pd.read_csv(StringIO(file_content.decode('utf-8')))
    except UnicodeDecodeError:
        df = pd.read_csv(StringIO(file_content.decode('latin-1')))
    
    # Normalize column names
    normalized_columns = [normalize_column_name(col) for col in df.columns]
    
    # Handle duplicate column names
    seen = {}
    final_columns = []
    for col in normalized_columns:
        if col in seen:
            seen[col] += 1
            final_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            final_columns.append(col)
    df.columns = final_columns
    
    # Infer column types
    columns_schema = []
    for col in df.columns:
        col_type = infer_column_type(df[col])
        columns_schema.append({"name": col, "type": col_type})
    
    # Build metadata
    metadata = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns_schema
    }
    
    return df, metadata


def dataframe_to_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame to list of row dictionaries"""
    df = df.where(pd.notna(df), None)  # Replace NaN with None
    return df.to_dict(orient='records')


# ============================================================================
# INGESTION SERVICE
# ============================================================================

class IngestionService:
    """Service for handling CSV uploads and storage"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def upload_csv(
        self,
        file_content: bytes,
        filename: str,
        owner_uid: str,  # Required - Firebase UID or 'anonymous'
        session_id: str = None
    ) -> Dict[str, Any]:
        """Upload CSV file and store in PostgreSQL with ownership"""
        # Generate IDs
        dataset_id = str(uuid.uuid4())
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Parse CSV and extract schema
        df, metadata = parse_csv(file_content)
        
        # Extract dataset name from filename
        dataset_name = filename.rsplit('.', 1)[0].replace(' ', '_').lower()
        
        # Create Dataset record (metadata only) with owner_uid
        dataset = Dataset(
            id=dataset_id,
            dataset_name=dataset_name,
            owner_uid=owner_uid,  # Backend-enforced ownership
            session_id=session_id,
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            columns=metadata["columns"]
        )
        self.db.add(dataset)
        
        # Convert DataFrame to rows
        rows = dataframe_to_rows(df)
        
        # Store each row in PostgreSQL
        dataset_rows = []
        for idx, row_data in enumerate(rows, start=1):
            dataset_row = DatasetRow(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                session_id=session_id,
                data=row_data,
                row_number=idx
            )
            dataset_rows.append(dataset_row)
        
        # Bulk insert
        self.db.bulk_save_objects(dataset_rows)
        self.db.commit()
        
        # Return schema metadata (LLM-ready format)
        return {
            "dataset_id": dataset_id,
            "session_id": session_id,
            "dataset_name": dataset_name,
            "row_count": metadata["row_count"],
            "column_count": metadata["column_count"],
            "columns": metadata["columns"]
        }
    
    def get_schema(self, dataset_id: str) -> Dict[str, Any]:
        """Retrieve schema metadata for a dataset"""
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        return {
            "dataset_id": str(dataset.id),
            "session_id": dataset.session_id,
            "dataset_name": dataset.dataset_name,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "columns": dataset.columns
        }
    
    def get_schema_by_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve schema metadata by session ID"""
        dataset = self.db.query(Dataset).filter(
            Dataset.session_id == session_id
        ).order_by(Dataset.created_at.desc()).first()
        
        if not dataset:
            raise ValueError(f"No dataset found for session {session_id}")
        
        return {
            "dataset_id": str(dataset.id),
            "session_id": dataset.session_id,
            "dataset_name": dataset.dataset_name,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "columns": dataset.columns
        }


# ============================================================================
# FASTAPI ROUTER
# ============================================================================

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    session_id: str = Query(None, description="Optional session ID"),
    uid: str = Depends(require_auth),  # Require authentication
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload CSV file - Returns schema metadata only (no raw data sent to LLM)
    
    Authentication: Required (401 if not authenticated)
    Authorization: Owner can only access their own datasets
    
    Response format:
    {
      "dataset_id": "abc-123",
      "session_id": "xyz-789",
      "dataset_name": "sales_data",
      "row_count": 100000,
      "columns": [...]
    }
    """
    if not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # uid is guaranteed to be present (require_auth enforces it)
    owner_uid = uid
    
    try:
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        service = IngestionService(db)
        result = service.upload_csv(
            file_content=file_content,
            filename=file.filename,
            owner_uid=owner_uid,  # Backend-enforced, never trust client
            session_id=session_id
        )

        # Ensure a ChatSession exists for this upload (upsert)
        used_session_id = result.get("session_id") or session_id
        if used_session_id:
            session = db.query(ChatSession).filter(ChatSession.id == used_session_id).first()
            if session:
                if session.owner_uid != owner_uid:
                    raise HTTPException(status_code=403, detail="Access denied: You don't own this session")
                session.dataset_id = result["dataset_id"]
                session.updated_at = datetime.utcnow()
            else:
                session = ChatSession(
                    id=used_session_id,
                    owner_uid=owner_uid,
                    dataset_id=result["dataset_id"],
                    title="New Chat",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(session)
            db.commit()
        
        return {
            "success": True,
            "message": "CSV uploaded successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/schema/{dataset_id}")
async def get_schema(dataset_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get schema metadata for a dataset"""
    try:
        service = IngestionService(db)
        schema = service.get_schema(dataset_id)
        return {"success": True, "data": schema}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")


@router.get("/schema/session/{session_id}")
async def get_schema_by_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get schema metadata by session ID"""
    try:
        service = IngestionService(db)
        schema = service.get_schema_by_session(session_id)
        return {"success": True, "data": schema}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schema: {str(e)}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="DataCue API - Phase 1",
    description="CSV Upload & Schema Extraction",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)


# ============================================================================
# LLM HELPER FUNCTIONS (Groq + Gemini Fallback)
# ============================================================================

def call_llm_with_fallback(prompt: str, system_message: str = "You are a helpful assistant.", temperature: float = 0.7, max_tokens: int = 1000, response_format: str = "text") -> str:
    """
    Call LLM with Groq primary, Gemini fallback
    
    Args:
        prompt: User prompt
        system_message: System message
        temperature: Temperature setting
        max_tokens: Max tokens
        response_format: "text" or "json"
    
    Returns:
        LLM response as string
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not groq_api_key and not gemini_api_key:
        raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY configured")

    # Try Groq first
    if groq_api_key:
        try:
            groq_client = Groq(api_key=groq_api_key)
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]

            if response_format == "json":
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
            else:
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            return completion.choices[0].message.content
        except Exception as groq_error:
            print(f"⚠️ Groq failed: {str(groq_error)}. Trying Gemini...")
            # Continue to Gemini fallback
    
    # Fallback to Gemini
    if gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
            # Use gemini-1.5-flash which is available in the stable API
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Combine system message and prompt
            full_prompt = f"{system_message}\n\n{prompt}"
            
            if response_format == "json":
                full_prompt += "\n\nReturn ONLY valid JSON, no markdown code blocks."
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            result_text = response.text
            # Strip markdown code blocks if present
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                result_text = "\n".join(lines)
            
            print(f"✅ Gemini fallback succeeded")
            return result_text
        except Exception as gemini_error:
            print(f"❌ Gemini also failed: {str(gemini_error)}")
            raise Exception(f"Both LLM providers failed. Groq: {groq_error if 'groq_error' in locals() else 'Not attempted'}. Gemini: {str(gemini_error)}")
    
    raise Exception("No LLM provider available")


# ============================================================================
# EMAIL / OTP SERVICE
# ============================================================================

class EmailSendRequest(BaseModel):
    email: str


class EmailVerifyRequest(BaseModel):
    email: str
    otp: str


class EmailService:
    """Simple OTP email service using SMTP (Gmail app password recommended)."""

    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_APP_PASSWORD")
        self.otp_expiry_seconds = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))
        self.max_otp_attempts = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))
        self.rate_limit_window_ms = int(os.getenv("OTP_RATE_WINDOW_MS", "60000"))
        self.max_requests_per_window = int(os.getenv("OTP_MAX_REQUESTS_PER_WINDOW", "5"))

        if not self.email_user or not self.email_password:
            print("⚠️  EMAIL_USER or EMAIL_APP_PASSWORD not configured. OTP emails will fail.")

        # In-memory stores
        self.otp_store: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_store: Dict[str, Dict[str, Any]] = {}

    def _generate_otp(self) -> str:
        return str(uuid.uuid4().int)[-6:]

    def _check_rate_limit(self, email: str) -> Tuple[bool, Optional[int]]:
        now = datetime.utcnow().timestamp() * 1000
        record = self.rate_limit_store.get(email)
        if not record or now > record["reset_at"]:
            self.rate_limit_store[email] = {"count": 1, "reset_at": now + self.rate_limit_window_ms}
            return True, None
        if record["count"] >= self.max_requests_per_window:
            retry_in = int((record["reset_at"] - now) / 1000)
            return False, max(retry_in, 1)
        record["count"] += 1
        return True, None

    def _save_otp(self, email: str, otp: str) -> None:
        expires_at = datetime.utcnow().timestamp() + self.otp_expiry_seconds
        self.otp_store[email] = {"otp": otp, "expires_at": expires_at, "attempts": 0}

    def _verify_otp(self, email: str, otp: str) -> Tuple[bool, str]:
        record = self.otp_store.get(email)
        if not record:
            return False, "No OTP found for this email"
        now = datetime.utcnow().timestamp()
        if now > record["expires_at"]:
            self.otp_store.pop(email, None)
            return False, "OTP has expired"
        if record["attempts"] >= self.max_otp_attempts:
            self.otp_store.pop(email, None)
            return False, "Too many failed attempts. Please request a new OTP"
        if record["otp"] != otp:
            record["attempts"] += 1
            remaining = max(self.max_otp_attempts - record["attempts"], 0)
            return False, f"Invalid OTP. {remaining} attempts remaining"
        # Success
        self.otp_store.pop(email, None)
        return True, "OTP verified successfully"

    def _send_email(self, to_email: str, otp: str) -> None:
        if not self.email_user or not self.email_password:
            raise HTTPException(status_code=500, detail="Email credentials not configured")

        subject = "Your DataCue verification code"
        body = f"""
        <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;\">
          <h2 style=\"color: #333;\">DataCue Email Verification</h2>
          <p>Your one-time verification code is:</p>
          <p style=\"font-size: 2rem; font-weight: bold; letter-spacing: 0.3rem; color: #0066cc; text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;\">
            {otp}
          </p>
          <p style=\"color: #666;\">This code will expire in {int(self.otp_expiry_seconds/60)} minutes.</p>
          <p style=\"color: #999; font-size: 0.9rem;\">If you didn't request this code, please ignore this email.</p>
        </div>
        """

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = self.email_user
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_user, [to_email], msg.as_string())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send OTP email: {str(e)}")

    def send_otp(self, request: EmailSendRequest) -> Dict[str, Any]:
        allowed, retry_in = self._check_rate_limit(request.email)
        if not allowed:
            raise HTTPException(status_code=429, detail=f"Too many requests. Try again in {retry_in} seconds")

        otp = self._generate_otp()
        self._save_otp(request.email, otp)
        self._send_email(request.email, otp)
        return {"success": True, "message": "OTP sent successfully"}

    def verify_otp(self, request: EmailVerifyRequest) -> Dict[str, Any]:
        valid, message = self._verify_otp(request.email, request.otp)
        if not valid:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}


email_router = APIRouter(prefix="/email", tags=["Email / OTP"])
email_service = EmailService()


@email_router.post("/send-otp")
def send_otp_endpoint(payload: EmailSendRequest):
    return email_service.send_otp(payload)


@email_router.post("/verify-otp")
def verify_otp_endpoint(payload: EmailVerifyRequest):
    return email_service.verify_otp(payload)


@email_router.get("/health")
def email_health():
    return {
        "status": "ok",
        "activeOtps": len(email_service.otp_store),
        "rateLimited": len(email_service.rate_limit_store),
        "uptime_seconds": int(datetime.utcnow().timestamp())
    }


# ============================================================================
# PHASE 2: DASHBOARD GENERATION (LLM + SQL EXECUTION)
# ============================================================================

class ChartSpec(BaseModel):
    """Chart specification from Phase 1 LLM"""
    chart_id: str
    title: str
    chart_type: str
    description: str
    dimensions: List[str]
    metrics: List[str]
    priority: Optional[int] = 1


class DashboardRequest(BaseModel):
    """Request for dashboard generation"""
    dataset_id: str
    session_id: str
    dashboard_title: Optional[str] = "Analytics Dashboard"
    charts: List[ChartSpec]


class DashboardService:
    """Phase 2: Generate dashboard by executing SQL queries for each chart"""
    
    def __init__(self, db: Session):
        self.db = db
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
        self.groq_client = Groq(api_key=groq_api_key)
    
    def generate_sql_query(self, schema: Dict, chart: ChartSpec, dataset_id: str) -> str:
        """Phase 2A: Generate SQL query using LLM (Groq + Gemini fallback)"""
        
        prompt = f"""You are generating a READ-ONLY PostgreSQL query.

Dataset schema:
{json.dumps(schema['columns'], indent=2)}

Table name: dataset_rows
The data is stored as JSON in the 'data' column.
Use: data->>'column_name' to access columns

Chart specification:
- Title: {chart.title}
- Chart type: {chart.chart_type}
- Dimensions: {', '.join(chart.dimensions)}
- Metrics: {', '.join(chart.metrics)}
- Description: {chart.description}

You are allowed to generate the following chart types when appropriate:
- bar, stacked_bar
- line, area
- pie
- scatter
- histogram
- box
- heatmap

Chart type guidelines:
- Use scatter when comparing two numeric columns
- Use histogram for numeric distributions
- Use box plots to show spread and outliers
- Use heatmaps for categorical × categorical aggregations
- Prefer diversity: avoid repeating the same chart type unless necessary

Rules:
- Output ONLY valid PostgreSQL SQL (no markdown, no explanations)
- SELECT statements only
- Use data->>'column_name' syntax to access JSON fields
- Use WHERE dataset_id = '{dataset_id}'
- Use GROUP BY where required
- Use correct aggregation functions (AVG, SUM, COUNT, etc.)
- Cast numeric columns: CAST(data->>'column' AS NUMERIC)
- Cast datetime columns: CAST(data->>'column' AS DATE)
- Do not hallucinate column names - use only columns from schema
- Return results with clear column aliases

Example:
SELECT 
  data->>'region' as region,
  AVG(CAST(data->>'revenue' AS NUMERIC)) as avg_revenue
FROM dataset_rows
WHERE dataset_id = '{dataset_id}'
GROUP BY data->>'region'
ORDER BY avg_revenue DESC;
"""
        
        try:
            response = call_llm_with_fallback(
                prompt=prompt,
                system_message="You are a PostgreSQL expert. Return only SQL queries without markdown or explanations.",
                temperature=0.3,
                max_tokens=500,
                response_format="text"
            )
            
            sql_query = response.strip()
            
            # Clean up markdown code blocks if present
            sql_query = re.sub(r'```sql\n?', '', sql_query)
            sql_query = re.sub(r'```\n?', '', sql_query)
            sql_query = sql_query.strip()
            
            return sql_query
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM query generation failed: {str(e)}")
    
    def validate_sql(self, sql: str) -> bool:
        """Phase 2B: Validate SQL is SELECT-only"""
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False

        # Must target our dataset table
        if 'FROM DATASET_ROWS' not in sql_upper:
            return False
        
        # Must not contain dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        return True
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Phase 2B: Execute SQL and return structured data"""
        
        if not self.validate_sql(sql):
            raise HTTPException(status_code=400, detail="Invalid SQL query - only SELECT queries allowed")
        
        try:
            result = self.db.execute(text(sql))
            rows = result.fetchall()
            
            if not rows:
                return {"labels": [], "values": []}
            
            # Get column names
            columns = list(result.keys())
            
            # Structure data based on number of columns
            if len(columns) == 1:
                # Single value (e.g., COUNT)
                value = rows[0][0]
                # Don't cast datetime to float
                if isinstance(value, (int, float)):
                    return {"value": value}
                else:
                    return {"value": str(value) if value is not None else 0}
            
            elif len(columns) == 2:
                # Label + Value (e.g., bar chart, pie chart)
                labels = [str(row[0]) if row[0] is not None else 'Unknown' for row in rows]
                values = []
                for row in rows:
                    val = row[1]
                    if val is None:
                        values.append(0)
                    elif isinstance(val, (int, float)):
                        values.append(float(val))
                    elif isinstance(val, datetime):
                        # Keep datetime as string, don't cast to float
                        values.append(str(val))
                    else:
                        # Try to convert to float, fallback to 0
                        try:
                            values.append(float(val))
                        except (ValueError, TypeError):
                            values.append(0)
                return {"labels": labels, "values": values}
            
            else:
                # Multiple series (e.g., line chart with multiple lines)
                # First column is label, rest are series
                labels = [str(row[0]) if row[0] is not None else 'Unknown' for row in rows]
                series = {}
                for i, col in enumerate(columns[1:], 1):
                    series_values = []
                    for row in rows:
                        val = row[i]
                        if val is None:
                            series_values.append(0)
                        elif isinstance(val, (int, float)):
                            series_values.append(float(val))
                        elif isinstance(val, datetime):
                            # Keep datetime as string
                            series_values.append(str(val))
                        else:
                            try:
                                series_values.append(float(val))
                            except (ValueError, TypeError):
                                series_values.append(0)
                    series[col] = series_values
                return {"labels": labels, "series": series}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
    
    def get_column_types(self, schema: Dict, dimensions: List[str]) -> Dict[str, str]:
        """Get data types for dimensions from schema"""
        column_map = {col['name']: col['type'] for col in schema['columns']}
        return {dim: column_map.get(dim, 'unknown') for dim in dimensions}
    
    def extract_metric_columns(self, metrics: List[str]) -> List[str]:
        """Extract column names from metric expressions like AVG(revenue), SUM(units_sold)"""
        metric_cols = []
        for metric in metrics:
            # Extract column name from aggregation: AVG(column) -> column
            match = re.search(r'\(([^)]+)\)', metric)
            if match:
                metric_cols.append(match.group(1))
            else:
                metric_cols.append(metric)
        return metric_cols
    
    def is_aggregated_metric(self, metric: str) -> bool:
        """Check if metric is an aggregation (COUNT, SUM, AVG, MIN, MAX) which always returns numeric"""
        metric_upper = metric.upper().strip()
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'MEDIAN', 'STDDEV', 'VARIANCE']
        for agg in agg_functions:
            if metric_upper.startswith(agg + '(') or metric_upper == agg:
                return True
        return False
    
    def validate_and_correct_chart_type(self, chart: ChartSpec, schema: Dict) -> tuple[str, Optional[str]]:
        """
        Validate chart type compatibility and auto-correct if needed (Power BI / Tableau style)
        
        KEY PRINCIPLE:
        - Metrics (aggregations) MUST be numeric
        - Dimensions can be categorical, numeric, or datetime depending on chart type
        
        Returns: (corrected_chart_type, reason_if_skipped)
        """
        
        # Get dimension types
        dim_types = self.get_column_types(schema, chart.dimensions)
        categorical_dims = [d for d, t in dim_types.items() if t in ['categorical', 'text']]
        numeric_dims = [d for d, t in dim_types.items() if t == 'numeric']
        datetime_dims = [d for d, t in dim_types.items() if t == 'datetime']
        
        chart_type = chart.chart_type.lower()
        
        # RULE 1: Validate metrics are numeric (only if metrics are specified)
        # NOTE: Aggregated metrics (COUNT, SUM, AVG, MIN, MAX) always produce numeric results
        if len(chart.metrics) > 0:
            # Check if metrics are aggregations - these are always valid regardless of underlying type
            non_agg_metrics = [m for m in chart.metrics if not self.is_aggregated_metric(m)]
            
            if non_agg_metrics:
                # For non-aggregated metrics, validate they are numeric
                metric_cols = self.extract_metric_columns(non_agg_metrics)
                if metric_cols:
                    metric_types = self.get_column_types(schema, metric_cols)
                    non_numeric_metrics = [m for m, t in metric_types.items() if t not in ['numeric', 'unknown']]
                    
                    if non_numeric_metrics:
                        # Only fail if we have explicitly non-numeric metrics (not unknown)
                        explicit_non_numeric = [m for m in non_numeric_metrics if metric_types.get(m) != 'unknown']
                        if explicit_non_numeric:
                            return chart_type, f"Non-aggregated metrics must be numeric (non-numeric: {explicit_non_numeric})"
        
        # RULE 2: Auto-correction logic (Power BI / Tableau style)
        
        # Bar with 2+ categorical dimensions → heatmap (better for cross-tabulation)
        if chart_type == "bar" and len(categorical_dims) >= 2:
            print(f"   🔧 Auto-correcting: bar → heatmap (2+ categorical dimensions for cross-tab)")
            return "heatmap", None
        
        # Scatter with categorical dimensions → bar chart
        if chart_type == "scatter":
            if len(categorical_dims) > 0:
                print(f"   🔧 Auto-correcting: scatter → bar (has categorical dimension)")
                return "bar", None
            if len(numeric_dims) < 2:
                print(f"   🔧 Auto-correcting: scatter → bar (needs 2 numeric dimensions)")
                return "bar", None
        
        # Area with 2 categorical dimensions → heatmap
        if chart_type == "area" and len(categorical_dims) == 2:
            print(f"   🔧 Auto-correcting: area → heatmap (2 categorical dimensions)")
            return "heatmap", None
        
        # Line/Area without time dimension → bar chart (if has categorical)
        if chart_type in ["line", "area"]:
            if len(datetime_dims) == 0 and len(categorical_dims) > 0:
                print(f"   🔧 Auto-correcting: {chart_type} → bar (no time dimension, has categorical)")
                return "bar", None
            if len(datetime_dims) == 0 and len(numeric_dims) == 0 and len(categorical_dims) == 0:
                return chart_type, f"{chart_type.title()} chart requires at least a time or numeric x-axis"
        
        # Heatmap with insufficient categorical dimensions
        if chart_type == "heatmap" and len(categorical_dims) < 2:
            if len(categorical_dims) == 1 and len(chart.metrics) > 0:
                print(f"   🔧 Auto-correcting: heatmap → bar (only 1 categorical dimension)")
                return "bar", None
            else:
                return chart_type, f"Heatmap requires 2 categorical dimensions (found {len(categorical_dims)})"
        
        # RULE 3: Final validation - these should pass after auto-correction
        
        if chart_type == "bar":
            # Bar charts accept categorical OR numeric dimensions
            if len(chart.dimensions) == 0:
                return chart_type, "Bar chart requires at least 1 dimension"
            # Bar charts work great with categorical dimensions - this is the most common use case
            return chart_type, None
        
        elif chart_type == "pie":
            # Pie charts require exactly 1 categorical dimension
            if len(categorical_dims) == 0 and len(chart.dimensions) > 0:
                # Try to use the first dimension even if it's numeric (less common but valid)
                print(f"   ⚠️  Pie chart with non-categorical dimension (unusual but allowed)")
            if len(chart.dimensions) == 0:
                return chart_type, "Pie chart requires at least 1 dimension"
            return chart_type, None
        
        elif chart_type == "heatmap":
            # Heatmap requires 2 categorical dimensions (already auto-corrected above)
            if len(categorical_dims) >= 2:
                return chart_type, None
            else:
                return chart_type, f"Heatmap requires 2 categorical dimensions (found {len(categorical_dims)})"
        
        elif chart_type == "scatter":
            # Scatter requires 2 numeric dimensions (already auto-corrected above)
            if len(numeric_dims) >= 2:
                return chart_type, None
            else:
                return chart_type, f"Scatter plot requires 2 numeric dimensions (found {len(numeric_dims)})"
        
        elif chart_type in ["line", "area"]:
            # Line/Area require time or numeric x-axis (already auto-corrected above)
            if len(datetime_dims) > 0 or len(numeric_dims) > 0:
                return chart_type, None
            else:
                return chart_type, f"{chart_type.title()} chart requires time or numeric x-axis"
        
        # Chart is valid
        return chart_type, None

    def generate_sql_queries_batch(self, schema: Dict, charts: List[ChartSpec], dataset_id: str) -> Dict[str, str]:
        """Generate SQL for all charts in a single LLM call to reduce rate limits."""

        chart_summaries = []
        for c in charts:
            chart_summaries.append({
                "chart_id": c.chart_id,
                "title": c.title,
                "chart_type": c.chart_type,
                "description": c.description,
                "dimensions": c.dimensions,
                "metrics": c.metrics,
            })

        prompt = f"""You are generating PostgreSQL SELECT queries for ALL charts in one response.

DATASET SCHEMA (columns with types):
{json.dumps(schema['columns'], indent=2)}

Table name: dataset_rows
Data stored as JSON in column 'data'
Access fields with data->>'column_name'
Use WHERE dataset_id = '{dataset_id}' in every query

Chart specifications:
{json.dumps(chart_summaries, indent=2)}

Rules:
- Output ONLY valid JSON, no markdown
- Return queries for every chart_id
- SELECT-only queries; read-only
- Use correct casts: numeric -> CAST(data->>'col' AS NUMERIC); date -> CAST(data->>'col' AS DATE)
- Use GROUP BY when aggregating dimensions
- Use ORDER BY when sorting
- Avoid hallucinating columns; only use schema columns

Return JSON in this exact shape:
{{
  "queries": [
    {{ "chart_id": "chart_1", "sql": "SELECT ..." }}
  ]
}}
"""

        try:
            response = call_llm_with_fallback(
                prompt=prompt,
                system_message="You are a PostgreSQL expert. Return only JSON with SQL queries for all charts.",
                temperature=0.3,
                max_tokens=2000,
                response_format="json"
            )

            parsed = json.loads(response)
            queries = parsed.get("queries", []) if isinstance(parsed, dict) else []

            # Build mapping chart_id -> sql
            sql_map = {}
            for item in queries:
                cid = item.get("chart_id")
                sql = item.get("sql") or item.get("sql_query")
                if cid and sql:
                    # Clean potential markdown fences
                    sql_clean = sql.replace("```sql", "").replace("```", "").strip()
                    sql_map[cid] = sql_clean

            return sql_map
        except Exception as e:
            print(f"⚠️  Batch SQL generation failed, falling back to per-chart: {str(e)}")
            return {}
    
    def generate_chart(self, schema: Dict, chart: ChartSpec, dataset_id: str, sql_overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Phase 2C: Generate single chart (SQL generation + execution)"""
        
        try:
            # Step 0: Validate and auto-correct chart type
            corrected_type, skip_reason = self.validate_and_correct_chart_type(chart, schema)
            
            if skip_reason:
                # Incompatible chart - skip gracefully
                print(f"⚠️  Chart {chart.chart_id} skipped: {skip_reason}")
                return {
                    "chart_id": chart.chart_id,
                    "title": chart.title,
                    "type": chart.chart_type,
                    "description": chart.description,
                    "data": {"labels": [], "values": []},
                    "reason": skip_reason,
                    "status": "skipped"
                }
            
            # Update chart type if corrected
            if corrected_type != chart.chart_type:
                chart.chart_type = corrected_type
            
            # Step 1: Generate SQL (prefer batch-generated if available)
            if sql_overrides and chart.chart_id in sql_overrides:
                sql_query = sql_overrides[chart.chart_id]
            else:
                sql_query = self.generate_sql_query(schema, chart, dataset_id)
            print(f"📊 Generated SQL for {chart.chart_id}:")
            print(f"   {sql_query[:100]}...")
            
            # Step 2: Execute query
            data = self.execute_query(sql_query)
            
            # Step 3: Format response
            return {
                "chart_id": chart.chart_id,
                "title": chart.title,
                "type": chart.chart_type,
                "description": chart.description,
                "data": data,
                "sql_query": sql_query,  # For debugging
                "status": "success"
            }
        
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}"
            # Add more context for debugging
            if "cast" in str(e).lower() or "type" in str(e).lower():
                error_detail = f"Type casting error: {str(e)}"
            elif "syntax" in str(e).lower():
                error_detail = f"SQL syntax error: {str(e)}"
            
            print(f"❌ Chart {chart.chart_id} failed: {error_detail}")
            print(f"   Traceback: {traceback.format_exc()[:200]}")
            
            # Return error chart but don't fail entire dashboard
            return {
                "chart_id": chart.chart_id,
                "title": chart.title,
                "chart_type": chart.chart_type,  # Ensure chart_type field exists
                "type": chart.chart_type,
                "description": chart.description,
                "data": {"labels": [], "values": []},
                "sql_query": "",
                "error": error_detail,
                "status": "failed"
            }
    
    def generate_dashboard(self, request: DashboardRequest) -> Dict[str, Any]:
        """Phase 2D: Generate complete dashboard"""
        
        # Get dataset schema
        ingestion_service = IngestionService(self.db)
        schema = ingestion_service.get_schema(request.dataset_id)
        
        if not schema:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        print(f"\n🚀 Generating dashboard with {len(request.charts)} charts...")

        # Single LLM call: generate SQL for all charts at once (reduces rate limits)
        sql_batch_map = self.generate_sql_queries_batch(schema, request.charts, request.dataset_id)
        
        # Generate all charts
        charts = []
        successful_charts = 0
        
        for i, chart_spec in enumerate(request.charts, 1):
            print(f"\n📈 Processing chart {i}/{len(request.charts)}: {chart_spec.title}")
            chart_result = self.generate_chart(schema, chart_spec, request.dataset_id, sql_overrides=sql_batch_map)
            
            # NORMALIZE: Ensure chart_type field exists (Phase 2 fix)
            if 'chart_type' not in chart_result and 'type' in chart_result:
                chart_result['chart_type'] = chart_result['type']
            elif 'chart_type' not in chart_result:
                chart_result['chart_type'] = chart_spec.chart_type
            
            charts.append(chart_result)
            
            if chart_result.get("status") == "success":
                successful_charts += 1
        
        # Count skipped and failed charts
        skipped_charts = sum(1 for c in charts if c.get("status") == "skipped")
        failed_charts = sum(1 for c in charts if c.get("status") == "failed")
        
        # Ensure minimum 6 charts rendered
        if successful_charts < 6:
            print(f"⚠️  Warning: Only {successful_charts} charts successful (minimum 6 required)")
        
        print(f"\n✓ Dashboard generated: {successful_charts}/{len(request.charts)} charts successful")
        if skipped_charts > 0:
            print(f"   {skipped_charts} charts skipped (incompatible)")
        if failed_charts > 0:
            print(f"   {failed_charts} charts failed")
        
        return {
            "dashboard_title": request.dashboard_title,
            "dataset_id": request.dataset_id,
            "session_id": request.session_id,
            "total_charts": len(charts),
            "successful_charts": successful_charts,
            "skipped_charts": skipped_charts,
            "failed_charts": failed_charts,
            "charts": charts
        }


# Phase 2 Router
dashboard_router = APIRouter()


@dashboard_router.post("/generate")
async def generate_dashboard_endpoint(
    request: DashboardRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 2: Generate dashboard from chart specifications
    
    Takes dataset_id + chart specifications from Phase 1 LLM
    For each chart:
      1. Generate SQL query using Groq LLM
      2. Execute query on PostgreSQL
      3. Format data for frontend
    
    Returns complete dashboard with all charts
    """
    service = DashboardService(db)
    dashboard = service.generate_dashboard(request)
    
    return {
        "success": True,
        "message": f"Dashboard generated with {dashboard['successful_charts']}/{dashboard['total_charts']} charts",
        "data": dashboard
    }


@dashboard_router.post("/generate-from-schema")
async def generate_dashboard_from_schema(
    dataset_id: str,
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Phase 2 Full Pipeline: Schema → LLM Chart Design → SQL Execution
    
    This endpoint combines Phase 1 output with Phase 2 execution:
    1. Get schema from dataset_id
    2. Call Groq LLM to design charts (Phase 1 LLM call)
    3. For each chart, generate SQL and execute (Phase 2)
    4. Return complete dashboard
    """
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    # Step 1: Get schema
    ingestion_service = IngestionService(db)
    schema = ingestion_service.get_schema(dataset_id)
    
    if not schema:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Step 2: Call LLM to design charts (with Groq + Gemini fallback)
    
    prompt = f"""You are a senior data analyst and BI architect.
You must only return valid JSON.

DATASET SCHEMA:
{json.dumps(schema, indent=2)}

Your task is to DESIGN a professional analytics dashboard.

Generate 10 chart specifications (minimum 6) that best visualize this data.

Return ONLY valid JSON in this format:
{{
  "dashboard_title": "Sales Analytics Dashboard",
  "charts": [
    {{
      "chart_id": "chart_1",
      "title": "Revenue by Region",
      "chart_type": "bar",
      "description": "Compare revenue across regions",
      "dimensions": ["region"],
      "metrics": ["AVG(revenue)"],
      "priority": 1
    }}
  ]
}}

Chart types you can use: bar, line, pie, scatter, area
Only use columns from the schema provided.
Generate diverse chart types covering different aspects of the data.
"""
    
    try:
        response = call_llm_with_fallback(
            prompt=prompt,
            system_message="You are a data visualization expert. Return only valid JSON.",
            temperature=0.7,
            max_tokens=2000,
            response_format="json"
        )
        
        dashboard_design = json.loads(response)
        
        # Step 3: Convert to DashboardRequest
        chart_specs = []
        for chart in dashboard_design.get("charts", []):
            chart_specs.append(ChartSpec(
                chart_id=chart.get("chart_id", f"chart_{len(chart_specs)+1}"),
                title=chart.get("title", "Untitled Chart"),
                chart_type=chart.get("chart_type", "bar"),
                description=chart.get("description", ""),
                dimensions=chart.get("dimensions", []),
                metrics=chart.get("metrics", []),
                priority=chart.get("priority", 1)
            ))
        
        request = DashboardRequest(
            dataset_id=dataset_id,
            session_id=session_id,
            dashboard_title=dashboard_design.get("dashboard_title", "Analytics Dashboard"),
            charts=chart_specs
        )
        
        # Step 4: Generate dashboard
        service = DashboardService(db)
        dashboard = service.generate_dashboard(request)
        
        return {
            "success": True,
            "message": f"Full pipeline complete: {dashboard['successful_charts']}/{dashboard['total_charts']} charts generated",
            "data": dashboard
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")


app.include_router(dashboard_router, prefix="/dashboard", tags=["Phase 2: Dashboard Generation"])


# =====================================================================
# EMAIL OTP SERVICE (from legacy email-service)
# =====================================================================

class SendOtpRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class EmailOtpService:
    """In-memory OTP service with rate limiting and expiry."""

    OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))
    MAX_OTP_ATTEMPTS = int(os.getenv("MAX_OTP_ATTEMPTS", "3"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("OTP_RATE_LIMIT_WINDOW_SECONDS", "60"))
    MAX_REQUESTS_PER_WINDOW = int(os.getenv("OTP_MAX_REQUESTS_PER_WINDOW", "5"))

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME") or os.getenv("EMAIL_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_APP_PASSWORD")
    FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL") or SMTP_USERNAME or ""
    FROM_NAME = os.getenv("SMTP_FROM_NAME", "DataCue")

    def __init__(self):
        self.otp_store: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_store: Dict[str, Dict[str, Any]] = {}

    def _generate_otp(self) -> str:
        return str(uuid.uuid4().int)[-6:]

    def _save_otp(self, email: str, otp: str) -> None:
        expires_at = datetime.utcnow().timestamp() + self.OTP_EXPIRY_SECONDS
        self.otp_store[email] = {"otp": otp, "expires_at": expires_at, "attempts": 0}

    def _verify_otp(self, email: str, otp: str) -> Tuple[bool, str]:
        record = self.otp_store.get(email)
        if not record:
            return False, "No OTP found for this email"
        now = datetime.utcnow().timestamp()
        if now > record["expires_at"]:
            self.otp_store.pop(email, None)
            return False, "OTP has expired"
        if record["attempts"] >= self.MAX_OTP_ATTEMPTS:
            self.otp_store.pop(email, None)
            return False, "Too many failed attempts. Please request a new OTP"
        if record["otp"] != otp:
            record["attempts"] += 1
            remaining = max(self.MAX_OTP_ATTEMPTS - record["attempts"], 0)
            return False, f"Invalid OTP. {remaining} attempts remaining"
        self.otp_store.pop(email, None)
        return True, "OTP verified successfully"

    def _check_rate_limit(self, email: str) -> Tuple[bool, Optional[int]]:
        now = datetime.utcnow().timestamp()
        record = self.rate_limit_store.get(email)
        if not record or now > record["reset_at"]:
            self.rate_limit_store[email] = {"count": 1, "reset_at": now + self.RATE_LIMIT_WINDOW_SECONDS}
            return True, None
        if record["count"] >= self.MAX_REQUESTS_PER_WINDOW:
            retry_in = int(record["reset_at"] - now)
            return False, max(retry_in, 0)
        record["count"] += 1
        return True, None

    def _send_email(self, to_email: str, subject: str, html_body: str) -> None:
        if not self.SMTP_USERNAME or not self.SMTP_PASSWORD:
            raise RuntimeError("SMTP credentials not configured")

        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = f"{self.FROM_NAME} <{self.FROM_EMAIL or self.SMTP_USERNAME}>"
        msg["To"] = to_email

        with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as server:
            server.starttls()
            server.login(self.SMTP_USERNAME, self.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())

    def send_otp(self, email: str) -> Dict[str, Any]:
        allowed, retry_in = self._check_rate_limit(email)
        if not allowed:
            raise HTTPException(status_code=429, detail=f"Too many requests. Please try again in {retry_in} seconds")

        otp = self._generate_otp()
        self._save_otp(email, otp)

        minutes = max(int(self.OTP_EXPIRY_SECONDS // 60), 1)
        body = f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px;'>
          <h2 style='color: #333;'>DataCue Email Verification</h2>
          <p>Your one-time verification code is:</p>
          <p style='font-size: 2rem; font-weight: bold; letter-spacing: 0.3rem; color: #0066cc; text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;'>
            {otp}
          </p>
          <p style='color: #666;'>This code will expire in {minutes} minute(s).</p>
          <p style='color: #999; font-size: 0.9rem;'>If you didn't request this code, please ignore this email.</p>
        </div>
        """

        self._send_email(
            to_email=email,
            subject="Your DataCue verification code",
            html_body=body
        )

        return {"success": True, "message": "OTP sent successfully"}

    def verify_otp(self, email: str, otp: str) -> Dict[str, Any]:
        valid, message = self._verify_otp(email, otp)
        if not valid:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}


email_router = APIRouter(prefix="/email", tags=["Email OTP"])
email_service = EmailOtpService()


@email_router.post("/send-otp")
def send_otp_endpoint(payload: SendOtpRequest):
    return email_service.send_otp(payload.email)


@email_router.post("/verify-otp")
def verify_otp_endpoint(payload: VerifyOtpRequest):
    return email_service.verify_otp(payload.email, payload.otp)


app.include_router(email_router)


# =====================================================================
# PHASE 3: CHAT WITH CSV (SQL + INSIGHT RENDERING)
# =====================================================================

class ChatRequest(BaseModel):
    """Request model for chat query"""
    dataset_id: str
    session_id: str
    question: str
    include_explanation: bool = True


class ChatResponse(BaseModel):
    """Response model for chat query"""
    question: str
    intent: str  # kpi, table, chart, text
    sql_query: str
    result_type: str  # single_value, rows, grouped_numeric
    data: Any
    explanation: Optional[str] = None
    status: str  # success, failed
    error: Optional[str] = None


class ChatService:
    """Service for handling natural language queries"""
    
    # Class-level SQL cache
    _sql_cache = {}
    
    def __init__(self, db: Session):
        self.db = db
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured")
        self.groq_client = Groq(api_key=self.groq_api_key)
    
    def _get_cache_key(self, schema: Dict[str, Any], question: str) -> str:
        """Generate cache key from schema + question"""
        schema_str = json.dumps(schema['columns'], sort_keys=True)
        return f"{schema['dataset_id']}:{hash(schema_str + question.lower())}"
    
    def generate_deterministic_sql(self, schema: Dict[str, Any], question: str) -> Optional[str]:
        """
        Rule-based SQL generator for common query patterns
        Intent will be determined from result shape, not hardcoded here.
        Returns sql_query or None if pattern not matched
        """
        q = question.lower().strip()
        dataset_id = schema['dataset_id']
        columns = {col['name']: col['type'] for col in schema['columns']}
        
        # Get numeric and categorical columns
        numeric_cols = [name for name, typ in columns.items() if typ == 'numeric']
        categorical_cols = [name for name, typ in columns.items() if typ == 'categorical']
        datetime_cols = [name for name, typ in columns.items() if typ == 'datetime']

        # PATTERN 0: List/show N raw rows
        # Examples: "list 10 rows", "show 5 rows", "display 20 rows"
        if any(word in q for word in ['list', 'show', 'display']) and (' row' in f" {q} " or ' rows' in f" {q} "):
            import re
            limit = 10
            numbers = re.findall(r'\d+', q)
            if numbers:
                try:
                    limit = max(1, min(int(numbers[0]), 100))
                except Exception:
                    limit = 10
            sql = (
                f"SELECT data FROM dataset_rows "
                f"WHERE dataset_id = '{dataset_id}' "
                f"ORDER BY row_number ASC "
                f"LIMIT {limit}"
            )
            return sql

        # PATTERN 0: "Which <date> has highest/lowest <metric>" (single-row answer)
        # Examples: "highest revenue in which date", "tell the date with highest revenue",
        #           "which month has the lowest sales"
        if datetime_cols and numeric_cols and any(word in q for word in ['which', 'what', 'tell']) and any(
            word in q for word in ['highest', 'max', 'maximum', 'lowest', 'min', 'minimum']
        ) and any(word in q for word in ['date', 'day', 'month', 'year', 'time']):
            # Pick a datetime column (prefer one whose name appears in the question)
            date_col = None
            for c in datetime_cols:
                if c.replace('_', ' ') in q or 'date' in c:
                    date_col = c
                    break
            if not date_col:
                date_col = datetime_cols[0]

            # Pick a numeric metric column (prefer one whose name appears in the question)
            metric_col = None
            for c in numeric_cols:
                if c.replace('_', ' ') in q:
                    metric_col = c
                    break
            if not metric_col:
                # Common fallbacks
                for candidate in ['revenue', 'sales', 'amount', 'total', 'profit']:
                    for c in numeric_cols:
                        if candidate in c:
                            metric_col = c
                            break
                    if metric_col:
                        break
            if not metric_col:
                metric_col = numeric_cols[0]

            direction = 'DESC' if any(word in q for word in ['highest', 'max', 'maximum']) else 'ASC'
            agg_name = f"total_{metric_col}"
            sql = (
                f"SELECT CAST(data->>'{date_col}' AS DATE) AS {date_col}, "
                f"SUM(CAST(data->>'{metric_col}' AS NUMERIC)) AS {agg_name} "
                f"FROM dataset_rows "
                f"WHERE dataset_id = '{dataset_id}' "
                f"GROUP BY CAST(data->>'{date_col}' AS DATE) "
                f"ORDER BY {agg_name} {direction} NULLS LAST "
                f"LIMIT 1"
            )
            return sql
        
        # PATTERN 1: Total/Sum KPI
        # "what is the total revenue", "sum of sales", "total units sold"
        if any(word in q for word in ['total', 'sum of']) and numeric_cols:
            for col in numeric_cols:
                if col.replace('_', ' ') in q:
                    sql = f"SELECT SUM(CAST(data->>'{col}' AS NUMERIC)) AS total_{col} FROM dataset_rows WHERE dataset_id = '{dataset_id}'"
                    return sql
        
        # PATTERN 2: Count KPI
        # "how many customers", "count of orders"
        if any(word in q for word in ['how many', 'count', 'number of']):
            # Try to find the entity being counted
            for col in list(columns.keys()):
                if col.replace('_', ' ') in q:
                    sql = f"SELECT COUNT(DISTINCT data->>'{col}') AS count_{col} FROM dataset_rows WHERE dataset_id = '{dataset_id}'"
                    return sql
            # Fallback: count all rows
            sql = f"SELECT COUNT(*) AS total_count FROM dataset_rows WHERE dataset_id = '{dataset_id}'"
            return sql
        
        # PATTERN 3: Average KPI
        # "average satisfaction", "mean age"
        if any(word in q for word in ['average', 'avg', 'mean']) and numeric_cols:
            for col in numeric_cols:
                if col.replace('_', ' ') in q:
                    sql = f"SELECT AVG(CAST(data->>'{col}' AS NUMERIC)) AS avg_{col} FROM dataset_rows WHERE dataset_id = '{dataset_id}'"
                    return sql
        
        # PATTERN 4: Group by aggregation (chart)
        # "revenue by region", "sales by product", "satisfaction by gender"
        if ' by ' in q and numeric_cols and categorical_cols:
            for num_col in numeric_cols:
                for cat_col in categorical_cols:
                    if num_col.replace('_', ' ') in q and cat_col.replace('_', ' ') in q:
                        # Determine aggregation type
                        if any(word in q for word in ['total', 'sum']):
                            agg = 'SUM'
                        elif any(word in q for word in ['average', 'avg', 'mean']):
                            agg = 'AVG'
                        elif any(word in q for word in ['count']):
                            agg = 'COUNT'
                        else:
                            agg = 'SUM'  # Default
                        
                        sql = f"SELECT data->>'{cat_col}' AS {cat_col}, {agg}(CAST(data->>'{num_col}' AS NUMERIC)) AS {num_col} FROM dataset_rows WHERE dataset_id = '{dataset_id}' GROUP BY data->>'{cat_col}' ORDER BY {num_col} DESC"
                        return sql
        
        # PATTERN 5: Top N queries (table)
        # "top 5 products", "show me the best regions"
        if any(word in q for word in ['top', 'best', 'highest']) and numeric_cols:
            limit = 5  # Default
            # Try to extract number
            import re
            numbers = re.findall(r'\d+', q)
            if numbers:
                limit = int(numbers[0])
            
            for num_col in numeric_cols:
                for cat_col in list(columns.keys()):
                    if cat_col.replace('_', ' ') in q and num_col.replace('_', ' ') in q:
                        sql = f"SELECT data->>'{cat_col}' AS {cat_col}, CAST(data->>'{num_col}' AS NUMERIC) AS {num_col} FROM dataset_rows WHERE dataset_id = '{dataset_id}' ORDER BY CAST(data->>'{num_col}' AS NUMERIC) DESC LIMIT {limit}"
                        return sql
        
        # PATTERN 6: List all with aggregation (chart)
        # "list all regions with total revenue"
        if 'list all' in q or 'all regions' in q or 'all products' in q:
            for cat_col in categorical_cols:
                if cat_col.replace('_', ' ') in q:
                    for num_col in numeric_cols:
                        if num_col.replace('_', ' ') in q:
                            sql = f"SELECT data->>'{cat_col}' AS {cat_col}, SUM(CAST(data->>'{num_col}' AS NUMERIC)) AS total_{num_col} FROM dataset_rows WHERE dataset_id = '{dataset_id}' GROUP BY data->>'{cat_col}' ORDER BY total_{num_col} DESC"
                            return sql
        
        # PATTERN 7: Time series (chart)
        # "revenue over time", "sales trend", "by date"
        if datetime_cols and any(word in q for word in ['over time', 'trend', 'by date', 'by month']):
            for date_col in datetime_cols:
                for num_col in numeric_cols:
                    if num_col.replace('_', ' ') in q:
                        sql = f"SELECT data->>'{date_col}' AS {date_col}, SUM(CAST(data->>'{num_col}' AS NUMERIC)) AS total_{num_col} FROM dataset_rows WHERE dataset_id = '{dataset_id}' GROUP BY data->>'{date_col}' ORDER BY data->>'{date_col}'"
                        return sql
        
        # No pattern matched
        return None
    
    def generate_sql_from_question(self, schema: Dict[str, Any], question: str) -> str:
        """
        Phase 3A: Convert natural language question to SQL
        Uses: 1. Cache lookup 2. Deterministic rules 3. LLM fallback
        Intent is determined from result shape, not here.
        
        Args:
            schema: Dataset schema with column names and types
            question: User's natural language question
        
        Returns:
            sql_query (intent will be determined from result shape)
        """
        
        # Step 1: Check cache
        cache_key = self._get_cache_key(schema, question)
        if cache_key in self._sql_cache:
            print(f"   💾 Cache hit for question")
            return self._sql_cache[cache_key]
        
        # Step 2: Try deterministic SQL generation
        deterministic_result = self.generate_deterministic_sql(schema, question)
        if deterministic_result:
            print(f"   🎯 Using deterministic SQL (no LLM call)")
            self._sql_cache[cache_key] = deterministic_result
            return deterministic_result
        
        # Step 3: Fall back to LLM
        print(f"   🤖 Calling LLM for complex query")
        
        prompt = f"""You are a SQL expert and data analyst.

DATASET SCHEMA:
{json.dumps(schema, indent=2)}

USER QUESTION: "{question}"

Your task:
Write a PostgreSQL SELECT query to answer this question.

RULES:
- Table name: dataset_rows
- Data stored as JSON in 'data' column
- Access columns using: data->>'column_name'
- Use WHERE dataset_id = '{schema['dataset_id']}'
- Cast numeric columns: CAST(data->>'column' AS NUMERIC)
- Cast datetime columns: CAST(data->>'column' AS DATE)
- Use appropriate aggregations (SUM, AVG, COUNT, etc.)
- Use GROUP BY when aggregating by dimensions
- Use ORDER BY for sorted results
- Use LIMIT for top N queries

QUALITY REQUIREMENTS:
- If the user asks "which/what/tell <dimension>" (e.g. which date, which region), your SELECT MUST include that dimension column.
- If the user asks for a maximum/minimum and also asks "which <dimension>", do NOT return only MAX(value). Instead, return the <dimension> + the aggregated value that makes it max/min (ORDER BY ... DESC/ASC LIMIT 1).
- Prefer aggregating per-date/per-category when the question is about a date/category (e.g. sum revenue per date, then pick the max date).

Return ONLY valid JSON in this format:
{{
  "sql_query": "SELECT ..."
}}
"""
        
        try:
            result = self._call_groq_with_safeguards(
                prompt=prompt,
                system_message="You are a SQL expert. Return only valid JSON.",
                temperature=0.3,
                max_tokens=500,
                response_format="json"
            )
            
            parsed = json.loads(result)
            sql_query = parsed.get("sql_query", "")
            
            # Clean up SQL (remove markdown code blocks if present)
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            # Cache the result
            self._sql_cache[cache_key] = sql_query
            
            return sql_query
            
        except Exception as e:
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL is safe (read-only)
        Reused from Phase 2
        """
        sql_upper = sql.upper().strip()
        
        # Must be a SELECT query
        if not sql_upper.startswith("SELECT"):
            return False
        
        # Deny dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        return True
    
    def execute_chat_query(self, sql: str) -> Dict[str, Any]:
        """
        Phase 3B: Execute SQL and return structured result
        
        Args:
            sql: PostgreSQL SELECT query
        
        Returns:
            Dictionary with result data and metadata
        """
        
        if not self.validate_sql(sql):
            raise ValueError("Invalid or unsafe SQL query")
        
        try:
            result = self.db.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())  # Convert RMKeyView to list
            
            # Empty result is valid (not an error)
            if not rows:
                return {
                    "result_type": "empty",
                    "data": [],
                    "row_count": 0,
                    "columns": columns
                }
            
            # Detect result type based on shape (Phase 3 fix)
            row_count = len(rows)
            col_count = len(columns)
            
            # Convert rows to list of dicts
            data_list = []
            for row in rows:
                row_dict = {columns[i]: row[i] for i in range(col_count)}
                data_list.append(row_dict)
            
            # Intent detection based on result shape:
            # 1 row, 1 column → KPI (single value, including zero)
            if row_count == 1 and col_count == 1:
                return {
                    "result_type": "kpi",
                    "data": data_list,
                    "row_count": 1,
                    "columns": columns
                }
            
            # Multiple rows, 1 column → Table (list)
            if col_count == 1:
                return {
                    "result_type": "table",
                    "data": data_list,
                    "row_count": row_count,
                    "columns": columns
                }
            
            # Multiple rows, 2 columns → Chart (grouped data for visualization)
            if col_count == 2 and row_count > 1:
                return {
                    "result_type": "chart",
                    "data": data_list,
                    "row_count": row_count,
                    "columns": columns
                }
            
            # Multiple columns → Table (detailed data)
            return {
                "result_type": "table",
                "data": data_list,
                "row_count": row_count,
                "columns": columns
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Query execution failed: {str(e)}")
    
    def generate_explanation(self, question: str, result: Dict[str, Any]) -> str:
        """
        Phase 3C: Generate natural language explanation of result
        
        Args:
            question: User's original question
            result: Query result data
        
        Returns:
            Natural language explanation
        """
        
        prompt = f"""You are a data analyst providing insights.

USER QUESTION: "{question}"

QUERY RESULT:
{json.dumps(result, indent=2, default=str)}

Provide a concise, natural language explanation of this result.
- Focus on key insights
- Use simple language
- Mention specific numbers when relevant
- Keep it under 3 sentences

IMPORTANT:
- If the result contains a date/time/category field that answers a "which/what" question (e.g. "which date"), you MUST state the exact value (e.g. the date) in the explanation.

Return ONLY the explanation text (no JSON, no formatting).
"""
        
        try:
            explanation = self._call_groq_with_safeguards(
                prompt=prompt,
                system_message="You are a data analyst. Provide clear, concise explanations.",
                temperature=0.5,
                max_tokens=200,
                response_format="text"
            )
            return explanation.strip()
            
        except Exception as e:
            return f"Result returned successfully. (Explanation generation failed: {str(e)})"
    
    @retry_on_transient_errors(max_retries=1, backoff_seconds=1.0)
    @timeout_wrapper(timeout_seconds=20)
    def _call_groq_with_safeguards(self, prompt: str, system_message: str, temperature: float, max_tokens: int, response_format: str = "text") -> str:
        """
        Call Groq with timeout and retry protection.
        
        Args:
            prompt: User prompt
            system_message: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            response_format: "text" or "json"
        
        Returns:
            LLM response text
        
        Raises:
            LLMTimeoutError: If call exceeds 20s timeout
            Exception: On non-retryable errors
        """
        completion = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if response_format == "json" else None
        )
        return completion.choices[0].message.content

    def _ensure_key_value_mentioned(self, question: str, result: Dict[str, Any], explanation: Optional[str]) -> Optional[str]:
        """Post-process explanation to ensure key dimension value (like a date) is explicitly mentioned when present."""
        if not explanation:
            return explanation
        q = (question or '').lower()
        if 'date' not in q and 'day' not in q and 'month' not in q and 'year' not in q:
            return explanation
        if result.get('result_type') != 'table':
            return explanation
        data = result.get('data')
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            return explanation

        row = data[0]
        # Find a likely date-like column by name
        date_key = None
        for k in row.keys():
            kl = str(k).lower()
            if 'date' in kl or 'day' in kl or 'month' in kl or 'year' in kl or 'time' in kl:
                date_key = k
                break
        if not date_key:
            return explanation

        date_val = row.get(date_key)
        if date_val is None:
            return explanation
        date_str = str(date_val)
        if date_str and date_str not in explanation:
            # Also include the strongest numeric value if present
            metric_bits = []
            for k, v in row.items():
                if k == date_key:
                    continue
                try:
                    float(v)
                    metric_bits.append(f"{k}={v}")
                except Exception:
                    continue
            suffix = f" ({', '.join(metric_bits)})" if metric_bits else ""
            return f"{explanation} Date: {date_str}{suffix}."
        return explanation
    
    def process_chat_query(self, request: ChatRequest) -> ChatResponse:
        """
        Phase 3D: Complete chat query pipeline
        
        1. Get schema
        2. Generate SQL + intent from question
        3. Execute SQL
        4. Format result
        5. Generate explanation (optional)
        """
        
        try:
            # Step 1: Get schema
            ingestion_service = IngestionService(self.db)
            schema = ingestion_service.get_schema(request.dataset_id)
            
            if not schema:
                return ChatResponse(
                    question=request.question,
                    intent="error",
                    sql_query="",
                    result_type="error",
                    data=None,
                    status="failed",
                    error="Dataset not found"
                )
            
            # Step 2: Generate SQL (no intent - will be determined from result)
            sql_query = self.generate_sql_from_question(schema, request.question)
            
            # Step 3: Execute query
            result = self.execute_chat_query(sql_query)
            
            # Step 4: Intent determined from result shape (auto-detection)
            intent = result["result_type"]  # kpi, table, chart, or empty
            
            # Step 5: Generate explanation (if requested)
            explanation = None
            if request.include_explanation:
                explanation = self.generate_explanation(request.question, result)
                explanation = self._ensure_key_value_mentioned(request.question, result, explanation)
            
            # Step 6: Return response
            return ChatResponse(
                question=request.question,
                intent=intent,
                sql_query=sql_query,
                result_type=result["result_type"],
                data=result["data"],
                explanation=explanation,
                status="success",
                error=None
            )
            
        except Exception as e:
            # Capture SQL query if it was generated before the error
            sql_query = ""
            try:
                sql_query = self.generate_sql_from_question(
                    ingestion_service.get_schema(request.dataset_id),
                    request.question
                )
            except:
                pass
            
            return ChatResponse(
                question=request.question,
                intent="error",
                sql_query=sql_query,
                result_type="error",
                data=None,
                explanation=None,
                status="failed",
                error=str(e)
            )


# Phase 3 Router
# ============================================================================
# CHAT SESSION ROUTER (PostgreSQL Persistence)
# ============================================================================

session_router = APIRouter(prefix="/chat/sessions", tags=["Chat Sessions"])


@session_router.post("")
async def create_session(
    dataset_id: Optional[str] = None,
    uid: str = Depends(require_auth),  # Strict auth - sessions need owner
    db: Session = Depends(get_db)
):
    """Create a new chat session (requires authentication)"""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        id=session_id,
        owner_uid=uid,
        dataset_id=dataset_id,
        title="New Chat"
    )
    db.add(session)
    db.commit()
    
    return {"session_id": session_id, "title": "New Chat"}


@session_router.get("/user/{user_id}")
async def get_user_sessions(
    user_id: str,
    uid: str = Depends(require_auth),  # Must be authenticated
    db: Session = Depends(get_db)
):
    """Get all chat sessions for authenticated user (403 if requesting another user)"""
    # Authorization: Can only fetch own sessions
    if uid != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Cannot access another user's sessions"
        )
    
    sessions = db.query(ChatSession).filter(
        ChatSession.owner_uid == uid
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [{
        "id": s.id,
        "title": s.title,
        "dataset_id": s.dataset_id,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat()
    } for s in sessions]


@session_router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    uid: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all messages for a session (403 if not owner)"""
    # Authorization: Verify session ownership
    session = check_session_ownership(session_id, uid, db)
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "dataset_id": session.dataset_id,
        "messages": [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "chart": m.chart,
            "metadata": m.message_metadata,
            "timestamp": m.timestamp
        } for m in messages]
    }


@session_router.post("/{session_id}/messages")
async def save_message(
    session_id: str,
    message: dict,
    uid: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save a chat message (403 if not owner)"""
    # Authorization: Verify session ownership
    session = check_session_ownership(session_id, uid, db)
    
    chat_message = ChatMessage(
        id=message.get("id", str(uuid.uuid4())),
        session_id=session_id,
        role=message["role"],
        content=message["content"],
        chart=message.get("chart"),
        message_metadata=message.get("metadata"),
        timestamp=message.get("timestamp")
    )
    db.add(chat_message)
    
    # Update session timestamp
    session.updated_at = datetime.utcnow()
    
    db.commit()
    return {"status": "saved"}


@session_router.patch("/{session_id}/title")
async def update_session_title(
    session_id: str,
    data: dict,
    uid: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update session title (403 if not owner)"""
    # Authorization: Verify session ownership
    session = check_session_ownership(session_id, uid, db)
    
    session.title = data["title"]
    session.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "updated"}


@session_router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    uid: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages (403 if not owner)"""
    # Authorization: Verify session ownership
    check_session_ownership(session_id, uid, db)
    
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.query(ChatSession).filter(ChatSession.id == session_id).delete()
    db.commit()
    
    return {"status": "deleted"}


# ============================================================================
# CHAT QUERY ROUTER
# ============================================================================

chat_router = APIRouter()


@chat_router.post("/query", response_model=ChatResponse)
@limiter.limit("30/minute")  # 30 requests per minute per user/IP
async def chat_query(
    request: Request,  # Required for rate limiting
    chat_request: ChatRequest,
    uid: str = Depends(require_auth),  # Require authentication
    db: Session = Depends(get_db)
):
    """
    Phase 3: Chat with CSV using natural language
    
    Authentication: Required (401 if not authenticated)
    Authorization: Owner can only query their own datasets
    Rate Limiting: 30 requests per minute per authenticated user (or IP if unauthenticated)
    Timeouts: 20s for LLM calls
    Retries: 1 retry on transient failures (5xx, timeout)
    
    Flow:
    1. Verify dataset ownership (403 if not owner)
    2. LLM converts question to SQL + detects intent
    3. Execute SQL on PostgreSQL
    4. Format result based on type (KPI/table/chart)
    5. Generate natural language explanation
    
    Example questions:
    - "What is the total revenue?"
    - "Show top 10 customers by purchase amount"
    - "Average satisfaction by region"
    
    Errors:
    - 401: Not authenticated
    - 403: Not dataset owner
    - 429: Rate limit exceeded
    - 504: LLM timeout
    """
    # uid is guaranteed to be present (require_auth enforces it)
    owner_uid = uid
    
    # Authorization: Verify dataset ownership
    check_dataset_ownership(chat_request.dataset_id, owner_uid, db)
    
    try:
        service = ChatService(db)
        # Run sync method in thread pool to avoid blocking async event loop
        response = await asyncio.to_thread(service.process_chat_query, chat_request)
        return response
    
    except LLMTimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "gateway_timeout",
                "message": "The AI service took too long to respond. Please try again.",
                "details": str(e)
            }
        )
    
    except Exception as e:
        # Log error for debugging
        print(f"❌ Chat query error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An error occurred processing your query. Please try again.",
                "details": str(e)
            }
        )


app.include_router(session_router)
app.include_router(chat_router, prefix="/chat", tags=["Phase 3: Chat With CSV"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting DataCue Backend - Phases 1, 2, 3")
    print("📊 Initializing PostgreSQL database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")
    print("✓ Server ready")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "phases": "1, 2 & 3",
        "description": "CSV Upload, Schema Extraction, Dashboard Generation & Chat with CSV",
        "endpoints": {
            "phase_1": {
                "upload": "POST /ingestion/upload",
                "get_schema": "GET /ingestion/schema/{dataset_id}",
                "get_schema_by_session": "GET /ingestion/schema/session/{session_id}"
            },
            "phase_2": {
                "generate_dashboard": "POST /dashboard/generate",
                "generate_from_schema": "POST /dashboard/generate-from-schema?dataset_id=xxx&session_id=yyy"
            },
            "phase_3": {
                "chat_query": "POST /chat/query"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy", "service": "datacue-backend", "phases": "1, 2 & 3"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
