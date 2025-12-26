"""
Base classes for Tahlil Tool Integration System.
Provides abstract base classes and registry for tool providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Import dependency manager for auto-installation
try:
    from .dependency_manager import auto_install_dependencies, check_external_software, check_and_install
    AUTO_INSTALL_ENABLED = True
except ImportError:
    AUTO_INSTALL_ENABLED = False
    logger.warning("Dependency manager not available - auto-install disabled")


class ToolCategory(Enum):
    """Categories of tools available in the platform."""
    STATISTICS = "statistics"
    DATABASE = "database"
    NLP = "nlp"
    MACHINE_LEARNING = "machine_learning"
    VISUALIZATION = "visualization"
    DATA_SOURCE = "data_source"
    WORKFLOW = "workflow"
    VERSION_CONTROL = "version_control"


@dataclass
class ToolResult:
    """Standard result format for tool operations."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class ToolInfo:
    """Information about a registered tool."""
    name: str
    category: ToolCategory
    description: str
    version: str
    is_available: bool
    requires_auth: bool = False
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)


class ToolProvider(ABC):
    """
    Abstract base class for all tool providers.
    Each tool integration must implement this interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
        self._available = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifier for the tool."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Category this tool belongs to."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the tool."""
        pass
    
    @property
    def version(self) -> str:
        """Version of the tool integration."""
        return "1.0.0"
    
    @property
    def requires_auth(self) -> bool:
        """Whether this tool requires authentication."""
        return False
    
    @property
    def dependencies(self) -> List[str]:
        """List of Python package dependencies."""
        return []
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this tool provides."""
        return []
    
    def is_available(self) -> bool:
        """Check if the tool is available (dependencies installed)."""
        if self._available is not None:
            return self._available
        
        # Auto-install dependencies if enabled
        if AUTO_INSTALL_ENABLED and self.dependencies:
            logger.info(f"🔍 Checking dependencies for {self.name}: {self.dependencies}")
            install_results = auto_install_dependencies(self.dependencies)
            
            # Log installation results
            for pkg, (success, error) in install_results.items():
                if success:
                    logger.info(f"✅ {pkg} is available")
                else:
                    logger.warning(f"⚠️ {pkg} installation failed: {error}")
        
        try:
            self._available = self._check_availability()
        except Exception as e:
            logger.warning(f"Tool {self.name} availability check failed: {e}")
            self._available = False
        
        return self._available
    
    @abstractmethod
    def _check_availability(self) -> bool:
        """Check if required dependencies are installed."""
        pass
    
    def initialize(self) -> ToolResult:
        """Initialize the tool. Called before first use."""
        if self._initialized:
            return ToolResult(success=True, metadata={'already_initialized': True})
        
        # Try to auto-install dependencies if not available
        if not self.is_available():
            # Try one more time with auto-install
            if AUTO_INSTALL_ENABLED and self.dependencies:
                logger.info(f"🔄 Attempting to install dependencies for {self.name}")
                install_results = auto_install_dependencies(self.dependencies)
                
                # Check again after installation attempt
                self._available = None  # Reset cache
                if not self.is_available():
                    failed_packages = [pkg for pkg, (success, _) in install_results.items() if not success]
                    return ToolResult(
                        success=False,
                        error=f"Tool {self.name} is not available. Failed to install: {failed_packages}. "
                              f"Some dependencies may require external software (R, MATLAB, Julia, SAS)."
                    )
            else:
                return ToolResult(
                    success=False,
                    error=f"Tool {self.name} is not available. Missing dependencies: {self.dependencies}"
                )
        
        try:
            result = self._initialize()
            if result.success:
                self._initialized = True
            return result
        except Exception as e:
            logger.error(f"Failed to initialize tool {self.name}: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _initialize(self) -> ToolResult:
        """Override to add custom initialization logic."""
        return ToolResult(success=True)
    
    @abstractmethod
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """
        Execute an operation using this tool.
        
        Args:
            operation: The operation to perform
            **kwargs: Operation-specific arguments
            
        Returns:
            ToolResult with the operation outcome
        """
        pass
    
    def get_info(self) -> ToolInfo:
        """Get information about this tool."""
        return ToolInfo(
            name=self.name,
            category=self.category,
            description=self.description,
            version=self.version,
            is_available=self.is_available(),
            requires_auth=self.requires_auth,
            dependencies=self.dependencies,
            capabilities=self.capabilities
        )
    
    def get_operations(self) -> List[Dict[str, Any]]:
        """Get list of available operations."""
        return []
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """
        Generate Python code for the operation.
        This code can be executed by the Tahlil agent.
        """
        return f"# No code generation available for {self.name}.{operation}"


class ToolRegistry:
    """
    Registry for managing tool providers.
    Singleton pattern to ensure single registry instance.
    """
    
    _instance = None
    _tools: Dict[str, ToolProvider] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tools = {}
        return cls._instance
    
    def register(self, provider_class: Type[ToolProvider], config: Optional[Dict] = None) -> bool:
        """Register a tool provider."""
        try:
            provider = provider_class(config)
            self._tools[provider.name] = provider
            logger.info(f"Registered tool: {provider.name} (available: {provider.is_available()})")
            return True
        except Exception as e:
            logger.error(f"Failed to register tool {provider_class}: {e}")
            return False
    
    def get(self, name: str) -> Optional[ToolProvider]:
        """Get a tool provider by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None, available_only: bool = False) -> List[ToolInfo]:
        """List all registered tools."""
        tools = []
        for provider in self._tools.values():
            if category and provider.category != category:
                continue
            if available_only and not provider.is_available():
                continue
            tools.append(provider.get_info())
        return tools
    
    def get_by_category(self, category: ToolCategory) -> List[ToolProvider]:
        """Get all tools in a category."""
        return [p for p in self._tools.values() if p.category == category]
    
    def initialize_all(self) -> Dict[str, ToolResult]:
        """Initialize all available tools."""
        results = {}
        for name, provider in self._tools.items():
            if provider.is_available():
                results[name] = provider.initialize()
        return results
    
    def execute(self, tool_name: str, operation: str, **kwargs) -> ToolResult:
        """Execute an operation on a specific tool."""
        provider = self.get(tool_name)
        if not provider:
            return ToolResult(success=False, error=f"Tool '{tool_name}' not found")
        
        if not provider.is_available():
            return ToolResult(success=False, error=f"Tool '{tool_name}' is not available")
        
        # Initialize if needed
        if not provider._initialized:
            init_result = provider.initialize()
            if not init_result.success:
                return init_result
        
        return provider.execute(operation, **kwargs)


