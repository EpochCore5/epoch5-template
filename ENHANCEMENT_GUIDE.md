# EdgeCapsule Cloud Mesh Ledger Enhancement Guide

**Version:** 1.0.0  
**Author:** EpochCore Business  
**Contact:** jryan2k19@gmail.com  
**Last Updated:** August 26, 2025  

---

## Overview

This guide provides comprehensive installation and usage instructions for the three value-compounding enhancements added to the EdgeCapsule Cloud mesh ledger system:

1. **Automated Audit & Markdown Reporting** - Detect anomalies and generate detailed audit reports
2. **SVG Ledger Visualization** - Convert mesh topology to visual graphs for analysis  
3. **REST API Access** - Programmatic access to ledger, capsules, and audit reports

These enhancements build upon the existing EPOCH5 architecture, providing enterprise-grade monitoring, visualization, and integration capabilities for EdgeCapsule Cloud deployments.

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- EPOCH5 template repository (this repository)
- Graphviz (for SVG generation)
- Flask and dependencies (for REST API)

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/EpochCore5/epoch5-template.git
   cd epoch5-template
   ```

2. **Install Python dependencies**:
   ```bash
   pip install flask flask-cors
   ```

3. **Install Graphviz** (for SVG visualization):
   ```bash
   # Ubuntu/Debian
   sudo apt install graphviz
   
   # macOS
   brew install graphviz
   
   # Windows
   # Download from https://graphviz.org/download/
   ```

4. **Verify installation**:
   ```bash
   python3 audit_scanner.py --help
   python3 svg_visualizer.py check
   python3 rest_api.py --help
   ```

---

## 1. Automated Audit & Markdown Reporting

### Overview

The audit scanner automatically analyzes your EPOCH5 ledger for:
- Hash chain integrity violations
- Timestamp anomalies  
- Agent behavior anomalies
- Capsule verification failures
- System health issues

### Basic Usage

**Run a complete audit**:
```bash
python3 audit_scanner.py
```

**Save report to specific file**:
```bash
python3 audit_scanner.py --output my_audit_report.md
```

**Get raw JSON data**:
```bash
python3 audit_scanner.py --json > audit_data.json
```

**Custom base directory**:
```bash
python3 audit_scanner.py --base-dir /path/to/your/epoch5/archive
```

### Sample Output

The audit scanner generates comprehensive Markdown reports:

```markdown
# EdgeCapsule Cloud Mesh Ledger Audit Report

**Generated:** 2025-08-26T18:00:00Z
**Audit System:** EPOCH5 Automated Scanner v1.0

## Executive Summary

✅ **Status: HEALTHY** - No critical issues detected
- Ledger integrity verified
- Hash chain validated
- No anomalies detected

## Ledger Integrity Analysis

✅ **Main Ledger:** VALID
- Total entries: 1,245
- Verified entries: 1,245
- Hash chain intact
```

### Integration Examples

**Schedule regular audits** (cron job):
```bash
# Daily audit at 2 AM
0 2 * * * cd /path/to/epoch5-template && python3 audit_scanner.py --output daily_audit_$(date +\%Y\%m\%d).md
```

**Alert on critical issues**:
```bash
#!/bin/bash
python3 audit_scanner.py --json > /tmp/audit.json
if grep -q '"valid": false' /tmp/audit.json; then
  echo "CRITICAL: Ledger integrity compromised!" | mail -s "EPOCH5 Alert" admin@company.com
