#!/usr/bin/env python3
"""
Script to analyze test coverage from coverage.xml and identify files needing improvement.
"""

import xml.etree.ElementTree as ET
import os
import sys
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def get_coverage_data(xml_file='coverage.xml'):
    """Extract coverage data from coverage.xml file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Get overall coverage
        line_rate = float(root.attrib.get('line-rate', 0)) * 100
        
        # Get coverage for each file
        classes = root.findall('.//class')
        file_coverage = []
        
        for cls in classes:
            filename = cls.attrib.get('filename', '')
            
            # Skip __init__.py and test files
            if filename.endswith('__init__.py') or '/tests/' in filename or filename.startswith('tests/'):
                continue
                
            file_line_rate = float(cls.attrib.get('line-rate', 0)) * 100
            lines_valid = int(cls.attrib.get('lines-valid', 0))
            lines_covered = int(lines_valid * file_line_rate / 100)
            
            file_coverage.append({
                'filename': filename,
                'coverage': file_line_rate,
                'lines_valid': lines_valid,
                'lines_covered': lines_covered
            })
        
        return line_rate, file_coverage
    except Exception as e:
        print(f"Error parsing coverage data: {e}")
        return 0, []

def print_coverage_report(overall_coverage, file_coverage):
    """Print coverage report in a formatted table."""
    # Sort by coverage (ascending)
    file_coverage.sort(key=lambda x: x['coverage'])
    
    # Prepare table data
    table_data = []
    for file_info in file_coverage:
        table_data.append([
            file_info['filename'],
            f"{file_info['coverage']:.2f}%",
            f"{file_info['lines_covered']}/{file_info['lines_valid']}"
        ])
    
    # Print report
    print(f"\nOverall Coverage: {overall_coverage:.2f}%\n")
    print(tabulate(table_data, headers=['File', 'Coverage', 'Lines'], tablefmt='grid'))
    
    # Calculate stats for recommendation
    files_below_target = [f for f in file_coverage if f['coverage'] < 80]
    total_lines_to_cover = sum(f['lines_valid'] - f['lines_covered'] for f in files_below_target)
    
    print(f"\nFiles below 80% target: {len(files_below_target)} of {len(file_coverage)}")
    print(f"Additional lines to cover to reach 80% in all files: {total_lines_to_cover}")

def generate_coverage_chart(overall_coverage, file_coverage, output_file='docs/images/coverage_chart.png'):
    """Generate a visual chart of the coverage data."""
    # Filter out files with no valid lines
    file_coverage = [f for f in file_coverage if f['lines_valid'] > 0]
    
    # Sort by coverage (ascending)
    file_coverage.sort(key=lambda x: x['coverage'])
    
    # Prepare data for plotting
    filenames = [os.path.basename(f['filename']) for f in file_coverage]
    coverages = [f['coverage'] for f in file_coverage]
    
    # Create colors (red for <50%, yellow for 50-80%, green for >80%)
    colors = ['#FF6B6B' if c < 50 else '#FFDD67' if c < 80 else '#4CAF50' for c in coverages]
    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create horizontal bar chart
    y_pos = np.arange(len(filenames))
    ax.barh(y_pos, coverages, align='center', color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(filenames)
    ax.invert_yaxis()  # Labels read top-to-bottom
    
    # Add coverage percentage at the end of each bar
    for i, v in enumerate(coverages):
        ax.text(v + 1, i, f"{v:.1f}%", va='center')
    
    # Add 80% target line
    ax.axvline(x=80, color='green', linestyle='--', alpha=0.7, label='80% Target')
    
    # Add overall coverage line
    ax.axvline(x=overall_coverage, color='blue', linestyle='-', alpha=0.7, 
               label=f'Overall: {overall_coverage:.1f}%')
    
    # Set chart title and labels
    ax.set_title('Test Coverage by File')
    ax.set_xlabel('Coverage (%)')
    ax.set_xlim(0, 105)  # Give space for the percentage text
    
    # Add legend
    ax.legend()
    
    # Add grid lines
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Coverage chart saved to {output_file}")

def generate_progress_chart(coverage_history, output_file='docs/images/coverage_progress.png'):
    """Generate a chart showing coverage progress over time."""
    # Example data - in a real scenario, this would be read from a file or database
    # Format: [(date, coverage_percentage), ...]
    if not coverage_history:
        coverage_history = [
            ('Initial', 35.37),
            ('Target', 80.0)
        ]
    
    # Extract data
    dates, coverages = zip(*coverage_history)
    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create line chart
    ax.plot(dates, coverages, marker='o', linestyle='-', linewidth=2, markersize=8)
    
    # Add target line
    ax.axhline(y=80, color='green', linestyle='--', alpha=0.7, label='80% Target')
    
    # Set chart title and labels
    ax.set_title('Test Coverage Progress')
    ax.set_ylabel('Coverage (%)')
    ax.set_ylim(0, 100)
    
    # Rotate x-axis labels if needed
    plt.xticks(rotation=45)
    
    # Add grid lines
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add legend
    ax.legend()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Progress chart saved to {output_file}")

def generate_prioritized_task_list(file_coverage):
    """Generate a prioritized list of testing tasks."""
    # Sort files by a priority score (lower coverage = higher priority)
    prioritized_files = sorted(file_coverage, key=lambda x: (
        x['coverage'],           # Sort by coverage (ascending)
        -x['lines_valid']        # For ties, sort by number of valid lines (descending)
    ))
    
    # Create tasks based on priority
    tasks = []
    for idx, file_info in enumerate(prioritized_files):
        filename = file_info['filename']
        base_filename = os.path.basename(filename)
        test_filename = f"test_{base_filename}"
        
        # Calculate target number of lines to cover
        current_covered = file_info['lines_covered']
        target_covered = int(file_info['lines_valid'] * 0.8)
        additional_lines_needed = max(0, target_covered - current_covered)
        
        # Determine priority based on coverage
        if file_info['coverage'] < 50:
            priority = "High"
        elif file_info['coverage'] < 80:
            priority = "Medium" 
        else:
            priority = "Low"
            
        tasks.append({
            'file': filename,
            'test_file': f"tests/{test_filename}",
            'coverage': file_info['coverage'],
            'priority': priority,
            'lines_to_add': additional_lines_needed
        })
    
    # Print tasks as markdown
    print("\n## Prioritized Testing Tasks\n")
    print("| Priority | File | Current Coverage | Lines to Add | Test File |")
    print("|----------|------|------------------|--------------|-----------|")
    
    for task in tasks:
        print(f"| {task['priority']} | {task['file']} | {task['coverage']:.2f}% | {task['lines_to_add']} | {task['test_file']} |")

if __name__ == '__main__':
    coverage_file = 'coverage.xml'
    if len(sys.argv) > 1:
        coverage_file = sys.argv[1]
    
    overall_coverage, file_coverage = get_coverage_data(coverage_file)
    print_coverage_report(overall_coverage, file_coverage)
    generate_coverage_chart(overall_coverage, file_coverage)
    generate_progress_chart([
        ('Current', overall_coverage),
        ('Target', 80.0)
    ])
    generate_prioritized_task_list(file_coverage)