# Global registry instance
tool_registry = ToolRegistry()


def register_default_tools():
    """Register all default tool providers."""
    try:
        from .statistics_tools import StatsmodelsProvider
        tool_registry.register(StatsmodelsProvider)
    except ImportError:
        logger.warning("StatsmodelsProvider not available")
    
    try:
        from .database_tools import SQLDatabaseProvider
        tool_registry.register(SQLDatabaseProvider)
    except ImportError:
        logger.warning("SQLDatabaseProvider not available")
    
    try:
        from .nlp_tools import SpacyProvider, HuggingFaceProvider
        tool_registry.register(SpacyProvider)
        tool_registry.register(HuggingFaceProvider)
    except ImportError:
        logger.warning("NLP providers not available")
    
    try:
        from .langchain_tools import LangChainProvider
        tool_registry.register(LangChainProvider)
    except ImportError:
        logger.warning("LangChainProvider not available")
    
    try:
        from .google_tools import GoogleSheetsProvider
        tool_registry.register(GoogleSheetsProvider)
    except ImportError:
        logger.warning("GoogleSheetsProvider not available")
    
    # Phase 2 tools
    try:
        from .r_tools import RProvider
        tool_registry.register(RProvider)
    except ImportError:
        logger.warning("RProvider not available")
    
    try:
        from .julia_tools import JuliaProvider
        tool_registry.register(JuliaProvider)
    except ImportError:
        logger.warning("JuliaProvider not available")
    
    try:
        from .file_format_tools import SPSSStataProvider
        tool_registry.register(SPSSStataProvider)
    except ImportError:
        logger.warning("SPSSStataProvider not available")
    
    logger.info(f"Registered {len(tool_registry._tools)} tools")
