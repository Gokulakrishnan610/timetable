import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict, Counter

def load_timetable(file_path):
    """Load timetable data from CSV file."""
    try:
        timetable_df = pd.read_csv(file_path)
        return timetable_df
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def analyze_workload_distribution(timetable_df):
    """Analyze the distribution of teaching workload."""
    # Count assignments per teacher
    teacher_load = timetable_df['Teacher'].value_counts().reset_index()
    teacher_load.columns = ['Teacher', 'AssignmentCount']
    
    # Get departments for each teacher
    teacher_dept = timetable_df.groupby('Teacher')['Department'].first().reset_index()
    
    # Merge to get department info
    teacher_load = pd.merge(teacher_load, teacher_dept, on='Teacher', how='left')
    
    # Calculate statistics
    overall_stats = {
        'Min': teacher_load['AssignmentCount'].min(),
        'Max': teacher_load['AssignmentCount'].max(),
        'Mean': teacher_load['AssignmentCount'].mean(),
        'Median': teacher_load['AssignmentCount'].median(),
        'Std Dev': teacher_load['AssignmentCount'].std()
    }
    
    # Calculate department-wise statistics
    dept_stats = teacher_load.groupby('Department')['AssignmentCount'].agg([
        'count', 'min', 'max', 'mean', 'median', 'std'
    ]).reset_index()
    
    return teacher_load, overall_stats, dept_stats

def generate_comparison_report(expertise_teacher_load, non_expertise_teacher_load, 
                               expertise_stats, non_expertise_stats,
                               expertise_dept_stats, non_expertise_dept_stats):
    """Generate a comparison report for workload distribution."""
    print("\n===== TEACHER WORKLOAD DISTRIBUTION COMPARISON =====")
    
    # Overall statistics
    print("\nOverall Statistics:")
    print(f"{'Metric':<10} {'With Expertise':<15} {'Without Expertise':<15} {'Difference':<10}")
    print(f"{'-'*50}")
    
    for metric in ['Min', 'Max', 'Mean', 'Median', 'Std Dev']:
        expertise_val = expertise_stats[metric]
        non_expertise_val = non_expertise_stats[metric]
        diff = expertise_val - non_expertise_val
        diff_str = f"{diff:.2f}"
        if diff > 0:
            diff_str = f"+{diff:.2f}"
        print(f"{metric:<10} {expertise_val:.2f}{' '*10} {non_expertise_val:.2f}{' '*10} {diff_str}")
    
    # Department statistics
    print("\nDepartment-wise Statistics:")
    
    # Create a combined dataframe for easier comparison
    dept_comparison = pd.merge(
        expertise_dept_stats, 
        non_expertise_dept_stats, 
        on='Department', 
        suffixes=('_expertise', '_non_expertise')
    )
    
    for _, row in dept_comparison.iterrows():
        dept = row['Department']
        print(f"\n  {dept}:")
        print(f"    {'Metric':<10} {'With Expertise':<15} {'Without Expertise':<15} {'Difference':<10}")
        print(f"    {'-'*50}")
        
        for metric in ['count', 'min', 'max', 'mean', 'median', 'std']:
            expertise_val = row[f'{metric}_expertise']
            non_expertise_val = row[f'{metric}_non_expertise']
            diff = expertise_val - non_expertise_val
            diff_str = f"{diff:.2f}"
            if diff > 0:
                diff_str = f"+{diff:.2f}"
            
            metric_name = {
                'count': 'Teachers',
                'min': 'Min',
                'max': 'Max',
                'mean': 'Mean',
                'median': 'Median',
                'std': 'Std Dev'
            }.get(metric, metric)
            
            print(f"    {metric_name:<10} {expertise_val:.2f}{' '*10} {non_expertise_val:.2f}{' '*10} {diff_str}")
    
    # Save comparison data to CSV
    dept_comparison.to_csv('workload_comparison_by_dept.csv', index=False)
    
    return dept_comparison

