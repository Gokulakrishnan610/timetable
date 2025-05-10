#!/usr/bin/env python3
"""
Timetable System Runner

This script runs the entire timetable generation and visualization process.
"""

import os
import sys
import time
from timetable_generator import TimetableGenerator
import visualize_timetable

def main():
    """Main function to run the timetable system"""
    print("=" * 80)
    print("COLLEGE TIMETABLE GENERATION SYSTEM")
    print("=" * 80)
    
    # Check if data directory exists
    if not os.path.exists('data'):
        print("Error: 'data' directory not found.")
        print("Please create a 'data' directory with the required CSV files.")
        return
    
    # Generate timetable
    print("\nSTEP 1: GENERATING TIMETABLE")
    print("-" * 40)
    start_time = time.time()
    
    generator = TimetableGenerator()
    success = generator.generate_timetable()
    
    generation_time = time.time() - start_time
    print(f"Timetable generation completed in {generation_time:.2f} seconds.")
    
    if not success:
        print("Timetable generation did not produce a feasible solution.")
        print("Please check your constraints and try again.")
        return
    
    # Create visualizations
    print("\nSTEP 2: CREATING VISUALIZATIONS")
    print("-" * 40)
    visualization_start = time.time()
    
    visualize_timetable.create_charts()
    
    visualization_time = time.time() - visualization_start
    print(f"Visualization completed in {visualization_time:.2f} seconds.")
    
    # Summary
    print("\nSUMMARY")
    print("-" * 40)
    print(f"Total processing time: {(generation_time + visualization_time):.2f} seconds")
    print("\nOutput files:")
    print("  - master_timetable.csv (Complete timetable)")
    print("  - Individual teacher timetables (timetable_teacher_*.csv)")
    print("  - Visualization charts:")
    print("    * timetable_heatmap.png (Overall class density)")
    print("    * teacher_load.png (Teaching load by teacher)")
    print("    * room_usage.png (Room utilization)")
    print("    * course_distribution.png (Classes per course)")
    print("    * department_load.png (Teaching load by department)")
    print("    * schedule_dept_*.png (Department schedules)")
    print("    * schedule_*.png (Individual teacher schedules)")
    
    print("\nComplete! You can now review the generated timetable files and visualizations.")

if __name__ == "__main__":
    main() 