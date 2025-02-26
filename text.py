import requests
from bs4 import BeautifulSoup
import argparse
import os
import csv
from urllib.parse import urlparse
import re
from collections import defaultdict

def scrape_story_quest_tables(url):
    """
    Scrape content from tables labeled 'list of story quests' from a given URL.
    
    Args:
        url (str): The URL to scrape.
        
    Returns:
        list: List of dictionaries, where each dict contains:
            - 'title': Table title/identifier
            - 'headers': List of column headers
            - 'rows': List of rows, where each row is a list of cell values
            - 'text_content': Formatted text representation of the table
    """
    try:
        # Add User-Agent header to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Send GET request to the URL
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # List to store all found tables
        found_tables = []
        
        # Method 1: Look for tables with caption containing the phrase
        for table in soup.find_all('table'):
            caption = table.find('caption')
            if caption and re.search(r'list\s+of\s+story\s+quests', caption.get_text().lower()):
                table_data = extract_table_data(table, f"Table with caption: {caption.get_text().strip()}")
                if table_data:
                    found_tables.append(table_data)
                continue
                
        # Method 2: Look for tables with a preceding heading containing the phrase
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if re.search(r'list\s+of\s+story\s+quests', heading.get_text().lower()):
                next_table = heading.find_next('table')
                if next_table:
                    table_data = extract_table_data(next_table, f"Table after heading: {heading.get_text().strip()}")
                    if table_data:
                        found_tables.append(table_data)
        
        # Method 3: Look for tables with specific class/id containing the phrase
        for table in soup.find_all('table'):
            table_id = table.get('id', '').lower()
            table_class = ' '.join(table.get('class', [])).lower()
            
            if ('list' in table_id and 'story' in table_id and 'quest' in table_id) or \
               ('list' in table_class and 'story' in table_class and 'quest' in table_class):
                class_or_id = f"id='{table_id}'" if table_id else f"class='{table_class}'"
                table_data = extract_table_data(table, f"Table with {class_or_id}")
                if table_data:
                    found_tables.append(table_data)
        
        # If no tables found yet, try a more general approach
        if not found_tables:
            # Look for tables near text containing "list of story quests"
            for element in soup.find_all(text=re.compile(r'list\s+of\s+story\s+quests', re.I)):
                parent = element.parent
                # Look for a table nearby (as a sibling or as a child of a nearby element)
                nearby_table = parent.find_next('table')
                if nearby_table:
                    table_data = extract_table_data(nearby_table, f"Table near text: '{element.strip()}'")
                    if table_data:
                        found_tables.append(table_data)
        
        return found_tables
    
    except requests.exceptions.RequestException as e:
        return [{"title": "Error", "headers": [], "rows": [], "text_content": f"Error fetching the URL: {e}"}]
    except Exception as e:
        return [{"title": "Error", "headers": [], "rows": [], "text_content": f"An error occurred: {e}"}]

def extract_table_data(table, title):
    """
    Extract structured data from a table.
    
    Args:
        table (BeautifulSoup tag): The table to extract content from.
        title (str): Title/identifier for the table.
        
    Returns:
        dict: Contains headers, rows, and formatted text content.
    """
    # Extract headers
    headers = []
    header_row = table.find('thead')
    if header_row:
        header_cells = header_row.find_all(['th', 'td'])
    else:
        # If no thead, try the first row
        first_row = table.find('tr')
        if first_row:
            header_cells = first_row.find_all(['th', 'td'])
        else:
            header_cells = []
    
    for cell in header_cells:
        headers.append(cell.get_text().strip())
    
    # Get the indices of important columns
    name_index = -1
    chapter_index = -1
    version_index = -1
    
    for i, header in enumerate(headers):
        header_lower = header.lower()
        if 'name' in header_lower:
            name_index = i
        elif 'chapter' in header_lower:
            chapter_index = i
        elif 'version' in header_lower:
            version_index = i
    
    # Extract rows (skip the first row if it was used for headers and no thead was found)
    all_rows = []
    rows = table.find_all('tr')
    start_index = 1 if headers and not table.find('thead') else 0
    
    for row in rows[start_index:]:
        cells = row.find_all(['td', 'th'])
        row_data = []
        for cell in cells:
            row_data.append(cell.get_text().strip())
        if row_data:
            all_rows.append(row_data)
    
    # Sort the rows by Version (if present), then by Name, then by Chapter
    try:
        # First try sorting by version numerically
        if version_index >= 0:
            all_rows.sort(key=lambda row: (
                float(re.search(r'(\d+(?:\.\d+)*)', row[version_index]).group(1)) if version_index < len(row) and re.search(r'(\d+(?:\.\d+)*)', row[version_index]) else 0,
                row[name_index].lower() if name_index >= 0 and name_index < len(row) else "",
                row[chapter_index].lower() if chapter_index >= 0 and chapter_index < len(row) else ""
            ))
    except (ValueError, AttributeError):
        # Fall back to string sorting
        if version_index >= 0:
            all_rows.sort(key=lambda row: (
                row[version_index] if version_index < len(row) else "",
                row[name_index].lower() if name_index >= 0 and name_index < len(row) else "",
                row[chapter_index].lower() if chapter_index >= 0 and chapter_index < len(row) else ""
            ))
    
    # Generate text representation with sorted rows
    text_content = ""
    if headers:
        text_content += " | ".join(headers) + "\n"
        text_content += "-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)) + "\n"
    
    for row in all_rows:
        text_content += " | ".join(row) + "\n"
    
    return {
        "title": title,
        "headers": headers,
        "rows": all_rows,
        "text_content": text_content,
        "name_index": name_index,
        "chapter_index": chapter_index,
        "version_index": version_index
    }

