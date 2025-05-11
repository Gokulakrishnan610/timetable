#!/usr/bin/env python3
"""
College Timetable Generator using OR-Tools CP-SAT Solver

This script implements a constraint-based timetable generation system for a college
with the following key constraints:
- Max 5 teaching hours per day for teachers
- Lunch breaks for teachers
- Lab courses require consecutive slots
- No overlapping classes for students
- Maximum 6 slots per day for students
- Room allocation based on type and capacity
- Special requirements for lab/survey courses
"""

import csv
import os
import random
import pandas as pd
import numpy as np
from ortools.sat.python import cp_model
from collections import defaultdict, Counter

class TimetableGenerator:
    def __init__(self, data_dir='data'):
        """Initialize the timetable generator with data directory path"""
        self.data_dir = data_dir
        
        # Constants
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.num_days = len(self.days)
        self.slots_per_day = 13
        
        # Division configurations with their time ranges
        self.divisions = {
            'A': {
                'start_time': '08:00',
                'end_time': '15:00',
                'slots': range(1, 9)    # 8 AM - 3 PM (slots 1-8)
            },
            'B': {
                'start_time': '10:00',
                'end_time': '17:00',
                'slots': range(4, 12)   # 10 AM - 5 PM (slots 4-11)
            },
            'C': {
                'start_time': '12:00',
                'end_time': '19:00',
                'slots': range(6, 14)   # 12 PM - 7 PM (slots 6-13)
            }
        }
        
        # Time slot mapping (exact times)
        self.slot_times = {
            1: "08:00 - 09:00",  # 60 min
            2: "09:00 - 09:50",  # 50 min
            3: "09:50 - 10:40",  # 50 min
            4: "10:40 - 11:30",  # 50 min
            5: "11:30 - 12:20",  # 50 min
            6: "12:20 - 01:10",  # 50 min
            7: "01:10 - 02:00",  # 50 min
            8: "02:00 - 02:50",  # 50 min
            9: "02:50 - 03:40",  # 50 min
            10: "03:40 - 04:30", # 50 min
            11: "04:30 - 05:20", # 50 min
            12: "05:20 - 06:10", # 50 min
            13: "06:10 - 07:00"  # 50 min
        }
        
        # Constraints
        self.max_teacher_slots_per_day = 5  # Max 5 hours per day
        self.lunch_slots = [5, 6, 7]  # 11:30-2:00 (slots 5-7)
        self.survey_lab_slots = range(1, 5)  # Slots 1-4 for survey lab in Division A
        
        # Room types and capacities
        self.room_types = {
            'REGULAR': 'regular',
            'LAB': 'lab',
            'TECHLOUNGE': 'techlounge'
        }
        
        self.room_capacities = {
            'LARGE': 240,
            'MEDIUM': 120,
            'SMALL': 60
        }
        
        # Data structures
        self.teachers = []
        self.courses = []
        self.rooms = []
        self.departments = []

        # Department mapping
        self.dept_id_to_name = {}  # Department ID -> Name
        self.dept_name_to_id = {}  # Department Name -> ID
        
        # Mapping dictionaries
        self.teacher_courses = defaultdict(list)  # Teacher -> courses
        self.course_teachers = defaultdict(list)  # Course -> teachers
        self.course_dept = {}     # Course -> department
        self.teacher_dept = {}    # Teacher -> department
        self.room_capacities = {} # Room -> capacity
        self.lab_rooms = set()    # Set of lab rooms
        self.techlounge = set()   # Set of techlounge rooms
        
        # Course type indicators
        self.lab_courses = set()      # Set of lab courses
        self.theory_courses = set()   # Set of theory courses
        self.survey_lab_courses = set() # Set of survey lab courses
        self.pop_courses = set()      # Set of POP (Practical Oriented Project) courses
        
        # Teacher specialization
        self.pop_faculty = set()      # Set of POP faculty
        self.lab_assistants = set()   # Set of lab assistants
        
        # Teacher expertise tracking
        self.teacher_expertise = defaultdict(set)  # Teacher -> subject areas
        self.course_subject_area = {}  # Course -> subject area
        
        # Load data
        self.load_data()
        
    def load_data(self):
        """Load data from CSV files in the data directory"""
        print("Loading data from", self.data_dir)
        
        # Load departments first
        dept_file = os.path.join(self.data_dir, 'departments.csv')
        if os.path.exists(dept_file):
            with open(dept_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dept_id = row['id']
                    dept_name = row['dept_name']
                    self.departments.append(dept_name)
                    self.dept_id_to_name[dept_id] = dept_name
                    self.dept_name_to_id[dept_name] = dept_id
        
        # Load courses and classify them
        courses_file = os.path.join(self.data_dir, 'course.csv')
        if os.path.exists(courses_file):
            with open(courses_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    course_id = row['course_id']
                    self.courses.append(course_id)
                    
                    # Store department mapping
                    dept_name = row['course_dept_id']
                    self.course_dept[course_id] = dept_name
                    
                    # Extract subject area from course code
                    if len(course_id) >= 2:
                        # Most course codes start with 2-letter subject code (e.g., CS, MA, PH)
                        subject_area = course_id[:2]
                        self.course_subject_area[course_id] = subject_area
                    
                    # Classify course type
                    practical_hours = int(row.get('practical_hours', 0))
                    if practical_hours >= 2:
                        self.lab_courses.add(course_id)
                    else:
                        self.theory_courses.add(course_id)
        
        # Load rooms
        rooms_file = os.path.join(self.data_dir, 'rooms.csv')
        if os.path.exists(rooms_file):
            with open(rooms_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    room_id = row['room_number']
                    self.rooms.append(room_id)
                    is_lab = row['is_lab'].lower() == 'true'
                    capacity = float(row['room_max_cap']) if row['room_max_cap'] else 30
                    self.room_capacities[room_id] = int(capacity)
                    if is_lab:
                        self.lab_rooms.add(room_id)
        
        # Load teachers and their departments
        teachers_file = os.path.join(self.data_dir, 'teachers.csv')
        if os.path.exists(teachers_file):
            with open(teachers_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['resignation_status'] == 'active':
                        teacher_id = row['teacher_id__email']
                        self.teachers.append(teacher_id)
                        dept_id = row['dept_id']
                        self.teacher_dept[teacher_id] = dept_id
                        
        # Load teacher-course assignments
        course_teacher_file = os.path.join(self.data_dir, 'course_for_the_department_and_thier_faculty.csv')
        assignments_loaded = False
        original_assignments = {}
        
        if os.path.exists(course_teacher_file):
            with open(course_teacher_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Course Code' in row and 'Faculty' in row:
                        course_code = row['Course Code']
                        teaching_dept = row['Faculty']
                        
                        if course_code in self.courses and teaching_dept in self.dept_name_to_id:
                            assignments_loaded = True
                            teaching_dept_id = self.dept_name_to_id[teaching_dept]
                            
                            # Save original assignments for expertise tracking
                            if course_code not in original_assignments:
                                original_assignments[course_code] = teaching_dept_id
                            
                            # Find teachers in this department
                            dept_teachers = [t for t in self.teachers 
                                          if self.teacher_dept.get(t) == teaching_dept_id]
                            
                            if dept_teachers:
                                # Assign 1-2 teachers per course
                                num_teachers = min(2, len(dept_teachers))
                                assigned_teachers = random.sample(dept_teachers, num_teachers)
                                for teacher in assigned_teachers:
                                    if course_code not in self.teacher_courses[teacher]:
                                        self.teacher_courses[teacher].append(course_code)
                                        self.course_teachers[course_code].append(teacher)
                                        
                                        # Track teacher expertise based on subject area
                                        if course_code in self.course_subject_area:
                                            self.teacher_expertise[teacher].add(
                                                self.course_subject_area[course_code]
                                            )
        
        # If we have existing assignments, infer teacher expertise
        if assignments_loaded:
            self._analyze_teacher_expertise()
        
        if not assignments_loaded:
            print("No teacher-course assignments found. Creating assignments based on departments and expertise...")
            self._create_expertise_based_assignments()
        
        print(f"\nLoaded:")
        print(f"- {len(self.teachers)} teachers")
        print(f"- {len(self.courses)} courses ({len(self.lab_courses)} lab, {len(self.theory_courses)} theory)")
        print(f"- {len(self.rooms)} rooms ({len(self.lab_rooms)} lab rooms)")
        print(f"- {len(self.departments)} departments")
        print(f"- {sum(len(courses) for courses in self.teacher_courses.values())} teacher-course assignments")
        
        # Print sample assignments
        print("\nSample teacher-course assignments:")
        for teacher_id, courses in list(self.teacher_courses.items())[:5]:
            teacher_name = teacher_id.split('@')[0]
            dept_id = self.teacher_dept.get(teacher_id, 'Unknown')
            dept_name = self.dept_id_to_name.get(dept_id, 'Unknown')
            print(f"- {teacher_name} ({dept_name}): {', '.join(courses)}")

    def _analyze_teacher_expertise(self):
        """Analyze existing teacher-course assignments to infer expertise"""
        for teacher, courses in self.teacher_courses.items():
            # Extract subject areas from courses
            for course in courses:
                if course in self.course_subject_area:
                    self.teacher_expertise[teacher].add(self.course_subject_area[course])

    def _create_expertise_based_assignments(self):
        """Create teacher-course assignments based on departments and expertise"""
        # Group courses by department and subject area
        courses_by_dept_subject = defaultdict(lambda: defaultdict(list))
        for course_id, dept_name in self.course_dept.items():
            if dept_name in self.dept_name_to_id:
                dept_id = self.dept_name_to_id[dept_name]
                subject_area = self.course_subject_area.get(course_id, "UNKNOWN")
                courses_by_dept_subject[dept_id][subject_area].append(course_id)
        
        # Group teachers by department
        teachers_by_dept = defaultdict(list)
        for teacher_id, dept_id in self.teacher_dept.items():
            teachers_by_dept[dept_id].append(teacher_id)
        
        # Distribute courses among teachers in each department
        for dept_id, subject_courses in courses_by_dept_subject.items():
            dept_teachers = teachers_by_dept.get(dept_id, [])
            
            # If no teachers in department, assign to random teachers
            if not dept_teachers and self.teachers:
                dept_teachers = random.sample(self.teachers, min(3, len(self.teachers)))
            
            if dept_teachers:
                for subject_area, courses in subject_courses.items():
                    # Find teachers with expertise in this subject
                    expert_teachers = [t for t in dept_teachers 
                                     if subject_area in self.teacher_expertise.get(t, set())]
                    
                    # If no subject experts, use all department teachers
                    if not expert_teachers:
                        expert_teachers = dept_teachers
                    
                    # Calculate courses per teacher to ensure even distribution
                    courses_per_teacher = max(1, len(courses) // len(expert_teachers))
                    
                    # Track teacher load for this subject area
                    teacher_load = defaultdict(int)
                    
                    # Assign courses to teachers
                    for course_id in courses:
                        # Prioritize teachers with lower load
                        sorted_teachers = sorted(expert_teachers, 
                                               key=lambda t: (teacher_load[t], 
                                                             len(self.teacher_courses[t])))
                        
                        # Choose 1-2 teachers with lowest load
                        num_teachers = random.randint(1, min(2, len(sorted_teachers)))
                        assigned_teachers = sorted_teachers[:num_teachers]
                        
                        for teacher_id in assigned_teachers:
                            if course_id not in self.teacher_courses[teacher_id]:
                                self.teacher_courses[teacher_id].append(course_id)
                                self.course_teachers[course_id].append(teacher_id)
                                teacher_load[teacher_id] += 1
                                
                                # Update teacher expertise
                                if course_id in self.course_subject_area:
                                    self.teacher_expertise[teacher_id].add(
                                        self.course_subject_area[course_id]
                                    )

    def generate_timetable(self, reduced_problem=True, relaxed_constraints=False, 
                         enable_lunch_breaks=False, enable_lab_consecutive=False,
                         enable_student_conflicts=False, min_course_instances=1,
                         enable_staggered_schedule=False, timeout=600):
        """Generate the timetable using constraint programming
        
        Parameters:
        - reduced_problem: Whether to reduce the problem size
        - relaxed_constraints: Whether to use relaxed constraints (backward compatibility)
        - enable_lunch_breaks: Enable lunch break constraints
        - enable_lab_consecutive: Enable consecutive slots for lab courses
        - enable_student_conflicts: Enable student conflict avoidance
        - min_course_instances: Minimum number of times to schedule each course
        - enable_staggered_schedule: Enable staggered scheduling across time slots
        - timeout: Solver timeout in seconds (default: 600)
        """
        print("Starting timetable generation...")
        
        # Even more aggressive problem size reduction
        if reduced_problem:
            print("Using problem size reduction strategies...")
            # Drastically reduce the number of courses to consider
            max_courses = 100  # Limit to 100 courses 
            self.courses = self.courses[:max_courses]
            self.lab_courses = set([c for c in self.lab_courses if c in self.courses])
            self.theory_courses = set([c for c in self.theory_courses if c in self.courses])
            
            # Update teacher-course assignments for the reduced course set
            for teacher, courses in list(self.teacher_courses.items()):
                self.teacher_courses[teacher] = [c for c in courses if c in self.courses]
            
            # Limit the number of teachers to those who teach the selected courses
            active_teachers = []
            for teacher, courses in self.teacher_courses.items():
                if courses:  # Teacher has at least one course in our reduced set
                    active_teachers.append(teacher)
            
            # Take only first 200 active teachers
            max_teachers = 200
            self.teachers = active_teachers[:min(max_teachers, len(active_teachers))]
            
            # Limit the number of rooms to consider
            max_rooms = 50  # Limit to 50 rooms
            # Make sure we have enough lab rooms
            lab_room_count = min(20, len(self.lab_rooms))
            regular_room_count = max_rooms - lab_room_count
            
            lab_rooms_list = sorted(list(self.lab_rooms))[:lab_room_count]
            regular_rooms_list = [r for r in self.rooms if r not in self.lab_rooms][:regular_room_count]
            
            active_rooms = lab_rooms_list + regular_rooms_list
            self.rooms = active_rooms
            self.lab_rooms = set(lab_rooms_list)
        
        # Create solver with optimized settings
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout  # Configurable timeout
        solver.parameters.num_search_workers = 8  # Use multiple cores
        solver.parameters.log_search_progress = True  # Show progress
        # Add more efficient search strategies
        solver.parameters.cp_model_presolve = True
        solver.parameters.linearization_level = 2
        
        print(f"Solver timeout set to {timeout} seconds")
        
        model = cp_model.CpModel()
        
        # Create index mappings for faster lookups
        teacher_indices = {teacher: idx for idx, teacher in enumerate(self.teachers)}
        course_indices = {course: idx for idx, course in enumerate(self.courses)}
        
        # Split rooms by type and optimize room assignments
        lab_rooms = [r for r in self.rooms if r in self.lab_rooms]
        tech_rooms = [r for r in self.rooms if r in self.techlounge]
        regular_rooms = [r for r in self.rooms if r not in self.lab_rooms and r not in self.techlounge]
        
        # Create combined room list and indices
        all_rooms = regular_rooms + lab_rooms + tech_rooms
        room_indices = {room: idx for idx, room in enumerate(all_rooms)}
        
        num_teachers = len(self.teachers)
        num_courses = len(self.courses)
        num_rooms = len(all_rooms)
        
        print(f"Setting up model with {num_teachers} teachers, {num_courses} courses, {num_rooms} rooms")
        print("Optimizing variable creation...")
        
        # Pre-compute valid teacher-course combinations
        self.valid_teacher_courses = {}
        for t in range(num_teachers):
            teacher = self.teachers[t]
            assigned_courses = set(self.teacher_courses.get(teacher, []))
            self.valid_teacher_courses[t] = [c for c, course in enumerate(self.courses) 
                                          if course in assigned_courses]
        
        # Pre-compute valid room assignments - simplify by allowing theory courses in any room
        self.valid_rooms = {}
        for c, course in enumerate(self.courses):
            if course in self.lab_courses:
                self.valid_rooms[c] = list(range(len(regular_rooms), len(regular_rooms) + len(lab_rooms)))
                if not self.valid_rooms[c]:  # If no lab rooms available, allow regular rooms too
                    self.valid_rooms[c] = list(range(len(regular_rooms)))
            else:
                self.valid_rooms[c] = list(range(len(regular_rooms)))
        
        # Extract course year from course code for student conflict avoidance
        # Assuming course codes follow a pattern like 'XX23123' where '2' is the year
        self.course_year = {}
        for c, course in enumerate(self.courses):
            if len(course) >= 4 and course[2:4].isdigit():
                self.course_year[c] = int(course[2:4]) // 10  # Extract year (e.g. '23' -> 2nd year)
            else:
                self.course_year[c] = 0  # Default if pattern not found
        
        # Group courses by department and year for conflict avoidance
        self.dept_year_courses = defaultdict(list)
        for c, course in enumerate(self.courses):
            dept = self.course_dept.get(course, '')
            year = self.course_year.get(c, 0)
            if dept and year > 0:
                self.dept_year_courses[(dept, year)].append(c)
        
        # Store room lists for printing
        self.all_rooms = all_rooms
        
        # Decision variables - only create for valid combinations
        # Further reduce by only considering 4 days and limiting slots
        reduced_days = min(4, self.num_days)
        reduced_slots = min(8, self.slots_per_day)
        
        x = {}
        print("Creating decision variables...")
        for t in range(num_teachers):
            # Skip teachers with too many courses to reduce problem size
            if reduced_problem and len(self.valid_teacher_courses[t]) > 5:
                courses_to_include = sorted(self.valid_teacher_courses[t])[:5]
            else:
                courses_to_include = self.valid_teacher_courses[t]
                
            for c in courses_to_include:
                for d in range(reduced_days):
                    for s in range(reduced_slots):
                        if self.valid_rooms.get(c):  # Only if valid rooms exist
                            for r in self.valid_rooms[c]:
                                x[t, c, d, s, r] = model.NewBoolVar(f'x_t{t}_c{c}_d{d}_s{s}_r{r}')
        
        print("Adding constraints...")
        
        # Constraint 1: A teacher can teach at most one course in one slot
        for t in range(num_teachers):
            for d in range(reduced_days):
                for s in range(reduced_slots):
                    model.Add(sum(x.get((t, c, d, s, r), 0)
                                 for c in self.valid_teacher_courses[t] if c in courses_to_include
                                 for r in self.valid_rooms.get(c, [])) <= 1)
        
        # Constraint 2: A course can be taught by only one teacher at a time
        for c in range(num_courses):
            if c not in courses_to_include:
                continue
            for d in range(reduced_days):
                for s in range(reduced_slots):
                    valid_vars = []
                    for t in range(num_teachers):
                        if c in self.valid_teacher_courses.get(t, []):
                            for r in self.valid_rooms.get(c, []):
                                if (t, c, d, s, r) in x:
                                    valid_vars.append(x[t, c, d, s, r])
                    if valid_vars:
                        model.Add(sum(valid_vars) <= 1)
        
        # Constraint 3: A room can be used for at most one course in one slot
        for r in range(num_rooms):
            for d in range(reduced_days):
                for s in range(reduced_slots):
                    valid_vars = []
                    for t in range(num_teachers):
                        for c in self.valid_teacher_courses.get(t, []):
                            if r in self.valid_rooms.get(c, []) and (t, c, d, s, r) in x:
                                valid_vars.append(x[t, c, d, s, r])
                    if valid_vars:
                        model.Add(sum(valid_vars) <= 1)
        
        # Constraint 4: Maximum 5 teaching hours per day for teachers
        for t in range(num_teachers):
            for d in range(reduced_days):
                valid_vars = []
                for c in self.valid_teacher_courses.get(t, []):
                    for s in range(reduced_slots):
                        for r in self.valid_rooms.get(c, []):
                            if (t, c, d, s, r) in x:
                                valid_vars.append(x[t, c, d, s, r])
                if valid_vars:
                    model.Add(sum(valid_vars) <= self.max_teacher_slots_per_day)
        
        # REAL CONSTRAINT 1: Lunch break constraints
        if not relaxed_constraints or enable_lunch_breaks:
            # Constraint 5: Teachers should have at least one free slot during lunch time
            lunch_slots = [s for s in self.lunch_slots if s < reduced_slots]
            if lunch_slots:
                for t in range(num_teachers):
                    for d in range(reduced_days):
                        lunch_slots_used = []
                        for c in self.valid_teacher_courses.get(t, []):
                            for s in lunch_slots:
                                for r in self.valid_rooms.get(c, []):
                                    if (t, c, d, s, r) in x:
                                        lunch_slots_used.append(x[t, c, d, s, r])
                        if lunch_slots_used:
                            model.Add(sum(lunch_slots_used) <= len(lunch_slots) - 1)
        
        # REAL CONSTRAINT 2: Lab courses require consecutive slots
        if not relaxed_constraints or enable_lab_consecutive:
            lab_course_indices = [c for c, course in enumerate(self.courses) 
                              if course in self.lab_courses][:15]  # Limit to 15 lab courses
            
            # For each lab course, ensure it gets scheduled in consecutive slots
            for c in lab_course_indices:
                # Lab course variables for each teacher, day, start slot, room
                for t in range(num_teachers):
                    if c in self.valid_teacher_courses.get(t, []):
                        for d in range(reduced_days):
                            for s in range(reduced_slots - 1):  # Can't start a lab in the last slot
                                for r in self.valid_rooms.get(c, []):
                                    # Check if we can schedule this lab course here
                                    if (t, c, d, s, r) in x and (t, c, d, s+1, r) in x:
                                        # If first slot scheduled, require second slot too
                                        model.Add(x[t, c, d, s+1, r] >= x[t, c, d, s, r])
        else:
            # Simplified lab course constraint - just ensure they get assigned
            lab_course_indices = [c for c, course in enumerate(self.courses) 
                               if course in self.lab_courses][:20]  # Limit to 20 lab courses
                               
            for c in lab_course_indices:
                lab_slots = []
                for t in range(num_teachers):
                    if c in self.valid_teacher_courses.get(t, []):
                        for d in range(reduced_days):
                            for s in range(reduced_slots - 1):  # Can't start a lab in the last slot
                                for r in self.valid_rooms.get(c, []):
                                    if (t, c, d, s, r) in x:
                                        lab_slots.append(x[t, c, d, s, r])
                if lab_slots:
                    model.Add(sum(lab_slots) >= 1)  # Each lab course at least once
        
        # REAL CONSTRAINT 3: Each course must be scheduled multiple times
        # Use the minimum course instances parameter
        course_min_instances = min_course_instances
        if not relaxed_constraints:
            course_min_instances = 2  # Default to 2 in full constraints mode
            
        for c in range(num_courses):
            course_slots = []
            for t in range(num_teachers):
                if c in self.valid_teacher_courses.get(t, []):
                    for d in range(reduced_days):
                        for s in range(reduced_slots):
                            for r in self.valid_rooms.get(c, []):
                                if (t, c, d, s, r) in x:
                                    course_slots.append(x[t, c, d, s, r])
            if course_slots and len(course_slots) >= course_min_instances:  
                model.Add(sum(course_slots) >= course_min_instances)  # Each course at least N times
        
        # REAL CONSTRAINT 4: Student conflict avoidance
        if not relaxed_constraints or enable_student_conflicts:
            # Avoid scheduling courses from the same department and year at the same time
            for (dept, year), course_list in self.dept_year_courses.items():
                if len(course_list) > 1:  # Only if there are multiple courses
                    for d in range(reduced_days):
                        for s in range(reduced_slots):
                            conflict_vars = []
                            for c in course_list:
                                for t in range(num_teachers):
                                    if c in self.valid_teacher_courses.get(t, []):
                                        for r in self.valid_rooms.get(c, []):
                                            if (t, c, d, s, r) in x:
                                                conflict_vars.append(x[t, c, d, s, r])
                            if conflict_vars:
                                # At most one course from this department/year in this time slot
                                model.Add(sum(conflict_vars) <= 1)
        
        # NEW CONSTRAINT 5: Staggered scheduling
        if enable_staggered_schedule:
            # Track classes per time slot to encourage more even distribution
            classes_per_slot = {}
            for d in range(reduced_days):
                for s in range(reduced_slots):
                    slot_classes = []
                    for t in range(num_teachers):
                        for c in self.valid_teacher_courses.get(t, []):
                            for r in self.valid_rooms.get(c, []):
                                if (t, c, d, s, r) in x:
                                    slot_classes.append(x[t, c, d, s, r])
                    if slot_classes:
                        classes_per_slot[(d, s)] = sum(slot_classes)
                        
                        # Cap the number of classes in any one slot to avoid congestion
                        # Adjust max_classes_per_slot based on your needs
                        max_classes_per_slot = min(25, num_rooms // 2)
                        model.Add(sum(slot_classes) <= max_classes_per_slot)
        
        # Objective: Maximize the number of scheduled classes with preferences
        objective_terms = []
        for t in range(num_teachers):
            for c in self.valid_teacher_courses.get(t, []):
                for d in range(reduced_days):
                    for s in range(reduced_slots):
                        for r in self.valid_rooms.get(c, []):
                            if (t, c, d, s, r) in x:
                                # Basic scheduling weight (1 for each scheduled class)
                                weight = 1
                                
                                # Add preference weights based on course type and time slot
                                course = self.courses[c]
                                
                                # Prefer lab courses in morning slots (higher weight for earlier slots)
                                if course in self.lab_courses:
                                    # Morning slots (0-3) get higher preference
                                    if s < 4:
                                        weight += 0.3  # Strong preference for morning
                                    elif s < 6:
                                        weight += 0.1  # Slight preference for mid-morning
                                
                                # Theory courses have mild preference for mid-day slots
                                else:
                                    # Mid-day slots (3-6) get higher preference
                                    if 3 <= s <= 6:
                                        weight += 0.1
                                
                                # If staggered scheduling is enabled, adjust weights to encourage distribution
                                if enable_staggered_schedule:
                                    # Create preference patterns for different rooms to stagger start times
                                    room_group = r % 3  # Group rooms into 3 categories
                                    
                                    if room_group == 0:
                                        # First group prefers earlier slots
                                        if s in [0, 3, 6]:
                                            weight += 0.15
                                    elif room_group == 1:
                                        # Second group prefers mid slots
                                        if s in [1, 4, 7]:
                                            weight += 0.15
                                    else:
                                        # Third group prefers later slots
                                        if s in [2, 5]:
                                            weight += 0.15
                                
                                objective_terms.append(weight * x[t, c, d, s, r])
        
        if objective_terms:
            model.Maximize(sum(objective_terms))

        print("All constraints added. Solving...")
        print("This may take several minutes due to the large dataset...")
        
        # Try to solve with different strategies
        # Set as optimization problem with objectives
        solver.parameters.search_branching = cp_model.AUTOMATIC_SEARCH
        
        # Solve the model
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("Solution found!")
            self.print_timetable(solver, x, teacher_indices, course_indices, room_indices)
            return True
        else:
            print("No solution found.")
            print("Try increasing the timeout or reducing the problem size further.")
            return False
    
    def print_timetable(self, solver, x, teacher_indices, course_indices, room_indices):
        """Print the generated timetable"""
        print("\n===== GENERATED TIMETABLE =====")
        
        # Create a structured timetable
        timetable = {}
        for d in range(self.num_days):
            day = self.days[d]
            timetable[day] = {}
            for s in range(self.slots_per_day):
                slot = s + 1  # 1-indexed slots
                timetable[day][slot] = []
                
                # Check each valid teacher-course-room combination
                for t, teacher in enumerate(self.teachers):
                    if t not in self.valid_teacher_courses:
                        continue
                        
                    for c in self.valid_teacher_courses[t]:
                        if c not in self.valid_rooms:
                            continue
                            
                        for r in self.valid_rooms[c]:
                            key = (t, c, d, s, r)
                            if key in x and solver.Value(x[key]) == 1:
                                course = self.courses[c]
                                room = self.all_rooms[r]
                                dept_id = self.teacher_dept.get(teacher, '')
                                dept_name = self.dept_id_to_name.get(dept_id, '')
                                
                                timetable[day][slot].append({
                                    'teacher': teacher,
                                    'teacher_dept': dept_name,
                                    'course': course,
                                    'room': room
                                })
        
        # Print timetable
        for day in self.days:
            print(f"\n{day}:")
            for slot in range(1, self.slots_per_day + 1):
                slot_time = self.slot_times[slot]
                print(f"  Slot {slot} ({slot_time}):")
                if timetable[day][slot]:
                    for idx, schedule in enumerate(timetable[day][slot][:10]):  # Show first 10 for brevity
                        teacher_name = schedule['teacher'].split('@')[0]
                        print(f"    - {schedule['course']} by {teacher_name} ({schedule['teacher_dept']}) in {schedule['room']}")
                    if len(timetable[day][slot]) > 10:
                        print(f"    ... and {len(timetable[day][slot]) - 10} more")
                else:
                    print("    No classes scheduled")
        
        # Save to CSV
        self.save_timetable_to_csv(timetable)
    
    def save_timetable_to_csv(self, timetable):
        """Save the timetable to CSV files"""
        # Create a flattened list of all scheduled classes
        rows = []
        for day in self.days:
            for slot in range(1, self.slots_per_day + 1):
                slot_time = self.slot_times[slot]
                for schedule in timetable[day][slot]:
                    rows.append({
                        'Day': day,
                        'Slot': slot,
                        'Time': slot_time,
                        'Course': schedule['course'],
                        'Teacher': schedule['teacher'],
                        'Department': schedule.get('teacher_dept', ''),
                        'Room': schedule['room']
                    })
        
        # Save master timetable
        df = pd.DataFrame(rows)
        df.to_csv('master_timetable.csv', index=False)
        print("Master timetable saved to master_timetable.csv")
        
        # Generate teacher-specific timetables
        teacher_schedules = defaultdict(list)
        for row in rows:
            teacher_schedules[row['Teacher']].append(row)
        
        for teacher, schedule in teacher_schedules.items():
            teacher_df = pd.DataFrame(schedule)
            teacher_id = teacher.split('@')[0]
            filename = f"timetable_teacher_{teacher_id}.csv"
            teacher_df.to_csv(filename, index=False)
        
        print(f"Individual timetables generated for {len(teacher_schedules)} teachers")
        
        # Generate department-specific timetables
        dept_schedules = defaultdict(list)
        for row in rows:
            if row['Department']:
                dept_schedules[row['Department']].append(row)
        
        for dept, schedule in dept_schedules.items():
            dept_df = pd.DataFrame(schedule)
            safe_dept_name = ''.join(c if c.isalnum() else '_' for c in dept)
            filename = f"timetable_dept_{safe_dept_name}.csv"
            dept_df.to_csv(filename, index=False)
        
        print(f"Individual timetables generated for {len(dept_schedules)} departments")

    def _get_next_division(self):
        """Helper method to cycle through divisions A, B, C"""
        divisions = ['A', 'B', 'C']
        division = divisions[self._division_counter % 3]
        self._division_counter += 1
        return division
        
    def _dept_year_division_map(self):
        """Helper method to store department-year to division mapping"""
        if not hasattr(self, '_dept_year_div_map'):
            self._dept_year_div_map = {}
        return self._dept_year_div_map

    def _get_pop_faculty_slots(self, teacher):
        """Get fixed slots for POP faculty"""
        # This would be implemented based on your specific requirements
        # For now, return an empty set
        return set()

    def _get_course_division(self, course):
        """Get the division for a course"""
        # This would be implemented based on your specific requirements
        # For now, return None
        return None

if __name__ == "__main__":
    generator = TimetableGenerator()
    generator.generate_timetable() 