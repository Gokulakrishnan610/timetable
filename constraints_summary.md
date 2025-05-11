# Timetable Generator Constraints Summary

This document summarizes the different constraints implemented in the timetable generation system and how they are handled in different constraint modes.

## Constraint Modes

The system offers three different constraint modes to balance between feasibility and realism:

1. **Relaxed Mode** (`--relaxed`): Minimal constraints for faster solving, useful for quick testing.
2. **Balanced Mode** (default): A practical middle ground with key constraints enabled.
3. **Hybrid Mode** (`--hybrid`): More realistic than balanced mode but still solvable.
4. **Real Mode** (`--real`): All constraints enabled for maximum realism.

## Hard Constraints (Always Enforced)

These constraints are enforced in all modes:

| Constraint | Description | Status |
|------------|-------------|--------|
| Teacher Availability | A teacher can teach at most one course in one slot | ✅ |
| Course Uniqueness | A course can be taught by only one teacher at a time | ✅ |
| Room Usage | A room can be used for at most one course in one slot | ✅ |
| Teacher Load | Maximum 5 teaching hours per day for teachers | ✅ |
| Room Type Compatibility | Lab courses must be in lab rooms | ✅ |

## Soft Constraints (Varies by Mode)

These constraints can be enabled or disabled based on the selected mode:

| Constraint | Relaxed | Balanced | Hybrid | Real | Description |
|------------|---------|----------|--------|------|-------------|
| Lunch Breaks | ❌ | ✅ | ✅ | ✅ | Teachers should have at least one free slot during lunch time |
| Lab Consecutive Slots | ❌ | ✅ | ✅ | ✅ | Lab courses require consecutive slots |
| Min Course Instances | 1 | 1 | 2 | 2 | Minimum number of times each course must be scheduled |
| Student Conflict Avoidance | ❌ | ❌ | ✅ | ✅ | Avoid scheduling courses from the same department/year at the same time |
| Staggered Scheduling | Optional | Optional | Optional | Optional | Distribute classes more evenly to reduce hallway congestion |
| Teacher Expertise Match | ✅ | ✅ | ✅ | ✅ | Prefer assigning teachers to courses in their expertise areas |

## Teacher Assignment Preferences

| Constraint | Original State | Current State | Impact |
|------------|----------------|---------------|--------|
| Teacher-Course Assignment | Random assignment based on department | **Expertise-based assignment**:<br>- Subject areas extracted from course codes<br>- Teachers matched to courses in their expertise areas<br>- Load balanced among qualified teachers | More realistic teacher assignments that respect teacher specializations and qualifications |

## Time Slot Preferences

| Constraint | Original State | Current State | Impact |
|------------|----------------|---------------|--------|
| Time Slot Preferences | No specific preferences | Using weighted objective function:<br>- Lab courses preferred in morning slots (slots 1-4)<br>- Theory courses evenly distributed with slight preference for mid-day slots | Creates more natural schedule, placing lab sessions earlier when students are more focused |
| Staggered Scheduling | Classes potentially clustered at popular times | When enabled (`--staggered`):<br>- Rooms divided into 3 groups with staggered time preferences<br>- Maximum classes per time slot limited<br>- Groups prefer different time patterns | Reduces hallway congestion during class changes and distributes load more evenly across campus facilities |

## Adaptive Constraint Relaxation

With the `--adaptive` flag, the system will automatically try different constraint levels when it fails to find a solution:

1. Starts with the selected constraint mode
2. If no solution found, gradually relaxes constraints by trying less strict modes
3. Continues until a solution is found or all appropriate modes have been tried

This provides the best balance between feasibility and realism for your specific dataset.

## Solver Performance Control

You can control the solver's timeout period using the `--timeout` parameter:

```
python run_timetable_system.py --timeout=3600  # Set timeout to 1 hour
```

The default timeout is 30 minutes (1800 seconds). For more complex constraint modes (hybrid and real), increasing the timeout may help find solutions.

## Constraint Categories

### 1. Problem Size Reduction

**Original**: Full set of teachers, courses, rooms, days, and slots.

**Current**: Significantly reduced to focus on a smaller subset:
- Limited to 100 courses
- Selected subset of teachers who teach these courses (max 200)
- Reduced to 50 rooms
- Limited to 4 days
- Limited to 8 time slots per day

**Impact**: Drastically reduces the complexity and computational requirements, making the problem solvable with available resources.

### 2. Consecutive Lab Sessions

**Original**: Lab courses must be scheduled in consecutive time slots.

