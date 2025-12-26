"""
Automatic Dependency Manager for Tahlil Platform.
Installs Python packages on-demand when tools are accessed.
"""

import subprocess
import sys
import logging
import importlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyManager:
    """
    Manages automatic installation of tool dependencies.
    Installs packages via pip when tools are first accessed.
    """
    
    _instance = None
    _installed_packages: Dict[str, bool] = {}
    _installation_attempts: Dict[str, int] = {}
    _max_attempts = 1  # Only try once per package
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
    
    def check_and_install(self, package_name: str, import_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if a package is installed, and install it if not.
        
        Args:
            package_name: Name of the package for pip install
            import_name: Name used in import statement (if different from package_name)
            
        Returns:
            Tuple of (success, error_message)
        """
        import_name = import_name or package_name
        
        # Check if already installed
        if self._is_installed(import_name):
            return True, None
        
        # Check if we've already tried installing
        if package_name in self._installation_attempts:
            if self._installation_attempts[package_name] >= self._max_attempts:
                return False, f"Package {package_name} installation failed previously"
        
        # Try to install
        logger.info(f"📦 Auto-installing package: {package_name}")
        success, error = self._install_package(package_name)
        
        if success:
            # Give it a moment for package to be available
            import time
            time.sleep(0.5)
            
            # Verify installation
            if self._is_installed(import_name):
                self._installed_packages[package_name] = True
                logger.info(f"✅ Successfully installed {package_name}")
                return True, None
            else:
                # Try alternative import names
                alt_names = [package_name.split('.')[0], package_name.replace('-', '_')]
                for alt_name in alt_names:
                    if self._is_installed(alt_name):
                        self._installed_packages[package_name] = True
                        logger.info(f"✅ Successfully installed {package_name} (imported as {alt_name})")
                        return True, None
                
                logger.warning(f"⚠️ {package_name} installed but import failed (tried: {import_name}, {alt_names})")
                return False, f"Package installed but import failed. Try: import {import_name}"
        else:
            self._installation_attempts[package_name] = self._installation_attempts.get(package_name, 0) + 1
            return False, error
    
    def _is_installed(self, package_name: str) -> bool:
        """Check if a package can be imported."""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False
    
    def _install_package(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """Install a package using pip."""
        try:
            # Use subprocess to run pip install
            # Use --quiet to reduce output, --user to install in user space
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name, "--quiet", "--user"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return True, None
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Failed to install {package_name}: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, "Installation timeout (exceeded 5 minutes)"
        except Exception as e:
            logger.error(f"Exception installing {package_name}: {e}")
            return False, str(e)
    
    def install_multiple(self, packages: List[str]) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Install multiple packages and return results for each."""
        results = {}
        for package in packages:
            results[package] = self.check_and_install(package)
        return results
    
    def check_external_software(self, software_name: str, check_command: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if external software (not Python packages) is installed.
        
        Args:
            software_name: Name of the software
            check_command: Command to run to check if software exists
            
        Returns:
            Tuple of (is_installed, error_message)
        """
        try:
            result = subprocess.run(
                check_command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, None
            else:
                return False, f"{software_name} not found. Please install it separately."
                
        except FileNotFoundError:
            return False, f"{software_name} not found. Please install it separately."
        except Exception as e:
            return False, str(e)


# Global instance
dependency_manager = DependencyManager()


# Package name mappings (pip package name -> import name)
PACKAGE_MAPPINGS = {
    'rpy2': 'rpy2',
    'julia': 'julia',
    'pyreadstat': 'pyreadstat',
    'statsmodels': 'statsmodels',
    'sqlalchemy': 'sqlalchemy',
    'spacy': 'spacy',
    'transformers': 'transformers',
    'torch': 'torch',
    'langchain': 'langchain',
    'gspread': 'gspread',
    'google-auth': 'google.auth',
    'google-api-python-client': 'googleapiclient',
    'pyarrow': 'pyarrow',
    'xlrd': 'xlrd',
}


def auto_install_dependencies(package_names: List[str]) -> Dict[str, Tuple[bool, Optional[str]]]:
    """
    Automatically install dependencies for a tool.
    
    Args:
        package_names: List of pip package names to install
        
    Returns:
        Dictionary mapping package names to (success, error) tuples
    """
    results = {}
    for package in package_names:
        import_name = PACKAGE_MAPPINGS.get(package, package.split('.')[0])
        success, error = dependency_manager.check_and_install(package, import_name)
        results[package] = (success, error)
    return results


def check_external_software(software_name: str, check_command: List[str]) -> Tuple[bool, Optional[str]]:
    """Check if external software is installed."""
    return dependency_manager.check_external_software(software_name, check_command)


def check_and_install(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check and install a single package.
    
    Args:
        package_name: Name of the package for pip install
        import_name: Name used in import statement (if different from package_name)
        
    Returns:
        Tuple of (success, error_message)
    """
    return dependency_manager.check_and_install(package_name, import_name)
