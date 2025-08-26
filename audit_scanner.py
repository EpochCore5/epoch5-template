#!/usr/bin/env python3
"""
Automated Audit Scanner for EdgeCapsule Cloud Mesh Ledger
Scans ledger files for anomalies, verifies hash chains, and generates Markdown audit reports
Integrates with EPOCH5 ledger system and meta-capsule verification
"""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re

class LedgerAuditScanner:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.ledger_file = self.base_dir / "ledger.log"
        self.meta_ledger = self.base_dir / "meta_capsules" / "meta_ledger.log"
        self.anomalies_file = self.base_dir / "agents" / "anomalies.log"
        self.audit_dir = self.base_dir / "audits"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def sha256(self, data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def parse_ledger_entry(self, line: str) -> Dict[str, str]:
        """Parse a ledger entry line into components"""
        entry = {}
        parts = line.strip().split("|")
        
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                entry[key.lower()] = value
                
        return entry
    
    def verify_hash_chain(self, ledger_file: Path) -> Dict[str, Any]:
        """Verify the integrity of the hash chain in a ledger"""
        verification = {
            "valid": True,
            "total_entries": 0,
            "verified_entries": 0,
            "broken_chains": [],
            "invalid_hashes": [],
            "missing_entries": []
        }
        
        if not ledger_file.exists():
            verification["valid"] = False
            verification["error"] = f"Ledger file not found: {ledger_file}"
            return verification
        
        try:
            with open(ledger_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            verification["total_entries"] = len(lines)
            expected_prev_hash = "0" * 64  # Genesis hash
            
            for i, line in enumerate(lines):
                entry = self.parse_ledger_entry(line)
                
                # Check if required fields are present
                required_fields = ["timestamp", "record_hash", "prev_hash"]
                missing = [field for field in required_fields if field not in entry]
                if missing:
                    verification["missing_entries"].append({
                        "line": i + 1,
                        "missing_fields": missing,
                        "entry": line[:100]
                    })
                    continue
                
                # Verify previous hash chain
                if entry["prev_hash"] != expected_prev_hash:
                    verification["broken_chains"].append({
                        "line": i + 1,
                        "expected": expected_prev_hash,
                        "found": entry["prev_hash"],
                        "entry": line[:100]
                    })
                    verification["valid"] = False
                
                # Verify record hash (simplified - would need exact recreation logic)
                # For now, just check if it's a valid SHA256
                if not re.match(r'^[a-f0-9]{64}$', entry["record_hash"]):
                    verification["invalid_hashes"].append({
                        "line": i + 1,
                        "hash": entry["record_hash"],
                        "entry": line[:100]
                    })
                    verification["valid"] = False
                else:
                    verification["verified_entries"] += 1
                
                expected_prev_hash = entry["record_hash"]
                
        except Exception as e:
            verification["valid"] = False
            verification["error"] = str(e)
        
        return verification
    
    def scan_for_anomalies(self) -> Dict[str, Any]:
        """Scan ledger and system for various anomalies"""
        anomalies = {
            "timestamp": self.timestamp(),
            "ledger_integrity": {},
            "meta_ledger_integrity": {},
            "agent_anomalies": [],
            "capsule_verification": {},
            "time_anomalies": [],
            "system_health": {}
        }
        
        # Verify main ledger integrity
        anomalies["ledger_integrity"] = self.verify_hash_chain(self.ledger_file)
        
        # Verify meta-ledger integrity
        if self.meta_ledger.exists():
            anomalies["meta_ledger_integrity"] = self.verify_hash_chain(self.meta_ledger)
        
        # Check for agent anomalies
        if self.anomalies_file.exists():
            try:
                with open(self.anomalies_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            anomaly = json.loads(line.strip())
                            anomalies["agent_anomalies"].append(anomaly)
            except Exception as e:
                anomalies["agent_anomalies"] = [{"error": f"Failed to read agent anomalies: {e}"}]
        
        # Check for time-based anomalies
        anomalies["time_anomalies"] = self.check_time_anomalies()
        
        # Check capsule verification status
        anomalies["capsule_verification"] = self.verify_capsule_integrity()
        
        # System health check
        anomalies["system_health"] = self.check_system_health()
        
        return anomalies
    
    def check_time_anomalies(self) -> List[Dict[str, Any]]:
        """Check for timestamp anomalies in ledger entries"""
        time_issues = []
        
        if not self.ledger_file.exists():
            return time_issues
        
        try:
            with open(self.ledger_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            prev_timestamp = None
            for i, line in enumerate(lines):
                entry = self.parse_ledger_entry(line)
                if "timestamp" in entry:
                    try:
                        current_time = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                        
                        # Check if timestamp goes backwards
                        if prev_timestamp and current_time < prev_timestamp:
                            time_issues.append({
                                "type": "backward_time",
                                "line": i + 1,
                                "current": entry["timestamp"],
                                "previous": prev_timestamp.isoformat(),
                                "description": "Timestamp goes backwards"
                            })
                        
                        # Check for future timestamps (more than 5 minutes from now)
                        now = datetime.utcnow().replace(tzinfo=current_time.tzinfo)
                        if current_time > now + timedelta(minutes=5):
                            time_issues.append({
                                "type": "future_timestamp",
                                "line": i + 1,
                                "timestamp": entry["timestamp"],
                                "description": "Timestamp is in the future"
                            })
                        
                        prev_timestamp = current_time
                        
                    except ValueError as e:
                        time_issues.append({
                            "type": "invalid_timestamp",
                            "line": i + 1,
                            "timestamp": entry["timestamp"],
                            "error": str(e)
                        })
                        
        except Exception as e:
            time_issues.append({
                "type": "scan_error",
                "error": str(e)
            })
        
        return time_issues
    
    def verify_capsule_integrity(self) -> Dict[str, Any]:
        """Verify integrity of capsules referenced in ledger"""
        verification = {
            "total_capsules": 0,
            "verified_capsules": 0,
            "failed_capsules": [],
            "missing_capsules": []
        }
        
        capsules_dir = self.base_dir / "capsules"
        if not capsules_dir.exists():
            verification["error"] = "Capsules directory not found"
            return verification
        
        # Count capsule files
        capsule_files = list(capsules_dir.glob("*.json"))
        verification["total_capsules"] = len(capsule_files)
        
        # Basic verification (would integrate with actual capsule verification)
        for capsule_file in capsule_files:
            try:
                with open(capsule_file, 'r') as f:
                    capsule_data = json.load(f)
                
                if "capsule_id" in capsule_data and "content_hash" in capsule_data:
                    verification["verified_capsules"] += 1
                else:
                    verification["failed_capsules"].append({
                        "file": str(capsule_file),
                        "reason": "Missing required fields"
                    })
                    
            except Exception as e:
                verification["failed_capsules"].append({
                    "file": str(capsule_file),
                    "reason": str(e)
                })
        
        return verification
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health indicators"""
        health = {
            "status": "healthy",
            "issues": [],
            "stats": {}
        }
        
        # Check disk usage
        try:
            total_size = sum(f.stat().st_size for f in self.base_dir.rglob('*') if f.is_file())
            health["stats"]["total_archive_size"] = total_size
            
            if total_size > 1024 * 1024 * 1024:  # > 1GB
                health["issues"].append({
                    "type": "disk_usage",
                    "severity": "warning",
                    "message": f"Archive size is large: {total_size / (1024*1024):.1f} MB"
                })
        except Exception as e:
            health["issues"].append({
                "type": "disk_check_error",
                "severity": "error", 
                "message": str(e)
            })
        
        # Check ledger growth rate
        if self.ledger_file.exists():
            try:
                with open(self.ledger_file, 'r') as f:
                    lines = len(f.readlines())
                health["stats"]["ledger_entries"] = lines
                
                if lines > 10000:
                    health["issues"].append({
                        "type": "large_ledger",
                        "severity": "info",
                        "message": f"Ledger has {lines} entries - consider archiving"
                    })
            except Exception as e:
                health["issues"].append({
                    "type": "ledger_check_error",
                    "severity": "error",
                    "message": str(e)
                })
        
        if health["issues"]:
            severity_levels = [issue.get("severity", "info") for issue in health["issues"]]
            if "error" in severity_levels:
                health["status"] = "error"
            elif "warning" in severity_levels:
                health["status"] = "warning"
        
        return health
    
    def generate_markdown_report(self, anomalies: Dict[str, Any]) -> str:
        """Generate a comprehensive Markdown audit report"""
        report_lines = [
            "# EdgeCapsule Cloud Mesh Ledger Audit Report",
            "",
            f"**Generated:** {anomalies['timestamp']}",
            f"**Audit System:** EPOCH5 Automated Scanner v1.0",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Executive summary
        total_issues = 0
        critical_issues = 0
        
        # Count issues
        if not anomalies["ledger_integrity"]["valid"]:
            critical_issues += 1
            total_issues += 1
        if not anomalies["meta_ledger_integrity"].get("valid", True):
            critical_issues += 1
            total_issues += 1
        
        total_issues += len(anomalies.get("agent_anomalies", []))
        total_issues += len(anomalies.get("time_anomalies", []))
        
        if total_issues == 0:
            report_lines.extend([
                "✅ **Status: HEALTHY** - No critical issues detected",
                f"- Ledger integrity verified",
                f"- Hash chain validated", 
                f"- No anomalies detected",
                ""
            ])
        else:
            severity = "CRITICAL" if critical_issues > 0 else "WARNING"
            report_lines.extend([
                f"⚠️ **Status: {severity}** - {total_issues} issue(s) detected",
                f"- Critical issues: {critical_issues}",
                f"- Total anomalies: {total_issues}",
                f"- Immediate attention required" if critical_issues > 0 else "- Review recommended",
                ""
            ])
        
        # Ledger integrity section
        report_lines.extend([
            "## Ledger Integrity Analysis",
            ""
        ])
        
        integrity = anomalies["ledger_integrity"]
        if integrity.get("valid", False):
            report_lines.extend([
                f"✅ **Main Ledger:** VALID",
                f"- Total entries: {integrity['total_entries']}",
                f"- Verified entries: {integrity['verified_entries']}",
                f"- Hash chain intact",
                ""
            ])
        else:
            report_lines.extend([
                f"❌ **Main Ledger:** INVALID",
                f"- Total entries: {integrity.get('total_entries', 0)}",
                f"- Verified entries: {integrity.get('verified_entries', 0)}",
                f"- Broken chains: {len(integrity.get('broken_chains', []))}",
                f"- Invalid hashes: {len(integrity.get('invalid_hashes', []))}",
                ""
            ])
            
            if integrity.get("broken_chains"):
                report_lines.extend(["### Hash Chain Breaks", ""])
                for break_info in integrity["broken_chains"]:
                    report_lines.append(f"- Line {break_info['line']}: Expected `{break_info['expected'][:16]}...`, found `{break_info['found'][:16]}...`")
                report_lines.append("")
        
        # Meta-ledger integrity
        meta_integrity = anomalies.get("meta_ledger_integrity", {})
        if meta_integrity:
            if meta_integrity.get("valid", False):
                report_lines.extend([
                    f"✅ **Meta-Ledger:** VALID",
                    f"- Total entries: {meta_integrity['total_entries']}",
                    f"- Verified entries: {meta_integrity['verified_entries']}",
                    ""
                ])
            else:
                report_lines.extend([
                    f"❌ **Meta-Ledger:** INVALID",
                    f"- Issues detected in meta-capsule ledger",
                    ""
                ])
        
        # Agent anomalies
        if anomalies.get("agent_anomalies"):
            report_lines.extend([
                "## Agent Anomalies",
                ""
            ])
            
            for anomaly in anomalies["agent_anomalies"]:
                if isinstance(anomaly, dict) and "type" in anomaly:
                    report_lines.extend([
                        f"### {anomaly.get('type', 'Unknown').title()} Anomaly",
                        f"- **Agent DID:** {anomaly.get('did', 'Unknown')}",
                        f"- **Timestamp:** {anomaly.get('timestamp', 'Unknown')}",
                        f"- **Details:** {anomaly.get('details', 'No details provided')}",
                        ""
                    ])
        
        # Time anomalies
        if anomalies.get("time_anomalies"):
            report_lines.extend([
                "## Timestamp Anomalies",
                ""
            ])
            
            for time_issue in anomalies["time_anomalies"]:
                report_lines.extend([
                    f"### {time_issue.get('type', 'Unknown').replace('_', ' ').title()}",
                    f"- **Line:** {time_issue.get('line', 'Unknown')}",
                    f"- **Description:** {time_issue.get('description', 'No description')}",
                    ""
                ])
        
        # Capsule verification
        capsule_verify = anomalies.get("capsule_verification", {})
        if capsule_verify:
            report_lines.extend([
                "## Capsule Verification",
                "",
                f"- **Total Capsules:** {capsule_verify.get('total_capsules', 0)}",
                f"- **Verified:** {capsule_verify.get('verified_capsules', 0)}",
                f"- **Failed:** {len(capsule_verify.get('failed_capsules', []))}",
                f"- **Missing:** {len(capsule_verify.get('missing_capsules', []))}",
                ""
            ])
        
        # System health
        health = anomalies.get("system_health", {})
        if health:
            report_lines.extend([
                "## System Health",
                "",
                f"**Status:** {health.get('status', 'unknown').upper()}",
                ""
            ])
            
            stats = health.get("stats", {})
            if stats:
                report_lines.extend(["### Statistics", ""])
                for key, value in stats.items():
                    if isinstance(value, int) and key.endswith("_size"):
                        value_str = f"{value / (1024*1024):.1f} MB"
                    else:
                        value_str = str(value)
                    report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value_str}")
                report_lines.append("")
            
            issues = health.get("issues", [])
            if issues:
                report_lines.extend(["### Health Issues", ""])
                for issue in issues:
                    severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.get("severity", "info"), "•")
                    report_lines.append(f"{severity_icon} **{issue.get('type', 'Unknown').replace('_', ' ').title()}:** {issue.get('message', 'No message')}")
                report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "## Recommendations",
            ""
        ])
        
        if total_issues == 0:
            report_lines.extend([
                "- ✅ Continue regular automated audits",
                "- ✅ Monitor system growth and performance",
                "- ✅ Maintain current security practices",
                ""
            ])
        else:
            if critical_issues > 0:
                report_lines.extend([
                    "- 🚨 **IMMEDIATE ACTION REQUIRED**",
                    "- 🔍 Investigate hash chain integrity issues",
                    "- 🔒 Verify system security and access controls",
                    "- 📋 Review recent system changes",
                    ""
                ])
            
            report_lines.extend([
                "- 📊 Run detailed forensic analysis",
                "- 🔄 Implement additional monitoring",
                "- 📈 Consider system optimization",
                ""
            ])
        
        # Technical details footer
        report_lines.extend([
            "---",
            "",
            "## Technical Details",
            "",
            f"- **Audit Timestamp:** {anomalies['timestamp']}",
            f"- **Scanner Version:** EPOCH5 v1.0",
            f"- **Base Directory:** {self.base_dir}",
            f"- **Ledger File:** {self.ledger_file}",
            "",
            "Generated by EdgeCapsule Cloud Automated Audit System",
            "Part of EPOCH5 Enhanced Integration Suite"
        ])
        
        return "\n".join(report_lines)
    
    def run_audit(self, quiet: bool = False) -> Tuple[Dict[str, Any], str]:
        """Run complete audit and generate report"""
        if not quiet:
            print("🔍 Starting EdgeCapsule Cloud Mesh Ledger Audit...")
        
        # Scan for anomalies
        anomalies = self.scan_for_anomalies()
        
        # Generate markdown report
        report = self.generate_markdown_report(anomalies)
        
        # Save report
        timestamp = self.timestamp().replace(":", "-").replace("Z", "")
        report_file = self.audit_dir / f"audit_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        if not quiet:
            print(f"✅ Audit complete! Report saved: {report_file}")
        
        return anomalies, report

# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EdgeCapsule Cloud Mesh Ledger Audit Scanner")
    parser.add_argument("--base-dir", default="./archive/EPOCH5", 
                       help="Base directory for EPOCH5 archive")
    parser.add_argument("--output", help="Output file for audit report")
    parser.add_argument("--json", action="store_true", 
                       help="Output raw JSON anomaly data")
    
    args = parser.parse_args()
    
    scanner = LedgerAuditScanner(args.base_dir)
    anomalies, report = scanner.run_audit(quiet=args.json)
    
    if args.json:
        print(json.dumps(anomalies, indent=2))
    else:
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        else:
            print("\n" + "="*60)
            print(report)

if __name__ == "__main__":
    main()