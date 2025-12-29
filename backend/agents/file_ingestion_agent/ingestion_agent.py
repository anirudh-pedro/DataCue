"""
File Ingestion Agent
Parses CSV/Excel files, cleans data, fixes column names with LLM, extracts metadata
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from .data_cleaner import DataCleaner
from .column_fixer import ColumnFixer

logger = logging.getLogger(__name__)


class FileIngestionAgent:
    """
    Handles the complete file ingestion pipeline:
    1. Read CSV/Excel files
    2. Fix column names using LLM if needed
    3. Clean and standardize data
    4. Extract essential metadata
    """
    
    def __init__(self):
        self.data_cleaner = DataCleaner()
        self.column_fixer = ColumnFixer()
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def ingest(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete ingestion pipeline for uploaded files
        
        Args:
            file_path: Path to the uploaded file
            sheet_name: (Optional) Specific sheet name for Excel files
            
        Returns:
            Dictionary containing:
                - data: Cleaned DataFrame records
                - metadata: Column names and data types
                - status: Success/error status
        """
        try:
            logger.info(f"Starting ingestion: {file_path}")
            
            # Step 1: Read the file
            df = self._read_file(file_path, sheet_name)
            logger.info(f"File read. Shape: {df.shape}")
            
            # Step 2: Fix column names with LLM if needed
            sample_data = df.head(5).to_dict(orient='records')
            column_fix_result = self.column_fixer.fix_columns(
                columns=df.columns.tolist(),
                sample_data=sample_data
            )
            
            if column_fix_result["fixed"]:
                df.columns = column_fix_result["columns"]
                logger.info(f"Fixed {len(column_fix_result['changes'])} column names")
            
            # Step 3: Clean and standardize
            df_cleaned = self.data_cleaner.clean_data(df)
            logger.info(f"Data cleaned. Shape: {df_cleaned.shape}")
            
            # Step 4: Extract essential metadata
            metadata = self._extract_metadata(df_cleaned)
            
            return {
                "status": "success",
                "message": "File ingested successfully",
                "data": df_cleaned.to_dict(orient='records'),
                "metadata": metadata,
                "column_fixes": column_fix_result.get("changes", []),
                "shape": {"rows": len(df_cleaned), "columns": len(df_cleaned.columns)}
            }
            
        except Exception as e:
            logger.error(f"Ingestion error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to ingest file: {str(e)}",
                "data": None,
                "metadata": None
            }
    
    def _extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract essential metadata: column names and data types only
        
        Args:
            df: Cleaned DataFrame
            
        Returns:
            Dictionary with columns and their types
        """
        columns = []
        
        for col in df.columns:
            col_data = df[col]
            
            # Determine data type
            if pd.api.types.is_numeric_dtype(col_data):
                dtype = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                dtype = "datetime"
            else:
                # Check if it could be datetime
                if self._is_datetime_column(col_data):
                    dtype = "datetime"
                else:
                    dtype = "categorical"
            
            columns.append({
                "name": col,
                "type": dtype,
                "unique_count": int(col_data.nunique()),
                "null_count": int(col_data.isnull().sum())
            })
        
        return {
            "columns": columns,
            "row_count": len(df),
            "column_count": len(df.columns)
        }
    
    def _is_datetime_column(self, series: pd.Series) -> bool:
        """Check if a column could be parsed as datetime"""
        try:
            sample = series.dropna().head(5)
            if len(sample) == 0:
                return False
            
            for val in sample:
                val_str = str(val)
                if any(c in val_str for c in ['-', '/', ':']):
                    pd.to_datetime(val_str)
                    return True
            return False
        except:
            return False
    
    def _read_file(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Read file based on its extension"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported format: {ext}. Supported: {self.supported_formats}")
        
        if ext == '.csv':
            return self._read_csv(file_path)
        else:
            return self._read_excel(file_path, sheet_name)
    
    def _read_csv(self, file_path: Path) -> pd.DataFrame:
        """Read CSV with auto-detection of encoding and delimiter"""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        delimiters = [',', ';', '\t', '|']
        
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        delimiter=delimiter,
                        on_bad_lines='skip',
                        engine='python'
                    )
                    if len(df.columns) > 0 and len(df) > 0:
                        return df
                except:
                    continue
        
        # Try auto-detection
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
            if len(df.columns) > 0 and len(df) > 0:
                return df
        except:
            pass
        
        raise ValueError("Unable to read CSV file. Check format and encoding.")
    
    def _read_excel(self, file_path: Path, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Read Excel file"""
        engine = 'openpyxl' if file_path.suffix == '.xlsx' else None
        return pd.read_excel(file_path, sheet_name=sheet_name or 0, engine=engine)
    
    def get_excel_sheets(self, file_path: str) -> List[str]:
        """Get list of sheet names from Excel file"""
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error reading Excel sheets: {e}")
            return []