def organize_by_character(tables):
    """
    Organize the table data by character name, with chapters and versions.
    
    Args:
        tables (list): List of table data dictionaries.
    
    Returns:
        dict: Data organized by character.
    """
    if not tables:
        return None
    
    character_data = defaultdict(list)
    headers = None
    
    for table in tables:
        if not headers:
            headers = table['headers']
        
        name_idx = table['name_index']
        chapter_idx = table['chapter_index']
        version_idx = table['version_index']
        
        if name_idx == -1 or chapter_idx == -1:
            continue
        
        for row in table['rows']:
            if len(row) > max(name_idx, chapter_idx):
                name = row[name_idx]
                # Add the row to the character's data
                character_data[name].append(row)
    
    # Sort each character's rows by version, then chapter
    for character, rows in character_data.items():
        if tables[0]['version_index'] >= 0:
            try:
                # Try numeric version sorting
                rows.sort(key=lambda row: (
                    float(re.search(r'(\d+(?:\.\d+)*)', row[version_idx]).group(1)) if version_idx < len(row) and re.search(r'(\d+(?:\.\d+)*)', row[version_idx]) else 0,
                    row[chapter_idx].lower() if chapter_idx < len(row) else ""
                ))
            except (ValueError, AttributeError):
                # Fall back to string sorting
                rows.sort(key=lambda row: (
                    row[version_idx] if version_idx < len(row) else "",
                    row[chapter_idx].lower() if chapter_idx < len(row) else ""
                ))
        else:
            # Sort by chapter if no version column
            rows.sort(key=lambda row: row[chapter_idx].lower() if chapter_idx < len(row) else "")
    
    return {
        "headers": headers,
        "character_data": character_data
    }

def save_character_based_txt(tables, url, output_path=None):
    """
    Save the scraped tables to a character-based text file.
    
    Args:
        tables (list): List of table data dictionaries.
        url (str): The URL that was scraped (used for filename generation).
        output_path (str, optional): Custom output path.
    
    Returns:
        str: Path to the saved file.
    """
    # Generate filename from URL if no output path is provided
    if not output_path:
        # Extract domain name from URL
        domain = urlparse(url).netloc
        # Clean domain name for filename
        domain = domain.replace('.', '_')
        filename = f"{domain}_story_quests.txt"
    else:
        filename = output_path
    
    # Get organized character data
    organized_data = organize_by_character(tables)
    
    # Save text to file
    with open(filename, 'w', encoding='utf-8') as file:
        if not tables:
            file.write("No tables labeled 'list of story quests' found on the page.")
        elif not organized_data:
            # Fall back to standard output if organization fails
            for i, table in enumerate(tables):
                file.write(f"--- {table['title']} ---\n")
                file.write(table['text_content'])
                file.write("\n\n")
        else:
            file.write("STORY QUESTS BY CHARACTER\n")
            file.write("=======================\n\n")
            
            # Get header string
            headers = organized_data["headers"]
            header_str = " | ".join(headers) if headers else ""
            divider = "-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)) if headers else ""
            
            # Write each character's data
            for character, rows in sorted(organized_data["character_data"].items()):
                file.write(f"CHARACTER: {character}\n")
                file.write("-------------\n")
                
                if header_str:
                    file.write(header_str + "\n")
                    file.write(divider + "\n")
                
                for row in rows:
                    file.write(" | ".join(row) + "\n")
                
                file.write("\n\n")
    
    return os.path.abspath(filename)

