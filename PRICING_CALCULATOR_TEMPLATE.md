# EPOCH5 Pricing Calculator Template

This document provides a template for creating a pricing calculator spreadsheet for EPOCH5 Autonomous System. You can implement this in Excel, Google Sheets, or any spreadsheet software of your choice.

## Sheet 1: Subscription Calculator

### Input Section

| Parameter | Value | Notes |
|-----------|-------|-------|
| Organization Name | [Customer Name] | |
| Number of Components to Monitor | [Enter Value] | Servers, applications, databases, etc. |
| Expected Autonomous Decisions per Month | [Enter Value] | Estimated remediation actions |
| Data Processing Volume (GB) | [Enter Value] | Telemetry data volume |
| Subscription Term | [Monthly/Annual] | Select one |
| Selected Tier | [Basic/Professional/Enterprise/Custom] | Select one |

### Calculation Section

| Tier | Monthly Price | Annual Price | Components Included | Additional Component Price |
|------|--------------|--------------|---------------------|----------------------------|
| Basic | $499 | $4,990 | 50 | $10 |
| Professional | $1,499 | $14,990 | 200 | $10 |
| Enterprise | $4,999 | $49,990 | Unlimited | $0 |

### Results Section

| Item | Calculation | Amount |
|------|------------|--------|
| Base Subscription | [Based on selected tier and term] | $ |
| Additional Components | [If applicable] | $ |
| Volume Discount | [Based on volume rules] | $ |
| Subtotal | | $ |
| Annual Savings (if annual) | [If annual term selected] | $ |
| **Total Subscription Cost** | | **$** |

## Sheet 2: Implementation Services Calculator

### Input Section

| Parameter | Value | Notes |
|-----------|-------|-------|
| Implementation Package | [Standard/Advanced/Enterprise] | Select one |
| Additional Custom Development Hours | [Enter Value] | If needed |
| Additional Training Days | [Enter Value] | Beyond included days |

### Calculation Section

| Package | Base Price | Included Training | Development |
|---------|-----------|-------------------|-------------|
| Standard | $10,000 | 2 days | Basic setup |
| Advanced | $25,000 | 5 days | Custom dashboards |
| Enterprise | $50,000 | 10 days | Full customization |
| Additional Training | $2,000 per day | | |
| Custom Development | $200 per hour | | |

### Results Section

| Item | Calculation | Amount |
|------|------------|--------|
| Implementation Package | [Based on selection] | $ |
| Additional Training | [Days × Rate] | $ |
| Custom Development | [Hours × Rate] | $ |
| **Total Implementation Cost** | | **$** |

## Sheet 3: ROI Calculator

### Input Section

| Parameter | Value | Notes |
|-----------|-------|-------|
| Current Annual IT Operations Staff Cost | [Enter Value] | Fully loaded cost |
| Current Annual Downtime Hours | [Enter Value] | Estimated hours |
| Cost Per Hour of Downtime | [Enter Value] | Lost productivity + revenue |
| Current Annual Security Incident Count | [Enter Value] | Number of incidents |
| Average Cost Per Security Incident | [Enter Value] | Response + remediation |
| Current Annual Maintenance Hours | [Enter Value] | Manual maintenance |
| IT Staff Hourly Rate | [Enter Value] | Fully loaded cost |

### Calculation Section

| Improvement Category | Typical Improvement | Formula |
|----------------------|---------------------|---------|
| Reduction in Downtime | 70-90% | Current Downtime Hours × Improvement % × Cost Per Hour |
| Security Incident Reduction | 65% | Current Incidents × Improvement % × Cost Per Incident |
| Staff Efficiency Gain | 40% | Maintenance Hours × Improvement % × Hourly Rate |
| Tool Consolidation | 5-10 tools | Based on current tooling costs |

### Results Section

