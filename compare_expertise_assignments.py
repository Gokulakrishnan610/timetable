import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import csv
import random
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

def load_expertise_data(file_path):
    """Load teacher expertise data from CSV file."""
    try:
        expertise_df = pd.read_csv(file_path)
        return expertise_df
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def create_teacher_expertise_map(expertise_df):
    """Create a map of teachers to their expertise areas."""
    teacher_expertise = defaultdict(set)
    
    for _, row in expertise_df.iterrows():
        teacher_id = row['TeacherID']
        subject_area = row['SubjectArea']
        teacher_expertise[teacher_id].add(subject_area)
    
    return teacher_expertise

def analyze_teacher_course_assignments(timetable_df, expertise_map):
    """Analyze how well teacher-course assignments match expertise."""
    assignments = []
    
    for _, row in timetable_df.iterrows():
        teacher = row['Teacher']
        course = row['Course']
        department = row['Department']
        
        # Extract course prefix to determine subject area
        # Assuming course codes follow a pattern like "XX12345" where XX is the subject area
        if course and isinstance(course, str) and len(course) >= 2:
            course_prefix = course[:2]
            
            # Check if teacher has expertise in this subject area
            matches_expertise = course_prefix in expertise_map.get(teacher, set())
            
            assignments.append({
                'Teacher': teacher,
                'Course': course,
                'Department': department,
                'CoursePrefix': course_prefix,
                'MatchesExpertise': matches_expertise
            })
    
    return pd.DataFrame(assignments)

def generate_comparison_report(expertise_df, non_expertise_df):
    """Generate a comparison report between expertise and non-expertise approaches."""
    # Overall statistics
    expertise_total = len(expertise_df)
    expertise_matching = expertise_df['MatchesExpertise'].sum()
    expertise_percentage = (expertise_matching / expertise_total * 100) if expertise_total > 0 else 0
    
    non_expertise_total = len(non_expertise_df)
    non_expertise_matching = non_expertise_df['MatchesExpertise'].sum()
    non_expertise_percentage = (non_expertise_matching / non_expertise_total * 100) if non_expertise_total > 0 else 0
    
    print("\n===== TEACHER-COURSE ASSIGNMENT COMPARISON =====")
    print(f"Total assignments analyzed:")
    print(f"  - With expertise matching: {expertise_total}")
    print(f"  - Without expertise matching: {non_expertise_total}")
    print("\nExpertise matching rates:")
    print(f"  - With expertise matching: {expertise_matching}/{expertise_total} ({expertise_percentage:.2f}%)")
    print(f"  - Without expertise matching: {non_expertise_matching}/{non_expertise_total} ({non_expertise_percentage:.2f}%)")
    
    # Department-wise comparison
    print("\nDepartment-wise comparison:")
    dept_expertise = expertise_df.groupby('Department').agg(
        Total=('MatchesExpertise', 'count'),
        Matching=('MatchesExpertise', 'sum')
    )
    dept_expertise['Percentage'] = (dept_expertise['Matching'] / dept_expertise['Total'] * 100)
    
    dept_non_expertise = non_expertise_df.groupby('Department').agg(
        Total=('MatchesExpertise', 'count'),
        Matching=('MatchesExpertise', 'sum')
    )
    dept_non_expertise['Percentage'] = (dept_non_expertise['Matching'] / dept_non_expertise['Total'] * 100)
    
    comparison_df = pd.DataFrame({
        'With_Expertise_Total': dept_expertise['Total'],
        'With_Expertise_Matching': dept_expertise['Matching'],
        'With_Expertise_Percentage': dept_expertise['Percentage'],
        'Without_Expertise_Total': dept_non_expertise['Total'],
        'Without_Expertise_Matching': dept_non_expertise['Matching'],
        'Without_Expertise_Percentage': dept_non_expertise['Percentage']
    })
    
    comparison_df['Difference'] = comparison_df['With_Expertise_Percentage'] - comparison_df['Without_Expertise_Percentage']
    
    for dept, row in comparison_df.iterrows():
        print(f"\n  {dept}:")
        print(f"    - With expertise: {row['With_Expertise_Matching']}/{row['With_Expertise_Total']} ({row['With_Expertise_Percentage']:.2f}%)")
        print(f"    - Without expertise: {row['Without_Expertise_Matching']}/{row['Without_Expertise_Total']} ({row['Without_Expertise_Percentage']:.2f}%)")
        print(f"    - Improvement: {row['Difference']:.2f}%")
    
    # Save comparison data
    comparison_df.to_csv('expertise_comparison_by_dept.csv')
    
    return comparison_df

def visualize_comparison(comparison_df):
    """Create visualization comparing expertise vs. non-expertise approaches."""
    plt.figure(figsize=(12, 8))
    
    departments = comparison_df.index
    x = np.arange(len(departments))
    width = 0.35
    
    plt.bar(x - width/2, comparison_df['With_Expertise_Percentage'], width, label='With Expertise Matching', color='green')
    plt.bar(x + width/2, comparison_df['Without_Expertise_Percentage'], width, label='Without Expertise Matching', color='red')
    
    plt.xlabel('Department')
    plt.ylabel('Expertise Match Percentage (%)')
    plt.title('Comparison of Teacher-Course Assignment Expertise Matching')
    plt.xticks(x, departments, rotation=45, ha='right')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add percentage labels on bars
    for i, dept in enumerate(departments):
        plt.text(i - width/2, comparison_df.loc[dept, 'With_Expertise_Percentage'] + 2, 
                 f"{comparison_df.loc[dept, 'With_Expertise_Percentage']:.1f}%", 
                 ha='center', va='bottom')
        plt.text(i + width/2, comparison_df.loc[dept, 'Without_Expertise_Percentage'] + 2, 
                 f"{comparison_df.loc[dept, 'Without_Expertise_Percentage']:.1f}%", 
                 ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('expertise_comparison.png')
    print("\nComparison chart saved as 'expertise_comparison.png'")

def main():
    # Paths to timetable files - use default filenames
    expertise_timetable_path = 'master_timetable.csv'
    non_expertise_timetable_path = 'master_timetable_no_expertise.csv'
    expertise_data_path = 'teacher_expertise_data.csv'
    
    # Load data
    expertise_timetable = load_timetable(expertise_timetable_path)
    non_expertise_timetable = load_timetable(non_expertise_timetable_path)
    expertise_data = load_expertise_data(expertise_data_path)
    
    if expertise_timetable is None or non_expertise_timetable is None or expertise_data is None:
        print("Error: Unable to load required data files.")
        return
    
    # Create expertise map
    teacher_expertise_map = create_teacher_expertise_map(expertise_data)
    
    # Analyze timetables
    expertise_analysis = analyze_teacher_course_assignments(expertise_timetable, teacher_expertise_map)
    non_expertise_analysis = analyze_teacher_course_assignments(non_expertise_timetable, teacher_expertise_map)
    
    # Generate and display comparison report
    comparison_df = generate_comparison_report(expertise_analysis, non_expertise_analysis)
    
    # Create visualization
    visualize_comparison(comparison_df)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main() 