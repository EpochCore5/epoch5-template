# EPOCH5 Sales Tools

This package provides advanced sales tools for EPOCH5 Autonomous System to help sales teams create accurate quotes and ROI analyses for potential customers.

## Quote Generator

The Quote Generator creates customized quotations based on customer requirements and selected options.

### Features

- Subscription tier pricing (Basic, Professional, Enterprise)
- Implementation package options (Standard, Advanced, Enterprise)
- Additional services (training, custom development, premium support)
- Volume and multi-year discounts
- Customizable output formats (Markdown, HTML, JSON)

### Usage

```bash
./generate_quote.sh --customer "Acme Corp" --tier professional --components 150 --implementation standard
```

For more options:

```bash
./generate_quote.sh --help
```

### Example Options

- `--customer`: Customer name
- `--tier`: Subscription tier (basic, professional, enterprise)
- `--term`: Billing term (monthly, annual)
- `--components`: Number of components to monitor
- `--years`: Contract duration in years
- `--implementation`: Implementation package (standard, advanced, enterprise)
- `--training`: Additional training days
- `--development`: Custom development hours
- `--premium-support`: Include premium support
- `--discount`: Additional discount percentage
- `--format`: Output format (json, md, html)

## ROI Calculator

The ROI Calculator helps demonstrate the financial benefits of implementing EPOCH5 Autonomous System.

### Features

- Labor cost savings analysis
- Incident reduction calculations
- Downtime reduction analysis
- Infrastructure scaling efficiency
- Compliance improvement benefits
- Comprehensive financial metrics (NPV, Payback Period, ROI, Benefit-Cost Ratio)
- Customizable output formats (Markdown, HTML, JSON, CSV)

### Usage

```bash
./calculate_roi.sh --customer "Acme Corp" --implementation 50000 --subscription 14990 --ops-staff 10 --dev-staff 20 --minor-incidents 50 --major-incidents 5 --downtime-hours 24 --infrastructure-cost 500000 --audit-cost 100000 --penalty-risk 200000
```

For more options:

```bash
./calculate_roi.sh --help
```

### Example Options

- `--customer`: Customer name
- `--implementation`: Implementation cost
- `--subscription`: Annual subscription cost
- `--ops-staff`: Number of operations staff affected
- `--dev-staff`: Number of developers affected
- `--exec-staff`: Number of executives affected
- `--minor-incidents`: Number of minor incidents per year
- `--major-incidents`: Number of major incidents per year
- `--critical-incidents`: Number of critical incidents per year
- `--downtime-hours`: Current annual downtime in hours
- `--downtime-cost`: Cost per hour of downtime
- `--infrastructure-cost`: Annual infrastructure cost
- `--audit-cost`: Annual compliance audit cost
- `--penalty-risk`: Annual financial risk from compliance penalties
- `--years`: Number of years for ROI calculation
- `--format`: Output format (json, md, html, csv)

## Customizing Pricing and ROI Data

The tools use configuration files that can be customized:

- `pricing_data.json`: Contains pricing information for quotes
- `roi_data.json`: Contains parameters for ROI calculations

You can modify these files to update pricing, discount rates, or adjust ROI parameters for your specific market and customer needs.

## Output

Both tools generate output files in the following directories:

- Quote Generator: `./quotes/`
- ROI Calculator: `./roi_analyses/`

The files are named with a unique identifier and customer name for easy reference.