fi
```

---

## 2. SVG Ledger Visualization

### Overview

The SVG visualizer converts DAG mesh topology into visual graphs showing:
- Task dependencies (primary connections)
- Fault tolerance mesh (secondary connections)
- Node status and health
- System overview diagrams

### Basic Usage

**Check Graphviz installation**:
```bash
python3 svg_visualizer.py check
```

**List available DAGs**:
```bash
python3 svg_visualizer.py list
```

**Generate visualization for specific DAG**:
```bash
python3 svg_visualizer.py generate my-dag-id
```

**Generate system overview**:
```bash
python3 svg_visualizer.py overview
```

**Generate all visualizations**:
```bash
python3 svg_visualizer.py all
```

### Visualization Features

The generated SVG files include:
- **Color-coded nodes** based on fault tolerance levels:
  - 🟢 Green: High fault tolerance (3+ backup paths)
  - 🔵 Blue: Medium fault tolerance (2 backup paths)  
  - 🟡 Yellow: Low fault tolerance (1 backup path)
- **Connection types**:
  - Solid blue lines: Primary dependencies
  - Dashed gray lines: Mesh fault tolerance connections
- **Interactive legend** explaining the visualization

### Sample DAG Creation

Create a sample DAG to visualize:

1. **Create task definition file** (`sample_tasks.json`):
   ```json
   {
     "description": "Sample EdgeCapsule processing pipeline",
     "tasks": [
       {
         "task_id": "data_ingestion",
         "command": "python3 ingest_data.py",
         "dependencies": [],
         "timeout": 300
       },
       {
         "task_id": "data_validation", 
         "command": "python3 validate_data.py",
         "dependencies": ["data_ingestion"],
         "timeout": 600
       },
       {
         "task_id": "capsule_creation",
         "command": "python3 create_capsules.py",
         "dependencies": ["data_validation"],
         "timeout": 900
       }
     ]
   }
   ```

2. **Create the DAG**:
   ```bash
   python3 dag_management.py create sample-pipeline sample_tasks.json
   ```

3. **Generate visualization**:
   ```bash
   python3 svg_visualizer.py generate sample-pipeline
   ```

4. **View the SVG** (will be in `archive/EPOCH5/visualizations/`):
   ```bash
   firefox archive/EPOCH5/visualizations/sample-pipeline_mesh_links.svg
   ```

---

## 3. REST API for Programmatic Access

### Overview

The REST API provides programmatic access to all EPOCH5 components:
- Ledger entries and hash chain data
- Capsule storage and verification
- Audit reports and system health
- Visualization generation and access
- Meta-capsule management

### Starting the API Server

**Basic server** (localhost only):
```bash
python3 rest_api.py
```

**Server accessible from network**:
```bash
python3 rest_api.py --host 0.0.0.0 --port 5000
```

**Debug mode** (for development):
```bash
python3 rest_api.py --debug
```

**Custom base directory**:
```bash
python3 rest_api.py --base-dir /path/to/epoch5/archive
```

### API Endpoints Reference

#### System Status
- `GET /` - API documentation and endpoint list
- `GET /health` - Service health check
- `GET /api/system/status` - Comprehensive system status

#### Ledger Access
- `GET /api/ledger` - List ledger entries (paginated)
  - Query params: `limit`, `offset`
- `GET /api/ledger/{line_number}` - Get specific ledger entry

#### Capsule Management  
- `GET /api/capsules` - List all capsules
- `GET /api/capsules/{capsule_id}` - Get specific capsule data
- `GET /api/capsules/{capsule_id}/verify` - Verify capsule integrity
- `GET /api/capsules/{capsule_id}/download` - Download capsule file

#### Audit & Reporting
- `POST /api/audit/run` - Run audit scan and get results
- `GET /api/audit/reports` - List available audit reports  
- `GET /api/audit/reports/{filename}` - Get specific audit report
- `GET /api/audit/reports/{filename}/download` - Download report

#### Visualization
- `GET /api/visualization/dags` - List visualizable DAGs
- `POST /api/visualization/generate/{dag_id}` - Generate visualization  
- `GET /api/visualization/svg/{dag_id}` - Get SVG file
- `GET /api/visualization/dot/{dag_id}` - Get DOT source file
- `GET /api/visualization/overview` - Get system overview SVG

#### Meta-Capsules
- `GET /api/meta-capsules` - List meta-capsules
- `GET /api/meta-capsules/{meta_id}` - Get specific meta-capsule
- `GET /api/meta-capsules/{meta_id}/verify` - Verify meta-capsule

### API Usage Examples

**Get system status**:
```bash
curl http://localhost:5000/api/system/status | jq .
```

**List recent ledger entries**:
```bash
curl "http://localhost:5000/api/ledger?limit=10&offset=0" | jq .
```

**Run audit and get results**:
```bash
curl -X POST http://localhost:5000/api/audit/run | jq .
```

**Generate DAG visualization**:
```bash
curl -X POST http://localhost:5000/api/visualization/generate/my-dag-id | jq .
```

**Download SVG visualization**:
```bash
curl http://localhost:5000/api/visualization/svg/my-dag-id > my-dag.svg
```

### Python Client Example

```python
import requests
import json

# API base URL
BASE_URL = "http://localhost:5000"

# Get system status
response = requests.get(f"{BASE_URL}/api/system/status")
status = response.json()
print(f"System Status: {status['status']}")
print(f"Ledger Entries: {status['statistics']['ledger_entries']}")

