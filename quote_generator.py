#!/usr/bin/env python3
"""
EPOCH5 Quote Generator

This script generates customized quotations for EPOCH5 Autonomous System based on
customer requirements and selected options.
"""

import argparse
import json
import os
import sys
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("quote_generator.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EPOCH5QuoteGenerator:
    """Generates quotes for EPOCH5 Autonomous System"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the quote generator"""
        # Set default config path if not provided
        if not config_path:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pricing_data.json")
        
        # Load pricing data from config file if it exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.pricing_data = json.load(f)
        else:
            # Use built-in default pricing
            self.pricing_data = self._get_default_pricing()
            
        # Initialize output directory
        self.output_dir = Path("./quotes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("EPOCH5 Quote Generator initialized")
    
    def _get_default_pricing(self) -> Dict[str, Any]:
        """Get default pricing data"""
        return {
            "subscription_tiers": {
                "basic": {
                    "name": "Basic Autonomous",
                    "monthly_price": 499,
                    "annual_price": 4990,
                    "components_included": 50,
                    "additional_component_price": 10
                },
                "professional": {
                    "name": "Professional Autonomous",
                    "monthly_price": 1499,
                    "annual_price": 14990,
                    "components_included": 200,
                    "additional_component_price": 10
                },
                "enterprise": {
                    "name": "Enterprise Autonomous",
                    "monthly_price": 4999,
                    "annual_price": 49990,
                    "components_included": float('inf'),  # Unlimited
                    "additional_component_price": 0
                }
            },
            "implementation_packages": {
                "standard": {
                    "name": "Standard Implementation",
                    "price": 10000,
                    "training_days_included": 2
                },
                "advanced": {
                    "name": "Advanced Implementation",
                    "price": 25000,
                    "training_days_included": 5
                },
                "enterprise": {
                    "name": "Enterprise Implementation",
                    "price": 50000,
                    "training_days_included": 10
                }
            },
            "additional_services": {
                "training_day_price": 2000,
                "custom_development_hourly": 200,
                "premium_support_percentage": 0.15
            },
            "volume_discounts": {
                "components": [
                    {"threshold": 100, "discount": 0.10},
                    {"threshold": 500, "discount": 0.20},
                    {"threshold": 1000, "discount": 0.30}
                ]
            },
            "multi_year_discounts": {
                "2_year": 0.15,
                "3_year": 0.25,
                "5_year": 0.35
            }
        }
    
    def calculate_subscription_price(self, 
                                    tier: str, 
                                    term: str, 
                                    components: int, 
                                    years: int = 1) -> Dict[str, Any]:
        """
        Calculate subscription price based on tier, term, and component count
        
        Args:
            tier: Subscription tier (basic, professional, enterprise)
            term: Billing term (monthly, annual)
            components: Number of components to monitor
            years: Number of years for contract
            
        Returns:
            Dictionary with subscription pricing details
        """
        # Validate inputs
        if tier not in self.pricing_data["subscription_tiers"]:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(self.pricing_data['subscription_tiers'].keys())}")
            
        if term not in ["monthly", "annual"]:
            raise ValueError(f"Invalid term: {term}. Must be 'monthly' or 'annual'")
            
        if components <= 0:
            raise ValueError(f"Components must be positive, got {components}")
            
        if years <= 0:
            raise ValueError(f"Years must be positive, got {years}")
        
        # Get tier pricing
        tier_data = self.pricing_data["subscription_tiers"][tier]
        
        # Calculate base price
        if term == "monthly":
            base_price = tier_data["monthly_price"]
            annual_base = base_price * 12
        else:  # annual
            base_price = tier_data["annual_price"]
            annual_base = base_price
        
        # Calculate additional component cost
        components_included = tier_data["components_included"]
        additional_components = max(0, components - components_included)
        additional_component_price = tier_data["additional_component_price"]
        additional_component_cost = additional_components * additional_component_price
        
        if term == "monthly":
            additional_component_cost_annual = additional_component_cost * 12
        else:
            additional_component_cost_annual = additional_component_cost
        
        # Apply volume discount if applicable
        volume_discount_percentage = 0
        for discount in self.pricing_data["volume_discounts"]["components"]:
            if components >= discount["threshold"]:
                volume_discount_percentage = discount["discount"]
        
        volume_discount = (annual_base + additional_component_cost_annual) * volume_discount_percentage
        
        # Calculate annual subtotal
        annual_subtotal = annual_base + additional_component_cost_annual - volume_discount
        
        # Apply multi-year discount if applicable
        multi_year_discount_percentage = 0
        if years > 1:
            discount_key = f"{years}_year"
            if discount_key in self.pricing_data["multi_year_discounts"]:
                multi_year_discount_percentage = self.pricing_data["multi_year_discounts"][discount_key]
        
        multi_year_discount = annual_subtotal * multi_year_discount_percentage
        final_annual_price = annual_subtotal - multi_year_discount
        
        # Calculate total contract value
        total_contract_value = final_annual_price * years
        
        # If monthly, calculate the monthly payment
        if term == "monthly":
            monthly_payment = final_annual_price / 12
        else:
            monthly_payment = None
        
        # Return detailed pricing information
        return {
            "tier": tier,
            "tier_name": tier_data["name"],
            "term": term,
            "years": years,
            "components": components,
            "components_included": components_included,
            "additional_components": additional_components,
            "base_price": base_price,
            "additional_component_cost": additional_component_cost,
            "volume_discount_percentage": volume_discount_percentage,
            "volume_discount": volume_discount,
            "multi_year_discount_percentage": multi_year_discount_percentage,
            "multi_year_discount": multi_year_discount,
            "annual_price": final_annual_price,
            "monthly_payment": monthly_payment,
            "total_contract_value": total_contract_value
        }
    
    def calculate_implementation_price(self, 
                                     package: str,
                                     additional_training_days: int = 0,
                                     custom_development_hours: int = 0) -> Dict[str, Any]:
        """
        Calculate implementation price based on package and add-ons
        
        Args:
            package: Implementation package (standard, advanced, enterprise)
            additional_training_days: Number of additional training days
            custom_development_hours: Number of custom development hours
            
        Returns:
            Dictionary with implementation pricing details
        """
        # Validate inputs
        if package not in self.pricing_data["implementation_packages"]:
            raise ValueError(f"Invalid package: {package}. Must be one of {list(self.pricing_data['implementation_packages'].keys())}")
            
        if additional_training_days < 0:
            raise ValueError(f"Additional training days cannot be negative, got {additional_training_days}")
            
        if custom_development_hours < 0:
            raise ValueError(f"Custom development hours cannot be negative, got {custom_development_hours}")
        
        # Get package pricing
        package_data = self.pricing_data["implementation_packages"][package]
        package_price = package_data["price"]
        
        # Calculate additional training cost
        training_day_price = self.pricing_data["additional_services"]["training_day_price"]
        additional_training_cost = additional_training_days * training_day_price
        
        # Calculate custom development cost
        custom_dev_hourly = self.pricing_data["additional_services"]["custom_development_hourly"]
        custom_development_cost = custom_development_hours * custom_dev_hourly
        
        # Calculate total implementation cost
        total_implementation_cost = package_price + additional_training_cost + custom_development_cost
        
        # Return detailed pricing information
        return {
            "package": package,
            "package_name": package_data["name"],
            "package_price": package_price,
            "training_days_included": package_data["training_days_included"],
            "additional_training_days": additional_training_days,
            "additional_training_cost": additional_training_cost,
            "custom_development_hours": custom_development_hours,
            "custom_development_cost": custom_development_cost,
            "total_implementation_cost": total_implementation_cost
        }
    
    def calculate_total_quote(self,
                           customer_name: str,
                           subscription: Dict[str, Any],
                           implementation: Dict[str, Any],
                           premium_support: bool = False,
                           discount_percentage: float = 0.0) -> Dict[str, Any]:
        """
        Calculate complete quote based on subscription and implementation
        
        Args:
            customer_name: Name of the customer
            subscription: Subscription pricing details
            implementation: Implementation pricing details
            premium_support: Whether to include premium support
            discount_percentage: Additional discount percentage to apply
            
        Returns:
            Complete quote details
        """
        # Calculate premium support cost if applicable
        premium_support_cost = 0
        if premium_support:
            premium_support_percentage = self.pricing_data["additional_services"]["premium_support_percentage"]
            premium_support_cost = subscription["annual_price"] * premium_support_percentage
        
        # Calculate subtotal
        year_one_subtotal = subscription["annual_price"] + implementation["total_implementation_cost"] + premium_support_cost
        
        # Apply additional discount if applicable
        if discount_percentage < 0 or discount_percentage > 1:
            raise ValueError(f"Discount percentage must be between 0 and 1, got {discount_percentage}")
            
        additional_discount = year_one_subtotal * discount_percentage
        
        # Calculate year one total
        year_one_total = year_one_subtotal - additional_discount
        
        # Calculate subsequent years (no implementation cost)
        subsequent_year_cost = subscription["annual_price"] + (premium_support_cost if premium_support else 0)
        
        # Calculate total contract value
        total_contract_value = year_one_total + (subsequent_year_cost * (subscription["years"] - 1))
        
        # Generate quote ID
        quote_id = f"Q-{uuid.uuid4().hex[:8].upper()}"
        
        # Create quote object
        quote = {
            "quote_id": quote_id,
            "customer_name": customer_name,
            "date_created": datetime.datetime.now().strftime("%Y-%m-%d"),
            "valid_until": (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
            "subscription": subscription,
            "implementation": implementation,
            "premium_support": {
                "included": premium_support,
                "annual_cost": premium_support_cost if premium_support else 0
            },
            "pricing": {
                "year_one_subtotal": year_one_subtotal,
                "additional_discount_percentage": discount_percentage,
                "additional_discount": additional_discount,
                "year_one_total": year_one_total,
                "subsequent_year_cost": subsequent_year_cost,
                "total_contract_value": total_contract_value
            }
        }
        
        return quote
    
    def generate_quote_document(self, quote: Dict[str, Any], format: str = "json") -> str:
        """
        Generate quote document in specified format
        
        Args:
            quote: Quote data
            format: Output format (json, md, html)
            
        Returns:
            Path to generated document
        """
        if format not in ["json", "md", "html"]:
            raise ValueError(f"Invalid format: {format}. Must be one of ['json', 'md', 'html']")
        
        # Create filename based on quote ID and customer name
        sanitized_customer = quote["customer_name"].replace(" ", "_").lower()
        filename = f"{quote['quote_id']}_{sanitized_customer}.{format}"
        output_path = self.output_dir / filename
        
        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(quote, f, indent=2)
        elif format == "md":
            markdown = self._quote_to_markdown(quote)
            with open(output_path, 'w') as f:
                f.write(markdown)
        elif format == "html":
            html = self._quote_to_html(quote)
            with open(output_path, 'w') as f:
                f.write(html)
        
        logger.info(f"Generated quote document: {output_path}")
        return str(output_path)
    
    def _quote_to_markdown(self, quote: Dict[str, Any]) -> str:
        """Convert quote to markdown format"""
        md = f"# EPOCH5 Autonomous System Quotation\n\n"
        md += f"**Quote ID:** {quote['quote_id']}  \n"
        md += f"**Date Created:** {quote['date_created']}  \n"
        md += f"**Valid Until:** {quote['valid_until']}  \n\n"
        
        md += f"## Customer Information\n\n"
        md += f"**Customer Name:** {quote['customer_name']}  \n\n"
        
        md += f"## Subscription Details\n\n"
        sub = quote['subscription']
        md += f"**Tier:** {sub['tier_name']}  \n"
        md += f"**Term:** {'Monthly' if sub['term'] == 'monthly' else 'Annual'} billing  \n"
        md += f"**Contract Duration:** {sub['years']} year{'s' if sub['years'] > 1 else ''}  \n"
        md += f"**Components:** {sub['components']} ({sub['additional_components']} above included {sub['components_included']})  \n\n"
        
        md += f"**Pricing Breakdown:**  \n\n"
        md += f"- Base Price: ${sub['base_price']:,}  \n"
        if sub['additional_component_cost'] > 0:
            md += f"- Additional Component Cost: ${sub['additional_component_cost']:,}  \n"
        if sub['volume_discount'] > 0:
            md += f"- Volume Discount ({sub['volume_discount_percentage']*100:.0f}%): -${sub['volume_discount']:,}  \n"
        if sub['multi_year_discount'] > 0:
            md += f"- Multi-Year Discount ({sub['multi_year_discount_percentage']*100:.0f}%): -${sub['multi_year_discount']:,}  \n"
        
        md += f"\n**Annual Subscription Price:** ${sub['annual_price']:,}  \n"
        if sub['monthly_payment']:
            md += f"**Monthly Payment:** ${sub['monthly_payment']:,.2f}  \n"
        md += f"**Total Subscription Value:** ${sub['total_contract_value']:,}  \n\n"
        
        md += f"## Implementation Details\n\n"
        imp = quote['implementation']
        md += f"**Package:** {imp['package_name']}  \n"
        md += f"**Base Price:** ${imp['package_price']:,}  \n"
        md += f"**Training Days Included:** {imp['training_days_included']}  \n"
        
        if imp['additional_training_days'] > 0:
            md += f"**Additional Training Days:** {imp['additional_training_days']} (${imp['additional_training_cost']:,})  \n"
        
        if imp['custom_development_hours'] > 0:
            md += f"**Custom Development Hours:** {imp['custom_development_hours']} (${imp['custom_development_cost']:,})  \n"
        
        md += f"\n**Total Implementation Cost:** ${imp['total_implementation_cost']:,}  \n\n"
        
        # Premium support
        if quote['premium_support']['included']:
            md += f"## Premium Support\n\n"
            md += f"**Annual Premium Support:** ${quote['premium_support']['annual_cost']:,}  \n\n"
        
        # Total pricing
        md += f"## Total Investment\n\n"
        pricing = quote['pricing']
        md += f"**Year One Subtotal:** ${pricing['year_one_subtotal']:,}  \n"
        
        if pricing['additional_discount'] > 0:
            md += f"**Additional Discount ({pricing['additional_discount_percentage']*100:.0f}%):** -${pricing['additional_discount']:,}  \n"
        
        md += f"**Year One Total:** ${pricing['year_one_total']:,}  \n"
        
        if sub['years'] > 1:
            md += f"**Subsequent Annual Cost:** ${pricing['subsequent_year_cost']:,}  \n"
        
        md += f"**Total Contract Value:** ${pricing['total_contract_value']:,}  \n\n"
        
        # Terms and conditions
        md += f"## Terms and Conditions\n\n"
        md += f"1. This quotation is valid until {quote['valid_until']}.\n"
        md += f"2. All prices are in USD.\n"
        md += f"3. Pricing is subject to EPOCH5's standard terms and conditions.\n"
        md += f"4. Implementation timeline will be finalized upon acceptance of this quote.\n\n"
        
        md += f"## Acceptance\n\n"
        md += f"To accept this quotation, please sign below and return to your EPOCH5 representative.\n\n"
        md += f"Signature: _______________________________  Date: _______________\n\n"
        md += f"Name: ___________________________________  Title: ______________\n\n"
        
        return md
    
    def _quote_to_html(self, quote: Dict[str, Any]) -> str:
        """Convert quote to HTML format"""
        # Basic HTML version - in a real implementation, this would include styling
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>EPOCH5 Quotation - {quote['quote_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; margin-top: 30px; }}
        .header {{ border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .pricing {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .total {{ font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EPOCH5 Autonomous System Quotation</h1>
        <p><strong>Quote ID:</strong> {quote['quote_id']}</p>
        <p><strong>Date Created:</strong> {quote['date_created']}</p>
        <p><strong>Valid Until:</strong> {quote['valid_until']}</p>
    </div>
    
    <div class="section">
        <h2>Customer Information</h2>
        <p><strong>Customer Name:</strong> {quote['customer_name']}</p>
    </div>
    
    <div class="section">
        <h2>Subscription Details</h2>
        <p><strong>Tier:</strong> {quote['subscription']['tier_name']}</p>
        <p><strong>Term:</strong> {'Monthly' if quote['subscription']['term'] == 'monthly' else 'Annual'} billing</p>
        <p><strong>Contract Duration:</strong> {quote['subscription']['years']} year{'s' if quote['subscription']['years'] > 1 else ''}</p>
        <p><strong>Components:</strong> {quote['subscription']['components']} ({quote['subscription']['additional_components']} above included {quote['subscription']['components_included']})</p>
        
        <div class="pricing">
            <h3>Pricing Breakdown</h3>
            <p>Base Price: ${quote['subscription']['base_price']:,}</p>
"""
        
        sub = quote['subscription']
        if sub['additional_component_cost'] > 0:
            html += f"            <p>Additional Component Cost: ${sub['additional_component_cost']:,}</p>\n"
        if sub['volume_discount'] > 0:
            html += f"            <p>Volume Discount ({sub['volume_discount_percentage']*100:.0f}%): -${sub['volume_discount']:,}</p>\n"
        if sub['multi_year_discount'] > 0:
            html += f"            <p>Multi-Year Discount ({sub['multi_year_discount_percentage']*100:.0f}%): -${sub['multi_year_discount']:,}</p>\n"
        
        html += f"""
            <p class="total">Annual Subscription Price: ${sub['annual_price']:,}</p>
"""
        
        if sub['monthly_payment']:
            html += f"            <p>Monthly Payment: ${sub['monthly_payment']:,.2f}</p>\n"
        
        html += f"""
            <p class="total">Total Subscription Value: ${sub['total_contract_value']:,}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Implementation Details</h2>
        <p><strong>Package:</strong> {quote['implementation']['package_name']}</p>
        <p><strong>Base Price:</strong> ${quote['implementation']['package_price']:,}</p>
        <p><strong>Training Days Included:</strong> {quote['implementation']['training_days_included']}</p>
"""
        
        imp = quote['implementation']
        if imp['additional_training_days'] > 0:
            html += f"        <p><strong>Additional Training Days:</strong> {imp['additional_training_days']} (${imp['additional_training_cost']:,})</p>\n"
        
        if imp['custom_development_hours'] > 0:
            html += f"        <p><strong>Custom Development Hours:</strong> {imp['custom_development_hours']} (${imp['custom_development_cost']:,})</p>\n"
        
        html += f"""
        <p class="total">Total Implementation Cost: ${imp['total_implementation_cost']:,}</p>
    </div>
"""
        
        # Premium support
        if quote['premium_support']['included']:
            html += f"""
    <div class="section">
        <h2>Premium Support</h2>
        <p><strong>Annual Premium Support:</strong> ${quote['premium_support']['annual_cost']:,}</p>
    </div>
"""
        
        # Total pricing
        pricing = quote['pricing']
        html += f"""
    <div class="section">
        <h2>Total Investment</h2>
        <div class="pricing">
            <p>Year One Subtotal: ${pricing['year_one_subtotal']:,}</p>
"""
        
        if pricing['additional_discount'] > 0:
            html += f"            <p>Additional Discount ({pricing['additional_discount_percentage']*100:.0f}%): -${pricing['additional_discount']:,}</p>\n"
        
        html += f"""
            <p class="total">Year One Total: ${pricing['year_one_total']:,}</p>
"""
        
        if sub['years'] > 1:
            html += f"            <p>Subsequent Annual Cost: ${pricing['subsequent_year_cost']:,}</p>\n"
        
        html += f"""
            <p class="total">Total Contract Value: ${pricing['total_contract_value']:,}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Terms and Conditions</h2>
        <ol>
            <li>This quotation is valid until {quote['valid_until']}.</li>
            <li>All prices are in USD.</li>
            <li>Pricing is subject to EPOCH5's standard terms and conditions.</li>
            <li>Implementation timeline will be finalized upon acceptance of this quote.</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>Acceptance</h2>
        <p>To accept this quotation, please sign below and return to your EPOCH5 representative.</p>
        <p>Signature: _______________________________ Date: _______________</p>
        <p>Name: ___________________________________ Title: ______________</p>
    </div>
</body>
</html>
"""
        
        return html

def main():
    """Parse command line arguments and generate quote"""
    parser = argparse.ArgumentParser(description="EPOCH5 Quote Generator")
    
    # Customer information
    parser.add_argument("--customer", required=True, help="Customer name")
    
    # Subscription options
    parser.add_argument("--tier", choices=["basic", "professional", "enterprise"], 
                      required=True, help="Subscription tier")
    parser.add_argument("--term", choices=["monthly", "annual"], default="annual",
                      help="Billing term (default: annual)")
    parser.add_argument("--components", type=int, required=True, 
                      help="Number of components to monitor")
    parser.add_argument("--years", type=int, default=1,
                      help="Contract duration in years (default: 1)")
    
    # Implementation options
    parser.add_argument("--implementation", choices=["standard", "advanced", "enterprise"],
                      required=True, help="Implementation package")
    parser.add_argument("--training", type=int, default=0,
                      help="Additional training days (default: 0)")
    parser.add_argument("--development", type=int, default=0,
                      help="Custom development hours (default: 0)")
    
    # Additional options
    parser.add_argument("--premium-support", action="store_true",
                      help="Include premium support")
    parser.add_argument("--discount", type=float, default=0.0,
                      help="Additional discount percentage (0.0-1.0, default: 0.0)")
    
    # Output options
    parser.add_argument("--format", choices=["json", "md", "html"], default="md",
                      help="Output format (default: md)")
    parser.add_argument("--config", help="Path to pricing configuration file")
    
    args = parser.parse_args()
    
    try:
        # Initialize quote generator
        generator = EPOCH5QuoteGenerator(args.config)
        
        # Calculate subscription price
        subscription = generator.calculate_subscription_price(
            args.tier, args.term, args.components, args.years
        )
        
        # Calculate implementation price
        implementation = generator.calculate_implementation_price(
            args.implementation, args.training, args.development
        )
        
        # Generate complete quote
        quote = generator.calculate_total_quote(
            args.customer, subscription, implementation, 
            args.premium_support, args.discount
        )
        
        # Generate quote document
        output_path = generator.generate_quote_document(quote, args.format)
        
        print(f"\nQuote generated successfully: {output_path}\n")
        
        # Print summary
        print(f"Quote Summary for {args.customer}:")
        print(f"- {subscription['tier_name']} tier, {args.years} year contract")
        print(f"- {implementation['package_name']} implementation package")
        print(f"- Year One Total: ${quote['pricing']['year_one_total']:,}")
        print(f"- Total Contract Value: ${quote['pricing']['total_contract_value']:,}")
        
    except Exception as e:
        logger.error(f"Error generating quote: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
