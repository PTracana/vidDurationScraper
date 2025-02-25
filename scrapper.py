import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from urllib.parse import quote_plus

def scrape_youtube_video_lengths(search_query, max_results=10):
    """
    Scrapes YouTube video lengths for videos containing a specific search query.
    Limited to 10 videos maximum to avoid IP blocking.
    
    Args:
        search_query (str): The search term to look for in YouTube videos
        max_results (int): Maximum number of results to return (defaults to 10, capped at 10)
        
    Returns:
        list: A list of dictionaries containing video title, length, and URL
    """
    # Enforce the 10 video limit regardless of input
    max_results = min(max_results, 10)
    
    # Format the search query for URL
    formatted_query = quote_plus(search_query)
    
    # Construct the YouTube search URL
    search_url = f"https://www.youtube.com/results?search_query={formatted_query}"
    
    # Send request with headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    
    print(f"Fetching search results for '{search_query}'...")
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve search results. Status code: {response.status_code}")
        return []
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize results list
    results = []
    
    # Direct regex approach for video IDs
    video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', response.text)
    unique_ids = list(dict.fromkeys(video_ids))  # Remove duplicates
    
    # Limit to max_results
    unique_ids = unique_ids[:max_results]
    
    print(f"Found {len(unique_ids)} unique videos. Processing details...")
    
    for i, video_id in enumerate(unique_ids):
        print(f"Processing video {i+1}/{len(unique_ids)}...")
        
        # Get the video page
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            video_response = requests.get(video_url, headers=headers)
            
            if video_response.status_code == 200:
                video_soup = BeautifulSoup(video_response.text, 'html.parser')
                
                # Extract title
                title_tag = video_soup.find("meta", property="og:title")
                title = title_tag["content"] if title_tag else "Unknown Title"
                
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
                
                results.append({
                    "title": title,
                    "length": duration,
                    "url": video_url
                })
                
                # Throttle requests to avoid being blocked - increased delay for safety
                time.sleep(2)
            else:
                print(f"  Couldn't access video page (status code: {video_response.status_code})")
        
        except Exception as e:
            print(f"  Error processing video {video_id}: {str(e)}")
    
    return results

def save_to_csv(results, filename="youtube_video_lengths.csv"):
    """
    Saves the scraped results to a CSV file
    
    Args:
        results (list): List of dictionaries containing video information
        filename (str): Name of the CSV file to save results to
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'length', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"Results saved to {filename}")

def main():
    search_query = input("Enter the search term to find in YouTube videos: ")
    
    print("Beginning YouTube search (limited to 10 videos maximum)...")
    results = scrape_youtube_video_lengths(search_query)
    
    if results:
        print(f"\nFound {len(results)} videos:")
        for i, video in enumerate(results, 1):
            print(f"{i}. {video['title']} - {video['length']}")
        
        save_csv = input("\nDo you want to save results to CSV? (y/n): ").lower()
        if save_csv == 'y':
            filename = input("Enter filename (default: youtube_video_lengths.csv): ") or "youtube_video_lengths.csv"
            save_to_csv(results, filename)
    else:
        print("No results found or there was an error with the scraping.")

if __name__ == "__main__":
    main()