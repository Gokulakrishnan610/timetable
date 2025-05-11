#!/usr/bin/env python3
"""
Teacher Expertise Visualization Script

This script processes the teacher expertise data and creates visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

def create_teacher_expertise_chart(expertise_data, save_path='teacher_expertise.png'):
    """Create a chart showing the distribution of teacher expertise across subject areas"""
    # Convert to DataFrame for plotting
    expertise_df = pd.DataFrame({
        'Subject': list(expertise_data.keys()),
        'Teachers': list(expertise_data.values())
    })
    
    # Sort by number of teachers
    expertise_df = expertise_df.sort_values('Teachers', ascending=False)
    
    # Plot
    plt.figure(figsize=(14, 8))
    bars = plt.bar(expertise_df['Subject'], expertise_df['Teachers'], color='goldenrod')
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2., 
            height + 0.1, 
            f'{height:.0f}', 
            ha='center', 
            va='bottom'
        )
    
    plt.title('Teacher Expertise by Subject Area', fontsize=16)
    plt.xlabel('Subject Area')
    plt.ylabel('Number of Teachers')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    
    print(f"Teacher expertise chart saved to {save_path}")

def create_subject_area_heatmap(course_assignments, save_path='subject_expertise_heatmap.png'):
    """Create a heatmap showing which departments have expertise in which subject areas"""
    # Convert dictionary to DataFrame
    departments = sorted(course_assignments.keys())
    subject_areas = sorted(set([area for dept_data in course_assignments.values() 
                             for area in dept_data.keys()]))
    
    data = []
    for dept in departments:
        row = []
        for subject in subject_areas:
            row.append(course_assignments[dept].get(subject, 0))
        data.append(row)
    
    heatmap_df = pd.DataFrame(data, index=departments, columns=subject_areas)
    
    # Create heatmap
    plt.figure(figsize=(16, 10))
    sns.heatmap(
        heatmap_df, 
        annot=True, 
        cmap='YlOrRd', 
        linewidths=0.5, 
        fmt='d',
        cbar_kws={'label': 'Number of Courses'}
    )
    plt.title('Subject Area Expertise by Department', fontsize=16)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    
    print(f"Subject expertise heatmap saved to {save_path}")

def main():
    """Generate expertise visualizations based on saved data"""
    try:
        # Check if expertise data file exists
        expertise_df = pd.read_csv('teacher_expertise_data.csv')
        print(f"Loaded expertise data for {expertise_df['TeacherID'].nunique()} teachers")
        
        # Create expertise count dictionary
        expertise_counts = expertise_df['SubjectArea'].value_counts().to_dict()
        create_teacher_expertise_chart(expertise_counts)
        
        # Create department-subject heatmap
        dept_subject_counts = defaultdict(lambda: defaultdict(int))
        for _, row in expertise_df.iterrows():
            dept_subject_counts[row['Department']][row['SubjectArea']] += 1
        
        create_subject_area_heatmap(dict(dept_subject_counts))
        
        print("Expertise visualizations created successfully!")
    
    except FileNotFoundError:
        print("Teacher expertise data file not found. Please run timetable generator first.")
    except Exception as e:
        print(f"Error creating visualizations: {e}")

if __name__ == "__main__":
    main() 