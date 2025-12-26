"""
Julia Integration for Tahlil Platform.
Provides integration with Julia via PyJulia for high-performance computing.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class JuliaProvider(ToolProvider):
    """
    Integration with Julia programming language via PyJulia.
    Supports Julia script execution and data exchange.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._julia = None
        self._Main = None
    
    @property
    def name(self) -> str:
        return "julia"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STATISTICS
    
    @property
    def description(self) -> str:
        return "Julia integration for high-performance numerical computing"
    
    @property
    def dependencies(self) -> List[str]:
        return ["julia"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "execute_script",
            "run_function",
            "data_to_julia",
            "data_from_julia",
            "install_package",
            "load_package",
            "julia_analysis"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install julia package if needed
            from .dependency_manager import check_and_install, check_external_software
            success, _ = check_and_install('julia', 'julia')
            if not success:
                return False
            
            import julia
            # Check if Julia is installed (external software)
            julia_available, julia_error = check_external_software('Julia', ['julia', '--version'])
            if not julia_available:
                logger.warning(f"Julia is not installed: {julia_error}")
                return False
            return True
        except (ImportError, FileNotFoundError):
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            from julia import Main as jl
            
            self._julia = jl
            self._Main = jl
            
            # Get Julia version
            version = jl.eval('VERSION')
            
            return ToolResult(
                success=True,
                metadata={'julia_version': str(version)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a Julia operation."""
        operations = {
            'execute_script': self._execute_script,
            'run_function': self._run_function,
            'to_julia': self._data_to_julia,
            'from_julia': self._data_from_julia,
            'install_package': self._install_package,
            'load_package': self._load_package,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"Julia {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _execute_script(self, script: str, **kwargs) -> ToolResult:
        """Execute Julia script."""
        try:
            result = self._julia.eval(script)
            
            # Convert result
            if hasattr(result, '__array__'):
                result_data = result.__array__().tolist()
            else:
                result_data = str(result)
            
            return ToolResult(
                success=True,
                data={
                    'result': result_data,
                    'script': script
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _run_function(self, function_code: str, **kwargs) -> ToolResult:
        """Run a Julia function."""
        try:
            # Define and execute function
            full_code = f"""
{function_code}
"""
            result = self._julia.eval(full_code)
            
            return ToolResult(
                success=True,
                data={
                    'result': str(result),
                    'function': function_code
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _data_to_julia(self, data, variable_name: str = 'data', **kwargs) -> ToolResult:
        """Convert Python data to Julia variable."""
        import numpy as np
        
        try:
            if isinstance(data, np.ndarray):
                self._julia[variable_name] = data
            elif isinstance(data, list):
                self._julia[variable_name] = np.array(data)
            else:
                self._julia[variable_name] = data
            
            return ToolResult(
                success=True,
                data={'variable_name': variable_name}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _data_from_julia(self, variable_name: str, **kwargs) -> ToolResult:
        """Get data from Julia."""
        try:
            julia_var = self._julia[variable_name]
            
            # Convert to Python
            if hasattr(julia_var, '__array__'):
                data = julia_var.__array__().tolist()
            else:
                data = str(julia_var)
            
            return ToolResult(
                success=True,
                data={'data': data, 'variable_name': variable_name}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _install_package(self, package_name: str, **kwargs) -> ToolResult:
        """Install a Julia package."""
        try:
            script = f'using Pkg; Pkg.add("{package_name}")'
            self._julia.eval(script)
            
            return ToolResult(
                success=True,
                data={'package': package_name, 'installed': True}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _load_package(self, package_name: str, **kwargs) -> ToolResult:
        """Load a Julia package."""
        try:
            script = f'using {package_name}'
            self._julia.eval(script)
            
            return ToolResult(
                success=True,
                data={'package': package_name, 'loaded': True}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for Julia operations."""
        code_templates = {
            'execute_script': '''
from julia import Main as jl

# Execute Julia script
script = """
{script}
"""

result = jl.eval(script)
print(result)
''',
            'data_exchange': '''
from julia import Main as jl
import numpy as np

# Convert Python data to Julia
data = np.array({data})
jl.data = data

# Use in Julia
jl.eval("result = sum(data)")

# Get result back
result = jl.result
print(result)
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'execute_script', 'description': 'Execute Julia script', 'params': ['script']},
            {'name': 'run_function', 'description': 'Run Julia function', 'params': ['function_code']},
            {'name': 'to_julia', 'description': 'Convert Python data to Julia', 'params': ['data', 'variable_name']},
            {'name': 'from_julia', 'description': 'Get data from Julia', 'params': ['variable_name']},
            {'name': 'install_package', 'description': 'Install Julia package', 'params': ['package_name']},
            {'name': 'load_package', 'description': 'Load Julia package', 'params': ['package_name']}
        ]
