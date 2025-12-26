"""
Statistical Analysis Tools for Tahlil Platform.
Provides integration with statsmodels for advanced statistical analysis.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class StatsmodelsProvider(ToolProvider):
    """
    Integration with statsmodels for statistical analysis.
    Supports regression, time series, hypothesis testing, and more.
    """
    
    @property
    def name(self) -> str:
        return "statsmodels"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.STATISTICS
    
    @property
    def description(self) -> str:
        return "Advanced statistical analysis including regression, time series, and hypothesis testing"
    
    @property
    def dependencies(self) -> List[str]:
        return ["statsmodels", "pandas", "numpy"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "linear_regression",
            "logistic_regression",
            "ols_regression",
            "time_series_analysis",
            "arima_forecast",
            "hypothesis_testing",
            "anova",
            "correlation_analysis",
            "descriptive_statistics"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install statsmodels if needed
            from .dependency_manager import check_and_install
            success, _ = check_and_install('statsmodels', 'statsmodels')
            if not success:
                return False
            
            import statsmodels
            import pandas
            import numpy
            return True
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            import statsmodels.api as sm
            import statsmodels.formula.api as smf
            self._sm = sm
            self._smf = smf
            return ToolResult(success=True, metadata={'version': sm.__version__})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a statistical operation."""
        operations = {
            'linear_regression': self._linear_regression,
            'ols_regression': self._ols_regression,
            'logistic_regression': self._logistic_regression,
            'correlation': self._correlation_analysis,
            'descriptive_stats': self._descriptive_stats,
            'arima': self._arima_forecast,
            'hypothesis_test': self._hypothesis_test,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"statsmodels {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _linear_regression(self, X, y, **kwargs) -> ToolResult:
        """Perform linear regression."""
        import pandas as pd
        import numpy as np
        
        X = np.array(X)
        y = np.array(y)
        
        # Add constant for intercept
        X_with_const = self._sm.add_constant(X)
        model = self._sm.OLS(y, X_with_const)
        results = model.fit()
        
        return ToolResult(
            success=True,
            data={
                'coefficients': results.params.tolist(),
                'r_squared': results.rsquared,
                'adj_r_squared': results.rsquared_adj,
                'p_values': results.pvalues.tolist(),
                'summary': str(results.summary())
            },
            metadata={'n_observations': len(y)}
        )
    
    def _ols_regression(self, formula: str, data, **kwargs) -> ToolResult:
        """Perform OLS regression with formula interface."""
        import pandas as pd
        
        if isinstance(data, dict):
            data = pd.DataFrame(data)
        
        model = self._smf.ols(formula, data=data)
        results = model.fit()
        
        return ToolResult(
            success=True,
            data={
                'coefficients': results.params.to_dict(),
                'r_squared': results.rsquared,
                'adj_r_squared': results.rsquared_adj,
                'p_values': results.pvalues.to_dict(),
                'f_statistic': results.fvalue,
                'f_pvalue': results.f_pvalue,
                'summary': str(results.summary())
            }
        )
    
    def _logistic_regression(self, X, y, **kwargs) -> ToolResult:
        """Perform logistic regression."""
        import numpy as np
        
        X = np.array(X)
        y = np.array(y)
        
        X_with_const = self._sm.add_constant(X)
        model = self._sm.Logit(y, X_with_const)
        results = model.fit(disp=0)
        
        return ToolResult(
            success=True,
            data={
                'coefficients': results.params.tolist(),
                'p_values': results.pvalues.tolist(),
                'pseudo_r_squared': results.prsquared,
                'log_likelihood': results.llf,
                'summary': str(results.summary())
            }
        )
    
    def _correlation_analysis(self, data, method: str = 'pearson', **kwargs) -> ToolResult:
        """Perform correlation analysis."""
        import pandas as pd
        
        if isinstance(data, dict):
            data = pd.DataFrame(data)
        
        corr_matrix = data.corr(method=method)
        
        return ToolResult(
            success=True,
            data={
                'correlation_matrix': corr_matrix.to_dict(),
                'method': method
            }
        )
    
    def _descriptive_stats(self, data, **kwargs) -> ToolResult:
        """Calculate descriptive statistics."""
        import pandas as pd
        
        if isinstance(data, dict):
            data = pd.DataFrame(data)
        
        stats = data.describe()
        
        return ToolResult(
            success=True,
            data={
                'statistics': stats.to_dict(),
                'columns': list(data.columns)
            }
        )
    
    def _arima_forecast(self, data, order: tuple = (1, 1, 1), steps: int = 10, **kwargs) -> ToolResult:
        """Perform ARIMA time series forecasting."""
        from statsmodels.tsa.arima.model import ARIMA
        import numpy as np
        
        data = np.array(data)
        model = ARIMA(data, order=order)
        results = model.fit()
        
        forecast = results.forecast(steps=steps)
        
        return ToolResult(
            success=True,
            data={
                'forecast': forecast.tolist(),
                'order': order,
                'aic': results.aic,
                'bic': results.bic
            }
        )
    
    def _hypothesis_test(self, data1, data2=None, test_type: str = 'ttest', **kwargs) -> ToolResult:
        """Perform hypothesis testing."""
        from scipy import stats
        import numpy as np
        
        data1 = np.array(data1)
        
        if test_type == 'ttest':
            if data2 is not None:
                data2 = np.array(data2)
                stat, pvalue = stats.ttest_ind(data1, data2)
            else:
                stat, pvalue = stats.ttest_1samp(data1, kwargs.get('popmean', 0))
        elif test_type == 'shapiro':
            stat, pvalue = stats.shapiro(data1)
        elif test_type == 'kstest':
            stat, pvalue = stats.kstest(data1, kwargs.get('distribution', 'norm'))
        else:
            return ToolResult(success=False, error=f"Unknown test type: {test_type}")
        
        return ToolResult(
            success=True,
            data={
                'test_type': test_type,
                'statistic': stat,
                'p_value': pvalue,
                'significant': pvalue < kwargs.get('alpha', 0.05)
            }
        )
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for statistical operations."""
        code_templates = {
            'linear_regression': '''
import statsmodels.api as sm
import pandas as pd

# Load your data
data = pd.read_csv('your_data.csv')
X = data[{x_cols}]
y = data['{y_col}']

# Add constant and fit model
X = sm.add_constant(X)
model = sm.OLS(y, X)
results = model.fit()

print(results.summary())
''',
            'ols_regression': '''
import statsmodels.formula.api as smf
import pandas as pd

# Load your data
data = pd.read_csv('your_data.csv')

# Fit OLS model with formula
model = smf.ols('{formula}', data=data)
results = model.fit()

print(results.summary())
print(f"R-squared: {{results.rsquared:.4f}}")
''',
            'arima': '''
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd

# Load time series data
data = pd.read_csv('your_data.csv')
series = data['{column}']

# Fit ARIMA model
model = ARIMA(series, order={order})
results = model.fit()

# Forecast
forecast = results.forecast(steps={steps})
print(f"Forecast: {{forecast}}")
print(f"AIC: {{results.aic:.2f}}")
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'linear_regression',
                'description': 'Perform linear regression analysis',
                'params': ['X', 'y']
            },
            {
                'name': 'ols_regression',
                'description': 'OLS regression with formula interface',
                'params': ['formula', 'data']
            },
            {
                'name': 'logistic_regression',
                'description': 'Binary logistic regression',
                'params': ['X', 'y']
            },
            {
                'name': 'correlation',
                'description': 'Correlation analysis',
                'params': ['data', 'method']
            },
            {
                'name': 'descriptive_stats',
                'description': 'Descriptive statistics',
                'params': ['data']
            },
            {
                'name': 'arima',
                'description': 'ARIMA time series forecasting',
                'params': ['data', 'order', 'steps']
            },
            {
                'name': 'hypothesis_test',
                'description': 'Statistical hypothesis testing',
                'params': ['data1', 'data2', 'test_type']
            }
        ]
