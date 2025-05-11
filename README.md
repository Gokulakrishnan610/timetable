# College Timetable Generator

This is a timetable generation system designed for a college environment using constraint programming with Google's OR-Tools CP-SAT solver. The system generates feasible timetables that satisfy a set of hard constraints while attempting to meet soft constraints.

## Key Features

- Respects teacher constraints (max hours per day, lunch breaks)
- Handles student constraints (max slots per day, no overlaps)
- Manages room allocation (lab rooms for lab courses)
- Ensures lab courses get consecutive slots
- Generates individual timetables for teachers and departments
- Creates comprehensive visualizations including department workload and schedules
- Multiple constraint modes to balance feasibility and realism
- Adaptive constraint relaxation to automatically find feasible solutions
- Staggered scheduling to reduce hallway congestion
- **NEW: Expertise-based teacher assignments** - Intelligently assigns courses based on teacher subject area expertise

## Teacher Expertise Tracking

The system now includes intelligent teacher-to-course assignment based on subject expertise:

1. **Expertise Identification**: Automatically extracts subject areas from course codes (e.g., "MA" from "MA23112")
2. **Expertise Learning**: Analyzes existing course assignments to infer teacher expertise areas
3. **Smart Assignment**: When creating new assignments, prioritizes teachers with relevant subject expertise
4. **Load Balancing**: Ensures even distribution of courses among qualified teachers
5. **Visualization**: Generates charts showing teacher expertise distribution and department-subject coverage

## Constraint Modes

The system offers four constraint modes to balance feasibility with realism:

1. **Relaxed Mode** (`--relaxed`): Fastest solving with minimal constraints, produces less realistic timetables
2. **Balanced Mode** (default): A middle ground that enables key constraints while keeping the problem solvable
3. **Hybrid Mode** (`--hybrid`): More realistic than balanced mode with stronger constraints, but still feasible
4. **Real Mode** (`--real`): All constraints enabled, most realistic but hardest to solve

See `constraints_summary.md` for a detailed breakdown of which constraints are active in each mode.

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
# Use default balanced mode
python run_timetable_system.py

# Use relaxed mode for faster solving
python run_timetable_system.py --relaxed

# Use hybrid mode for more realistic timetables
python run_timetable_system.py --hybrid

# Use real mode for most realistic timetables
python run_timetable_system.py --real

# Enable staggered scheduling to reduce hallway congestion
python run_timetable_system.py --staggered

# Adjust solver timeout (default: 30 minutes)
python run_timetable_system.py --timeout=3600  # 1 hour

# Use adaptive constraint relaxation (automatically tries different constraint levels)
python run_timetable_system.py --hybrid --adaptive

# Control the number of fallback attempts in adaptive mode
python run_timetable_system.py --real --adaptive --max-attempts=2

# Disable expertise-based teacher assignments (use random assignment)
python run_timetable_system.py --no-expertise

# Use mock data for testing
python run_timetable_system.py --mock
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
     * **NEW: Teacher expertise charts**
     * **NEW: Department-subject expertise heatmap**

## Expertise Visualizations

To generate visualizations specifically for teacher expertise:

```bash
python create_expertise_charts.py
```

This will create:
1. **Teacher Expertise Chart**: Shows the number of teachers with expertise in each subject area
2. **Subject Expertise Heatmap**: Shows how different departments cover various subject areas

## Visualizations

The system generates several visualizations to help analyze the timetable:

1. **Timetable Heatmap**: Shows the density of classes by day and time slot
2. **Teacher Load Chart**: Bar chart of teaching load by teacher
3. **Department Load Chart**: Bar chart of teaching load by department
4. **Room Usage Chart**: Bar chart showing room utilization
5. **Course Distribution Chart**: Bar chart showing distribution of courses
6. **Teacher Timetable Grids**: Visual schedules for individual teachers
7. **Department Timetable Grids**: Aggregated schedules for each department
8. **Teacher Expertise Chart**: Distribution of subject expertise among teachers
9. **Department-Subject Heatmap**: Shows which departments cover different subject areas

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

## Staggered Scheduling

The staggered scheduling feature (`--staggered`) helps reduce congestion in hallways and common areas during class changes by:

1. Distributing classes more evenly across time slots
2. Grouping rooms into patterns with different preferred start times
3. Limiting the maximum number of classes in any one time slot

This creates a more natural flow of students throughout the day and reduces strain on campus facilities.

## Adaptive Constraint Mode

With `--adaptive`, the system will automatically try different constraint levels when it fails to find a solution:

1. Starts with the selected constraint mode
2. If no solution found, gradually relaxes constraints
3. Continues until a solution is found or all appropriate modes have been tried

## Analysis Tools

The system includes several analysis tools to evaluate timetable quality and teacher assignments:

### Expertise Matching Analysis

The `analyze_expertise_matching.py` script evaluates how well teachers are matched to courses based on their expertise:

```
python analyze_expertise_matching.py
```

This tool:
- Analyzes matches between teacher expertise and course assignments
- Provides department-wise expertise matching statistics
- Generates a visualization of expertise matching by department
- Outputs detailed analysis to `expertise_matching_analysis.csv`

### Expertise Assignment Comparison

The `compare_expertise_assignments.py` script compares timetables generated with and without expertise-based assignments:

```
python compare_expertise_assignments.py
```

This tool:
- Compares teacher-course assignments from two timetables
- Shows expertise matching rates for each approach
- Breaks down improvements by department
- Visualizes the differences in a side-by-side bar chart

### Workload Distribution Analysis

The `analyze_workload_distribution.py` script examines how teacher workloads are distributed:

```
python analyze_workload_distribution.py
```

This tool:
- Analyzes workload distribution across teachers
- Compares workload statistics with and without expertise-based assignments
- Provides department-wise workload metrics
- Creates histograms and boxplots showing workload distributions

## Command-line Options

The timetable generator supports various command-line options:

```
python run_timetable_system.py [--relaxed|--balanced|--strict|--hybrid] [--staggered] [--no-expertise] [--timeout=SECONDS]
```

- `--relaxed`: Uses relaxed constraints for feasibility
- `--balanced`: Uses balanced constraints (default)
- `--strict`: Uses strict constraints, prioritizing optimal scheduling
- `--hybrid`: Uses hybrid constraints, adjusting based on dataset size
- `--adaptive`: Automatically relaxes constraints if no solution is found
- `--staggered`: Enables staggered scheduling to reduce congestion in hallways
- `--no-expertise`: Disables expertise-based teacher assignments
- `--timeout=SECONDS`: Sets solver timeout in seconds (default: 1800)