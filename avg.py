import pandas as pd
import argparse

def convert_to_seconds(length_str):
    """Convert hh:mm format to total seconds"""
    hours, minutes = map(int, length_str.split(':'))
    return hours * 3600 + minutes * 60

def seconds_to_hhmm(seconds):
    """Convert seconds back to hh:mm format"""
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    return f"{int(hours)}:{int(mins):02}"  # Ensure hours and minutes are formatted as integers

def analyze_csv_lengths(input_csv, output_txt=None, print_output=True):
    """
    Analyzes a CSV file containing 'search_term' and 'length' columns.
    Calculates average length for each search term and outputs to a text file and/or console.
    
    Args:
        input_csv (str): Path to the input CSV file
        output_txt (str, optional): Path to the output text file, if None, no file is created
        print_output (bool): Whether to print results to console
    """
    try:
        # Load the CSV file
        data = pd.read_csv(input_csv)
        
        # Convert lengths to seconds
        data['length_seconds'] = data['length'].apply(convert_to_seconds)
        
        # Group by search_term and calculate average length in seconds
        average_lengths = data.groupby('search_term')['length_seconds'].mean().reset_index()
        
        # Convert average length back to hh:mm format
        average_lengths['average_length_hh:mm'] = average_lengths['length_seconds'].apply(seconds_to_hhmm)
        
        # Output results to a text file if specified
        if output_txt:
            with open(output_txt, 'w') as file:
                for index, row in average_lengths.iterrows():
                    file.write(f"Search Term: {row['search_term']}, Average Length: {row['average_length_hh:mm']}\n")
            print(f"Results have been written to {output_txt}")
        
        # Print the results to console if requested
        if print_output:
            print("\nAnalysis Results:")
            print("="*50)
            print(f"{'Search Term':<30} {'Average Length':<15}")
            print("-"*50)
            for index, row in average_lengths.iterrows():
                print(f"{row['search_term']:<30} {row['average_length_hh:mm']:<15}")
            print("="*50)
            print(f"Total: {len(average_lengths)} search terms analyzed")
        
        return True
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Analyze length data from CSV file.')
    parser.add_argument('input_file', help='Path to the input CSV file')
    parser.add_argument('-o', '--output-file', dest='output_file', 
                        help='Path to the output text file (optional)')
    parser.add_argument('--console-only', action='store_true',
                        help='Output to console only, no file will be created')
    parser.add_argument('--no-print', dest='print_output', action='store_false',
                        help='Disable printing results to console')
    parser.set_defaults(print_output=True)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine output file based on arguments
    output_file = None
    if not args.console_only:
        output_file = args.output_file
    
    # If console output is disabled and no file output, warn and set console output back on
    if not args.print_output and output_file is None:
        print("Warning: Both console output and file output were disabled. Enabling console output.")
        args.print_output = True
    
    # Run the analysis with the provided parameters
    success = analyze_csv_lengths(args.input_file, output_file, args.print_output)
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())