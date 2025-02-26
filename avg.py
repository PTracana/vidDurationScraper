import pandas as pd

# Load the CSV file
file_path = 'results.csv'  # Replace with your CSV file path
data = pd.read_csv(file_path)

# Function to convert hh:mm to total seconds
def convert_to_seconds(length_str):
    hours, minutes = map(int, length_str.split(':'))
    return hours * 3600 + minutes * 60

# Convert lengths to seconds
data['length_seconds'] = data['length'].apply(convert_to_seconds)

# Group by search_term and calculate average length in seconds
average_lengths = data.groupby('search_term')['length_seconds'].mean().reset_index()

# Convert average length back to hh:mm format
def seconds_to_hhmm(seconds):
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    return f"{int(hours)}:{mins:02}"  # Ensure hours are formatted as an integer

# Apply conversion to hh:mm format
average_lengths['average_length_hh:mm'] = average_lengths['length_seconds'].apply(seconds_to_hhmm)

# Output results to a text file
output_file = 'final-result.txt'  # Specify the output file name
with open(output_file, 'w') as file:
    for index, row in average_lengths.iterrows():
        file.write(f"Search Term: {row['search_term']}, Average Length: {row['average_length_hh:mm']}\n")

print(f"Results have been written to {output_file}")
