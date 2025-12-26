"""
R Integration for Tahlil Platform.
Provides Python-R bridge using rpy2 for statistical analysis.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class RProvider(ToolProvider):
    """
    Integration with R statistical environment via rpy2.
    Supports R scripts execution, data exchange, and R package usage.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._r = None
        self._robjects = None
        self._pandas2ri = None
    
    @property
    def name(self) -> str:
        return "r"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STATISTICS
    
    @property
    def description(self) -> str:
        return "R statistical environment integration via rpy2 for advanced statistical analysis"
    
    @property
    def dependencies(self) -> List[str]:
        return ["rpy2", "pandas"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "execute_r_script",
            "run_r_function",
            "data_to_r",
            "data_from_r",
            "install_r_package",
            "load_r_package",
            "r_regression",
            "r_time_series",
            "r_visualization"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install rpy2 if needed
            from .dependency_manager import check_and_install, check_external_software
            success, _ = check_and_install('rpy2', 'rpy2')
            if not success:
                return False
            
            import rpy2
            # Check if R is installed (external software)
            r_available, r_error = check_external_software('R', ['R', '--version'])
            if not r_available:
                logger.warning(f"R is not installed: {r_error}")
                return False
            return True
        except (ImportError, FileNotFoundError):
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            import rpy2.robjects as robjects
            from rpy2.robjects import pandas2ri
            from rpy2.robjects.packages import importr
            
            pandas2ri.activate()
            
            self._r = robjects.r
            self._robjects = robjects
            self._pandas2ri = pandas2ri
            self._importr = importr
            
            return ToolResult(
                success=True,
                metadata={'r_version': str(self._r('R.version.string')[0])}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute an R operation."""
        operations = {
            'execute_script': self._execute_script,
            'run_function': self._run_function,
            'to_r': self._data_to_r,
            'from_r': self._data_from_r,
            'install_package': self._install_package,
            'load_package': self._load_package,
            'regression': self._r_regression,
            'time_series': self._r_time_series,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"R {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _execute_script(self, script: str, **kwargs) -> ToolResult:
        """Execute R script and return results."""
        try:
            result = self._r(script)
            
            # Try to convert result to Python
            try:
                result_data = self._pandas2ri.rpy2py(result)
            except:
                result_data = str(result)
            
            return ToolResult(
                success=True,
                data={
                    'result': result_data,
                    'script': script
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"R script execution failed: {str(e)}")
    
    def _run_function(self, package: str, function: str, **kwargs) -> ToolResult:
        """Run an R function from a package."""
        try:
            r_package = self._importr(package)
            r_func = getattr(r_package, function)
            
            # Convert kwargs to R arguments
            r_args = {}
            for key, value in kwargs.items():
                if isinstance(value, (list, dict)):
                    r_args[key] = self._robjects.vectors.ListVector(value)
                else:
                    r_args[key] = value
            
            result = r_func(**r_args)
            
            # Convert result
            try:
                result_data = self._pandas2ri.rpy2py(result)
            except:
                result_data = str(result)
            
            return ToolResult(
                success=True,
                data={
                    'result': result_data,
                    'package': package,
                    'function': function
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _data_to_r(self, data, variable_name: str = 'data', **kwargs) -> ToolResult:
        """Convert Python data to R object."""
        import pandas as pd
        
        try:
            if isinstance(data, pd.DataFrame):
                r_data = self._pandas2ri.py2rpy(data)
                self._r.assign(variable_name, r_data)
            elif isinstance(data, (list, dict)):
                r_data = self._robjects.vectors.ListVector(data)
                self._r.assign(variable_name, r_data)
            else:
                self._r.assign(variable_name, data)
            
            return ToolResult(
                success=True,
                data={'variable_name': variable_name, 'type': type(data).__name__}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _data_from_r(self, variable_name: str, **kwargs) -> ToolResult:
        """Convert R object to Python data."""
        try:
            r_obj = self._r(variable_name)
            
            # Try to convert to pandas DataFrame
            try:
                df = self._pandas2ri.rpy2py(r_obj)
                return ToolResult(
                    success=True,
                    data={
                        'data': df.to_dict('records') if hasattr(df, 'to_dict') else str(df),
                        'type': 'DataFrame' if hasattr(df, 'to_dict') else 'other'
                    }
                )
            except:
                return ToolResult(
                    success=True,
                    data={'data': str(r_obj), 'type': 'string'}
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _install_package(self, package_name: str, **kwargs) -> ToolResult:
        """Install an R package."""
        try:
            script = f'install.packages("{package_name}", repos="https://cran.rstudio.com/")'
            self._r(script)
            
            return ToolResult(
                success=True,
                data={'package': package_name, 'installed': True}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _load_package(self, package_name: str, **kwargs) -> ToolResult:
        """Load an R package."""
        try:
            r_package = self._importr(package_name)
            
            return ToolResult(
                success=True,
                data={
                    'package': package_name,
                    'loaded': True,
                    'functions': dir(r_package)[:20]  # First 20 functions
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _r_regression(self, formula: str, data, **kwargs) -> ToolResult:
        """Perform R regression analysis."""
        import pandas as pd
        
        try:
            # Convert data to R
            if isinstance(data, pd.DataFrame):
                r_data = self._pandas2ri.py2rpy(data)
                self._r.assign('data', r_data)
            
            # Run regression
            script = f'lm_model <- lm({formula}, data=data); summary(lm_model)'
            result = self._r(script)
            
            return ToolResult(
                success=True,
                data={
                    'formula': formula,
                    'summary': str(result)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _r_time_series(self, data, method: str = 'arima', **kwargs) -> ToolResult:
        """Perform R time series analysis."""
        import pandas as pd
        
        try:
            # Convert data to R
            if isinstance(data, pd.DataFrame):
                r_data = self._pandas2ri.py2rpy(data)
                self._r.assign('ts_data', r_data)
            
            if method == 'arima':
                script = 'arima_model <- arima(ts_data); summary(arima_model)'
            elif method == 'forecast':
                script = 'library(forecast); forecast_model <- auto.arima(ts_data); forecast(forecast_model)'
            else:
                return ToolResult(success=False, error=f"Unknown method: {method}")
            
            result = self._r(script)
            
            return ToolResult(
                success=True,
                data={
                    'method': method,
                    'result': str(result)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for R operations."""
        code_templates = {
            'execute_script': '''
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
pandas2ri.activate()

r = ro.r

# Execute R script
script = """
{script}
"""

result = r(script)
print(result)
''',
            'regression': '''
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
import pandas as pd

pandas2ri.activate()
r = ro.r

# Load data
data = pd.read_csv('data.csv')

# Convert to R
r_data = pandas2ri.py2rpy(data)
r.assign('data', r_data)

# Run regression
formula = "{formula}"
r(f'lm_model <- lm({{formula}}, data=data)')
summary = r('summary(lm_model)')
print(summary)
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'execute_script', 'description': 'Execute R script', 'params': ['script']},
            {'name': 'run_function', 'description': 'Run R function from package', 'params': ['package', 'function']},
            {'name': 'to_r', 'description': 'Convert Python data to R', 'params': ['data', 'variable_name']},
            {'name': 'from_r', 'description': 'Convert R data to Python', 'params': ['variable_name']},
            {'name': 'install_package', 'description': 'Install R package', 'params': ['package_name']},
            {'name': 'load_package', 'description': 'Load R package', 'params': ['package_name']},
            {'name': 'regression', 'description': 'R regression analysis', 'params': ['formula', 'data']},
            {'name': 'time_series', 'description': 'R time series analysis', 'params': ['data', 'method']}
        ]
