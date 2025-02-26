import csv

def parse_csv_and_format(input_csv, output_txt):
    """
    Parses a CSV file and formats the first and second elements of each row
    into 'Element1 quest Element2 gameplay' format, then saves to a text file.

    Args:
        input_csv (str): Path to the input CSV file.
        output_txt (str): Path to the output text file.
    """
    try:
        with open(input_csv, 'r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)

            formatted_lines = []
            for row in reader:
                if len(row) >= 2:  # Ensure at least two elements exist
                    formatted_line = f"{row[0]} quest {row[1]} gameplay"
                    formatted_lines.append(formatted_line)

        # Save formatted lines to output file
        with open(output_txt, 'w', encoding='utf-8') as txt_file:
            txt_file.write("\n".join(formatted_lines))

        print(f"Formatted data saved to: {output_txt}")

    except Exception as e:
        print(f"Error processing file: {e}")

# Example usage
input_csv_file = "genshin-impact_fandom_com_story_quests.csv"  # Replace with actual CSV file path
output_txt_file = "output.txt"  # Replace with desired output filename
parse_csv_and_format(input_csv_file, output_txt_file)
