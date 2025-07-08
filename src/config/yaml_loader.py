"""
YAML criteria catalog loader for the Offenheitscrawler.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger


class YAMLCriteriaLoader:
    """Loads and manages YAML criteria catalogs."""
    
    def __init__(self, criteria_dir: str = "criteria"):
        """
        Initialize YAML loader.
        
        Args:
            criteria_dir: Directory containing YAML criteria files
        """
        self.criteria_dir = Path(criteria_dir)
        self.logger = logger.bind(name=self.__class__.__name__)
        
        # Ensure criteria directory exists
        self.criteria_dir.mkdir(exist_ok=True)
    
    def get_available_catalogs(self) -> List[str]:
        """
        Get list of available YAML criteria catalogs.
        
        Returns:
            List of catalog names (without .yaml extension)
        """
        try:
            yaml_files = list(self.criteria_dir.glob("*.yaml")) + list(self.criteria_dir.glob("*.yml"))
            catalog_names = [f.stem for f in yaml_files]
            
            self.logger.info(f"Found {len(catalog_names)} criteria catalogs")
            return sorted(catalog_names)
            
        except Exception as e:
            self.logger.error(f"Error getting available catalogs: {str(e)}")
            return []
    
    def load_catalog(self, catalog_name: str) -> Dict[str, Any]:
        """
        Load a specific criteria catalog.
        
        Args:
            catalog_name: Name of the catalog (without extension)
        
        Returns:
            Loaded catalog dictionary
        
        Raises:
            FileNotFoundError: If catalog file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            # Try both .yaml and .yml extensions
            yaml_path = self.criteria_dir / f"{catalog_name}.yaml"
            if not yaml_path.exists():
                yaml_path = self.criteria_dir / f"{catalog_name}.yml"
            
            if not yaml_path.exists():
                raise FileNotFoundError(f"Catalog '{catalog_name}' not found in {self.criteria_dir}")
            
            with open(yaml_path, 'r', encoding='utf-8') as file:
                catalog = yaml.safe_load(file)
            
            # Validate catalog structure
            self._validate_catalog(catalog, catalog_name)
            
            self.logger.info(f"Loaded catalog '{catalog_name}' with {self._count_criteria(catalog)} criteria")
            return catalog
            
        except Exception as e:
            self.logger.error(f"Error loading catalog '{catalog_name}': {str(e)}")
            raise
    
    def get_catalog_info(self, catalog_name: str) -> Dict[str, Any]:
        """
        Get basic information about a catalog without fully loading it.
        
        Args:
            catalog_name: Name of the catalog
        
        Returns:
            Dictionary with catalog information
        """
        try:
            catalog = self.load_catalog(catalog_name)
            
            info = {
                'name': catalog.get('metadata', {}).get('name', catalog_name),
                'description': catalog.get('metadata', {}).get('description', ''),
                'version': catalog.get('metadata', {}).get('version', '1.0'),
                'organization_type': catalog.get('metadata', {}).get('organization_type', ''),
                'dimensions': len(catalog.get('dimensions', {})),
                'total_criteria': self._count_criteria(catalog)
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting catalog info for '{catalog_name}': {str(e)}")
            return {'name': catalog_name, 'error': str(e)}
    
    def _validate_catalog(self, catalog: Dict[str, Any], catalog_name: str) -> None:
        """
        Validate catalog structure.
        
        Args:
            catalog: Catalog dictionary
            catalog_name: Name of the catalog for error messages
        
        Raises:
            ValueError: If catalog structure is invalid
        """
        required_keys = ['metadata', 'dimensions']
        missing_keys = [key for key in required_keys if key not in catalog]
        
        if missing_keys:
            raise ValueError(f"Catalog '{catalog_name}' missing required keys: {missing_keys}")
        
        # Validate metadata
        metadata = catalog['metadata']
        required_metadata = ['name', 'organization_type']
        missing_metadata = [key for key in required_metadata if key not in metadata]
        
        if missing_metadata:
            raise ValueError(f"Catalog '{catalog_name}' metadata missing: {missing_metadata}")
        
        # Validate dimensions structure
        dimensions = catalog['dimensions']
        if not isinstance(dimensions, dict):
            raise ValueError(f"Catalog '{catalog_name}' dimensions must be a dictionary")
        
        for dim_name, dimension in dimensions.items():
            if not isinstance(dimension, dict):
                raise ValueError(f"Dimension '{dim_name}' must be a dictionary")
            
            if 'factors' not in dimension:
                raise ValueError(f"Dimension '{dim_name}' missing 'factors' key")
            
            # Validate factors
            for factor_name, factor in dimension['factors'].items():
                if not isinstance(factor, dict):
                    raise ValueError(f"Factor '{factor_name}' must be a dictionary")
                
                if 'criteria' not in factor:
                    raise ValueError(f"Factor '{factor_name}' missing 'criteria' key")
                
                # Validate criteria
                for criterion_id, criterion in factor['criteria'].items():
                    self._validate_criterion(criterion, criterion_id, factor_name, dim_name)
    
    def _validate_criterion(
        self, 
        criterion: Dict[str, Any], 
        criterion_id: str, 
        factor_name: str, 
        dim_name: str
    ) -> None:
        """
        Validate individual criterion structure.
        
        Args:
            criterion: Criterion dictionary
            criterion_id: Criterion ID
            factor_name: Parent factor name
            dim_name: Parent dimension name
        
        Raises:
            ValueError: If criterion structure is invalid
        """
        required_keys = ['name', 'description', 'type']
        missing_keys = [key for key in required_keys if key not in criterion]
        
        if missing_keys:
            raise ValueError(
                f"Criterion '{criterion_id}' in {dim_name}.{factor_name} missing: {missing_keys}"
            )
        
        # Validate criterion type
        valid_types = ['operational', 'strategic']
        if criterion['type'] not in valid_types:
            raise ValueError(
                f"Criterion '{criterion_id}' has invalid type. Must be one of: {valid_types}"
            )
        
        # Validate patterns if present
        if 'patterns' in criterion:
            patterns = criterion['patterns']
            valid_pattern_types = ['text', 'url', 'logo']
            
            for pattern_type, pattern_list in patterns.items():
                if pattern_type not in valid_pattern_types:
                    self.logger.warning(
                        f"Unknown pattern type '{pattern_type}' in criterion '{criterion_id}'"
                    )
                
                if not isinstance(pattern_list, list):
                    raise ValueError(
                        f"Pattern '{pattern_type}' in criterion '{criterion_id}' must be a list"
                    )
    
    def _count_criteria(self, catalog: Dict[str, Any]) -> int:
        """
        Count total number of criteria in catalog.
        
        Args:
            catalog: Catalog dictionary
        
        Returns:
            Total number of criteria
        """
        total = 0
        
        for dimension in catalog.get('dimensions', {}).values():
            for factor in dimension.get('factors', {}).values():
                total += len(factor.get('criteria', {}))
        
        return total
    
    def get_all_criteria(self, catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all criteria from catalog with full context.
        
        Args:
            catalog: Catalog dictionary
        
        Returns:
            List of criteria with context information
        """
        criteria_list = []
        
        for dim_name, dimension in catalog.get('dimensions', {}).items():
            for factor_name, factor in dimension.get('factors', {}).items():
                for criterion_id, criterion in factor.get('criteria', {}).items():
                    criterion_with_context = {
                        'id': criterion_id,
                        'dimension': dim_name,
                        'factor': factor_name,
                        'name': criterion['name'],
                        'description': criterion['description'],
                        'type': criterion['type'],
                        'patterns': criterion.get('patterns', {}),
                        'weight': criterion.get('weight', 1.0),
                        'confidence_threshold': criterion.get('confidence_threshold', 0.5)
                    }
                    criteria_list.append(criterion_with_context)
        
        return criteria_list
    
    def create_sample_catalog(self, catalog_name: str, organization_type: str) -> None:
        """
        Create a sample criteria catalog file.
        
        Args:
            catalog_name: Name for the new catalog
            organization_type: Type of organization
        """
        sample_catalog = {
            'metadata': {
                'name': f'{organization_type} Offenheitskriterien',
                'description': f'Kriterienkatalog für {organization_type}',
                'version': '1.0',
                'organization_type': organization_type,
                'created_date': '2025-01-01',
                'author': 'Offenheitscrawler'
            },
            'dimensions': {
                'transparenz': {
                    'name': 'Transparenz',
                    'description': 'Offenheit und Transparenz der Organisation',
                    'factors': {
                        'finanzielle_transparenz': {
                            'name': 'Finanzielle Transparenz',
                            'description': 'Veröffentlichung von Finanzinformationen',
                            'criteria': {
                                'jahresbericht': {
                                    'name': 'Jahresbericht verfügbar',
                                    'description': 'Organisation veröffentlicht einen Jahresbericht',
                                    'type': 'operational',
                                    'patterns': {
                                        'text': ['jahresbericht', 'annual report', 'geschäftsbericht'],
                                        'url': ['/jahresbericht', '/annual-report', '/finanzen']
                                    },
                                    'weight': 1.0,
                                    'confidence_threshold': 0.3
                                }
                            }
                        }
                    }
                }
            }
        }
        
        output_path = self.criteria_dir / f"{catalog_name}.yaml"
        
        with open(output_path, 'w', encoding='utf-8') as file:
            yaml.dump(sample_catalog, file, default_flow_style=False, allow_unicode=True)
        
        self.logger.info(f"Created sample catalog: {output_path}")
