# College Timetable Generator

This is a timetable generation system designed for a college environment using constraint programming with Google's OR-Tools CP-SAT solver. The system generates feasible timetables that satisfy a set of hard constraints while attempting to meet soft constraints.

## Key Features

- Respects teacher constraints (max hours per day, lunch breaks)
- Handles student constraints (max slots per day, no overlaps)
- Manages room allocation (lab rooms for lab courses)
- Ensures lab courses get consecutive slots
- Generates individual timetables for teachers and departments
- Creates comprehensive visualizations including department workload and schedules

## Constraints Implemented

### Teacher Constraints
- Maximum 5 hours per day
- Must have 1 free slot between 11:30-2:00 for lunch
- Assigned only 1 subject per slot
- Lab requires 2 consecutive slots

### Student Constraints
- No student should exceed 6 slots/day
- No overlapping classes (no 2 classes in the same slot)
- Only enrolled in their registered courses

### Room Constraints
- Each room used only once per slot
- Lab subjects only in lab rooms

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Place your data files in the `data` directory:
   - departments.csv
   - teachers.csv
   - courses.csv
   - rooms.csv
   - students.csv
   - course_for_the_department_and_thier_faculty.csv

2. Run the complete timetable system:

```bash
python run_timetable_system.py
```

3. The program will generate:
   - A master timetable (`master_timetable.csv`)
   - Individual teacher timetables (`timetable_teacher_*.csv`)
   - Department timetables (`timetable_dept_*.csv`)
   - Various visualizations:
     * Overall timetable heatmap
     * Teacher workload charts
     * Department workload charts
     * Room usage statistics
     * Course distribution
     * Individual teacher and department schedule visualizations

## Visualizations

The system generates several visualizations to help analyze the timetable:

1. **Timetable Heatmap**: Shows the density of classes by day and time slot
2. **Teacher Load Chart**: Bar chart of teaching load by teacher
3. **Department Load Chart**: Bar chart of teaching load by department
4. **Room Usage Chart**: Bar chart showing room utilization
5. **Course Distribution Chart**: Bar chart showing distribution of courses
6. **Teacher Timetable Grids**: Visual schedules for individual teachers
7. **Department Timetable Grids**: Aggregated schedules for each department

## Data Format

The program expects the following CSV file structure:

### departments.csv
- id: Unique department identifier
- dept_name: Department name
- date_established: Date when department was established
- contact_info: Contact information for the department

### rooms.csv
- room_number: Unique room identifier
- block: Building block (A, B, C, etc.)
- description: Room description
- is_lab: Boolean indicating if the room is a lab (True/False)
- room_type: Type of room
- room_min_cap: Minimum capacity
- room_max_cap: Maximum capacity
- has_projector: Boolean
- has_ac: Boolean
- tech_level: Technology level
- maintained_by_id: Maintaining department

### teachers.csv
- id: Unique identifier
- teacher_id__email: Email address (used as primary key)
- teacher_id__first_name, teacher_id__last_name: Name
- dept_id: Department ID (linked to departments.csv id)
- staff_code: Staff code
- teacher_role: Role (Professor, Assistant Professor, etc.)
- is_industry_professional: Boolean
- resignation_status: Status (active/resigned)

### course.csv
- id: Unique identifier
- course_id: Course code (used as primary key)
- course_name: Course name
- course_dept_id: Department offering the course
- credits: Number of credits
- lecture_hours, practical_hours, tutorial_hours: Hours per week
- regulation, REGULATION: Regulation year
- course_type: Type of course
- Year, SEMESTER: Year and semester
- for_dept, teaching_dept: Departments offering/teaching

### students.csv
- student_id__email: Email address (used as primary key)
- student_id__first_name, student_id__last_name: Name
- current_semester: Current semester
- year: Year of study
- roll_no: Roll number
- dept: Department

### course_for_the_department_and_thier_faculty.csv
- Various fields including Course Code and Faculty (department teaching)

## License

This project is available under the MIT License.

## Acknowledgments

- Uses Google's OR-Tools for constraint programming
- Designed to handle complex educational timetabling challenges 