def visualize_workload_distribution(expertise_teacher_load, non_expertise_teacher_load):
    """Create visualizations for workload distribution comparison."""
    # Create histograms
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 1, 1)
    plt.hist(expertise_teacher_load['AssignmentCount'], bins=range(0, int(expertise_teacher_load['AssignmentCount'].max()) + 2), 
             alpha=0.7, label='With Expertise', color='green')
    plt.axvline(expertise_teacher_load['AssignmentCount'].mean(), color='green', linestyle='dashed', linewidth=2, 
                label=f'Mean: {expertise_teacher_load["AssignmentCount"].mean():.2f}')
    plt.axvline(expertise_teacher_load['AssignmentCount'].median(), color='green', linestyle='dotted', linewidth=2, 
                label=f'Median: {expertise_teacher_load["AssignmentCount"].median():.2f}')
    plt.xlabel('Number of Assignments')
    plt.ylabel('Number of Teachers')
    plt.title('Distribution of Teacher Workload with Expertise-Based Assignments')
    plt.grid(alpha=0.3)
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.hist(non_expertise_teacher_load['AssignmentCount'], bins=range(0, int(non_expertise_teacher_load['AssignmentCount'].max()) + 2), 
             alpha=0.7, label='Without Expertise', color='red')
    plt.axvline(non_expertise_teacher_load['AssignmentCount'].mean(), color='red', linestyle='dashed', linewidth=2, 
                label=f'Mean: {non_expertise_teacher_load["AssignmentCount"].mean():.2f}')
    plt.axvline(non_expertise_teacher_load['AssignmentCount'].median(), color='red', linestyle='dotted', linewidth=2, 
                label=f'Median: {non_expertise_teacher_load["AssignmentCount"].median():.2f}')
    plt.xlabel('Number of Assignments')
    plt.ylabel('Number of Teachers')
    plt.title('Distribution of Teacher Workload without Expertise-Based Assignments')
    plt.grid(alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('workload_distribution_histograms.png')
    print("\nWorkload distribution histograms saved as 'workload_distribution_histograms.png'")
    
    # Create boxplots by department
    plt.figure(figsize=(15, 10))
    
    expertise_dept_boxplot = expertise_teacher_load.pivot(columns='Department', values='AssignmentCount')
    non_expertise_dept_boxplot = non_expertise_teacher_load.pivot(columns='Department', values='AssignmentCount')
    
    plt.subplot(2, 1, 1)
    plt.boxplot([expertise_dept_boxplot[col].dropna() for col in expertise_dept_boxplot.columns],
               labels=expertise_dept_boxplot.columns)
    plt.xlabel('Department')
    plt.ylabel('Number of Assignments')
    plt.title('Department-wise Workload Distribution with Expertise-Based Assignments')
    plt.grid(alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    
    plt.subplot(2, 1, 2)
    plt.boxplot([non_expertise_dept_boxplot[col].dropna() for col in non_expertise_dept_boxplot.columns],
               labels=non_expertise_dept_boxplot.columns)
    plt.xlabel('Department')
    plt.ylabel('Number of Assignments')
    plt.title('Department-wise Workload Distribution without Expertise-Based Assignments')
    plt.grid(alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('workload_distribution_boxplots.png')
    print("Department-wise workload boxplots saved as 'workload_distribution_boxplots.png'")

def main():
    # Paths to timetable files
    expertise_timetable_path = 'master_timetable.csv'
    non_expertise_timetable_path = 'master_timetable_no_expertise.csv'
    
    # Load data
    expertise_timetable = load_timetable(expertise_timetable_path)
    non_expertise_timetable = load_timetable(non_expertise_timetable_path)
    
    if expertise_timetable is None or non_expertise_timetable is None:
        print("Error: Unable to load required data files.")
        return
    
    # Analyze workload distribution
    expertise_teacher_load, expertise_stats, expertise_dept_stats = analyze_workload_distribution(expertise_timetable)
    non_expertise_teacher_load, non_expertise_stats, non_expertise_dept_stats = analyze_workload_distribution(non_expertise_timetable)
    
    # Generate and display comparison report
    dept_comparison = generate_comparison_report(
        expertise_teacher_load, non_expertise_teacher_load,
        expertise_stats, non_expertise_stats,
        expertise_dept_stats, non_expertise_dept_stats
    )
    
    # Create visualizations
    visualize_workload_distribution(expertise_teacher_load, non_expertise_teacher_load)
    
    print("\nWorkload distribution analysis complete!")

if __name__ == "__main__":
    main() 