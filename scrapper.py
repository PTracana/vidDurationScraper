import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from urllib.parse import quote_plus

def scrape_youtube_video_lengths(search_query, max_results=10, safety_limit=20):
    """
    Scrapes YouTube video lengths for videos containing a specific search query in their title.
    
    Args:
        search_query (str): The search term to look for in YouTube video titles
        max_results (int): Maximum number of results to return
        safety_limit (int): Hard upper limit for results to prevent IP blocking
        
    Returns:
        list: A list of dictionaries containing video title, length, url and relevance score
    """
    # Enforce the safety limit regardless of input
    max_results = min(max_results, safety_limit)
    
    # Format the search query for URL - add "intitle:" to focus on titles
    search_terms = search_query.lower().split()
    formatted_query = quote_plus(f"intitle:{search_query}")
    
    # Construct the YouTube search URL
    search_url = f"https://www.youtube.com/results?search_query={formatted_query}"
    
    # Send request with headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    print(f"Fetching search results for '{search_query}'...")
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve search results. Status code: {response.status_code}")
        return []
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize results list
    candidate_videos = []
    
    # Direct regex approach for video IDs
    video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', response.text)
    unique_ids = list(dict.fromkeys(video_ids))  # Remove duplicates
    
    print(f"Found {len(unique_ids)} potential videos. Filtering for relevance...")
    
    # First pass: collect all candidate videos with their titles
    processed_count = 0
    for video_id in unique_ids:
        if processed_count >= max_results * 2:  # Process twice as many as we need to filter for relevance
            break
            
        # Get the video page
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            video_response = requests.get(video_url, headers=headers)
            processed_count += 1
            
            if video_response.status_code == 200:
                video_soup = BeautifulSoup(video_response.text, 'html.parser')
                
                # Extract title
                title_tag = video_soup.find("meta", property="og:title")
                title = title_tag["content"] if title_tag else "Unknown Title"
                
                # Calculate relevance score (simple word matching)
                title_lower = title.lower()
                # Count how many search terms appear in the title
                matching_terms = sum(1 for term in search_terms if term in title_lower)
                # Score is percentage of search terms that appear in title
                relevance_score = (matching_terms / len(search_terms)) * 100 if search_terms else 0
                
                # Only consider videos with at least one matching term
                if matching_terms > 0:
                    # Extract duration
                    duration_tag = video_soup.find("meta", itemprop="duration")
                    duration = duration_tag["content"] if duration_tag else "Unknown"
                    
                    # Format ISO 8601 duration (PT1H2M3S) to a readable format
                    if duration.startswith("PT"):
                        duration = duration[2:]  # Remove PT prefix
                        hours = re.search(r'(\d+)H', duration)
                        minutes = re.search(r'(\d+)M', duration)
                        seconds = re.search(r'(\d+)S', duration)
                        
                        formatted_duration = ""
                        if hours:
                            formatted_duration += f"{hours.group(1)}:"
                        if minutes:
                            if hours:
                                formatted_duration += f"{minutes.group(1).zfill(2)}:"
                            else:
                                formatted_duration += f"{minutes.group(1)}:"
                        else:
                            formatted_duration += "0:"
                        if seconds:
                            formatted_duration += f"{seconds.group(1).zfill(2)}"
                        else:
                            formatted_duration += "00"
                            
                        duration = formatted_duration
                    
                    candidate_videos.append({
                        "title": title,
                        "length": duration,
                        "url": video_url,
                        "relevance": relevance_score
                    })
                
                # Throttle requests to avoid being blocked
                time.sleep(2)
        
        except Exception as e:
            print(f"  Error processing video {video_id}: {str(e)}")
    
    # Sort by relevance score and take top max_results
    results = sorted(candidate_videos, key=lambda x: x['relevance'], reverse=True)[:max_results]
    
    return results

def trim_title(title, max_length=70):
    """
    Trims a title to a reasonable length and adds ellipsis if needed
    
    Args:
        title (str): The video title to trim
        max_length (int): Maximum length for the title
        
    Returns:
        str: The trimmed title
    """
    if len(title) <= max_length:
        return title
    return title[:max_length] + "..."

def save_to_csv(results, filename="youtube_video_lengths.csv"):
    """
    Saves the scraped results to a CSV file
    
    Args:
        results (list): List of dictionaries containing video information
        filename (str): Name of the CSV file to save results to
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'length', 'url', 'relevance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"Results saved to {filename}")

def main():
    search_query = input("Enter the search term to find in YouTube video titles: ")
    
    # Make max_results configurable but with a reasonable default and a clear safety warning
    while True:
        try:
            max_results_input = input("Enter maximum number of results to retrieve (default: 10, max recommended: 20): ")
            max_results = 10 if max_results_input == "" else int(max_results_input)
            
            if max_results <= 0:
                print("Number of results must be positive. Using default of 10.")
                max_results = 10
            elif max_results > 20:
                confirmation = input(f"WARNING: Requesting {max_results} results may increase the risk of being temporarily blocked by YouTube. Continue? (y/n): ").lower()
                if confirmation != 'y':
                    print("Using safer limit of 20 results.")
                    max_results = 20
            break
        except ValueError:
            print("Please enter a valid number. Using default of 10.")
            max_results = 10
            break
    
    # Set a safety limit that's 2x the user's requested max but capped at 30
    safety_limit = min(max_results * 2, 30)
    
    print(f"Beginning YouTube search (limited to {max_results} videos maximum)...")
    results = scrape_youtube_video_lengths(search_query, max_results, safety_limit)
    
    if results:
        print(f"\nFound {len(results)} relevant videos:")
        for i, video in enumerate(results, 1):
            trimmed_title = trim_title(video['title'])
            print(f"{i}. [{video['relevance']:.0f}%] {trimmed_title} - {video['length']}")
        
        save_csv = input("\nDo you want to save results to CSV? (y/n): ").lower()
        if save_csv == 'y':
            filename = input("Enter filename (default: youtube_video_lengths.csv): ") or "youtube_video_lengths.csv"
            save_to_csv(results, filename)
    else:
        print("No results found or there was an error with the scraping.")

if __name__ == "__main__":
    main()