def save_character_based_csv(tables, url, output_path=None):
    """
    Save the scraped tables to character-based CSV files.
    
    Args:
        tables (list): List of table data dictionaries.
        url (str): The URL that was scraped (used for filename generation).
        output_path (str, optional): Custom output path prefix.
    
    Returns:
        list: Paths to the saved CSV files.
    """
    if not tables:
        return []
    
    saved_files = []
    
    # Extract domain name from URL for filename generation
    domain = urlparse(url).netloc.replace('.', '_')
    
    # Get organized character data
    organized_data = organize_by_character(tables)
    
    if not organized_data:
        # Fall back to standard output if organization fails
        for i, table in enumerate(tables):
            # Generate filename
            if not output_path:
                if len(tables) == 1:
                    filename = f"{domain}_story_quests.csv"
                else:
                    filename = f"{domain}_story_quests_{i+1}.csv"
            else:
                if len(tables) == 1:
                    filename = f"{output_path}.csv" if not output_path.endswith('.csv') else output_path
                else:
                    base = output_path.rsplit('.', 1)[0] if output_path.endswith('.csv') else output_path
                    filename = f"{base}_{i+1}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers if they exist
                if table['headers']:
                    writer.writerow(table['headers'])
                
                # Write data rows
                for row in table['rows']:
                    writer.writerow(row)
                
            saved_files.append(os.path.abspath(filename))
    else:
        # Save main combined CSV
        if not output_path:
            main_filename = f"{domain}_story_quests_all.csv"
        else:
            main_filename = f"{output_path}.csv" if output_path.endswith('.csv') else f"{output_path}.csv"
        
        with open(main_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            if organized_data['headers']:
                writer.writerow(organized_data['headers'])
            
            # Write all rows, sorted by character name
            for character, rows in sorted(organized_data["character_data"].items()):
                for row in rows:
                    writer.writerow(row)
        
        saved_files.append(os.path.abspath(main_filename))
        
        # Save individual character CSVs
        for character, rows in sorted(organized_data["character_data"].items()):
            # Create a safe filename from the character name
            safe_character = re.sub(r'[^a-zA-Z0-9_-]', '_', character)
            
            if not output_path:
                char_filename = f"{domain}_character_{safe_character}.csv"
            else:
                base = output_path.rsplit('.', 1)[0] if output_path.endswith('.csv') else output_path
                char_filename = f"{base}_character_{safe_character}.csv"
            
            with open(char_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                if organized_data['headers']:
                    writer.writerow(organized_data['headers'])
                
                # Write character rows
                for row in rows:
                    writer.writerow(row)
            
            saved_files.append(os.path.abspath(char_filename))
    
    return saved_files

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape "list of story quests" tables and organize by character name with chapters and versions.')
    parser.add_argument('url', help='URL of the webpage to scrape')
    parser.add_argument('-o', '--output', help='Output filename base (without extension, optional)')
    parser.add_argument('-c', '--combined', action='store_true', help='Only create combined files, not individual character files')
    
    # Parse arguments
    args = parser.parse_args()
    
    print(f"Scraping 'list of story quests' tables from: {args.url}")
    
    # Scrape tables from URL
    tables = scrape_story_quest_tables(args.url)
    
    # Generate output path base (without extension)
    output_base = None
    if args.output:
        output_base = args.output.rsplit('.', 1)[0] if '.' in args.output else args.output
    
    # Save to TXT format
    txt_path = save_character_based_txt(tables, args.url, f"{output_base}.txt" if output_base else None)
    
    # Save to CSV format(s)
    csv_paths = save_character_based_csv(tables, args.url, output_base)
    
    # Print results
    print(f"Tables scraped and organized by character name, chapter, and version!")
    print(f"Text output saved to: {txt_path}")
    
    if csv_paths:
        if len(csv_paths) == 1:
            print(f"CSV output saved to: {csv_paths[0]}")
        else:
            main_csv = next((p for p in csv_paths if "all" in p or not "character" in p), None)
            if main_csv:
                print(f"Main CSV output saved to: {main_csv}")
                
                if not args.combined:
                    character_csvs = [p for p in csv_paths if "character" in p]
                    if character_csvs:
                        print(f"Individual character CSV files:")
                        for path in character_csvs:
                            char_name = os.path.basename(path).split('_character_')[1].split('.csv')[0]
                            print(f"  - {char_name}: {path}")
    elif tables:
        print("Note: No CSV files were created as no valid tables were found.")
    else:
        print("No tables matching 'list of story quests' were found on the page.")

if __name__ == "__main__":
    main()