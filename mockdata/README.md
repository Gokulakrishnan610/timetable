# Mock Data for Timetable Generator Testing

This folder contains simplified mock data for testing the timetable generator system. The data structure follows the same format as the real data but with a reduced dataset for easier testing and development.

## Files Included

1. **departments.csv** - Contains 7 mock departments
2. **teachers.csv** - Contains 20 mock teachers across different departments
3. **students.csv** - Contains 60 mock students across 3 departments (20 each)
4. **course.csv** - Contains 30 mock courses with their details
5. **rooms.csv** - Contains 20 mock classrooms and labs
6. **course_for_the_department_and_thier_faculty.csv** - Contains 30 mock course assignments with faculty

## Data Structure

The mock data maintains all the required fields from the original dataset but with simplified values. Each file uses the exact same column structure as the real data to ensure compatibility with the timetable generator.

## Usage

To use this mock data for testing:

1. Make sure the timetable generator is configured to read from the `mockdata` directory instead of the `data` directory
2. Run the timetable generator with appropriate parameters
3. Verify the generated timetable based on the constraints

This simplified dataset allows for faster testing cycles and easier debugging since the data volume is significantly reduced compared to the real dataset. 