import argparse

def parse_text_and_format(input_txt, output_txt, print_output=True):
    """
    Parses a text file where each line is considered a separate entry,
    splits each line by comma, and formats the first and second elements
    into 'Element1 quest Element2 gameplay' format, then saves to a text file.

    Args:
        input_txt (str): Path to the input text file.
        output_txt (str): Path to the output text file.
        print_output (bool): Whether to print formatted lines to console.
    """
    try:
        with open(input_txt, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        formatted_lines = []
        for line in lines:
            # Strip whitespace and split by comma
            parts = [part.strip() for part in line.strip().split(',')]
            if len(parts) >= 2:  # Ensure at least two elements exist
                formatted_line = f"{parts[0]} quest {parts[1]} Walkthrough"
                formatted_lines.append(formatted_line)

        # Save formatted lines to output file
        with open(output_txt, 'w', encoding='utf-8') as txt_file:
            txt_file.write("\n".join(formatted_lines))

        print(f"Formatted data saved to: {output_txt}")
        
        # Print the formatted lines to console if requested
        if print_output:
            print("\nFormatted Results:")
            print("="*40)
            for line in formatted_lines:
                print(line)
            print("="*40)
            print(f"Total: {len(formatted_lines)} entries processed")
        
        return True

    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Parse text file and format specific elements.')
    parser.add_argument('input_file', help='Path to the input text file')
    parser.add_argument('output_file', help='Path to the output text file')
    parser.add_argument('--no-print', dest='print_output', action='store_false', 
                      help='Disable printing results to console')
    parser.set_defaults(print_output=True)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the parser with the provided file paths
    success = parse_text_and_format(args.input_file, args.output_file, args.print_output)
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())