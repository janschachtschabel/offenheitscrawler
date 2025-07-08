"""
CSV handling utilities for the Offenheitscrawler.
"""

import pandas as pd
import io
from typing import List, Dict, Any, Union
from pathlib import Path
from loguru import logger


class CSVHandler:
    """Handles CSV file operations for organizations and results."""
    
    def __init__(self, delimiter: str = ";"):
        """
        Initialize CSV handler.
        
        Args:
            delimiter: CSV delimiter character
        """
        self.delimiter = delimiter
        self.logger = logger.bind(name=self.__class__.__name__)
    
    def load_organizations(self, file_input: Union[str, Path, io.StringIO]) -> pd.DataFrame:
        """
        Load organizations from CSV file or uploaded file.
        
        Args:
            file_input: File path, Path object, or uploaded file object
        
        Returns:
            DataFrame with organizations
        
        Raises:
            ValueError: If CSV format is invalid
            FileNotFoundError: If file doesn't exist
        """
        try:
            # First, try to read with headers to detect if they exist
            if hasattr(file_input, 'read'):
                # Uploaded file object
                content = file_input.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                
                # Try to detect if first row contains headers
                lines = content.strip().split('\n')
                if len(lines) > 0:
                    first_row = lines[0].split(self.delimiter)
                    # Check if first row looks like headers (contains 'Organisation' or 'URL')
                    has_headers = any(col.strip().lower() in ['organisation', 'url'] for col in first_row)
                    
                    if has_headers:
                        df = pd.read_csv(io.StringIO(content), delimiter=self.delimiter)
                        self.logger.info("CSV file loaded with headers")
                    else:
                        df = pd.read_csv(io.StringIO(content), delimiter=self.delimiter, header=None)
                        df.columns = ['Organisation', 'URL'] if len(df.columns) >= 2 else df.columns
                        self.logger.info("CSV file loaded without headers, assigned column names")
                else:
                    raise ValueError("CSV file is empty")
            else:
                # File path - similar logic
                with open(file_input, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    first_row = first_line.split(self.delimiter)
                    has_headers = any(col.strip().lower() in ['organisation', 'url'] for col in first_row)
                
                if has_headers:
                    df = pd.read_csv(file_input, delimiter=self.delimiter)
                    self.logger.info("CSV file loaded with headers")
                else:
                    df = pd.read_csv(file_input, delimiter=self.delimiter, header=None)
                    df.columns = ['Organisation', 'URL'] if len(df.columns) >= 2 else df.columns
                    self.logger.info("CSV file loaded without headers, assigned column names")
            
            # Ensure we have the required columns
            required_columns = ['Organisation', 'URL']
            if len(df.columns) < 2:
                raise ValueError(f"CSV file must have at least 2 columns, found {len(df.columns)}")
            
            # If we have more than 2 columns, use only the first 2
            if len(df.columns) > 2:
                df = df.iloc[:, :2]
                df.columns = required_columns
                self.logger.info(f"Using first 2 columns as Organisation and URL")
            
            # Clean and validate data
            df = df.dropna(subset=required_columns)
            df['Organisation'] = df['Organisation'].str.strip()
            df['URL'] = df['URL'].str.strip()
            
            # Validate URLs (basic check)
            invalid_urls = df[~df['URL'].str.contains(r'^https?://', na=False)]
            if not invalid_urls.empty:
                self.logger.warning(f"Found {len(invalid_urls)} potentially invalid URLs")
            
            self.logger.info(f"Loaded {len(df)} organizations from CSV")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading organizations CSV: {str(e)}")
            raise
    
    def results_to_dataframe(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert crawling results to DataFrame.
        
        Args:
            results: List of evaluation results
        
        Returns:
            DataFrame with results
        """
        try:
            if not results:
                return pd.DataFrame()
            
            # Flatten results into rows
            rows = []
            for result in results:
                org_name = result.get('organization_name', 'Unknown')
                
                for criterion_result in result.get('criteria_results', []):
                    row = {
                        'Organisation': org_name,
                        'Kriterium': criterion_result.get('criterion_name', ''),
                        'Bewertung': int(criterion_result.get('evaluation', 0)),
                        'Konfidenz': float(criterion_result.get('confidence', 0.0)),
                        'Begründung': criterion_result.get('justification', ''),
                        'Quelle': criterion_result.get('source_url', '')
                    }
                    rows.append(row)
            
            df = pd.DataFrame(rows)
            self.logger.info(f"Converted {len(results)} results to DataFrame with {len(df)} rows")
            return df
            
        except Exception as e:
            self.logger.error(f"Error converting results to DataFrame: {str(e)}")
            raise
    
    def dataframe_to_csv(self, df: pd.DataFrame) -> str:
        """
        Convert DataFrame to CSV string.
        
        Args:
            df: DataFrame to convert
        
        Returns:
            CSV string
        """
        try:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, sep=self.delimiter, index=False)
            csv_string = csv_buffer.getvalue()
            
            self.logger.info(f"Converted DataFrame with {len(df)} rows to CSV")
            return csv_string
            
        except Exception as e:
            self.logger.error(f"Error converting DataFrame to CSV: {str(e)}")
            raise
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
        """
        Save results to CSV file.
        
        Args:
            results: List of evaluation results
            output_path: Output file path
        """
        try:
            df = self.results_to_dataframe(results)
            df.to_csv(output_path, sep=self.delimiter, index=False)
            
            self.logger.info(f"Saved {len(df)} results to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving results to CSV: {str(e)}")
            raise
    
    def validate_csv_format(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate CSV file format and content.
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            Validation results dictionary
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'row_count': 0,
            'column_count': 0
        }
        
        try:
            df = pd.read_csv(file_path, delimiter=self.delimiter)
            validation_result['row_count'] = len(df)
            validation_result['column_count'] = len(df.columns)
            
            # Check required columns
            required_columns = ['Organisation', 'URL']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                validation_result['errors'].append(f"Missing columns: {missing_columns}")
            
            # Check for empty values
            empty_orgs = df['Organisation'].isna().sum() if 'Organisation' in df.columns else 0
            empty_urls = df['URL'].isna().sum() if 'URL' in df.columns else 0
            
            if empty_orgs > 0:
                validation_result['warnings'].append(f"{empty_orgs} empty organization names")
            
            if empty_urls > 0:
                validation_result['warnings'].append(f"{empty_urls} empty URLs")
            
            # Check URL format
            if 'URL' in df.columns:
                invalid_urls = df[~df['URL'].str.contains(r'^https?://', na=False)]
                if not invalid_urls.empty:
                    validation_result['warnings'].append(f"{len(invalid_urls)} potentially invalid URLs")
            
            # Set valid if no critical errors
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['errors'].append(f"File reading error: {str(e)}")
        
        return validation_result
