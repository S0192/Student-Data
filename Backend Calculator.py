import pandas as pd

def update_course_counts(Center_Overview, student_data):
    # Debug: Print initial state of Center_Overview
    print("\nBefore update:\n", Center_Overview.head())

    # Reset all course counts and student numbers
    Center_Overview.loc[:, Center_Overview.columns[2:]] = 0
    Center_Overview['Number_of_Students'] = 0

    # Iterate through each row in Student Data
    for index, student in student_data.iterrows():
        center_name = student['Center']

        # Debug: Log missing centers
        if center_name not in Center_Overview['Center Name'].values:
            print(f"Center '{center_name}' is missing in Center_Overview.")
            continue

        # Identify shared course columns
        common_course_columns = set(Center_Overview.columns[2:]) & set(student_data.columns[3:])

        for course_column in common_course_columns:
            progress_value = pd.to_numeric(student[course_column], errors='coerce')  # Convert to numeric
            if not pd.isna(progress_value) and progress_value > 0:
                Center_Overview.loc[Center_Overview['Center Name'] == center_name, course_column] += 1

        # Update the number of students for the center
        Center_Overview.loc[Center_Overview['Center Name'] == center_name, 'Number_of_Students'] += 1

    # Debug: Print updated state of Center_Overview
    print("\nAfter update:\n", Center_Overview.head())

def update_and_write_data():
    # Read data from the Excel sheets
    Center_Overview = pd.read_excel('AAE4B220.xlsx', sheet_name='Center_Overview').fillna(0)
    student_data = pd.read_excel('AAE4B220.xlsx', sheet_name='Student Data').fillna(0)

    # Ensure the 'Center' column exists in Student Data
    if 'Center' not in student_data.columns:
        raise ValueError("'Center' column is missing in Student Data sheet.")

    # Clean column names in Center_Overview
    Center_Overview.columns = Center_Overview.columns.str.strip()

    # Remove duplicate columns
    Center_Overview = Center_Overview.loc[:, ~Center_Overview.columns.duplicated()]

    # Update course counts
    update_course_counts(Center_Overview, student_data)

    # Update average progress
    for center in Center_Overview['Center Name'].unique():
        center_rows = Center_Overview[Center_Overview['Center Name'] == center]

        for course_column in Center_Overview.columns:
            if course_column.startswith('Course'):
                course_name = course_column.replace('Course', '').strip()

                total_progress_in_center = 0
                total_students_in_center = 0

                for _, student in student_data.iterrows():
                    if student['Center'] == center:
                        progress_value = pd.to_numeric(student[course_column], errors='coerce')
                        if not pd.isna(progress_value):
                            total_progress_in_center += progress_value
                            total_students_in_center += 1

                average_progress = (
                    total_progress_in_center / total_students_in_center
                    if total_students_in_center > 0
                    else 0
                )

                # Create progress column if missing
                progress_column_name = f'Progress_{course_name}'
                if progress_column_name not in Center_Overview.columns:
                    Center_Overview[progress_column_name] = 0

                Center_Overview.loc[Center_Overview['Center Name'] == center, progress_column_name] = min(100, average_progress)

    # Debug: Print final state before saving
    print("\nFinal Center_Overview:\n", Center_Overview.head())

    # Write data back to the Excel sheets
    with pd.ExcelWriter('Updated_AAE4B220.xlsx', engine='openpyxl') as writer:
        Center_Overview.to_excel(writer, sheet_name='Center_Overview', index=False)
        student_data.to_excel(writer, sheet_name='Student Data', index=False)

# Run the script once for debugging
update_and_write_data()
