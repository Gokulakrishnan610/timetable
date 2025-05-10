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
        self.lunch_slots = [4, 5, 6]  # Slots 5, 6, 7 (11:30-2:00)
        self.max_teacher_slots_per_day = 5
        self.max_student_slots_per_day = 6
        
        # Time slot mapping
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
        
        # Data structures
        self.teachers = []
        self.students = []
        self.courses = []
        self.rooms = []
        self.departments = []
        
        # Department mapping
        self.dept_id_to_name = {}  # Department ID -> Name
        self.dept_name_to_id = {}  # Department Name -> ID
        
        # Mapping dictionaries
        self.teacher_courses = defaultdict(list)  # Teacher -> courses
        self.course_teachers = defaultdict(list)  # Course -> teachers
        self.student_courses = defaultdict(list)  # Student -> courses
        self.course_students = defaultdict(list)  # Course -> students
        self.lab_courses = set()  # Set of lab courses
        self.course_dept = {}  # Course -> department
        self.teacher_dept = {}  # Teacher -> department
        self.room_capacities = {}  # Room -> capacity
        self.lab_rooms = set()  # Set of lab rooms
        self.division_map = {}  # Student -> division (A/B/C)
        
        # Load data
        self.load_data()
        
    def load_data(self):
        """Load data from CSV files in the data directory"""
        print("Loading data from", self.data_dir)
        
        # Load departments - first to establish ID mappings
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
        
        # Load rooms and classify them
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
        
        # Load teachers
        teachers_file = os.path.join(self.data_dir, 'teachers.csv')
        if os.path.exists(teachers_file):
            with open(teachers_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['resignation_status'] == 'active':
                        teacher_id = row['teacher_id__email']
                        self.teachers.append(teacher_id)
                        dept_id = row['dept_id']
                        
                        # Store both ID and name references
                        self.teacher_dept[teacher_id] = dept_id
                        
                        # For debug/display purposes - get the name if available
                        dept_name = self.dept_id_to_name.get(dept_id, f"Unknown Dept ({dept_id})")
                        
                        # Print a message for missing departments
                        if dept_id not in self.dept_id_to_name:
                            print(f"Warning: Teacher {teacher_id} has department ID {dept_id} which is not in departments.csv")
        
        # Load courses and determine lab courses
        courses_file = os.path.join(self.data_dir, 'course.csv')
        if os.path.exists(courses_file):
            with open(courses_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    course_id = row['course_id']
                    self.courses.append(course_id)
                    
                    # Store department by name
                    dept_name = row['course_dept_id']
                    self.course_dept[course_id] = dept_name
                    
                    # Check if the course is a lab course
                    practical_hours = int(row.get('practical_hours', 0))
                    if practical_hours >= 2:  # Lab courses have 2+ practical hours
                        self.lab_courses.add(course_id)
        
        # Load course-teacher assignments
        course_teacher_file = os.path.join(self.data_dir, 'course_for_the_department_and_thier_faculty.csv')
        if os.path.exists(course_teacher_file):
            with open(course_teacher_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    course_code = row['Course Code']
                    teaching_dept = row['Faculty']
                    
                    # Find teachers who belong to this department by name
                    matching_teachers = []
                    
                    # First try to get the ID from the name
                    teaching_dept_id = self.dept_name_to_id.get(teaching_dept)
                    
                    if teaching_dept_id:
                        # Get teachers by department ID
                        matching_teachers = [t for t in self.teachers if self.teacher_dept.get(t) == teaching_dept_id]
                    else:
                        # Fallback: try exact name matching
                        matching_teachers = [t for t in self.teachers 
                                           if self.dept_id_to_name.get(self.teacher_dept.get(t)) == teaching_dept]
                    
                    if matching_teachers:
                        # Assign up to 2 teachers for the course
                        assigned_teachers = random.sample(matching_teachers, min(2, len(matching_teachers)))
                        for teacher in assigned_teachers:
                            self.teacher_courses[teacher].append(course_code)
                            self.course_teachers[course_code].append(teacher)
        
        # Load students and assign to courses
        students_file = os.path.join(self.data_dir, 'students.csv')
        if os.path.exists(students_file):
            with open(students_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    student_id = row['student_id__email']
                    self.students.append(student_id)
                    dept = row['dept']
                    year = row['year']
                    semester = row['current_semester']
                    
                    # Randomly assign students to division A, B, or C
                    self.division_map[student_id] = random.choice(['A', 'B', 'C'])
                    
                    # Find courses that match the student's department, year, and semester
                    matching_courses = [
                        c for c in self.courses 
                        if self.course_dept.get(c) == dept
                    ]
                    
                    # Assign students to courses (in reality, this would be from enrollment data)
                    # For now, assign 5-7 courses per student
                    num_courses = min(random.randint(5, 7), len(matching_courses))
                    if num_courses > 0:
                        assigned_courses = random.sample(matching_courses, num_courses)
                        for course in assigned_courses:
                            self.student_courses[student_id].append(course)
                            self.course_students[course].append(student_id)
        
        print(f"Loaded {len(self.teachers)} teachers, {len(self.students)} students, "
              f"{len(self.courses)} courses, {len(self.rooms)} rooms, {len(self.departments)} departments")
                
    def generate_timetable(self):
        """Generate the timetable using OR-Tools CP-SAT solver"""
        model = cp_model.CpModel()
        
        # Create index mappings for faster lookups
        teacher_indices = {teacher: idx for idx, teacher in enumerate(self.teachers)}
        course_indices = {course: idx for idx, course in enumerate(self.courses)}
        room_indices = {room: idx for idx, room in enumerate(self.rooms)}
        student_indices = {student: idx for idx, student in enumerate(self.students)}
        
        num_teachers = len(self.teachers)
        num_courses = len(self.courses)
        num_rooms = len(self.rooms)
        num_students = len(self.students)
        
        print(f"Setting up model with {num_teachers} teachers, {num_courses} courses, "
              f"{num_rooms} rooms, {num_students} students")
        
        # Decision variables
        # x[t][c][d][s][r] = 1 if teacher t teaches course c on day d, slot s, room r
        x = {}
        for t in range(num_teachers):
            for c in range(num_courses):
                for d in range(self.num_days):
                    for s in range(self.slots_per_day):
                        for r in range(num_rooms):
                            x[t, c, d, s, r] = model.NewBoolVar(f'x_t{t}_c{c}_d{d}_s{s}_r{r}')
        
        # Student attendance variables
        # y[s][c][d][sl] = 1 if student s attends course c on day d, slot sl
        y = {}
        for s in range(min(1000, num_students)):  # Limit to 1000 students for performance
            for c in range(num_courses):
                for d in range(self.num_days):
                    for sl in range(self.slots_per_day):
                        y[s, c, d, sl] = model.NewBoolVar(f'y_s{s}_c{c}_d{d}_sl{sl}')
        
        print("Adding constraints...")
        
        # Constraint 1: A course is taught by only one teacher at a time
        for c in range(num_courses):
            for d in range(self.num_days):
                for s in range(self.slots_per_day):
                    model.Add(sum(x[t, c, d, s, r] 
                                  for t in range(num_teachers) 
                                  for r in range(num_rooms)) <= 1)
        
        # Constraint 2: A teacher can teach at most one course in one slot
        for t in range(num_teachers):
            for d in range(self.num_days):
                for s in range(self.slots_per_day):
                    model.Add(sum(x[t, c, d, s, r] 
                                 for c in range(num_courses) 
                                 for r in range(num_rooms)) <= 1)
        
        # Constraint 3: A room can be used for at most one course in one slot
        for r in range(num_rooms):
            for d in range(self.num_days):
                for s in range(self.slots_per_day):
                    model.Add(sum(x[t, c, d, s, r] 
                                 for t in range(num_teachers) 
                                 for c in range(num_courses)) <= 1)
        
        # Constraint 4: A teacher teaches only assigned courses
        for t in range(num_teachers):
            teacher = self.teachers[t]
            assigned_courses = self.teacher_courses.get(teacher, [])
            assigned_course_indices = [course_indices[c] for c in assigned_courses if c in course_indices]
            
            for c in range(num_courses):
                if c not in assigned_course_indices:
                    for d in range(self.num_days):
                        for s in range(self.slots_per_day):
                            for r in range(num_rooms):
                                model.Add(x[t, c, d, s, r] == 0)
        
        # Constraint 5: Teachers have maximum 5 teaching hours per day
        for t in range(num_teachers):
            for d in range(self.num_days):
                model.Add(sum(x[t, c, d, s, r] 
                             for c in range(num_courses) 
                             for s in range(self.slots_per_day) 
                             for r in range(num_rooms)) <= self.max_teacher_slots_per_day)
        
        # Constraint 6: Teachers must have at least one free slot in lunch period
        for t in range(num_teachers):
            for d in range(self.num_days):
                lunch_slot_count = sum(x[t, c, d, s, r] 
                                     for c in range(num_courses) 
                                     for s in self.lunch_slots 
                                     for r in range(num_rooms))
                model.Add(lunch_slot_count <= len(self.lunch_slots) - 1)  # At least one lunch slot free
        
        # Constraint 7: Lab courses must be scheduled in consecutive slots
        for course_name, c in course_indices.items():
            if course_name in self.lab_courses:
                for d in range(self.num_days):
                    for s in range(self.slots_per_day - 1):  # Avoid last slot
                        # Define variables to track if a lab starts at slot s
                        lab_starts = model.NewBoolVar(f'lab_starts_c{c}_d{d}_s{s}')
                        
                        # Link lab_starts with actual scheduling
                        model.Add(sum(x[t, c, d, s, r] for t in range(num_teachers) for r in range(num_rooms)) >= 1).OnlyEnforceIf(lab_starts)
                        model.Add(sum(x[t, c, d, s, r] for t in range(num_teachers) for r in range(num_rooms)) == 0).OnlyEnforceIf(lab_starts.Not())
                        
                        # If lab starts at slot s, it must continue at slot s+1
                        for t in range(num_teachers):
                            for r in range(num_rooms):
                                # If teacher t teaches course c on day d at slot s in room r,
                                # then same teacher must teach same course on day d at slot s+1 in same room
                                lab_continues = model.NewBoolVar(f'lab_continues_t{t}_c{c}_d{d}_s{s}_r{r}')
                                model.Add(x[t, c, d, s, r] == 1).OnlyEnforceIf(lab_continues)
                                model.Add(x[t, c, d, s, r] == 0).OnlyEnforceIf(lab_continues.Not())
                                
                                model.AddImplication(lab_continues, x[t, c, d, s+1, r])
                        
                        # Ensure the lab is scheduled in consecutive slots
                        model.AddImplication(lab_starts, 
                                           sum(x[t, c, d, s+1, r] for t in range(num_teachers) for r in range(num_rooms)) >= 1)
        
        # Constraint 8: Lab courses must be scheduled in lab rooms
        for course_name, c in course_indices.items():
            if course_name in self.lab_courses:
                for t in range(num_teachers):
                    for d in range(self.num_days):
                        for s in range(self.slots_per_day):
                            for room_name, r in room_indices.items():
                                if room_name not in self.lab_rooms:
                                    model.Add(x[t, c, d, s, r] == 0)
        
        # Constraint 9: Survey lab must be scheduled in slots 1-4 in Division A
        # (This would need to be implemented if we had specific survey lab courses identified)
        
        # Constraint 10: Student assignment and limitations
        # Since we're working with the first 1000 students only for performance
        limited_students = self.students[:1000]
        for student_name, s in enumerate(limited_students):
            if s >= num_students:
                continue
                
            # Student must be assigned only enrolled courses
            enrolled_courses = self.student_courses.get(s, [])
            enrolled_course_indices = [course_indices[c] for c in enrolled_courses if c in course_indices]
            
            for c in range(num_courses):
                if c not in enrolled_course_indices:
                    for d in range(self.num_days):
                        for sl in range(self.slots_per_day):
                            model.Add(y[s, c, d, sl] == 0)
            
            # Student can attend at most one course per slot
            for d in range(self.num_days):
                for sl in range(self.slots_per_day):
                    model.Add(sum(y[s, c, d, sl] for c in range(num_courses)) <= 1)
            
            # Student has maximum 6 slots per day
            for d in range(self.num_days):
                model.Add(sum(y[s, c, d, sl] 
                             for c in range(num_courses) 
                             for sl in range(self.slots_per_day)) <= self.max_student_slots_per_day)
        
        # Link teacher scheduling with student attendance
        for s in range(min(1000, num_students)):
            for c in range(num_courses):
                for d in range(self.num_days):
                    for sl in range(self.slots_per_day):
                        # If any teacher teaches course c on day d at slot sl, students can attend
                        course_scheduled = model.NewBoolVar(f'course_scheduled_c{c}_d{d}_sl{sl}')
                        model.Add(sum(x[t, c, d, sl, r] 
                                     for t in range(num_teachers) 
                                     for r in range(num_rooms)) >= 1).OnlyEnforceIf(course_scheduled)
                        model.Add(sum(x[t, c, d, sl, r] 
                                     for t in range(num_teachers) 
                                     for r in range(num_rooms)) == 0).OnlyEnforceIf(course_scheduled.Not())
                        
                        # Student can only attend if course is scheduled
                        model.AddImplication(y[s, c, d, sl], course_scheduled)
        
        # Soft constraint: Try to balance teacher loads
        # We'll implement this as an optimization objective
        
        # Soft constraint: Allow for student breaks
        # This is complex to model, so we'll focus on the hard constraints first
        
        print("Setting up solver...")
        
        # Objective function - minimize total cost
        # For now, we'll just aim to find a feasible solution
        
        # Solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300  # Set a time limit of 5 minutes
        
        print("Solving model...")
        status = solver.Solve(model)
        
        print("Solver status:", status)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("Solution found!")
            self.print_timetable(solver, x, teacher_indices, course_indices, room_indices)
            return True
        else:
            print("No solution found within the time limit.")
            return False
    
    def print_timetable(self, solver, x, teacher_indices, course_indices, room_indices):
        """Print the generated timetable"""
        num_teachers = len(self.teachers)
        num_courses = len(self.courses)
        num_rooms = len(self.rooms)
        
        # Create a structured timetable
        timetable = {}
        for d in range(self.num_days):
            day = self.days[d]
            timetable[day] = {}
            for s in range(self.slots_per_day):
                slot = s + 1  # 1-indexed slots
                timetable[day][slot] = []
                
                for t in range(num_teachers):
                    for c in range(num_courses):
                        for r in range(num_rooms):
                            if solver.Value(x[t, c, d, s, r]) == 1:
                                teacher = self.teachers[t]
                                course = self.courses[c]
                                room = self.rooms[r]
                                
                                # Get teacher department name if possible
                                dept_id = self.teacher_dept.get(teacher, '')
                                dept_name = self.dept_id_to_name.get(dept_id, '')
                                
                                timetable[day][slot].append({
                                    'teacher': teacher,
                                    'teacher_dept': dept_name,
                                    'course': course,
                                    'room': room
                                })
        
        # Print timetable
        print("\n===== GENERATED TIMETABLE =====")
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

if __name__ == "__main__":
    generator = TimetableGenerator()
    generator.generate_timetable() 