# Run audit
response = requests.post(f"{BASE_URL}/api/audit/run")
audit_results = response.json()
print(f"Audit Status: {'HEALTHY' if audit_results['audit_results']['ledger_integrity']['valid'] else 'ISSUES DETECTED'}")

# List capsules
response = requests.get(f"{BASE_URL}/api/capsules")
capsules = response.json()
print(f"Total Capsules: {capsules['total']}")

# Generate visualization
dag_id = "my-pipeline"
response = requests.post(f"{BASE_URL}/api/visualization/generate/{dag_id}")
viz_result = response.json()
if viz_result['visualization_result']['status'] == 'success':
    print(f"Visualization generated: {viz_result['visualization_result']['svg_file']}")
```

---

## EdgeCapsule Cloud Integration

### Business Model Integration

The enhancements support the EdgeCapsule Cloud business model through multiple value streams:

#### Service Tiers

**Developer Tier ($49/month)**:
- Basic audit reports
- Standard visualizations  
- Limited API calls (10K/month)
- Community support

**Professional Tier ($149/month)**:
- Real-time audit alerts
- Advanced visualizations
- Full API access (100K calls/month)
- Priority support

**Enterprise Tier ($499/month)**:
- Custom audit rules
- White-label visualizations
- Unlimited API access
- Dedicated support

### Example Integration Scenarios

#### Supply Chain Tracking
```json
{
  "use_case": "Product authenticity verification",
  "capsule_content": "product_certifications",  
  "audit_frequency": "daily",
  "visualization_type": "supply_flow_diagram",
  "api_integration": "real_time_tracking"
}
```

#### Financial Services  
```json
{
  "use_case": "Regulatory compliance ledger",
  "capsule_content": "transaction_records",
  "audit_frequency": "real_time", 
  "visualization_type": "transaction_mesh",
  "api_integration": "compliance_reporting"
}
```

#### Healthcare Network
```json
{
  "use_case": "Patient data integrity",
  "capsule_content": "medical_records",
  "audit_frequency": "per_access",
  "visualization_type": "data_lineage_graph", 
  "api_integration": "hipaa_audit_trails"
}
```

---

## Advanced Configuration

### Custom Audit Rules

Create custom audit rules by extending the `LedgerAuditScanner` class:

```python
from audit_scanner import LedgerAuditScanner

class CustomAuditScanner(LedgerAuditScanner):
    def check_custom_business_rules(self):
        """Add custom business logic validation"""
        issues = []
        
        # Example: Check for suspicious transaction patterns
        if self.detect_unusual_patterns():
            issues.append({
                "type": "suspicious_pattern",
                "severity": "warning",
                "message": "Unusual transaction pattern detected"
            })
        
        return issues
```

### Custom Visualization Themes

Modify visualization appearance:

```python
from svg_visualizer import SVGLedgerVisualizer

class CustomVisualizer(SVGLedgerVisualizer):
    def apply_custom_theme(self, dot_content):
        """Apply custom styling to DOT content"""
        # Add custom colors, fonts, layouts
        custom_styles = '''
        node [fontname="Arial", fontsize=12];
        edge [fontname="Arial", fontsize=10];
        '''
        return dot_content.replace('digraph', f'digraph\n{custom_styles}')
```

### API Authentication

Add authentication to the REST API:

```python
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to protected endpoints
@app.route('/api/audit/run')
@require_api_key
def run_audit():
    # Protected endpoint
    pass