| Savings Category | Annual Savings | 3-Year Savings |
|------------------|---------------|----------------|
| Downtime Reduction | $ | $ |
| Security Incident Reduction | $ | $ |
| Staff Efficiency | $ | $ |
| Tool Consolidation | $ | $ |
| **Total Annual Savings** | **$** | **$** |
| Total Cost of Ownership (3 years) | | $ |
| **Net Savings (3 years)** | | **$** |
| **ROI Percentage** | | **%** |
| **Payback Period (months)** | | **months** |

## Sheet 4: Total Investment Summary

### Summary Table

| Cost Category | Year 1 | Year 2 | Year 3 | Total |
|---------------|--------|--------|--------|-------|
| Subscription | $ | $ | $ | $ |
| Implementation | $ | | | $ |
| Training | $ | $ | $ | $ |
| Support | $ | $ | $ | $ |
| **Total Investment** | **$** | **$** | **$** | **$** |
| Estimated Annual Savings | $ | $ | $ | $ |
| **Net Annual Benefit** | **$** | **$** | **$** | **$** |
| **Cumulative Benefit** | **$** | **$** | **$** | **$** |

### Visual Elements

- Bar chart comparing costs vs. savings over 3 years
- Line chart showing cumulative benefit over time
- Pie chart showing breakdown of savings by category
- ROI and payback period indicators

## Sheet 5: Comparison with Alternatives

### Cost Comparison Table

| Solution Approach | Year 1 Cost | 3-Year TCO | Expected ROI | Payback Period |
|-------------------|------------|------------|-------------|----------------|
| EPOCH5 Autonomous System | $ | $ | % | months |
| Traditional Monitoring Tools | $ | $ | % | months |
| Managed Services Provider | $ | $ | % | months |
| Internal Development | $ | $ | % | months |

### Qualitative Comparison Table

| Capability | EPOCH5 | Traditional Tools | MSP | Internal Development |
|------------|--------|-------------------|-----|----------------------|
| Autonomous Remediation | ✓✓✓ | ✗ | ✓ | ✓ |
| AI-Driven Security | ✓✓✓ | ✗ | ✓ | ✓ |
| Time to Value | ✓✓✓ | ✓ | ✓✓ | ✗ |
| Customizability | ✓✓ | ✓ | ✗ | ✓✓✓ |
| Maintenance Overhead | ✓✓✓ | ✗ | ✓✓ | ✗ |
| Scalability | ✓✓✓ | ✓ | ✓ | ✓ |
| Future-Proofing | ✓✓✓ | ✓ | ✓ | ✓ |

## Implementation Notes

1. Use conditional formatting to highlight ROI and payback periods:
   - Green for ROI > 300% and payback < 6 months
   - Yellow for ROI 100-300% and payback 6-12 months
   - Red for ROI < 100% or payback > 12 months

2. Include dropdown menus for:
   - Subscription tiers
   - Implementation packages
   - Subscription terms

3. Add data validation rules to prevent invalid inputs

4. Include a cover sheet with:
   - Customer name and logo
   - EPOCH5 logo
   - Date prepared
   - Prepared by (sales representative)
   - Contact information

5. Add a notes sheet for:
   - Assumptions used in calculations
   - Implementation timeline
   - Customization options
   - Terms and conditions

6. Protect calculation cells to prevent accidental changes

7. Add print settings for professional output

## Formulas Reference

### Component Pricing
```
IF(Number_of_Components <= Components_Included, 0, 
   (Number_of_Components - Components_Included) * Additional_Component_Price)
```

### Volume Discount
```
IF(Number_of_Components >= 1000, Subtotal * 0.3, 
   IF(Number_of_Components >= 500, Subtotal * 0.2, 
      IF(Number_of_Components >= 100, Subtotal * 0.1, 0)))
```

### ROI Calculation
```
(Total_3Year_Savings - Total_3Year_Cost) / Total_3Year_Cost * 100
```

### Payback Period (Months)
```
(Total_Investment / (Annual_Savings / 12))
```

## Usage Instructions

1. Create a new copy of this spreadsheet for each prospect
2. Fill in the customer information on the cover sheet
3. Walk through each input section with the customer
4. Present the results and summary information
5. Export to PDF for the proposal document
6. Save a copy in the CRM system
