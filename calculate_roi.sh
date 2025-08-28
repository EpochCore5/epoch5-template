#!/bin/bash

# Make the script executable
chmod +x roi_calculator.py

# Display help information
echo "========================================"
echo "EPOCH5 ROI Calculator Utility"
echo "========================================"
echo "This utility helps calculate ROI for EPOCH5 Autonomous System."
echo ""
echo "Usage Examples:"
echo ""
echo "1. Basic ROI Analysis:"
echo "./calculate_roi.sh --customer 'Acme Corp' --implementation 50000 --subscription 14990 --ops-staff 10 --dev-staff 20 --minor-incidents 50 --major-incidents 5 --downtime-hours 24 --infrastructure-cost 500000 --audit-cost 100000 --penalty-risk 200000"
echo ""
echo "2. Enterprise ROI Analysis for 5 Years:"
echo "./calculate_roi.sh --customer 'Global Industries' --implementation 100000 --subscription 49990 --ops-staff 30 --dev-staff 100 --exec-staff 5 --minor-incidents 200 --major-incidents 20 --critical-incidents 2 --downtime-hours 48 --downtime-cost 20000 --infrastructure-cost 2000000 --audit-cost 500000 --penalty-risk 1000000 --years 5"
echo ""
echo "3. Custom Output Format:"
echo "./calculate_roi.sh --customer 'Tech Innovators' --implementation 25000 --subscription 14990 --ops-staff 5 --dev-staff 15 --minor-incidents 20 --major-incidents 2 --downtime-hours 12 --infrastructure-cost 300000 --audit-cost 50000 --penalty-risk 100000 --format html"
echo ""
echo "For full options, run:"
echo "./roi_calculator.py --help"
echo ""
echo "========================================"

# Execute the Python script with all arguments passed to this script
./roi_calculator.py "$@"
