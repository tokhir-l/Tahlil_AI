"""
KPI Calculation Helper Module for Tahlil Platform
Provides helper functions and prompts for calculating common business KPIs
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KPIInfo:
    """Information about a KPI."""
    name: str
    category: str
    formula: str
    description: str
    required_columns: List[str]

class KPICalculator:
    """Helper class for KPI calculations and guidance."""
    
    # KPI definitions organized by category
    KPI_DEFINITIONS = {
        'financial': [
            {
                'name': 'Gross Profit Margin',
                'formula': '(Revenue - COGS) / Revenue * 100',
                'description': 'Percentage of revenue remaining after direct costs',
                'required': ['Revenue', 'COGS']
            },
            {
                'name': 'Net Profit Margin',
                'formula': 'Net Profit / Revenue * 100',
                'description': 'Percentage of revenue remaining after all expenses',
                'required': ['Revenue', 'Net Profit']
            },
            {
                'name': 'Revenue Growth Rate',
                'formula': '(Current Revenue - Previous Revenue) / Previous Revenue * 100',
                'description': 'Percentage change in revenue over time',
                'required': ['Revenue', 'Date']
            },
            {
                'name': 'Cost Per Unit',
                'formula': 'Total Cost / Units Produced',
                'description': 'Average cost to produce one unit',
                'required': ['Total Cost', 'Units']
            },
        ],
        'operational': [
            {
                'name': 'Inventory Turnover',
                'formula': 'Cost of Goods Sold / Average Inventory',
                'description': 'How often inventory is sold and replaced',
                'required': ['COGS', 'Inventory']
            },
            {
                'name': 'On-Time Delivery Rate',
                'formula': 'On-Time Deliveries / Total Deliveries * 100',
                'description': 'Percentage of deliveries made on time',
                'required': ['Delivery Date', 'Promised Date']
            },
            {
                'name': 'Capacity Utilization Rate',
                'formula': 'Actual Output / Maximum Capacity * 100',
                'description': 'Percentage of production capacity used',
                'required': ['Actual Output', 'Capacity']
            },
        ],
        'customer': [
            {
                'name': 'Customer Lifetime Value (CLV)',
                'formula': 'Average Order Value * Purchase Frequency * Customer Lifespan',
                'description': 'Total value a customer brings over their lifetime',
                'required': ['Order Value', 'Purchase Frequency', 'Customer Age']
            },
            {
                'name': 'Customer Retention Rate',
                'formula': '(Customers at End - New Customers) / Customers at Start * 100',
                'description': 'Percentage of customers retained',
                'required': ['Customer ID', 'Date']
            },
            {
                'name': 'Customer Acquisition Cost (CAC)',
                'formula': 'Total Marketing Cost / New Customers Acquired',
                'description': 'Cost to acquire one new customer',
                'required': ['Marketing Cost', 'New Customers']
            },
        ],
        'marketing': [
            {
                'name': 'Return on Ad Spend (ROAS)',
                'formula': 'Revenue from Ads / Ad Spend',
                'description': 'Revenue generated per dollar spent on ads',
                'required': ['Ad Revenue', 'Ad Spend']
            },
            {
                'name': 'Cost Per Lead (CPL)',
                'formula': 'Total Marketing Cost / Number of Leads',
                'description': 'Cost to generate one lead',
                'required': ['Marketing Cost', 'Leads']
            },
            {
                'name': 'Conversion Rate',
                'formula': 'Conversions / Total Visitors * 100',
                'description': 'Percentage of visitors who convert',
                'required': ['Conversions', 'Visitors']
            },
        ],
        'project': [
            {
                'name': 'Budget Variance',
                'formula': 'Actual Cost - Budgeted Cost',
                'description': 'Difference between actual and budgeted costs',
                'required': ['Actual Cost', 'Budgeted Cost']
            },
            {
                'name': 'On-Time Completion Rate',
                'formula': 'Projects Completed On Time / Total Projects * 100',
                'description': 'Percentage of projects completed on schedule',
                'required': ['Completion Date', 'Planned Date']
            },
            {
                'name': 'Cost Overrun Percentage',
                'formula': '(Actual Cost - Budgeted Cost) / Budgeted Cost * 100',
                'description': 'Percentage by which costs exceed budget',
                'required': ['Actual Cost', 'Budgeted Cost']
            },
        ],
    }
    
    def detect_kpi_from_query(self, query: str) -> Optional[Dict]:
        """Detect which KPI the user is asking about."""
        query_lower = query.lower()
        
        # Search through all KPIs
        for category, kpis in self.KPI_DEFINITIONS.items():
            for kpi in kpis:
                kpi_name_lower = kpi['name'].lower()
                # Check if KPI name or key terms appear in query
                if kpi_name_lower in query_lower or any(term in query_lower for term in kpi['name'].split()):
                    return {
                        'kpi': kpi,
                        'category': category
                    }
        
        return None
    
    def generate_kpi_prompt(self, query: str, kpi_info: Optional[Dict] = None) -> str:
        """Generate a prompt to help calculate a KPI."""
        if not kpi_info:
            kpi_info = self.detect_kpi_from_query(query)
        
        if kpi_info:
            kpi = kpi_info['kpi']
            prompt = f"""Calculate the {kpi['name']} KPI.

Formula: {kpi['formula']}
Description: {kpi['description']}
Required columns: {', '.join(kpi['required'])}

Instructions:
1. Identify the required columns in the data (they may have different names)
2. Calculate the KPI using the formula
3. Print the result clearly with units (percentage, currency, etc.)
4. If calculating over time, show trends
5. If comparing periods, show the comparison clearly

If the required columns are not found, identify the closest matching columns and calculate using those.
"""
            return prompt
        
        # Generic KPI calculation prompt
        return """Calculate the requested KPI (Key Performance Indicator) from the data.

Instructions:
1. Identify what KPI is being requested
2. Determine the appropriate formula based on standard business metrics
3. Find the required data columns (they may have different names)
4. Calculate the KPI accurately
5. Present the result clearly with:
   - The calculated value
   - Units (percentage, currency, count, etc.)
   - Time period (if applicable)
   - Comparison to previous periods (if data available)
6. If multiple values are calculated, present them in a table
7. If trends are available, create a visualization

Common KPI categories:
- Financial: Profit margins, revenue growth, cost metrics
- Operational: Efficiency, utilization, cycle times
- Customer: Retention, acquisition cost, lifetime value
- Marketing: Conversion rates, ROI, cost per lead
- Project: Budget variance, completion rates, cost overruns
"""
    
    def get_kpi_suggestions(self, data_columns: List[str]) -> List[Dict]:
        """Suggest KPIs that can be calculated from available columns."""
        suggestions = []
        columns_lower = [col.lower() for col in data_columns]
        
        for category, kpis in self.KPI_DEFINITIONS.items():
            for kpi in kpis:
                # Check if we have columns that match required columns
                required_lower = [req.lower() for req in kpi['required']]
                matches = sum(1 for req in required_lower if any(req in col for col in columns_lower))
                
                if matches >= len(required_lower) * 0.5:  # At least 50% match
                    suggestions.append({
                        'kpi': kpi,
                        'category': category,
                        'match_score': matches / len(required_lower)
                    })
        
        # Sort by match score
        suggestions.sort(key=lambda x: x['match_score'], reverse=True)
        return suggestions[:10]  # Top 10 suggestions
