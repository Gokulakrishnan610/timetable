#!/usr/bin/env python3
"""
Timetable System Runner

This script runs the entire timetable generation and visualization process.
"""

import os
import sys
import time
import argparse
import pandas as pd
from timetable_generator import TimetableGenerator
from visualize_timetable import visualize_timetable

def main():
    """Main function to run the timetable system"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate and visualize a timetable.')
    parser.add_argument('--mock', action='store_true', help='Use mock data for testing')
    parser.add_argument('--relaxed', action='store_true', help='Use relaxed constraints (fastest but least realistic)')
    parser.add_argument('--balanced', action='store_true', help='Use balanced constraints (compromise between relaxed and real)')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid constraints (more realistic than balanced, but still feasible)')
    parser.add_argument('--real', action='store_true', help='Use real constraints (most realistic but hardest to solve)')
    parser.add_argument('--reduced', type=bool, default=True, help='Use reduced problem size')
    parser.add_argument('--timeout', type=int, default=1800, 
                        help='Solver timeout in seconds (default: 1800 seconds / 30 minutes). '
                             'Increase this value for more complex constraint modes.')
    parser.add_argument('--adaptive', action='store_true', 
                        help='Enable adaptive constraint relaxation (automatically relaxes constraints if no solution is found)')
    parser.add_argument('--max-attempts', type=int, default=3,
                        help='Maximum number of attempts with different constraint levels when using adaptive mode')
    parser.add_argument('--staggered', action='store_true',
                        help='Enable staggered scheduling to distribute classes more evenly across time slots')
    parser.add_argument('--no-expertise', action='store_true',
                        help='Disable expertise-based teacher assignments')
    args = parser.parse_args()

    # Use mock data or real data
    if args.mock:
        data_dir = 'mockdata'
    else:
        data_dir = 'data'

    # Determine constraint mode - default to balanced if no flag is specified
    constraint_mode = "balanced"
    if args.relaxed:
        constraint_mode = "relaxed"
    elif args.hybrid:
        constraint_mode = "hybrid"
    elif args.real:
        constraint_mode = "real"

    print(f"Using {constraint_mode} constraints mode")
    print(f"Loading data from {data_dir} directory...")
    print(f"Solver timeout set to {args.timeout} seconds ({args.timeout/60:.1f} minutes)")
    
    if args.adaptive:
        print("Adaptive constraint relaxation enabled - will try different constraint levels if needed")
    
    if args.staggered:
        print("Staggered scheduling enabled - classes will be distributed more evenly across time slots")
    
    # Check if data directory exists
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} directory not found. Please make sure it exists.")
        sys.exit(1)

    # Initialize generator
    start_time = time.time()
    generator = TimetableGenerator(data_dir=data_dir)
    
    # If expertise-based assignments are disabled, clear the expertise data
    if args.no_expertise:
        print("Expertise-based teacher assignments disabled")
        generator.teacher_expertise.clear()
        generator.course_subject_area.clear()
    
    # Save teacher expertise data for visualization
    save_expertise_data(generator)
    
    # Set solver timeout
    solver_timeout = args.timeout
    
    # Define constraint modes in order of strictness (most relaxed to most strict)
    constraint_modes = ["relaxed", "balanced", "hybrid", "real"]
    
    # If adaptive mode is enabled, we'll try different constraint levels
    if args.adaptive and constraint_mode != "relaxed":
        # Start with the selected mode and progressively relax constraints
        current_mode_idx = constraint_modes.index(constraint_mode)
        max_attempts = min(args.max_attempts, current_mode_idx + 1)
        
        for attempt in range(max_attempts):
            current_mode = constraint_modes[current_mode_idx - attempt]
            print(f"\nAttempt {attempt+1}/{max_attempts}: Trying {current_mode} constraint mode")
            
            timetable = generate_with_constraint_mode(generator, current_mode, args.reduced, solver_timeout, args.staggered)
            
            if timetable:
                print(f"Solution found with {current_mode} constraint mode!")
                break
            else:
                print(f"No solution found with {current_mode} constraint mode.")
                if attempt < max_attempts - 1:
                    print("Relaxing constraints and trying again...")
    else:
        # Single attempt with the specified constraint mode
        timetable = generate_with_constraint_mode(generator, constraint_mode, args.reduced, solver_timeout, args.staggered)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # If timetable was generated successfully
    if timetable:
        print(f"Timetable generation completed in {execution_time:.2f} seconds!")
        print("Creating visualizations...")
        
        try:
            # Visualize the timetable
            visualize_timetable(timetable)
            print("Visualizations created successfully!")
        except Exception as e:
            print(f"Error creating visualizations: {e}")
            
        # Summary of output files
        print("\nOutput files:")
        print("- master_timetable.csv: Master timetable with all classes")
        teacher_count = len(set([t for _, t, _, _, _ in timetable]))
        dept_count = len(set([generator.course_dept.get(generator.courses[c], "Unknown") 
                          for _, _, c, _, _ in timetable]))
        print(f"- Individual timetables for {teacher_count} teachers and {dept_count} departments")
        print(f"- Visualization charts: timetable_heatmap.png, teacher_load.png, etc.")
        
        print("\nTo convert the CSV to Excel format, run: python convert_timetable.py")
    else:
        print(f"No feasible timetable could be generated in {execution_time:.2f} seconds.")
        print("Try increasing the timeout or reducing the problem size further.")
        if constraint_mode != "relaxed":
            print("You can also try with --adaptive flag to automatically try different constraint levels.")
            print("Or try with --relaxed flag to use relaxed constraints.")

def save_expertise_data(generator):
    """Save teacher expertise data for visualization purposes"""
    # Create a DataFrame with teacher expertise information
    data = []
    
    for teacher_id, subject_areas in generator.teacher_expertise.items():
        teacher_name = teacher_id.split('@')[0]
        dept_id = generator.teacher_dept.get(teacher_id, 'Unknown')
        dept_name = generator.dept_id_to_name.get(dept_id, 'Unknown')
        
        for subject in subject_areas:
            data.append({
                'TeacherID': teacher_id,
                'TeacherName': teacher_name,
                'Department': dept_name,
                'SubjectArea': subject
            })
    
    # Save to CSV if we have data
    if data:
        expertise_df = pd.DataFrame(data)
        expertise_df.to_csv('teacher_expertise_data.csv', index=False)
        print(f"Saved expertise data for {len(generator.teacher_expertise)} teachers")

def generate_with_constraint_mode(generator, constraint_mode, reduced_problem, timeout, staggered=False):
    """Generate timetable with the specified constraint mode"""
    if constraint_mode == "relaxed":
        # Fully relaxed mode - fastest but least realistic
        return generator.generate_timetable(
            reduced_problem=reduced_problem, 
            relaxed_constraints=True,
            enable_staggered_schedule=staggered,
            timeout=timeout
        )
    elif constraint_mode == "balanced":
        # Balanced mode - enable some real constraints but not all
        return generator.generate_timetable(
            reduced_problem=reduced_problem,
            relaxed_constraints=True,  # Base is relaxed
            enable_lab_consecutive=True,  # Enable consecutive lab slots
            enable_lunch_breaks=True,    # Enable lunch breaks
            min_course_instances=1,      # Still only require 1 instance per course
            enable_staggered_schedule=staggered,
            timeout=timeout
        )
    elif constraint_mode == "hybrid":
        # Hybrid mode - more realistic than balanced, but still feasible
        return generator.generate_timetable(
            reduced_problem=reduced_problem,
            relaxed_constraints=True,    # Base is still relaxed
            enable_lab_consecutive=True, # Enable consecutive lab slots
            enable_lunch_breaks=True,    # Enable lunch breaks
            enable_student_conflicts=True, # Avoid student conflicts
            min_course_instances=2,      # Require at least 2 instances per course
            enable_staggered_schedule=staggered,
            timeout=timeout
        )
    else:  # Real constraints mode
        # All constraints enabled - most realistic but hardest to solve
        return generator.generate_timetable(
            reduced_problem=reduced_problem,
            relaxed_constraints=False,   # Enable all real constraints
            min_course_instances=2,       # Require at least 2 instances per course
            enable_staggered_schedule=staggered,
            timeout=timeout
        )

if __name__ == "__main__":
    main() 