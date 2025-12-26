"""
Tahlil Platform - Tool Integration System
Provides modular integrations for various data science and analytics tools.
"""

from .base import ToolProvider, ToolRegistry, ToolResult, ToolCategory
from .dependency_manager import dependency_manager, auto_install_dependencies, check_and_install
from .statistics_tools import StatsmodelsProvider
from .database_tools import SQLDatabaseProvider
from .nlp_tools import SpacyProvider, HuggingFaceProvider
from .langchain_tools import LangChainProvider
from .google_tools import GoogleSheetsProvider
from .r_tools import RProvider
from .julia_tools import JuliaProvider
from .file_format_tools import SPSSStataProvider

__all__ = [
    'ToolProvider',
    'ToolRegistry', 
    'ToolResult',
    'ToolCategory',
    'dependency_manager',
    'auto_install_dependencies',
    'check_and_install',
    'StatsmodelsProvider',
    'SQLDatabaseProvider',
    'SpacyProvider',
    'HuggingFaceProvider',
    'LangChainProvider',
    'GoogleSheetsProvider',
    'RProvider',
    'JuliaProvider',
    'SPSSStataProvider',
]
