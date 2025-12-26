# Automatic Dependency Installation Feature

## Overview

The Tahlil Platform now includes **automatic dependency installation** - users no longer need to manually install Python packages. When a tool is accessed for the first time, the platform automatically checks for required dependencies and installs them if missing.

## How It Works

### Automatic Installation Flow

1. **User accesses a tool** via API endpoint (e.g., `/api/tools/statsmodels/execute`)
2. **Platform checks availability** - `is_available()` method is called
3. **Dependency manager checks** if Python packages are installed
4. **Auto-installs missing packages** using `pip install --user --quiet`
5. **Verifies installation** by attempting to import the package
6. **Tool becomes available** if all dependencies are satisfied

### Example Flow

```python
# User makes API call
POST /api/tools/r/execute
{
    "operation": "regression",
    "params": {...}
}

# Behind the scenes:
1. Tool checks: Is rpy2 installed? → No
2. Auto-install: pip install rpy2 --user --quiet
3. Verify: Can import rpy2? → Yes
4. Check: Is R software installed? → Yes (external check)
5. Tool available: ✅ Ready to use
```

## Features

### ✅ What Gets Auto-Installed

**Python Packages (via pip):**
- `statsmodels` - Statistical analysis
- `sqlalchemy` - Database connectivity
- `spacy` - NLP processing
- `transformers` - Hugging Face models
- `torch` - PyTorch for ML
- `langchain` - AI workflows
- `gspread` - Google Sheets
- `google-auth` - Google authentication
- `rpy2` - R integration bridge
- `julia` - Julia bridge
- `pyreadstat` - SPSS/Stata file reading

### ⚠️ What Requires Manual Installation

**External Software (cannot be auto-installed):**
- **R** - Must be installed separately: https://www.r-project.org/ (Free)
- **Julia** - Must be installed separately: https://julialang.org/ (Free)

The platform will detect if these are missing and provide helpful error messages.

## Implementation Details

### Dependency Manager

Located in `tools/dependency_manager.py`:

```python
from tools.dependency_manager import dependency_manager, auto_install_dependencies

# Auto-install multiple packages
results = auto_install_dependencies(['statsmodels', 'pandas'])

# Check and install single package
success, error = check_and_install('rpy2', 'rpy2')
```

### Tool Integration

All tools automatically use the dependency manager:

```python
class StatsmodelsProvider(ToolProvider):
    def _check_availability(self) -> bool:
        # Auto-install if needed
        from .dependency_manager import check_and_install
        success, _ = check_and_install('statsmodels', 'statsmodels')
        if not success:
            return False
        
        import statsmodels
        return True
```

### Installation Settings

- **Installation location:** User space (`--user` flag)
- **Output:** Quiet mode (`--quiet` flag)
- **Timeout:** 5 minutes per package
- **Retry:** Only attempts once per package (prevents loops)

## User Experience

### Before (Manual Installation)

```bash
# User had to run:
pip install statsmodels sqlalchemy spacy transformers torch langchain gspread rpy2 matlab.engine julia splunk-sdk saspy pyreadstat

# Then configure each tool separately
```

### After (Automatic)

```python
# User just uses the tool - installation happens automatically
POST /api/tools/statsmodels/execute
{
    "operation": "linear_regression",
    "params": {...}
}

# First time: Package installs automatically
# Subsequent times: Uses cached installation
```

## Error Handling

### Package Installation Fails

If a package fails to install:
- Error is logged
- Tool reports as unavailable
- User receives clear error message
- Platform continues to work with other tools

### External Software Missing

For tools requiring external software (R, MATLAB, Julia, SAS):
- Python bridge packages install automatically
- External software check fails gracefully
- Clear message: "R is not installed. Please install it separately."

### Network Issues

If pip installation fails due to network:
- Timeout after 5 minutes
- Error logged
- Tool remains unavailable
- User can retry later

## Performance Considerations

### First Access

- **First tool access:** May take 30-60 seconds (installation time)
- **Subsequent accesses:** Instant (package already installed)
- **Installation is cached:** Only installs once per package

