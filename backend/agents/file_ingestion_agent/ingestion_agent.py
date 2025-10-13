"""
File Ingestion Agent
Main agent responsible for reading, cleaning, and extracting metadata from uploaded files
"""

import pandas as pd
import openpyxl
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .data_cleaner import DataCleaner
from .metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileIngestionAgent:
    """
    Handles the complete file ingestion pipeline:
    1. Read CSV/Excel files
    2. Clean and standardize data
    3. Extract metadata
    """
    
    def __init__(self):
        self.data_cleaner = DataCleaner()
        self.metadata_extractor = MetadataExtractor()
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def ingest_file(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete ingestion pipeline for uploaded files
        
        Args:
            file_path: Path to the uploaded file
            sheet_name: (Optional) Specific sheet name for Excel files. If None, reads first sheet.
            
        Returns:
            Dictionary containing:
                - data: Cleaned DataFrame (as dict)
                - metadata: Extracted metadata
                - status: Success/error status
                - message: Status message
        """
        try:
            logger.info(f"Starting ingestion for file: {file_path}")
            
            # Step 1: Read the file
            df = self._read_file(file_path, sheet_name)
            logger.info(f"File read successfully. Shape: {df.shape}")
            
            # Step 2: Clean and standardize
            df_cleaned = self.data_cleaner.clean_data(df)
            logger.info(f"Data cleaned. Shape after cleaning: {df_cleaned.shape}")
            
            # Step 3: Extract metadata
            metadata = self.metadata_extractor.extract_metadata(df_cleaned)
            logger.info(f"Metadata extracted for {len(metadata['columns'])} columns")
            
            return {
                "status": "success",
                "message": "File ingested successfully",
                "data": df_cleaned.to_dict(orient='records'),
                "data_preview": df_cleaned.head(10).to_dict(orient='records'),
                "metadata": metadata,
                "original_shape": {"rows": len(df), "columns": len(df.columns)},
                "cleaned_shape": {"rows": len(df_cleaned), "columns": len(df_cleaned.columns)}
            }
            
        except Exception as e:
            logger.error(f"Error during file ingestion: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to ingest file: {str(e)}",
                "data": None,
                "metadata": None
            }
    
    def ingest_excel_all_sheets(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest all sheets from an Excel file
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary with results for each sheet
        """
        try:
            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()
            
            if file_extension not in ['.xlsx', '.xls']:
                return {
                    "status": "error",
                    "message": "This method only works with Excel files"
                }
            
            # Get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            logger.info(f"Found {len(sheet_names)} sheets in Excel file: {sheet_names}")
            
            results = {}
            for sheet_name in sheet_names:
                logger.info(f"Processing sheet: {sheet_name}")
                result = self.ingest_file(str(file_path), sheet_name=sheet_name)
                results[sheet_name] = result
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(sheet_names)} sheets",
                "sheets": sheet_names,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error ingesting Excel sheets: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to ingest Excel sheets: {str(e)}"
            }
    
    def _read_file(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Read file based on its extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            pandas DataFrame
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
        
        if file_extension == '.csv':
            # Try different encodings and delimiters for CSV
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            delimiters = [',', ';', '\t', '|']
            
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        # Try with error handling for malformed lines
                        df = pd.read_csv(
                            file_path, 
                            encoding=encoding,
                            delimiter=delimiter,
                            on_bad_lines='skip',  # Skip bad lines instead of failing
                            engine='python'  # More flexible parser
                        )
                        
                        # Validate that we got meaningful data
                        if len(df.columns) > 0 and len(df) > 0:
                            logger.info(f"CSV read successfully with encoding: {encoding}, delimiter: '{delimiter}'")
                            return df
                    except (UnicodeDecodeError, pd.errors.ParserError):
                        continue
                    except Exception as e:
                        logger.debug(f"Failed with encoding {encoding}, delimiter '{delimiter}': {str(e)}")
                        continue
            
            # If all combinations fail, try with automatic delimiter detection
            try:
                df = pd.read_csv(
                    file_path,
                    encoding='utf-8',
                    sep=None,  # Auto-detect delimiter
                    engine='python',
                    on_bad_lines='skip'
                )
                if len(df.columns) > 0 and len(df) > 0:
                    logger.info("CSV read successfully with auto-detected delimiter")
                    return df
            except Exception as e:
                logger.error(f"Auto-detection also failed: {str(e)}")
            
            raise ValueError(
                "Unable to read CSV file. Please ensure your file:\n"
                "1. Has a valid header row\n"
                "2. Uses consistent delimiters (comma, semicolon, or tab)\n"
                "3. Has the same number of columns in all rows\n"
                "4. Doesn't have corrupted or incomplete rows"
            )
        
        elif file_extension in ['.xlsx', '.xls']:
            # Read Excel file with optional sheet specification
            engine = 'openpyxl' if file_extension == '.xlsx' else None
            
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
                logger.info(f"Excel sheet '{sheet_name}' read successfully")
            else:
                df = pd.read_excel(file_path, engine=engine)
                logger.info(f"Excel file read successfully (first sheet)")
            
            return df
        
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def diagnose_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Diagnose issues with a problematic CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Diagnostic information about the CSV
        """
        try:
            file_path = Path(file_path)
            
            # Read first few lines as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline().strip() for _ in range(5)]
            
            # Analyze line structure
            line_analysis = []
            for i, line in enumerate(lines, 1):
                comma_count = line.count(',')
                semicolon_count = line.count(';')
                tab_count = line.count('\t')
                pipe_count = line.count('|')
                
                line_analysis.append({
                    "line_number": i,
                    "commas": comma_count,
                    "semicolons": semicolon_count,
                    "tabs": tab_count,
                    "pipes": pipe_count,
                    "length": len(line)
                })
            
            # Determine likely delimiter
            delimiters = {
                'comma': sum(l['commas'] for l in line_analysis),
                'semicolon': sum(l['semicolons'] for l in line_analysis),
                'tab': sum(l['tabs'] for l in line_analysis),
                'pipe': sum(l['pipes'] for l in line_analysis)
            }
            likely_delimiter = max(delimiters, key=delimiters.get)
            
            return {
                "status": "diagnostic",
                "first_lines": lines[:3],
                "line_analysis": line_analysis,
                "likely_delimiter": likely_delimiter,
                "delimiter_counts": delimiters,
                "suggestion": f"Your CSV appears to use '{likely_delimiter}' as delimiter. "
                             f"Line consistency: {self._check_line_consistency(line_analysis)}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not diagnose file: {str(e)}"
            }
    
    def _check_line_consistency(self, line_analysis: list) -> str:
        """Check if all lines have consistent delimiter counts"""
        if not line_analysis:
            return "Unable to determine"
        
        # Get most common delimiter
        first_line = line_analysis[0]
        delimiter_keys = ['commas', 'semicolons', 'tabs', 'pipes']
        max_key = max(delimiter_keys, key=lambda k: first_line[k])
        
        counts = [line[max_key] for line in line_analysis]
        if len(set(counts)) == 1:
            return f"✅ Consistent ({counts[0]} {max_key} per line)"
        else:
            return f"❌ Inconsistent ({min(counts)}-{max(counts)} {max_key} per line)"
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate if file can be read without full ingestion
        
        Args:
            file_path: Path to the file
            
        Returns:
            Validation result dictionary
        """
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                return {
                    "valid": False,
                    "message": "File does not exist"
                }
            
            # Check file extension
            if file_path.suffix.lower() not in self.supported_formats:
                return {
                    "valid": False,
                    "message": f"Unsupported file format. Supported: {', '.join(self.supported_formats)}"
                }
            
            # Try to read first few rows
            df = self._read_file(str(file_path))
            
            if df.empty:
                return {
                    "valid": False,
                    "message": "File is empty"
                }
            
            return {
                "valid": True,
                "message": "File is valid",
                "preview_shape": {"rows": len(df), "columns": len(df.columns)},
                "columns": df.columns.tolist()
            }
            
        except Exception as e:
            # If validation fails, provide diagnostic info
            if file_path.suffix.lower() == '.csv':
                diagnostic = self.diagnose_csv(str(file_path))
                return {
                    "valid": False,
                    "message": f"Validation failed: {str(e)}",
                    "diagnostic": diagnostic
                }
            return {
                "valid": False,
                "message": f"Validation failed: {str(e)}"
            }
    
    def get_excel_sheets(self, file_path: str) -> Dict[str, Any]:
        """
        Get list of all sheet names in an Excel file
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary with sheet names and preview info
        """
        try:
            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()
            
            if file_extension not in ['.xlsx', '.xls']:
                return {
                    "status": "error",
                    "message": "This method only works with Excel files (.xlsx, .xls)"
                }
            
            # Get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Get preview info for each sheet
            sheets_info = []
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)
                    sheets_info.append({
                        "name": sheet_name,
                        "rows": len(pd.read_excel(file_path, sheet_name=sheet_name)),
                        "columns": len(df.columns),
                        "column_names": df.columns.tolist()
                    })
                except Exception as e:
                    sheets_info.append({
                        "name": sheet_name,
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "message": f"Found {len(sheet_names)} sheets",
                "sheet_count": len(sheet_names),
                "sheets": sheets_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read Excel sheets: {str(e)}"
            }
