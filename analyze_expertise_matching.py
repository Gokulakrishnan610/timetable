#!/usr/bin/env python3
"""
Expertise Matching Analysis Script

This script analyzes how well the expertise-based assignments worked in the generated timetable.
"""

import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import os

def load_data():
    """Load the timetable and expertise data"""
    if not os.path.exists('master_timetable.csv'):
        print("Error: master_timetable.csv not found!")
        return None, None
    
    if not os.path.exists('teacher_expertise_data.csv'):
        print("Error: teacher_expertise_data.csv not found!")
        return None, None
    
    timetable_df = pd.read_csv('master_timetable.csv')
    expertise_df = pd.read_csv('teacher_expertise_data.csv')
    
    return timetable_df, expertise_df

def analyze_matching(timetable_df, expertise_df):
    """Analyze how well teacher expertise matches assigned courses"""
    # Create a dictionary mapping teachers to their expertise areas
    teacher_expertise = defaultdict(set)
    for _, row in expertise_df.iterrows():
        teacher_expertise[row['TeacherID']].add(row['SubjectArea'])
    
    # Extract subject areas from course codes in the timetable
    timetable_df['SubjectArea'] = timetable_df['Course'].str[:2]
    
    # Check if teachers are teaching in their expertise areas
    match_results = []
    for _, row in timetable_df.iterrows():
        teacher = row['Teacher']
        subject = row['SubjectArea']
        expertise_areas = teacher_expertise.get(teacher, set())
        
        match_results.append({
            'Teacher': teacher,
            'TeacherName': teacher.split('@')[0],
            'Department': row['Department'],
            'Course': row['Course'],
            'SubjectArea': subject,
            'ExpertiseMatch': subject in expertise_areas,
            'NumExpertiseAreas': len(expertise_areas)
        })
    
    return pd.DataFrame(match_results)

def generate_report(analysis_df):
    """Generate a report of the expertise matching analysis"""
    if analysis_df is None:
        return
    
    total_assignments = len(analysis_df)
    matching_assignments = analysis_df['ExpertiseMatch'].sum()
    matching_percentage = (matching_assignments / total_assignments) * 100 if total_assignments > 0 else 0
    
    print("\n===== EXPERTISE MATCHING ANALYSIS =====")
    print(f"Total assignments: {total_assignments}")
    print(f"Expertise-matching assignments: {matching_assignments} ({matching_percentage:.2f}%)")
    
    # Summary by department
    dept_summary = analysis_df.groupby('Department').agg({
        'ExpertiseMatch': ['sum', 'count']
    })
    dept_summary['percentage'] = (dept_summary[('ExpertiseMatch', 'sum')] / 
                                 dept_summary[('ExpertiseMatch', 'count')] * 100)
    
    print("\nExpertise matching by department:")
    for dept, data in dept_summary.iterrows():
        matches = data[('ExpertiseMatch', 'sum')]
        total = data[('ExpertiseMatch', 'count')]
        percentage = data['percentage']
        print(f"  {dept}: {int(matches)}/{int(total)} ({float(percentage):.2f}%)")
    
    # Summary for teachers with most assignments
    teacher_summary = analysis_df.groupby(['TeacherName', 'Teacher']).agg({
        'ExpertiseMatch': ['sum', 'count']
    }).sort_values(('ExpertiseMatch', 'count'), ascending=False)
    teacher_summary['percentage'] = (teacher_summary[('ExpertiseMatch', 'sum')] / 
                                    teacher_summary[('ExpertiseMatch', 'count')] * 100)
    
    print("\nExpertise matching for top 5 teachers (by assignment count):")
    for (name, _), data in teacher_summary.head(5).iterrows():
        matches = data[('ExpertiseMatch', 'sum')]
        total = data[('ExpertiseMatch', 'count')]
        percentage = data['percentage']
        print(f"  {name}: {int(matches)}/{int(total)} ({float(percentage):.2f}%)")
    
    # Create visualization
    plt.figure(figsize=(10, 6))
    dept_data = dept_summary.reset_index()
    dept_data.columns = ['Department', 'Matches', 'Total', 'Percentage']
    
    # Sort by percentage for better visualization
    dept_data = dept_data.sort_values('Percentage', ascending=True)
    
    plt.barh(dept_data['Department'], dept_data['Percentage'], color='teal')
    plt.xlabel('Expertise Match Percentage')
    plt.ylabel('Department')
    plt.title('Teacher-Course Expertise Matching by Department')
    plt.xlim(0, 100)
    
    # Add percentage labels
    for i, v in enumerate(dept_data['Percentage']):
        plt.text(v + 1, i, f"{float(v):.1f}%", va='center')
    
    plt.tight_layout()
    plt.savefig('expertise_matching_by_dept.png', dpi=300)
    print("\nExpertise matching chart saved as expertise_matching_by_dept.png")
    
    # Also save the analysis to CSV for further review
    analysis_df.to_csv('expertise_matching_analysis.csv', index=False)
    print("Detailed analysis saved to expertise_matching_analysis.csv")

def main():
    """Main function"""
    timetable_df, expertise_df = load_data()
    if timetable_df is None or expertise_df is None:
        return
    
    analysis_df = analyze_matching(timetable_df, expertise_df)
    generate_report(analysis_df)

if __name__ == "__main__":
    main() 