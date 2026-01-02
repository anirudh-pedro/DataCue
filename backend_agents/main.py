"""
DataCue Backend - Phase 1 & 2: CSV Upload, Schema Extraction & Dashboard Generation (All-in-One)
Complete implementation in a single file
"""

import os
import re
import uuid
import os
import re
import uuid
import json
import smtplib
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import Dict, List, Any, Tuple, Generator, Optional
from email.mime.text import MIMEText
from pydantic import BaseModel

from fastapi import FastAPI, APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Index, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai

load_dotenv()

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
    user_id = Column(String(36), nullable=True)
    session_id = Column(String(36), nullable=False, index=True)
    
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    columns = Column(JSON, nullable=False)  # Schema array
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
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
        user_id: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Upload CSV file and store in PostgreSQL"""
        # Generate IDs
        dataset_id = str(uuid.uuid4())
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Parse CSV and extract schema
        df, metadata = parse_csv(file_content)
        
        # Extract dataset name from filename
        dataset_name = filename.rsplit('.', 1)[0].replace(' ', '_').lower()
        
        # Create Dataset record (metadata only)
        dataset = Dataset(
            id=dataset_id,
            dataset_name=dataset_name,
            user_id=user_id,
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
    user_id: str = Query(None, description="Optional user ID"),
    session_id: str = Query(None, description="Optional session ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload CSV file - Returns schema metadata only (no raw data sent to LLM)
    
    Response format:
    {
      "dataset_id": "abc-123",
      "session_id": "xyz-789",
      "dataset_name": "sales_data",
      "row_count": 100000,
      "columns": [
        { "name": "customer_id", "type": "categorical" },
        { "name": "age", "type": "numeric" }
      ]
    }
    """
    if not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        service = IngestionService(db)
        result = service.upload_csv(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id,
            session_id=session_id
        )
        
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
            # Use gemini-2.0-flash which is available as of 2026
            model = genai.GenerativeModel('gemini-2.0-flash')
            
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
            if len(categorical_dims) == 1 and len(numeric_metrics) > 0:
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


# Simple navigation router (login -> dashboard redirect)
nav_router = APIRouter(tags=["Navigation"])


@nav_router.get("/login")
def redirect_login_to_dashboard():
    return RedirectResponse(url="/dashboard", status_code=307)


app.include_router(email_router)
app.include_router(nav_router)


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

Return ONLY valid JSON in this format:
{{
  "sql_query": "SELECT ..."
}}
"""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(completion.choices[0].message.content)
            sql_query = result.get("sql_query", "")
            
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

Return ONLY the explanation text (no JSON, no formatting).
"""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a data analyst. Provide clear, concise explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            explanation = completion.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            return f"Result returned successfully. (Explanation generation failed: {str(e)})"
    
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
chat_router = APIRouter()


@chat_router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 3: Chat with CSV using natural language
    
    Flow:
    1. User asks question in plain English
    2. LLM converts to SQL + detects intent
    3. Execute SQL on PostgreSQL
    4. Format result based on type (KPI/table/chart)
    5. Generate natural language explanation
    
    Example questions:
    - "What is the total revenue?"
    - "Show top 10 customers by purchase amount"
    - "Average satisfaction by region"
    - "Revenue trend over time"
    """
    service = ChatService(db)
    response = service.process_chat_query(request)
    
    return response


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
