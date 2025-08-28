#!/usr/bin/env python3
"""
Ceiling Management System - Dynamic limits and thresholds for EPOCH5 system
Provides adaptive ceiling adjustment, multi-tier service levels, and predictive optimization
Focuses on revenue-maximizing ceiling strategies aligned with business goals
Integrated with EPOCH5 Audit System for secure logging and enforcement
"""

import json
import hashlib
import time
import statistics
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Import security and audit components if available
try:
    from epoch_audit import EpochAudit
    SECURITY_SYSTEM_AVAILABLE = True
except ImportError:
    SECURITY_SYSTEM_AVAILABLE = False


class ServiceTier(Enum):
    FREEMIUM = "freemium"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class CeilingType(Enum):
    BUDGET = "budget"
    LATENCY = "latency"
    TRUST_THRESHOLD = "trust_threshold"
    SUCCESS_RATE = "success_rate"
    RESOURCE_USAGE = "resource_usage"
    RATE_LIMIT = "rate_limit"


class CeilingManager:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.ceiling_dir = self.base_dir / "ceilings"
        self.ceiling_dir.mkdir(parents=True, exist_ok=True)
        self.ceilings_file = self.ceiling_dir / "dynamic_ceilings.json"
        self.service_tiers_file = self.ceiling_dir / "service_tiers.json"
        self.performance_history_file = self.ceiling_dir / "performance_history.json"
        self.ceiling_events_log = self.ceiling_dir / "ceiling_events.log"

        # Initialize audit system if available
        if SECURITY_SYSTEM_AVAILABLE:
            self.audit_system = EpochAudit(base_dir)
        else:
            self.audit_system = None

        # Initialize default service tier configurations
        self._initialize_default_tiers()

    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def sha256(self, data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _initialize_default_tiers(self):
        """Initialize default service tier configurations for revenue optimization"""
        default_tiers = {
            ServiceTier.FREEMIUM.value: {
                "name": "Freemium",
                "monthly_cost": 0.0,
                "ceilings": {
                    CeilingType.BUDGET.value: 50.0,
                    CeilingType.LATENCY.value: 120.0,
                    CeilingType.SUCCESS_RATE.value: 0.90,
                    CeilingType.TRUST_THRESHOLD.value: 0.75,
                    CeilingType.RATE_LIMIT.value: 100,  # requests per hour
                },
                "features": ["basic_execution", "community_support"],
                "upgrade_incentives": {
                    "performance_boost": "2x faster execution",
                    "reliability_boost": "99.5% uptime SLA",
                    "cost_efficiency": "50% lower per-task cost",
                },
            },
            ServiceTier.PROFESSIONAL.value: {
                "name": "Professional",
                "monthly_cost": 49.99,
                "ceilings": {
                    CeilingType.BUDGET.value: 200.0,
                    CeilingType.LATENCY.value: 60.0,
                    CeilingType.SUCCESS_RATE.value: 0.95,
                    CeilingType.TRUST_THRESHOLD.value: 0.85,
                    CeilingType.RATE_LIMIT.value: 1000,  # requests per hour
                },
                "features": [
                    "priority_execution",
                    "advanced_analytics",
                    "email_support",
                ],
                "upgrade_incentives": {
                    "enterprise_features": "Custom integrations available",
                    "dedicated_support": "24/7 phone support",
                    "unlimited_scale": "No resource limits",
                },
            },
            ServiceTier.ENTERPRISE.value: {
                "name": "Enterprise",
                "monthly_cost": 199.99,
                "ceilings": {
                    CeilingType.BUDGET.value: 1000.0,
                    CeilingType.LATENCY.value: 30.0,
                    CeilingType.SUCCESS_RATE.value: 0.995,
                    CeilingType.TRUST_THRESHOLD.value: 0.95,
                    CeilingType.RATE_LIMIT.value: 10000,  # requests per hour
                },
                "features": [
                    "dedicated_resources",
                    "custom_sla",
                    "phone_support",
                    "api_access",
                ],
                "upgrade_incentives": {
                    "contact_sales": "Custom pricing and features available"
                },
            },
        }

        if not self.service_tiers_file.exists():
            self.save_service_tiers(
                {
                    "tiers": default_tiers,
                    "created_at": self.timestamp(),
                    "last_updated": self.timestamp(),
                }
            )

    def save_service_tiers(self, tiers_data: Dict[str, Any]):
        """Save service tier configuration"""
        tiers_data["last_updated"] = self.timestamp()
        with open(self.service_tiers_file, "w") as f:
            json.dump(tiers_data, f, indent=2)

    def load_service_tiers(self) -> Dict[str, Any]:
        """Load service tier configuration"""
        if self.service_tiers_file.exists():
            with open(self.service_tiers_file, "r") as f:
                return json.load(f)
        return {"tiers": {}, "last_updated": self.timestamp()}

    def get_ceiling_for_tier(
        self, service_tier: ServiceTier, ceiling_type: CeilingType
    ) -> float:
        """Get ceiling value for specific service tier and ceiling type"""
        tiers_data = self.load_service_tiers()
        tier_config = tiers_data.get("tiers", {}).get(service_tier.value, {})
        ceilings = tier_config.get("ceilings", {})
        return ceilings.get(ceiling_type.value, 0.0)

    def calculate_dynamic_ceiling(
        self,
        ceiling_type: CeilingType,
        service_tier: ServiceTier,
        performance_history: List[Dict[str, Any]] = None,
    ) -> float:
        """Calculate adaptive ceiling based on performance history and market conditions"""
        base_ceiling = self.get_ceiling_for_tier(service_tier, ceiling_type)

        if not performance_history or len(performance_history) < 3:
            return base_ceiling

        # Performance-based adjustment algorithm
        recent_performance = performance_history[-10:]  # Last 10 data points

        if ceiling_type == CeilingType.BUDGET:
            # Increase budget ceiling if success rates are high and costs are under control
            success_rates = [p.get("success_rate", 0) for p in recent_performance]
            avg_success = statistics.mean(success_rates) if success_rates else 0

            if avg_success > 0.98:
                # High performance - increase ceiling by 20%
                return base_ceiling * 1.2
            elif avg_success > 0.95:
                # Good performance - increase by 10%
                return base_ceiling * 1.1
            elif avg_success < 0.85:
                # Poor performance - decrease by 15%
                return base_ceiling * 0.85

        elif ceiling_type == CeilingType.LATENCY:
            # Adjust latency ceiling based on actual performance
            latencies = [p.get("actual_latency", 0) for p in recent_performance]
            avg_latency = statistics.mean(latencies) if latencies else base_ceiling

            # Set ceiling to 1.5x average actual latency, but within reasonable bounds
            dynamic_ceiling = avg_latency * 1.5
            return min(max(dynamic_ceiling, base_ceiling * 0.5), base_ceiling * 2.0)

        return base_ceiling

    def create_ceiling_configuration(
        self,
        config_id: str,
        service_tier: ServiceTier,
        custom_ceilings: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """Create a ceiling configuration for a specific context"""
        base_tiers = self.load_service_tiers()
        tier_config = base_tiers.get("tiers", {}).get(service_tier.value, {})

        ceiling_config = {
            "config_id": config_id,
            "service_tier": service_tier.value,
            "created_at": self.timestamp(),
            "base_ceilings": tier_config.get("ceilings", {}),
            "custom_ceilings": custom_ceilings or {},
            "dynamic_adjustments": {},
            "last_adjustment": None,
            "performance_score": 1.0,
            "revenue_impact": 0.0,
            "hash": self.sha256(
                f"{config_id}|{service_tier.value}|{json.dumps(custom_ceilings or {}, sort_keys=True)}"
            ),
        }

        return ceiling_config

    def adjust_ceiling_for_performance(
        self, config_id: str, performance_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adjust ceilings based on real-time performance metrics"""
        ceilings_data = self.load_ceilings()

        if config_id not in ceilings_data.get("configurations", {}):
            return {"error": "Configuration not found"}

        config = ceilings_data["configurations"][config_id]
        service_tier = ServiceTier(config["service_tier"])

        # Calculate performance score (0.0 to 2.0, where 1.0 is baseline)
        success_rate = performance_metrics.get("success_rate", 0.95)
        actual_latency = performance_metrics.get("actual_latency", 60.0)
        spent_budget = performance_metrics.get("spent_budget", 100.0)

        # Get the baseline values from the service tier
        base_success_rate = 0.95  # Professional tier baseline
        base_latency = config["base_ceilings"].get("latency", 60.0)
        base_budget = config["base_ceilings"].get("budget", 200.0)

        # Calculate individual efficiency scores
        success_efficiency = success_rate / base_success_rate  # Higher is better
        latency_efficiency = base_latency / max(
            actual_latency, 1.0
        )  # Lower latency is better
        budget_efficiency = base_budget / max(
            spent_budget, 1.0
        )  # Lower spending is better

        performance_score = (
            success_efficiency + latency_efficiency + budget_efficiency
        ) / 3.0
        config["performance_score"] = performance_score

        # Dynamic adjustments based on performance
        adjustments = {}

        if performance_score > 1.3:  # Excellent performance
            adjustments[CeilingType.BUDGET.value] = 1.25  # 25% increase
            adjustments[CeilingType.RATE_LIMIT.value] = 1.5  # 50% increase
            adjustments["performance_bonus"] = (
                "Excellent performance - increased limits"
            )
        elif performance_score > 1.1:  # Good performance
            adjustments[CeilingType.BUDGET.value] = 1.1  # 10% increase
            adjustments[CeilingType.RATE_LIMIT.value] = 1.2  # 20% increase
            adjustments["performance_bonus"] = "Good performance - modest increases"
        elif performance_score < 0.8:  # Poor performance
            adjustments[CeilingType.BUDGET.value] = 0.8  # 20% decrease
            adjustments[CeilingType.RATE_LIMIT.value] = 0.7  # 30% decrease
            adjustments["performance_penalty"] = "Poor performance - reduced limits"

        config["dynamic_adjustments"] = adjustments
        config["last_adjustment"] = self.timestamp()

        # Log the adjustment
        self.log_ceiling_event(
            "DYNAMIC_ADJUSTMENT",
            {
                "config_id": config_id,
                "performance_score": performance_score,
                "adjustments": adjustments,
                "metrics": performance_metrics,
            },
        )

        self.save_ceilings(ceilings_data)
        return config

    def get_effective_ceiling(self, config_id: str, ceiling_type: CeilingType) -> float:
        """Get the effective ceiling value considering all adjustments"""
        ceilings_data = self.load_ceilings()

        if config_id not in ceilings_data.get("configurations", {}):
            # Return default for service tier
            return self.get_ceiling_for_tier(ServiceTier.FREEMIUM, ceiling_type)

        config = ceilings_data["configurations"][config_id]

        # Start with base ceiling
        base_ceiling = config["base_ceilings"].get(ceiling_type.value, 0.0)

        # Apply custom ceiling if set
        custom_ceiling = config["custom_ceilings"].get(ceiling_type.value)
        if custom_ceiling is not None:
            base_ceiling = custom_ceiling

        # Apply dynamic adjustment
        adjustment_factor = config["dynamic_adjustments"].get(ceiling_type.value, 1.0)
        effective_ceiling = base_ceiling * adjustment_factor
        
        # Apply audit system enforcement if available
        if self.audit_system and hasattr(self.audit_system, 'enforce_ceiling'):
            # Create a temporary ceiling setting in audit system if needed
            if ceiling_type.value not in self.audit_system.ceilings:
                self.audit_system.ceilings[ceiling_type.value] = effective_ceiling
                
            # This is just to verify the ceiling is registered, no actual enforcement here
            self.audit_system.log_event(
                "ceiling_verification",
                f"Ceiling verified for {ceiling_type.value}: {effective_ceiling}",
                {"config_id": config_id, "ceiling_type": ceiling_type.value, "value": effective_ceiling}
            )

        return effective_ceiling

    def calculate_revenue_impact(
        self,
        config_id: str,
        performance_before: Dict[str, Any],
        performance_after: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate the revenue impact of ceiling adjustments"""
        # Estimate revenue impact based on performance improvements
        success_rate_improvement = performance_after.get(
            "success_rate", 0
        ) - performance_before.get("success_rate", 0)

        latency_improvement = performance_before.get(
            "actual_latency", 60
        ) - performance_after.get("actual_latency", 60)

        # Revenue impact calculation (simplified model)
        # Assumption: 1% success rate improvement = $100/month value
        # Assumption: 1 second latency improvement = $50/month value
        revenue_impact = (success_rate_improvement * 100 * 100) + (
            latency_improvement * 50
        )

        impact_analysis = {
            "config_id": config_id,
            "calculated_at": self.timestamp(),
            "success_rate_improvement": success_rate_improvement,
            "latency_improvement_seconds": latency_improvement,
            "estimated_monthly_revenue_impact": revenue_impact,
            "confidence_level": 0.75,  # 75% confidence in estimate
            "recommendation": self._generate_revenue_recommendation(revenue_impact),
        }
        
        # Log revenue impact calculation to audit system
        if self.audit_system:
            self.audit_system.log_event(
                "revenue_impact_calculation",
                f"Revenue impact calculated for {config_id}: ${revenue_impact:.2f}/month",
                impact_analysis
            )

        return impact_analysis
        
    def enforce_value_ceiling(self, config_id: str, ceiling_type: CeilingType, value: float) -> Dict[str, Any]:
        """
        Enforce a ceiling on a specific value based on configuration settings
        
        Args:
            config_id: Configuration ID
            ceiling_type: Type of ceiling to enforce
            value: Value to check against ceiling
            
        Returns:
            Dictionary with enforcement results
        """
        # Get effective ceiling
        ceiling = self.get_effective_ceiling(config_id, ceiling_type)
        
        # Track original value
        original_value = value
        capped = False
        
        # Apply ceiling if needed
        if value > ceiling:
            value = ceiling
            capped = True
            
            # Log ceiling enforcement
            self.log_ceiling_event("ENFORCEMENT", {
                "config_id": config_id,
                "ceiling_type": ceiling_type.value,
                "original_value": original_value,
                "capped_value": value,
                "ceiling": ceiling
            })
            
            # Use audit system if available
            if self.audit_system:
                self.audit_system.enforce_ceiling(
                    ceiling_type.value, 
                    original_value,
                    config_id
                )
        
        return {
            "config_id": config_id,
            "ceiling_type": ceiling_type.value,
            "original_value": original_value,
            "final_value": value,
            "ceiling": ceiling,
            "capped": capped
        }

    def _generate_revenue_recommendation(self, revenue_impact: float) -> str:
        """Generate revenue optimization recommendation"""
        if revenue_impact > 500:
            return "Strong positive impact - maintain or increase ceiling adjustments"
        elif revenue_impact > 100:
            return "Moderate positive impact - consider gradual ceiling increases"
        elif revenue_impact < -100:
            return "Negative impact detected - review ceiling adjustments"
        else:
            return "Neutral impact - monitor performance and adjust incrementally"

    def save_ceilings(self, ceilings_data: Dict[str, Any]):
        """Save ceiling configurations"""
        ceilings_data["last_updated"] = self.timestamp()
        with open(self.ceilings_file, "w") as f:
            json.dump(ceilings_data, f, indent=2)

    def load_ceilings(self) -> Dict[str, Any]:
        """Load ceiling configurations"""
        if self.ceilings_file.exists():
            with open(self.ceilings_file, "r") as f:
                return json.load(f)
        return {"configurations": {}, "last_updated": self.timestamp()}

    def add_configuration(self, ceiling_config: Dict[str, Any]) -> bool:
        """Add ceiling configuration to the system"""
        ceilings_data = self.load_ceilings()
        ceilings_data["configurations"][ceiling_config["config_id"]] = ceiling_config
        self.save_ceilings(ceilings_data)
        return True

    def log_ceiling_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log ceiling management events"""
        log_entry = {
            "timestamp": self.timestamp(),
            "event_type": event_type,
            "data": event_data,
            "hash": self.sha256(
                f"{event_type}|{json.dumps(event_data, sort_keys=True)}"
            ),
        }

        with open(self.ceiling_events_log, "a") as f:
            f.write(f"{json.dumps(log_entry)}\n")
            
        # Use audit system if available
        if self.audit_system:
            self.audit_system.log_event(
                f"ceiling_{event_type.lower()}", 
                f"Ceiling event: {event_type}", 
                event_data
            )

    def get_upgrade_recommendations(self, config_id: str) -> Dict[str, Any]:
        """Generate service tier upgrade recommendations based on usage patterns"""
        ceilings_data = self.load_ceilings()

        if config_id not in ceilings_data.get("configurations", {}):
            return {"error": "Configuration not found"}

        config = ceilings_data["configurations"][config_id]
        current_tier = ServiceTier(config["service_tier"])
        performance_score = config.get("performance_score", 1.0)

        recommendations = {
            "current_tier": current_tier.value,
            "performance_score": performance_score,
            "should_upgrade": False,
            "recommended_tier": None,
            "benefits": [],
            "estimated_roi": 0.0,
            "urgency": "low",
        }

        # Upgrade logic based on performance and ceiling utilization
        if performance_score > 1.3 and current_tier != ServiceTier.ENTERPRISE:
            if current_tier == ServiceTier.FREEMIUM:
                recommendations["recommended_tier"] = ServiceTier.PROFESSIONAL.value
                recommendations["estimated_roi"] = 2.5  # 2.5x ROI
                recommendations["benefits"] = [
                    "2x higher budget ceiling for complex tasks",
                    "50% faster execution with priority processing",
                    "Advanced analytics for performance optimization",
                    "Email support for faster issue resolution",
                ]
            elif current_tier == ServiceTier.PROFESSIONAL:
                recommendations["recommended_tier"] = ServiceTier.ENTERPRISE.value
                recommendations["estimated_roi"] = 3.0  # 3.0x ROI
                recommendations["benefits"] = [
                    "5x higher budget ceiling for enterprise workloads",
                    "Sub-30 second latency guarantee",
                    "99.95% success rate SLA",
                    "Dedicated resources and 24/7 support",
                ]

            recommendations["should_upgrade"] = True
            recommendations["urgency"] = "high" if performance_score > 1.5 else "medium"

        return recommendations


def main():
    """CLI interface for ceiling management"""
    import argparse

    parser = argparse.ArgumentParser(description="EPOCH5 Ceiling Management System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create configuration command
    create_parser = subparsers.add_parser(
        "create-config", help="Create ceiling configuration"
    )
    create_parser.add_argument("config_id", help="Configuration ID")
    create_parser.add_argument(
        "--tier",
        choices=["freemium", "professional", "enterprise"],
        default="freemium",
        help="Service tier",
    )

    # Adjust ceiling command
    adjust_parser = subparsers.add_parser(
        "adjust", help="Adjust ceilings based on performance"
    )
    adjust_parser.add_argument("config_id", help="Configuration ID")
    adjust_parser.add_argument(
        "--success-rate", type=float, default=0.95, help="Success rate"
    )
    adjust_parser.add_argument(
        "--latency", type=float, default=60.0, help="Actual latency"
    )
    adjust_parser.add_argument(
        "--budget", type=float, default=50.0, help="Spent budget"
    )

    # Get ceiling command
    get_parser = subparsers.add_parser("get", help="Get effective ceiling value")
    get_parser.add_argument("config_id", help="Configuration ID")
    get_parser.add_argument(
        "ceiling_type",
        choices=["budget", "latency", "trust_threshold", "success_rate", "rate_limit"],
        help="Ceiling type",
    )
    
    # Enforce ceiling command
    enforce_parser = subparsers.add_parser("enforce", help="Enforce ceiling on a value")
    enforce_parser.add_argument("config_id", help="Configuration ID")
    enforce_parser.add_argument(
        "ceiling_type",
        choices=["budget", "latency", "trust_threshold", "success_rate", "rate_limit"],
        help="Ceiling type",
    )
    enforce_parser.add_argument("value", type=float, help="Value to check against ceiling")

    # Upgrade recommendation command
    upgrade_parser = subparsers.add_parser(
        "upgrade-rec", help="Get upgrade recommendations"
    )
    upgrade_parser.add_argument("config_id", help="Configuration ID")
    
    # Security verification command
    if SECURITY_SYSTEM_AVAILABLE:
        verify_parser = subparsers.add_parser("verify", help="Verify ceiling security")
        verify_parser.add_argument("--max-events", type=int, default=20, 
                                 help="Maximum number of ceiling events to verify")
        
        # Security alerts command
        alerts_parser = subparsers.add_parser("security-alerts", help="Monitor security alerts")
        alerts_parser.add_argument("--continuous", action="store_true", default=True,
                                  help="Continuously monitor for security alerts")
        alerts_parser.add_argument("--interval", type=int, default=5,
                                  help="Interval in seconds between checks")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = CeilingManager()

    if args.command == "create-config":
        service_tier = ServiceTier(args.tier)
        config = manager.create_ceiling_configuration(args.config_id, service_tier)
        manager.add_configuration(config)
        print(
            f"✓ Created ceiling configuration '{args.config_id}' for {service_tier.value} tier"
        )
        print(f"  Base ceilings: {config['base_ceilings']}")

    elif args.command == "adjust":
        performance_metrics = {
            "success_rate": args.success_rate,
            "actual_latency": args.latency,
            "spent_budget": args.budget,
        }
        result = manager.adjust_ceiling_for_performance(
            args.config_id, performance_metrics
        )

        if "error" in result:
            print(f"✗ Error: {result['error']}")
        else:
            print(f"✓ Adjusted ceilings for '{args.config_id}'")
            print(f"  Performance score: {result['performance_score']:.2f}")
            print(f"  Dynamic adjustments: {result['dynamic_adjustments']}")

    elif args.command == "get":
        ceiling_type = CeilingType(args.ceiling_type)
        ceiling_value = manager.get_effective_ceiling(args.config_id, ceiling_type)
        print(
            f"Effective {ceiling_type.value} ceiling for '{args.config_id}': {ceiling_value}"
        )

    elif args.command == "upgrade-rec":
        recommendations = manager.get_upgrade_recommendations(args.config_id)

        if "error" in recommendations:
            print(f"✗ Error: {recommendations['error']}")
        else:
            print(f"Upgrade Recommendations for '{args.config_id}':")
            print(f"  Current tier: {recommendations['current_tier']}")
            print(f"  Performance score: {recommendations['performance_score']:.2f}")

            if recommendations["should_upgrade"]:
                print(
                    f"  ✓ RECOMMENDED: Upgrade to {recommendations['recommended_tier']}"
                )
                print(f"  Estimated ROI: {recommendations['estimated_roi']}x")
                print(f"  Benefits:")
                for benefit in recommendations["benefits"]:
                    print(f"    - {benefit}")
            else:
                print(f"  No upgrade recommended at this time")
                
    elif args.command == "enforce":
        ceiling_type = CeilingType(args.ceiling_type)
        result = manager.enforce_value_ceiling(args.config_id, ceiling_type, args.value)
        
        if result["capped"]:
            print(f"🔒 Ceiling enforced: {result['original_value']} → {result['final_value']}")
            print(f"  Config: {args.config_id}")
            print(f"  Ceiling type: {ceiling_type.value}")
            print(f"  Ceiling value: {result['ceiling']}")
        else:
            print(f"✓ Value {result['original_value']} is within ceiling ({result['ceiling']})")
    
    elif args.command == "verify" and SECURITY_SYSTEM_AVAILABLE:
        # Verify recent ceiling events using the audit system
        if manager.audit_system:
            results = manager.audit_system.verify_seals(args.max_events)
            
            print(f"Security verification status: {results['status']}")
            print(f"Verified {results['verified_count']} events")
            print(f"Valid: {results['valid_count']}, Invalid: {results['invalid_count']}")
            
            if results['invalid_count'] > 0:
                print("\n⚠️ WARNING: Invalid events detected:")
                for event in results['invalid_events']:
                    print(f"  [{event['ts']}] {event['event']}")
            else:
                print("\n✅ All ceiling events verified successfully")
                
    elif args.command == "security-alerts" and SECURITY_SYSTEM_AVAILABLE:
        # Start security alert monitoring - continuously checks for security alerts and ceiling violations
        # Simulates a real-time security monitoring system that would typically be part of a SOC dashboard
        if manager.audit_system:
            try:
                print("🚨 Starting Security Alert Monitor...")
                print("Press Ctrl+C to stop monitoring")
                
                # Track the last alert timestamp to avoid duplicates
                last_alert_time = None
                
                while True:
                    alerts = manager.audit_system.get_security_alerts(since=last_alert_time)
                    
                    if alerts and len(alerts) > 0:
                        print(f"\n🔔 {len(alerts)} new security alert(s) detected:")
                        for alert in alerts:
                            print(f"  [{alert['timestamp']}] {alert['severity'].upper()}: {alert['message']}")
                            print(f"      {alert['details']}")
                            last_alert_time = alert['timestamp']
                    
                    # Check for ceiling violations
                    violations = manager.audit_system.get_ceiling_violations()
                    if violations and len(violations) > 0:
                        print(f"\n⚠️ {len(violations)} ceiling violation(s) detected:")
                        for violation in violations:
                            print(f"  [{violation['timestamp']}] {violation['ceiling_type']}")
                            print(f"      Attempted: {violation['attempted_value']}, Limit: {violation['ceiling_value']}")
                            print(f"      Config: {violation['config_id']}")
                    
                    time.sleep(args.interval)
                    
            except KeyboardInterrupt:
                print("\n✓ Security monitoring stopped")
        else:
            print("❌ Audit system not available. Security alerts cannot be monitored.")


if __name__ == "__main__":
    main()
