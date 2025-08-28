#!/usr/bin/env python3
"""
EPOCH5 ROI Calculator

This script calculates the potential Return on Investment (ROI) for
implementing EPOCH5 Autonomous System.
"""

import argparse
import json
import os
import sys
import datetime
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("roi_calculator.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EPOCH5ROICalculator:
    """Calculates ROI for EPOCH5 Autonomous System"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the ROI calculator"""
        # Set default config path if not provided
        if not config_path:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roi_data.json")
        
        # Load ROI calculation data from config file if it exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.roi_data = json.load(f)
        else:
            # Use built-in default ROI data
            self.roi_data = self._get_default_roi_data()
            
        # Initialize output directory
        self.output_dir = Path("./roi_analyses")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("EPOCH5 ROI Calculator initialized")
    
    def _get_default_roi_data(self) -> Dict[str, Any]:
        """Get default ROI calculation data"""
        return {
            "labor_cost_savings": {
                "operations_staff_hourly": 75,
                "developer_hourly": 120,
                "executive_hourly": 200,
                "annual_hours": 2080,
                "productivity_improvement": {
                    "year_1": 0.20,
                    "year_2": 0.35,
                    "year_3": 0.45
                }
            },
            "incident_reduction": {
                "minor_incident": {
                    "cost": 5000,
                    "reduction": {
                        "year_1": 0.30,
                        "year_2": 0.50,
                        "year_3": 0.70
                    }
                },
                "major_incident": {
                    "cost": 50000,
                    "reduction": {
                        "year_1": 0.20,
                        "year_2": 0.40,
                        "year_3": 0.60
                    }
                },
                "critical_incident": {
                    "cost": 500000,
                    "reduction": {
                        "year_1": 0.10,
                        "year_2": 0.30,
                        "year_3": 0.50
                    }
                }
            },
            "downtime_reduction": {
                "hourly_cost": 10000,
                "reduction": {
                    "year_1": 0.15,
                    "year_2": 0.30,
                    "year_3": 0.45
                }
            },
            "scaling_efficiency": {
                "infrastructure_savings": {
                    "year_1": 0.10,
                    "year_2": 0.20,
                    "year_3": 0.30
                }
            },
            "compliance_improvement": {
                "audit_cost_reduction": {
                    "year_1": 0.15,
                    "year_2": 0.30,
                    "year_3": 0.40
                },
                "penalty_reduction": {
                    "year_1": 0.20,
                    "year_2": 0.40,
                    "year_3": 0.60
                }
            },
            "standard_metrics": {
                "discount_rate": 0.10,
                "inflation_rate": 0.025
            }
        }
    
    def calculate_labor_savings(self, 
                               ops_staff_count: int,
                               dev_staff_count: int,
                               exec_staff_count: int,
                               years: int = 3) -> Dict[str, Any]:
        """
        Calculate labor cost savings over time
        
        Args:
            ops_staff_count: Number of operations staff affected
            dev_staff_count: Number of developers affected
            exec_staff_count: Number of executives affected
            years: Number of years for ROI calculation
            
        Returns:
            Dictionary with labor savings details
        """
        labor_data = self.roi_data["labor_cost_savings"]
        annual_hours = labor_data["annual_hours"]
        
        # Calculate base annual labor costs
        ops_annual_cost = ops_staff_count * labor_data["operations_staff_hourly"] * annual_hours
        dev_annual_cost = dev_staff_count * labor_data["developer_hourly"] * annual_hours
        exec_annual_cost = exec_staff_count * labor_data["executive_hourly"] * annual_hours
        total_annual_labor_cost = ops_annual_cost + dev_annual_cost + exec_annual_cost
        
        # Calculate savings for each year
        yearly_savings = []
        cumulative_savings = 0
        
        for year in range(1, years + 1):
            year_key = f"year_{year}"
            
            # Use provided improvement rate or default to last known year if beyond data
            if year_key in labor_data["productivity_improvement"]:
                improvement_rate = labor_data["productivity_improvement"][year_key]
            else:
                # Use the last available year's data
                last_year = max([int(k.split('_')[1]) for k in labor_data["productivity_improvement"].keys()])
                improvement_rate = labor_data["productivity_improvement"][f"year_{last_year}"]
            
            # Calculate savings for this year
            year_savings = total_annual_labor_cost * improvement_rate
            cumulative_savings += year_savings
            
            yearly_savings.append({
                "year": year,
                "improvement_rate": improvement_rate,
                "savings": year_savings,
                "cumulative_savings": cumulative_savings
            })
        
        return {
            "staff_counts": {
                "operations": ops_staff_count,
                "developers": dev_staff_count,
                "executives": exec_staff_count
            },
            "annual_costs": {
                "operations": ops_annual_cost,
                "developers": dev_annual_cost,
                "executives": exec_annual_cost,
                "total": total_annual_labor_cost
            },
            "yearly_savings": yearly_savings,
            "total_savings": cumulative_savings
        }
    
    def calculate_incident_savings(self,
                                 minor_incidents_per_year: int,
                                 major_incidents_per_year: int,
                                 critical_incidents_per_year: int,
                                 years: int = 3) -> Dict[str, Any]:
        """
        Calculate incident reduction savings
        
        Args:
            minor_incidents_per_year: Number of minor incidents per year
            major_incidents_per_year: Number of major incidents per year
            critical_incidents_per_year: Number of critical incidents per year
            years: Number of years for ROI calculation
            
        Returns:
            Dictionary with incident savings details
        """
        incident_data = self.roi_data["incident_reduction"]
        
        # Calculate base annual incident costs
        minor_annual_cost = minor_incidents_per_year * incident_data["minor_incident"]["cost"]
        major_annual_cost = major_incidents_per_year * incident_data["major_incident"]["cost"]
        critical_annual_cost = critical_incidents_per_year * incident_data["critical_incident"]["cost"]
        total_annual_incident_cost = minor_annual_cost + major_annual_cost + critical_annual_cost
        
        # Calculate savings for each year
        yearly_savings = []
        cumulative_savings = 0
        
        for year in range(1, years + 1):
            year_key = f"year_{year}"
            
            # Get reduction rates for each incident type (or use last known year if beyond data)
            minor_reduction = self._get_reduction_rate(incident_data["minor_incident"]["reduction"], year)
            major_reduction = self._get_reduction_rate(incident_data["major_incident"]["reduction"], year)
            critical_reduction = self._get_reduction_rate(incident_data["critical_incident"]["reduction"], year)
            
            # Calculate savings for this year
            minor_savings = minor_annual_cost * minor_reduction
            major_savings = major_annual_cost * major_reduction
            critical_savings = critical_annual_cost * critical_reduction
            year_savings = minor_savings + major_savings + critical_savings
            cumulative_savings += year_savings
            
            yearly_savings.append({
                "year": year,
                "minor_reduction": minor_reduction,
                "major_reduction": major_reduction,
                "critical_reduction": critical_reduction,
                "minor_savings": minor_savings,
                "major_savings": major_savings,
                "critical_savings": critical_savings,
                "total_savings": year_savings,
                "cumulative_savings": cumulative_savings
            })
        
        return {
            "incident_counts": {
                "minor": minor_incidents_per_year,
                "major": major_incidents_per_year,
                "critical": critical_incidents_per_year
            },
            "annual_costs": {
                "minor": minor_annual_cost,
                "major": major_annual_cost,
                "critical": critical_annual_cost,
                "total": total_annual_incident_cost
            },
            "yearly_savings": yearly_savings,
            "total_savings": cumulative_savings
        }
    
    def calculate_downtime_savings(self,
                                 current_downtime_hours: float,
                                 hourly_cost: Optional[float] = None,
                                 years: int = 3) -> Dict[str, Any]:
        """
        Calculate downtime reduction savings
        
        Args:
            current_downtime_hours: Current annual downtime in hours
            hourly_cost: Cost per hour of downtime (uses default if None)
            years: Number of years for ROI calculation
            
        Returns:
            Dictionary with downtime savings details
        """
        downtime_data = self.roi_data["downtime_reduction"]
        
        # Use provided hourly cost or default
        if hourly_cost is None:
            hourly_cost = downtime_data["hourly_cost"]
        
        # Calculate base annual downtime cost
        annual_downtime_cost = current_downtime_hours * hourly_cost
        
        # Calculate savings for each year
        yearly_savings = []
        cumulative_savings = 0
        
        for year in range(1, years + 1):
            # Get reduction rate for this year
            reduction_rate = self._get_reduction_rate(downtime_data["reduction"], year)
            
            # Calculate savings for this year
            reduced_hours = current_downtime_hours * reduction_rate
            year_savings = reduced_hours * hourly_cost
            cumulative_savings += year_savings
            
            yearly_savings.append({
                "year": year,
                "reduction_rate": reduction_rate,
                "reduced_hours": reduced_hours,
                "savings": year_savings,
                "cumulative_savings": cumulative_savings
            })
        
        return {
            "current_downtime": {
                "hours": current_downtime_hours,
                "hourly_cost": hourly_cost,
                "annual_cost": annual_downtime_cost
            },
            "yearly_savings": yearly_savings,
            "total_savings": cumulative_savings
        }
    
    def calculate_infrastructure_savings(self,
                                       annual_infrastructure_cost: float,
                                       years: int = 3) -> Dict[str, Any]:
        """
        Calculate infrastructure scaling efficiency savings
        
        Args:
            annual_infrastructure_cost: Current annual infrastructure cost
            years: Number of years for ROI calculation
            
        Returns:
            Dictionary with infrastructure savings details
        """
        scaling_data = self.roi_data["scaling_efficiency"]
        
        # Calculate savings for each year
        yearly_savings = []
        cumulative_savings = 0
        
        for year in range(1, years + 1):
            # Get savings rate for this year
            savings_rate = self._get_reduction_rate(scaling_data["infrastructure_savings"], year)
            
            # Calculate savings for this year
            year_savings = annual_infrastructure_cost * savings_rate
            cumulative_savings += year_savings
            
            yearly_savings.append({
                "year": year,
                "savings_rate": savings_rate,
                "savings": year_savings,
                "cumulative_savings": cumulative_savings
            })
        
        return {
            "annual_infrastructure_cost": annual_infrastructure_cost,
            "yearly_savings": yearly_savings,
            "total_savings": cumulative_savings
        }
    
    def calculate_compliance_savings(self,
                                   annual_audit_cost: float,
                                   annual_penalty_risk: float,
                                   years: int = 3) -> Dict[str, Any]:
        """
        Calculate compliance improvement savings
        
        Args:
            annual_audit_cost: Current annual compliance audit cost
            annual_penalty_risk: Annual financial risk from compliance penalties
            years: Number of years for ROI calculation
            
        Returns:
            Dictionary with compliance savings details
        """
        compliance_data = self.roi_data["compliance_improvement"]
        
        # Calculate savings for each year
        yearly_savings = []
        cumulative_savings = 0
        
        for year in range(1, years + 1):
            # Get reduction rates for this year
            audit_reduction = self._get_reduction_rate(compliance_data["audit_cost_reduction"], year)
            penalty_reduction = self._get_reduction_rate(compliance_data["penalty_reduction"], year)
            
            # Calculate savings for this year
            audit_savings = annual_audit_cost * audit_reduction
            penalty_savings = annual_penalty_risk * penalty_reduction
            year_savings = audit_savings + penalty_savings
            cumulative_savings += year_savings
            
            yearly_savings.append({
                "year": year,
                "audit_reduction": audit_reduction,
                "penalty_reduction": penalty_reduction,
                "audit_savings": audit_savings,
                "penalty_savings": penalty_savings,
                "total_savings": year_savings,
                "cumulative_savings": cumulative_savings
            })
        
        return {
            "annual_costs": {
                "audit": annual_audit_cost,
                "penalty_risk": annual_penalty_risk,
                "total": annual_audit_cost + annual_penalty_risk
            },
            "yearly_savings": yearly_savings,
            "total_savings": cumulative_savings
        }
    
    def calculate_roi(self,
                    implementation_cost: float,
                    annual_subscription_cost: float,
                    labor_savings: Dict[str, Any],
                    incident_savings: Dict[str, Any],
                    downtime_savings: Dict[str, Any],
                    infrastructure_savings: Dict[str, Any],
                    compliance_savings: Dict[str, Any],
                    years: int = 3) -> Dict[str, Any]:
        """
        Calculate overall ROI based on costs and savings
        
        Args:
            implementation_cost: One-time implementation cost
            annual_subscription_cost: Annual subscription cost
            labor_savings: Labor savings calculation results
            incident_savings: Incident savings calculation results
            downtime_savings: Downtime savings calculation results
            infrastructure_savings: Infrastructure savings calculation results
            compliance_savings: Compliance savings calculation results
            years: Number of years for ROI calculation
            
        Returns:
            Dictionary with ROI analysis
        """
        # Get standard metrics
        discount_rate = self.roi_data["standard_metrics"]["discount_rate"]
        inflation_rate = self.roi_data["standard_metrics"]["inflation_rate"]
        
        # Initialize lists for yearly calculations
        yearly_analysis = []
        cumulative_costs = implementation_cost
        cumulative_benefits = 0
        cumulative_net = -implementation_cost
        
        # Calculate cash flows for each year
        cash_flows = [-implementation_cost]  # Initial investment is negative cash flow
        
        for year in range(1, years + 1):
            # Calculate costs for this year (adjusted for inflation)
            year_subscription_cost = annual_subscription_cost * (1 + inflation_rate) ** (year - 1)
            year_costs = year_subscription_cost
            cumulative_costs += year_costs
            
            # Get benefits for this year
            year_labor_savings = labor_savings["yearly_savings"][year - 1]["savings"]
            year_incident_savings = incident_savings["yearly_savings"][year - 1]["total_savings"]
            year_downtime_savings = downtime_savings["yearly_savings"][year - 1]["savings"]
            year_infrastructure_savings = infrastructure_savings["yearly_savings"][year - 1]["savings"]
            year_compliance_savings = compliance_savings["yearly_savings"][year - 1]["total_savings"]
            
            # Calculate total benefits for this year
            year_benefits = (
                year_labor_savings +
                year_incident_savings +
                year_downtime_savings +
                year_infrastructure_savings +
                year_compliance_savings
            )
            cumulative_benefits += year_benefits
            
            # Calculate net for this year
            year_net = year_benefits - year_costs
            cumulative_net += year_net
            
            # Add to cash flows for NPV calculation
            cash_flows.append(year_net)
            
            # Add to yearly analysis
            yearly_analysis.append({
                "year": year,
                "costs": {
                    "subscription": year_subscription_cost,
                    "total": year_costs
                },
                "benefits": {
                    "labor": year_labor_savings,
                    "incident": year_incident_savings,
                    "downtime": year_downtime_savings,
                    "infrastructure": year_infrastructure_savings,
                    "compliance": year_compliance_savings,
                    "total": year_benefits
                },
                "net": year_net,
                "cumulative_costs": cumulative_costs,
                "cumulative_benefits": cumulative_benefits,
                "cumulative_net": cumulative_net
            })
        
        # Calculate NPV
        npv = self._calculate_npv(cash_flows, discount_rate)
        
        # Calculate payback period
        payback_period = self._calculate_payback_period(cash_flows)
        
        # Calculate ROI
        roi = (cumulative_benefits - cumulative_costs) / cumulative_costs * 100
        
        # Calculate benefit-cost ratio
        bcr = cumulative_benefits / cumulative_costs
        
        return {
            "initial_investment": implementation_cost,
            "annual_subscription": annual_subscription_cost,
            "years": years,
            "yearly_analysis": yearly_analysis,
            "summary": {
                "total_costs": cumulative_costs,
                "total_benefits": cumulative_benefits,
                "net_benefit": cumulative_net,
                "roi_percentage": roi,
                "npv": npv,
                "payback_period": payback_period,
                "benefit_cost_ratio": bcr
            }
        }
    
    def generate_roi_report(self, roi_analysis: Dict[str, Any], customer_name: str, format: str = "md") -> str:
        """
        Generate ROI report in specified format
        
        Args:
            roi_analysis: ROI analysis data
            customer_name: Name of the customer
            format: Output format (json, md, html, csv)
            
        Returns:
            Path to generated document
        """
        if format not in ["json", "md", "html", "csv"]:
            raise ValueError(f"Invalid format: {format}. Must be one of ['json', 'md', 'html', 'csv']")
        
        # Create filename
        sanitized_customer = customer_name.replace(" ", "_").lower()
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"roi_analysis_{sanitized_customer}_{date_str}.{format}"
        output_path = self.output_dir / filename
        
        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(roi_analysis, f, indent=2)
        elif format == "md":
            markdown = self._roi_to_markdown(roi_analysis, customer_name)
            with open(output_path, 'w') as f:
                f.write(markdown)
        elif format == "html":
            html = self._roi_to_html(roi_analysis, customer_name)
            with open(output_path, 'w') as f:
                f.write(html)
        elif format == "csv":
            self._roi_to_csv(roi_analysis, customer_name, output_path)
        
        logger.info(f"Generated ROI report: {output_path}")
        return str(output_path)
    
    def _get_reduction_rate(self, reduction_data: Dict[str, float], year: int) -> float:
        """Helper method to get reduction rate for specific year"""
        year_key = f"year_{year}"
        
        if year_key in reduction_data:
            return reduction_data[year_key]
        else:
            # Use the last available year's data
            last_year = max([int(k.split('_')[1]) for k in reduction_data.keys()])
            return reduction_data[f"year_{last_year}"]
    
    def _calculate_npv(self, cash_flows: List[float], discount_rate: float) -> float:
        """Calculate Net Present Value"""
        npv = 0
        for i, cf in enumerate(cash_flows):
            npv += cf / (1 + discount_rate) ** i
        return npv
    
    def _calculate_payback_period(self, cash_flows: List[float]) -> float:
        """Calculate payback period in years"""
        cumulative = 0
        for i, cf in enumerate(cash_flows):
            cumulative += cf
            if cumulative >= 0:
                # If we just reached positive, calculate partial year
                if i > 0 and cumulative - cf < 0:
                    # Interpolate to find partial year
                    prev_cumulative = cumulative - cf
                    fraction = abs(prev_cumulative) / abs(cf)
                    return i - 1 + fraction
                return i
        
        # If we never reach positive cash flow
        return float('inf')
    
    def _roi_to_markdown(self, roi: Dict[str, Any], customer_name: str) -> str:
        """Convert ROI analysis to markdown format"""
        md = f"# EPOCH5 ROI Analysis for {customer_name}\n\n"
        md += f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Executive Summary
        md += f"## Executive Summary\n\n"
        summary = roi["summary"]
        md += f"Based on our analysis, implementing EPOCH5 Autonomous System for {customer_name} is projected to deliver:\n\n"
        md += f"- **Total Investment:** ${roi['initial_investment']:,.2f} implementation + ${roi['annual_subscription']:,.2f} annual subscription\n"
        md += f"- **Total Benefits (over {roi['years']} years):** ${summary['total_benefits']:,.2f}\n"
        md += f"- **Net Benefit:** ${summary['net_benefit']:,.2f}\n"
        md += f"- **Return on Investment:** {summary['roi_percentage']:.2f}%\n"
        md += f"- **Payback Period:** {summary['payback_period']:.2f} years\n"
        md += f"- **Benefit-Cost Ratio:** {summary['benefit_cost_ratio']:.2f}\n\n"
        
        # Year-by-year Analysis
        md += f"## Year-by-Year Analysis\n\n"
        
        md += f"| Year | Total Costs | Total Benefits | Net Benefit | Cumulative Net |\n"
        md += f"|------|-------------|----------------|-------------|---------------|\n"
        
        for year_data in roi["yearly_analysis"]:
            year = year_data["year"]
            costs = year_data["costs"]["total"]
            benefits = year_data["benefits"]["total"]
            net = year_data["net"]
            cumulative = year_data["cumulative_net"]
            
            md += f"| {year} | ${costs:,.2f} | ${benefits:,.2f} | ${net:,.2f} | ${cumulative:,.2f} |\n"
        
        # Detailed Benefits Breakdown
        md += f"\n## Detailed Benefits Breakdown\n\n"
        
        md += f"| Year | Labor Savings | Incident Savings | Downtime Savings | Infrastructure Savings | Compliance Savings | Total Benefits |\n"
        md += f"|------|---------------|------------------|------------------|-----------------------|--------------------|-----------------|\n"
        
        for year_data in roi["yearly_analysis"]:
            year = year_data["year"]
            labor = year_data["benefits"]["labor"]
            incident = year_data["benefits"]["incident"]
            downtime = year_data["benefits"]["downtime"]
            infrastructure = year_data["benefits"]["infrastructure"]
            compliance = year_data["benefits"]["compliance"]
            total = year_data["benefits"]["total"]
            
            md += f"| {year} | ${labor:,.2f} | ${incident:,.2f} | ${downtime:,.2f} | ${infrastructure:,.2f} | ${compliance:,.2f} | ${total:,.2f} |\n"
        
        # Methodology and Assumptions
        md += f"\n## Methodology and Assumptions\n\n"
        md += f"This ROI analysis is based on the following key assumptions:\n\n"
        md += f"- **Discount Rate:** {self.roi_data['standard_metrics']['discount_rate'] * 100:.1f}%\n"
        md += f"- **Inflation Rate:** {self.roi_data['standard_metrics']['inflation_rate'] * 100:.1f}%\n"
        md += f"- Implementation costs are incurred upfront at the beginning of Year 0\n"
        md += f"- Subscription costs are paid annually at the beginning of each year\n"
        md += f"- Benefits accrue continuously throughout each year\n\n"
        
        md += f"This analysis takes into account productivity improvements, incident reduction, downtime reduction, "
        md += f"infrastructure optimization, and compliance benefits based on industry benchmarks and client-specific data.\n\n"
        
        # Conclusion
        md += f"## Conclusion\n\n"
        md += f"The projected ROI indicates that EPOCH5 Autonomous System is a sound investment for {customer_name}. "
        
        if summary["payback_period"] <= 1:
            md += f"With a payback period of less than a year, the solution quickly generates positive returns. "
        elif summary["payback_period"] <= 2:
            md += f"With a payback period of {summary['payback_period']:.2f} years, the solution generates positive returns in a reasonable timeframe. "
        else:
            md += f"While the payback period of {summary['payback_period']:.2f} years indicates a longer-term investment, "
            md += f"the substantial ROI of {summary['roi_percentage']:.2f}% over {roi['years']} years demonstrates significant long-term value. "
        
        md += f"The benefit-cost ratio of {summary['benefit_cost_ratio']:.2f} further confirms that the benefits substantially outweigh the costs.\n\n"
        
        return md
    
    def _roi_to_html(self, roi: Dict[str, Any], customer_name: str) -> str:
        """Convert ROI analysis to HTML format"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>EPOCH5 ROI Analysis for {customer_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; margin-top: 30px; }}
        .header {{ border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .metrics {{ display: flex; flex-wrap: wrap; }}
        .metric {{ flex: 1; min-width: 250px; margin: 10px; padding: 15px; background-color: #e3f2fd; border-radius: 5px; }}
        .metric h3 {{ margin-top: 0; color: #1976d2; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
        th {{ background-color: #f2f2f2; text-align: center; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .chart {{ height: 300px; margin: 20px 0; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 5px; padding: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EPOCH5 ROI Analysis for {customer_name}</h1>
        <p><strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d')}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="summary">
            <p>Based on our analysis, implementing EPOCH5 Autonomous System for {customer_name} is projected to deliver:</p>
            
            <div class="metrics">
                <div class="metric">
                    <h3>ROI</h3>
                    <p class="positive">{roi['summary']['roi_percentage']:.2f}%</p>
                </div>
                <div class="metric">
                    <h3>Net Benefit</h3>
                    <p class="positive">${roi['summary']['net_benefit']:,.2f}</p>
                </div>
                <div class="metric">
                    <h3>Payback Period</h3>
                    <p>{roi['summary']['payback_period']:.2f} years</p>
                </div>
                <div class="metric">
                    <h3>Benefit-Cost Ratio</h3>
                    <p>{roi['summary']['benefit_cost_ratio']:.2f}</p>
                </div>
            </div>
            
            <p><strong>Total Investment:</strong> ${roi['initial_investment']:,.2f} implementation + ${roi['annual_subscription']:,.2f} annual subscription</p>
            <p><strong>Total Benefits (over {roi['years']} years):</strong> ${roi['summary']['total_benefits']:,.2f}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Year-by-Year Analysis</h2>
        <table>
            <tr>
                <th>Year</th>
                <th>Total Costs</th>
                <th>Total Benefits</th>
                <th>Net Benefit</th>
                <th>Cumulative Net</th>
            </tr>
"""
        
        for year_data in roi["yearly_analysis"]:
            year = year_data["year"]
            costs = year_data["costs"]["total"]
            benefits = year_data["benefits"]["total"]
            net = year_data["net"]
            cumulative = year_data["cumulative_net"]
            
            net_class = "positive" if net >= 0 else "negative"
            cumulative_class = "positive" if cumulative >= 0 else "negative"
            
            html += f"""
            <tr>
                <td style="text-align: center;">Year {year}</td>
                <td>${costs:,.2f}</td>
                <td>${benefits:,.2f}</td>
                <td class="{net_class}">${net:,.2f}</td>
                <td class="{cumulative_class}">${cumulative:,.2f}</td>
            </tr>"""
        
        html += """
        </table>
    </div>
    
    <div class="section">
        <h2>Detailed Benefits Breakdown</h2>
        <table>
            <tr>
                <th>Year</th>
                <th>Labor Savings</th>
                <th>Incident Savings</th>
                <th>Downtime Savings</th>
                <th>Infrastructure Savings</th>
                <th>Compliance Savings</th>
                <th>Total Benefits</th>
            </tr>
"""
        
        for year_data in roi["yearly_analysis"]:
            year = year_data["year"]
            labor = year_data["benefits"]["labor"]
            incident = year_data["benefits"]["incident"]
            downtime = year_data["benefits"]["downtime"]
            infrastructure = year_data["benefits"]["infrastructure"]
            compliance = year_data["benefits"]["compliance"]
            total = year_data["benefits"]["total"]
            
            html += f"""
            <tr>
                <td style="text-align: center;">Year {year}</td>
                <td>${labor:,.2f}</td>
                <td>${incident:,.2f}</td>
                <td>${downtime:,.2f}</td>
                <td>${infrastructure:,.2f}</td>
                <td>${compliance:,.2f}</td>
                <td>${total:,.2f}</td>
            </tr>"""
        
        html += f"""
        </table>
    </div>
    
    <div class="section">
        <h2>Methodology and Assumptions</h2>
        <p>This ROI analysis is based on the following key assumptions:</p>
        <ul>
            <li><strong>Discount Rate:</strong> {self.roi_data['standard_metrics']['discount_rate'] * 100:.1f}%</li>
            <li><strong>Inflation Rate:</strong> {self.roi_data['standard_metrics']['inflation_rate'] * 100:.1f}%</li>
            <li>Implementation costs are incurred upfront at the beginning of Year 0</li>
            <li>Subscription costs are paid annually at the beginning of each year</li>
            <li>Benefits accrue continuously throughout each year</li>
        </ul>
        
        <p>This analysis takes into account productivity improvements, incident reduction, downtime reduction, 
        infrastructure optimization, and compliance benefits based on industry benchmarks and client-specific data.</p>
    </div>
    
    <div class="section">
        <h2>Conclusion</h2>
        <p>
            The projected ROI indicates that EPOCH5 Autonomous System is a sound investment for {customer_name}. 
"""
        
        if roi["summary"]["payback_period"] <= 1:
            html += f"With a payback period of less than a year, the solution quickly generates positive returns. "
        elif roi["summary"]["payback_period"] <= 2:
            html += f"With a payback period of {roi['summary']['payback_period']:.2f} years, the solution generates positive returns in a reasonable timeframe. "
        else:
            html += f"While the payback period of {roi['summary']['payback_period']:.2f} years indicates a longer-term investment, "
            html += f"the substantial ROI of {roi['summary']['roi_percentage']:.2f}% over {roi['years']} years demonstrates significant long-term value. "
        
        html += f"""
            The benefit-cost ratio of {roi['summary']['benefit_cost_ratio']:.2f} further confirms that the benefits substantially outweigh the costs.
        </p>
    </div>
</body>
</html>
"""
        
        return html
    
    def _roi_to_csv(self, roi: Dict[str, Any], customer_name: str, output_path: Path) -> None:
        """Write ROI analysis to CSV format"""
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['EPOCH5 ROI Analysis for ' + customer_name])
            writer.writerow(['Date', datetime.datetime.now().strftime('%Y-%m-%d')])
            writer.writerow([])
            
            # Executive Summary
            writer.writerow(['Executive Summary'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Investment', f"${roi['initial_investment']:,.2f} implementation + ${roi['annual_subscription']:,.2f} annual"])
            writer.writerow(['Total Benefits', f"${roi['summary']['total_benefits']:,.2f}"])
            writer.writerow(['Net Benefit', f"${roi['summary']['net_benefit']:,.2f}"])
            writer.writerow(['ROI', f"{roi['summary']['roi_percentage']:.2f}%"])
            writer.writerow(['Payback Period', f"{roi['summary']['payback_period']:.2f} years"])
            writer.writerow(['Benefit-Cost Ratio', f"{roi['summary']['benefit_cost_ratio']:.2f}"])
            writer.writerow([])
            
            # Year-by-year Analysis
            writer.writerow(['Year-by-Year Analysis'])
            writer.writerow(['Year', 'Total Costs', 'Total Benefits', 'Net Benefit', 'Cumulative Net'])
            
            for year_data in roi["yearly_analysis"]:
                writer.writerow([
                    f"Year {year_data['year']}",
                    f"${year_data['costs']['total']:,.2f}",
                    f"${year_data['benefits']['total']:,.2f}",
                    f"${year_data['net']:,.2f}",
                    f"${year_data['cumulative_net']:,.2f}"
                ])
            
            writer.writerow([])
            
            # Detailed Benefits Breakdown
            writer.writerow(['Detailed Benefits Breakdown'])
            writer.writerow(['Year', 'Labor Savings', 'Incident Savings', 'Downtime Savings', 
                           'Infrastructure Savings', 'Compliance Savings', 'Total Benefits'])
            
            for year_data in roi["yearly_analysis"]:
                writer.writerow([
                    f"Year {year_data['year']}",
                    f"${year_data['benefits']['labor']:,.2f}",
                    f"${year_data['benefits']['incident']:,.2f}",
                    f"${year_data['benefits']['downtime']:,.2f}",
                    f"${year_data['benefits']['infrastructure']:,.2f}",
                    f"${year_data['benefits']['compliance']:,.2f}",
                    f"${year_data['benefits']['total']:,.2f}"
                ])

def main():
    """Parse command line arguments and generate ROI analysis"""
    parser = argparse.ArgumentParser(description="EPOCH5 ROI Calculator")
    
    # Customer information
    parser.add_argument("--customer", required=True, help="Customer name")
    
    # Cost information
    parser.add_argument("--implementation", type=float, required=True, 
                      help="Implementation cost")
    parser.add_argument("--subscription", type=float, required=True,
                      help="Annual subscription cost")
    
    # Staff information
    parser.add_argument("--ops-staff", type=int, required=True,
                      help="Number of operations staff affected")
    parser.add_argument("--dev-staff", type=int, required=True,
                      help="Number of developers affected")
    parser.add_argument("--exec-staff", type=int, default=0,
                      help="Number of executives affected (default: 0)")
    
    # Incident information
    parser.add_argument("--minor-incidents", type=int, required=True,
                      help="Number of minor incidents per year")
    parser.add_argument("--major-incidents", type=int, required=True,
                      help="Number of major incidents per year")
    parser.add_argument("--critical-incidents", type=int, default=0,
                      help="Number of critical incidents per year (default: 0)")
    
    # Downtime information
    parser.add_argument("--downtime-hours", type=float, required=True,
                      help="Current annual downtime in hours")
    parser.add_argument("--downtime-cost", type=float,
                      help="Cost per hour of downtime (optional)")
    
    # Infrastructure cost
    parser.add_argument("--infrastructure-cost", type=float, required=True,
                      help="Annual infrastructure cost")
    
    # Compliance costs
    parser.add_argument("--audit-cost", type=float, required=True,
                      help="Annual compliance audit cost")
    parser.add_argument("--penalty-risk", type=float, required=True,
                      help="Annual financial risk from compliance penalties")
    
    # Time period
    parser.add_argument("--years", type=int, default=3,
                      help="Number of years for ROI calculation (default: 3)")
    
    # Output options
    parser.add_argument("--format", choices=["json", "md", "html", "csv"], default="md",
                      help="Output format (default: md)")
    parser.add_argument("--config", help="Path to ROI configuration file")
    
    args = parser.parse_args()
    
    try:
        # Initialize ROI calculator
        calculator = EPOCH5ROICalculator(args.config)
        
        # Calculate labor savings
        labor_savings = calculator.calculate_labor_savings(
            args.ops_staff, args.dev_staff, args.exec_staff, args.years
        )
        
        # Calculate incident savings
        incident_savings = calculator.calculate_incident_savings(
            args.minor_incidents, args.major_incidents, args.critical_incidents, args.years
        )
        
        # Calculate downtime savings
        downtime_savings = calculator.calculate_downtime_savings(
            args.downtime_hours, args.downtime_cost, args.years
        )
        
        # Calculate infrastructure savings
        infrastructure_savings = calculator.calculate_infrastructure_savings(
            args.infrastructure_cost, args.years
        )
        
        # Calculate compliance savings
        compliance_savings = calculator.calculate_compliance_savings(
            args.audit_cost, args.penalty_risk, args.years
        )
        
        # Calculate overall ROI
        roi_analysis = calculator.calculate_roi(
            args.implementation, args.subscription,
            labor_savings, incident_savings, downtime_savings,
            infrastructure_savings, compliance_savings, args.years
        )
        
        # Generate ROI report
        output_path = calculator.generate_roi_report(roi_analysis, args.customer, args.format)
        
        print(f"\nROI analysis generated successfully: {output_path}\n")
        
        # Print summary
        summary = roi_analysis["summary"]
        print(f"ROI Summary for {args.customer}:")
        print(f"- ROI: {summary['roi_percentage']:.2f}%")
        print(f"- Net Benefit: ${summary['net_benefit']:,.2f}")
        print(f"- Payback Period: {summary['payback_period']:.2f} years")
        print(f"- Benefit-Cost Ratio: {summary['benefit_cost_ratio']:.2f}")
        
    except Exception as e:
        logger.error(f"Error generating ROI analysis: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
