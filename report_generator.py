"""
Automated Report Generator
This script reads data from CSV/Excel files, analyzes it, and generates a formatted PDF report.
"""

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import datetime
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

class ReportGenerator:
    def __init__(self, data_file_path, output_path="report.pdf"):
        """
        Initialize the Report Generator
        
        Args:
            data_file_path (str): Path to the input data file (CSV or Excel)
            output_path (str): Path for the output PDF report
        """
        self.data_file_path = data_file_path
        self.output_path = output_path
        self.data = None
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Subheading style
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.black
        )
    
    def read_data(self):
        """Read data from CSV or Excel file"""
        try:
            file_extension = os.path.splitext(self.data_file_path)[1].lower()
            
            if file_extension == '.csv':
                self.data = pd.read_csv(self.data_file_path)
            elif file_extension in ['.xlsx', '.xls']:
                self.data = pd.read_excel(self.data_file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            print(f"Data loaded successfully. Shape: {self.data.shape}")
            return True
            
        except Exception as e:
            print(f"Error reading data: {e}")
            return False
    
    def analyze_data(self):
        """Perform basic data analysis"""
        if self.data is None:
            print("No data loaded. Please read data first.")
            return None
        
        analysis = {
            'total_records': len(self.data),
            'date_range': None,
            'summary_stats': {},
            'categorical_summary': {}
        }
        
        # Basic info
        analysis['columns'] = list(self.data.columns)
        analysis['data_types'] = self.data.dtypes.to_dict()
        
        # Date range analysis (if date column exists)
        date_columns = []
        for col in self.data.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    self.data[col] = pd.to_datetime(self.data[col])
                    date_columns.append(col)
                except:
                    pass
        
        if date_columns:
            date_col = date_columns[0]  # Use first date column
            analysis['date_range'] = {
                'start': self.data[date_col].min(),
                'end': self.data[date_col].max(),
                'column': date_col
            }
        
        # Numerical columns analysis
        numerical_cols = self.data.select_dtypes(include=['number']).columns
        for col in numerical_cols:
            analysis['summary_stats'][col] = {
                'mean': self.data[col].mean(),
                'median': self.data[col].median(),
                'std': self.data[col].std(),
                'min': self.data[col].min(),
                'max': self.data[col].max(),
                'sum': self.data[col].sum()
            }
        
        # Categorical columns analysis
        categorical_cols = self.data.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col not in date_columns:  # Exclude date columns
                value_counts = self.data[col].value_counts()
                analysis['categorical_summary'][col] = {
                    'unique_values': len(value_counts),
                    'top_values': value_counts.head(5).to_dict()
                }
        
        self.analysis = analysis
        return analysis
    
    def create_charts(self):
        """Create charts for the report"""
        charts = []
        
        if self.data is None:
            return charts
        
        try:
            # Chart 1: Numerical data distribution (if exists)
            numerical_cols = self.data.select_dtypes(include=['number']).columns
            if len(numerical_cols) > 0:
                plt.figure(figsize=(10, 6))
                for i, col in enumerate(numerical_cols[:4]):  # Max 4 columns
                    plt.subplot(2, 2, i+1)
                    self.data[col].hist(bins=20, alpha=0.7)
                    plt.title(f'Distribution of {col}')
                    plt.xlabel(col)
                    plt.ylabel('Frequency')
                
                plt.tight_layout()
                
                # Save directly to file instead of BytesIO
                chart_path = os.path.abspath('temp_numerical_distribution.png')
                plt.savefig(chart_path, format='png', dpi=300, bbox_inches='tight')
                plt.close()
                
                # Verify file was created
                if os.path.exists(chart_path):
                    charts.append(('numerical_distribution.png', chart_path))
                    print(f"Created chart: {chart_path}")
            
            # Chart 2: Categorical data (if exists)
            categorical_cols = self.data.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                col = categorical_cols[0]  # Use first categorical column
                value_counts = self.data[col].value_counts().head(10)
                
                plt.figure(figsize=(10, 6))
                plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
                plt.title(f'Distribution of {col}')
                
                # Save directly to file
                chart_path = os.path.abspath('temp_categorical_distribution.png')
                plt.savefig(chart_path, format='png', dpi=300, bbox_inches='tight')
                plt.close()
                
                # Verify file was created
                if os.path.exists(chart_path):
                    charts.append(('categorical_distribution.png', chart_path))
                    print(f"Created chart: {chart_path}")
            
            # Chart 3: Time series (if date column exists)
            if hasattr(self, 'analysis') and self.analysis.get('date_range'):
                date_col = self.analysis['date_range']['column']
                numerical_cols = self.data.select_dtypes(include=['number']).columns
                
                if len(numerical_cols) > 0:
                    plt.figure(figsize=(12, 6))
                    for col in numerical_cols[:3]:  # Max 3 lines
                        plt.plot(self.data[date_col], self.data[col], marker='o', label=col)
                    
                    plt.title('Time Series Analysis')
                    plt.xlabel('Date')
                    plt.ylabel('Values')
                    plt.legend()
                    plt.xticks(rotation=45)
                    
                    # Save directly to file
                    chart_path = os.path.abspath('temp_time_series.png')
                    plt.savefig(chart_path, format='png', dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    # Verify file was created
                    if os.path.exists(chart_path):
                        charts.append(('time_series.png', chart_path))
                        print(f"Created chart: {chart_path}")
        
        except Exception as e:
            print(f"Error creating charts: {e}")
            # Close any open figures
            plt.close('all')
        
        return charts
    
    def generate_report(self):
        """Generate the complete PDF report"""
        try:
            if not self.read_data():
                return False
            
            analysis = self.analyze_data()
            if analysis is None:
                return False
            
            charts = self.create_charts()
            
            # Create PDF document
            doc = SimpleDocTemplate(self.output_path, pagesize=A4, topMargin=1*inch)
            story = []
            
            # Title
            title = Paragraph("Automated Data Analysis Report", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.3*inch))
            
            # Report metadata
            report_date = datetime.now().strftime("%B %d, %Y")
            metadata = f"""
            <b>Report Generated:</b> {report_date}<br/>
            <b>Data Source:</b> {os.path.basename(self.data_file_path)}<br/>
            <b>Total Records:</b> {analysis['total_records']:,}
            """
            story.append(Paragraph(metadata, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", self.heading_style))
            
            summary_text = f"""
            This report provides a comprehensive analysis of the dataset containing {analysis['total_records']:,} records 
            across {len(analysis['columns'])} columns. The analysis includes statistical summaries, 
            visualizations, and key insights derived from the data.
            """
            
            if analysis['date_range']:
                date_range_text = f"""
                <br/><br/>The data covers the period from {analysis['date_range']['start'].strftime('%B %d, %Y')} 
                to {analysis['date_range']['end'].strftime('%B %d, %Y')}.
                """
                summary_text += date_range_text
            
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Data Overview
            story.append(Paragraph("Data Overview", self.heading_style))
            
            # Create table for column information
            table_data = [['Column Name', 'Data Type', 'Description']]
            for col, dtype in analysis['data_types'].items():
                description = self.get_column_description(col, dtype)
                table_data.append([col, str(dtype), description])
            
            table = Table(table_data, colWidths=[2*inch, 1.5*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.3*inch))
            
            # Statistical Summary
            if analysis['summary_stats']:
                story.append(Paragraph("Statistical Summary", self.heading_style))
                
                for col, stats in analysis['summary_stats'].items():
                    story.append(Paragraph(f"{col} Statistics:", self.subheading_style))
                    
                    stats_text = f"""
                    Mean: {stats['mean']:.2f} | Median: {stats['median']:.2f} | 
                    Standard Deviation: {stats['std']:.2f}<br/>
                    Minimum: {stats['min']:.2f} | Maximum: {stats['max']:.2f} | 
                    Total: {stats['sum']:.2f}
                    """
                    story.append(Paragraph(stats_text, self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Categorical Analysis
            if analysis['categorical_summary']:
                story.append(Paragraph("Categorical Analysis", self.heading_style))
                
                for col, summary in analysis['categorical_summary'].items():
                    story.append(Paragraph(f"{col} Analysis:", self.subheading_style))
                    
                    cat_text = f"Unique values: {summary['unique_values']}<br/><br/>Top values:<br/>"
                    for value, count in summary['top_values'].items():
                        percentage = (count / analysis['total_records']) * 100
                        cat_text += f"• {value}: {count} ({percentage:.1f}%)<br/>"
                    
                    story.append(Paragraph(cat_text, self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Add page break before charts
            story.append(PageBreak())
            
            # Charts section
            chart_files_to_cleanup = []
            if charts:
                story.append(Paragraph("Data Visualizations", self.heading_style))
                
                for chart_name, chart_path in charts:
                    try:
                        # Verify file exists
                        if os.path.exists(chart_path):
                            # Add chart to story (don't delete yet)
                            img = Image(chart_path, width=6*inch, height=3.6*inch)
                            story.append(img)
                            story.append(Spacer(1, 0.2*inch))
                            print(f"Added chart to report: {chart_name}")
                            
                            # Track for cleanup after PDF is built
                            chart_files_to_cleanup.append(chart_path)
                        else:
                            print(f"Warning: Chart file {chart_path} not found, skipping chart")
                    except Exception as e:
                        print(f"Error adding chart {chart_name}: {e}")
                        continue
            else:
                story.append(Paragraph("Data Visualizations", self.heading_style))
                story.append(Paragraph("Charts could not be generated for this dataset.", self.styles['Normal']))
            
            # Sample Data
            story.append(PageBreak())
            story.append(Paragraph("Sample Data", self.heading_style))
            
            # Display first 10 rows of data
            sample_data = self.data.head(10)
            table_data = [list(sample_data.columns)]
            
            for _, row in sample_data.iterrows():
                table_data.append([str(val) for val in row.values])
            
            # Calculate column widths
            num_cols = len(table_data[0])
            col_width = 6.5*inch / num_cols
            
            sample_table = Table(table_data, colWidths=[col_width] * num_cols)
            sample_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(sample_table)
            
            # Build PDF
            doc.build(story)
            
            # Clean up chart files after PDF is built
            for chart_path in chart_files_to_cleanup:
                try:
                    if os.path.exists(chart_path):
                        os.remove(chart_path)
                        print(f"Cleaned up: {chart_path}")
                except Exception as e:
                    print(f"Warning: Could not clean up {chart_path}: {e}")
            
            print(f"Report generated successfully: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return False
        finally:
            # Always clean up temporary files
            self.cleanup_temp_files()
    
    def get_column_description(self, column_name, data_type):
        """Generate description for column based on name and type"""
        col_lower = column_name.lower()
        
        if 'date' in col_lower or 'time' in col_lower:
            return "Date/time information"
        elif 'id' in col_lower:
            return "Identifier field"
        elif 'name' in col_lower:
            return "Name/label field"
        elif 'sales' in col_lower or 'revenue' in col_lower or 'amount' in col_lower:
            return "Financial/sales data"
        elif 'quantity' in col_lower or 'count' in col_lower:
            return "Quantity/count data"
        elif 'region' in col_lower or 'location' in col_lower:
            return "Geographic information"
        elif data_type in ['int64', 'float64']:
            return "Numerical data"
        else:
            return "Categorical data"
    
    def cleanup_temp_files(self):
        """Clean up any temporary chart files"""
        temp_files = [
            'temp_numerical_distribution.png',
            'temp_categorical_distribution.png',
            'temp_time_series.png'
        ]
        
        for temp_file in temp_files:
            temp_path = os.path.abspath(temp_file)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    print(f"Cleaned up: {temp_path}")
                except Exception as e:
                    print(f"Warning: Could not remove {temp_path}: {e}")


def main():
    """Main function to run the report generator"""
    print("=== Automated Report Generator ===")
    print()
    
    # Default data file
    data_file = "sample_data.csv"
    
    # Check if file exists
    if not os.path.exists(data_file):
        print(f"Error: Data file '{data_file}' not found!")
        print("Please ensure the data file exists in the current directory.")
        return
    
    # Generate report
    output_file = f"automated_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    generator = ReportGenerator(data_file, output_file)
    
    print(f"Processing data from: {data_file}")
    print(f"Output report: {output_file}")
    print()
    
    success = generator.generate_report()
    
    if success:
        print("✓ Report generated successfully!")
        print(f"✓ Output saved as: {output_file}")
    else:
        print("✗ Failed to generate report!")


if __name__ == "__main__":
    main()