**Modification**:
- **Relaxed Mode**: No consecutive slot requirement
- **Balanced Mode**: Restored - Lab courses are scheduled in consecutive slots
- **Hybrid Mode**: Restored - Lab courses are scheduled in consecutive slots
- **Real Mode**: Fully enforced - Lab courses require consecutive time slots

**Impact**: Ensures lab courses have sufficient time for practical work in balanced, hybrid, and real modes.

### 3. Lunch Break Requirements

**Original**: Teachers should have at least one free slot during lunch hours.

**Modification**:
- **Relaxed Mode**: No lunch break guarantee
- **Balanced Mode**: Restored - Teachers have at least one free slot during lunch
- **Hybrid Mode**: Restored - Teachers have at least one free slot during lunch
- **Real Mode**: Fully enforced - Lunch breaks guaranteed

**Impact**: Creates more humane schedules for teachers in balanced, hybrid, and real modes.

### 4. Course Scheduling Frequency

**Original**: Each course must be scheduled multiple times per week based on credit hours.

**Modification**:
- **Relaxed Mode**: Each course scheduled at least once
- **Balanced Mode**: Each course scheduled at least once
- **Hybrid Mode**: Each course scheduled at least twice
- **Real Mode**: Each course scheduled at least twice

**Impact**: Reduces constraints while ensuring all courses are scheduled, with hybrid and real modes providing better educational distribution.

### 5. Teacher Load Balance

**Original**: Teachers have maximum load preferences and specific course preferences.

**Current**: Each teacher limited to maximum of 5 courses, no preference consideration.

**Impact**: Simplifies constraints while preventing teacher overload.

### 6. Room Type Compatibility

**Original**: Strict matching of course types to room types.

**Current**: Theory courses can be scheduled in any room, lab courses preferentially scheduled in lab rooms.

**Impact**: More flexible room assignments, but may lead to capacity or equipment mismatches.

### 7. Student Schedule Constraints

**Original**: Courses that share students cannot be scheduled simultaneously.

**Modification**:
- **Relaxed Mode**: No student conflict avoidance
- **Balanced Mode**: No student conflict avoidance
- **Hybrid Mode**: Restored - Courses from the same department and year aren't scheduled simultaneously
- **Real Mode**: Restored - Courses from the same department and year aren't scheduled simultaneously

**Impact**: Prevents conflicts for students in the same program in hybrid and real modes.

### 8. Time Slot Preferences

**Original**: No specific time slot preferences for different course types.

**Current**: The system now uses a weighted objective function to prefer:
- Lab courses in morning slots (slots 1-4)
- Theory courses evenly distributed with a slight preference for mid-day slots

**Impact**: Creates a more natural schedule with lab sessions earlier in the day when students are more focused, while still keeping the timetable feasible.

### 9. Teacher-Course Assignment

**Original**: Random assignment based on department affiliation.

**Current**: 
- Subject areas automatically extracted from course codes (e.g., "MA" from "MA23112" for Mathematics)
- Teacher expertise inferred from existing assignments and tracked
- New assignments prioritize teachers with expertise in the relevant subject area
- Load balancing ensures even distribution among qualified teachers

**Impact**: More realistic teacher assignments that respect teacher specializations, leading to better quality education and teacher satisfaction.

### 10. Department-specific Constraints

**Original**: Various department-specific requirements for course scheduling.

**Current**: Department-specific constraints are not implemented.

**Impact**: May not meet all department needs, but greatly simplifies the model.

## Summary

The current implementation successfully generates a feasible timetable by strategically reducing the problem size and selectively applying constraints. The four modes offer different trade-offs between speed and realism:

1. **Relaxed mode** prioritizes finding a solution quickly
2. **Balanced mode** enables the most important constraints (consecutive lab slots and lunch breaks)
3. **Hybrid mode** adds student conflict avoidance and requires multiple course instances
4. **Real mode** enforces all constraints for a more realistic timetable

With the adaptive mode, the system can automatically find the right balance between realism and feasibility.

## Command-line Usage

Generate a timetable with:

```
python run_timetable_system.py [--relaxed|--balanced|--hybrid|--real] [--timeout=SECONDS] [--adaptive] [--max-attempts=NUM] [--mock]
```

- Use `--relaxed` for faster, less realistic generation
- Use `--balanced` (default) for a compromise between speed and realism
- Use `--hybrid` for a more realistic timetable that's still feasible to solve
- Use `--real` for the most realistic timetable (may be difficult to solve)
- Use `--timeout=SECONDS` to adjust the solver timeout (default: 1800 seconds)
- Use `--adaptive` to automatically try different constraint levels if needed
- Use `--max-attempts=NUM` to control how many constraint levels to try with adaptive mode
- Add `--mock` to use mock data for testing 