### Installation Time Estimates

- Small packages (statsmodels, sqlalchemy): 5-15 seconds
- Medium packages (spacy, transformers): 30-60 seconds
- Large packages (torch): 2-5 minutes

### Optimization

- Packages installed in user space (no admin required)
- Quiet mode reduces output
- Single attempt per package (no retry loops)
- Installation happens in background

## Security Considerations

### Safe Installation

- **User space only:** `--user` flag prevents system-wide changes
- **No admin required:** Works without sudo/administrator
- **Isolated:** Each package installs independently
- **Verified:** Imports verified after installation

### Package Sources

- Uses standard PyPI (Python Package Index)
- No custom repositories
- Standard pip security applies

## Configuration

### Disable Auto-Install (if needed)

To disable auto-installation, modify `tools/base.py`:

```python
AUTO_INSTALL_ENABLED = False  # Disable auto-install
```

### Custom Installation

For custom package sources or configurations, modify `dependency_manager.py`:

```python
# In _install_package method
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", package_name, 
     "--quiet", "--user", "--index-url", "custom-url"],
    ...
)
```

## Monitoring

### Log Messages

The platform logs all installation attempts:

```
INFO: 🔍 Checking dependencies for statsmodels: ['statsmodels', 'pandas', 'numpy']
INFO: 📦 Auto-installing package: statsmodels
INFO: ✅ Successfully installed statsmodels
INFO: ✅ statsmodels is available
```

### Error Logs

Failed installations are logged:

```
WARNING: ⚠️ rpy2 installation failed: [error message]
WARNING: R is not installed: R not found. Please install it separately.
```

## Testing

### Verify Auto-Installation

```python
# Test dependency manager
from tools.dependency_manager import check_and_install

success, error = check_and_install('tabulate', 'tabulate')
print(f"Installation: {'Success' if success else f'Failed: {error}'}")
```

### Test Tool Availability

```python
# Check if tool auto-installs dependencies
from tools.base import tool_registry, register_default_tools

register_default_tools()
tool = tool_registry.get('statsmodels')
print(f"Available: {tool.is_available()}")  # Auto-installs if needed
```

## Troubleshooting

### Package Won't Install

**Issue:** Package installation fails repeatedly

**Solutions:**
1. Check network connection
2. Verify pip is working: `python -m pip --version`
3. Check disk space
4. Review error logs for specific issues

### External Software Not Detected

**Issue:** R/MATLAB/Julia not found

**Solutions:**
1. Install the external software
2. Ensure it's in system PATH
3. Restart the platform after installation

### Installation Timeout

**Issue:** Large packages (like torch) timeout

**Solutions:**
1. Increase timeout in `dependency_manager.py`
2. Pre-install large packages manually
3. Use smaller package variants if available

## Best Practices

### For Platform Administrators

1. **Pre-install common packages** in production for faster startup
2. **Monitor installation logs** for failed packages
3. **Set up package caching** if using private repositories
4. **Document external software requirements** clearly

### For Users

1. **First access may be slower** - be patient during first tool use
2. **Check tool availability** before use: `GET /api/tools/list?available_only=true`
3. **Install external software** (R, MATLAB, etc.) if needed
4. **Report issues** if auto-installation fails

## Future Enhancements

### Planned Features

- **Parallel installation** - Install multiple packages simultaneously
- **Progress reporting** - Show installation progress to users
- **Package versioning** - Specify exact package versions
- **Offline mode** - Use cached packages when offline
- **Installation queue** - Queue installations for better resource management

## Summary

✅ **Automatic dependency installation** eliminates the need for users to manually install Python packages  
✅ **Seamless experience** - tools work immediately when accessed  
✅ **Safe and secure** - installs in user space, no admin required  
✅ **Smart error handling** - clear messages for missing external software  
✅ **Performance optimized** - caches installations, only installs once  

**Users can now use any tool without manual installation!** 🎉

---

*Auto-Install Feature - December 2025*  
*Tahlil Platform*
