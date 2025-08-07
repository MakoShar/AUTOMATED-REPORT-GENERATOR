"""
Simple Report Generator Example
This script demonstrates the basic functionality of the automated report generator.
"""

import os
import sys

def simple_example():
    """Run a simple example of the report generator"""
    try:
        from report_generator import ReportGenerator
        import pandas as pd
        
        print("=== Simple Report Generator Example ===")
        print()
        
        # Check if sample data exists
        data_file = "sample_data.csv"
        if not os.path.exists(data_file):
            print(f"Error: {data_file} not found!")
            return
        
        # Load and display basic info about the data
        data = pd.read_csv(data_file)
        print(f"Data loaded: {len(data)} rows, {len(data.columns)} columns")
        print(f"Columns: {', '.join(data.columns)}")
        print()
        
        # Generate report
        generator = ReportGenerator(data_file, "sample_report.pdf")
        success = generator.generate_report()
        
        if success:
            print("✓ Sample report generated successfully!")
            print("✓ Check 'sample_report.pdf' in the current directory")
        else:
            print("✗ Failed to generate sample report")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required packages: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simple_example()