```

---

## Monitoring and Alerting

### Setting Up Monitoring

**System health monitoring**:
```bash
#!/bin/bash
# health_monitor.sh
while true; do
  STATUS=$(curl -s http://localhost:5000/health | jq -r '.status')
  if [ "$STATUS" != "healthy" ]; then
    echo "$(date): API health check failed" >> /var/log/epoch5_monitor.log
    # Send alert
  fi
  sleep 300  # Check every 5 minutes
done
```

**Ledger integrity monitoring**:
```bash
#!/bin/bash
# integrity_monitor.sh  
python3 audit_scanner.py --json > /tmp/audit_check.json
VALID=$(jq -r '.ledger_integrity.valid' /tmp/audit_check.json)
if [ "$VALID" != "true" ]; then
  echo "CRITICAL: Ledger integrity compromised at $(date)" | \
    mail -s "EPOCH5 Critical Alert" admin@company.com
fi
```

### Grafana Dashboard Integration

Export metrics for Grafana monitoring:

```python
import requests
import time
from prometheus_client import start_http_server, Gauge, Counter

# Prometheus metrics
ledger_entries_gauge = Gauge('epoch5_ledger_entries_total', 'Total ledger entries')
audit_health_gauge = Gauge('epoch5_audit_health', 'Audit health status (1=healthy, 0=issues)')
api_requests_counter = Counter('epoch5_api_requests_total', 'Total API requests', ['endpoint'])

def collect_metrics():
    """Collect EPOCH5 metrics for monitoring"""
    try:
        # Get system status
        response = requests.get('http://localhost:5000/api/system/status')
        status = response.json()
        
        # Update metrics
        ledger_entries_gauge.set(status['statistics']['ledger_entries'])
        audit_health_gauge.set(1 if status['ledger_integrity'] else 0)
        
    except Exception as e:
        print(f"Metrics collection failed: {e}")

# Start Prometheus metrics server
start_http_server(8000)
while True:
    collect_metrics()
    time.sleep(60)
```

---

## Troubleshooting

### Common Issues

**1. Graphviz not found**:
```
❌ Graphviz is not installed
```
**Solution**: Install Graphviz for your platform (see Installation section)

**2. Flask not available**:  
```
❌ Flask is required to run the REST API
```
**Solution**: `pip install flask flask-cors`

**3. Permission denied on ledger files**:
```
FileNotFoundError: [Errno 13] Permission denied: 'archive/EPOCH5/ledger.log'
```
**Solution**: Check file permissions and ensure the process has read access

**4. Port already in use**:
```
OSError: [Errno 98] Address already in use
```
**Solution**: Use different port with `--port 5001` or kill existing process

**5. Large ledger performance issues**:
```
Audit taking too long on large ledgers
```
**Solution**: Use pagination parameters and consider implementing ledger rotation

### Debug Mode

Enable verbose logging:

```bash
# Set debug environment variable
export EPOCH5_DEBUG=1

# Run components with debug output  
python3 audit_scanner.py --json | jq .
python3 svg_visualizer.py --help
python3 rest_api.py --debug
```

### Log Analysis

Check system logs for issues:

```bash
# View recent audit logs
tail -f archive/EPOCH5/audits/audit_report_*.md

# Check API access logs  
grep "ERROR" /var/log/flask.log

# Monitor system resource usage
top -p $(pgrep -f rest_api.py)
```

---

## Performance Optimization

### Large-Scale Deployments

**Ledger optimization**:
- Implement ledger rotation for files >100MB
- Use database backend for enterprise deployments
- Enable compression for archived ledger files

**API optimization**:
- Deploy with production WSGI server (gunicorn/uWSGI)
- Implement caching for frequently accessed data
- Use load balancer for multiple API instances

**Visualization optimization**:
- Cache generated SVG files
- Use background job queue for large visualizations
- Implement lazy loading for complex diagrams

### Resource Requirements

**Minimum requirements**:
- CPU: 2 cores
- RAM: 4GB  
- Storage: 10GB
- Network: 100Mbps

**Recommended for production**:
- CPU: 8 cores
- RAM: 16GB
- Storage: 100GB SSD
- Network: 1Gbps

---

## Security Considerations

### Access Control

- API authentication and authorization
- Network-level access controls
- Audit trail for all administrative actions
- Regular security scans

### Data Protection  

- Encryption at rest for sensitive capsules
- TLS/SSL for API communications  
- Regular backup and recovery testing
- Compliance with data protection regulations

---

## Support and Licensing

### Commercial Support

**EpochCore Business** provides commercial support and licensing for EdgeCapsule Cloud:

- **Email**: jryan2k19@gmail.com  
- **Documentation**: https://github.com/EpochCore5/epoch5-template
- **License**: Commercial - All Rights Reserved

### Support Tiers

- **Community**: GitHub issues and documentation
- **Professional**: Email support with 24-48h response
- **Enterprise**: Dedicated support with custom SLAs

---

## Contributing

While this is a commercial product, we welcome feedback and feature requests:

1. Report issues on GitHub
2. Submit feature requests via email
3. Request custom integrations for enterprise customers

---

**Copyright (c) 2024 John Ryan, EpochCore Business, Charlotte NC. All rights reserved.**

For commercial licensing, partnerships, or custom development, contact: jryan2k19@gmail.com