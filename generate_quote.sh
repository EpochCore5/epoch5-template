#!/bin/bash

# Make the script executable
chmod +x quote_generator.py

# Display help information
echo "========================================"
echo "EPOCH5 Quote Generator Utility"
echo "========================================"
echo "This utility helps generate customized quotes for EPOCH5 Autonomous System."
echo ""
echo "Usage Examples:"
echo ""
echo "1. Basic Quote:"
echo "./generate_quote.sh --customer 'Acme Corp' --tier professional --components 150 --implementation standard"
echo ""
echo "2. Enterprise Quote with Premium Support:"
echo "./generate_quote.sh --customer 'Global Industries' --tier enterprise --components 800 --implementation enterprise --premium-support --years 3"
echo ""
echo "3. Custom Quote with Discount:"
echo "./generate_quote.sh --customer 'Tech Innovators' --tier professional --components 300 --implementation advanced --training 3 --development 40 --discount 0.1 --format html"
echo ""
echo "For full options, run:"
echo "./quote_generator.py --help"
echo ""
echo "========================================"

# Execute the Python script with all arguments passed to this script
./quote_generator.py "$@"
