# vidDurationScraper

A Python toolset for scraping YouTube walkthrough video durations for game quests. The pipeline fetches quest data from a wiki page, generates YouTube search queries, retrieves video lengths, and calculates average durations per quest.

Originally built for **Genshin Impact** character story quests, but adaptable to any game with a wiki and YouTube walkthroughs.

---

## Features

- Scrapes quest tables from any wiki page (via `text.py`)
- Generates formatted YouTube search queries from quest data (via `parser.py`)
- Searches YouTube for walkthrough videos and records their durations (via `scrapper.py`)
- Calculates average video lengths per search term (via `avg.py`)
- Filters results by relevance score and minimum video duration
- Saves all results to CSV and TXT files

---

## Prerequisites

- Python 3.8+
- The packages listed in `requirements.txt`:
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `numpy`

---

## Installation

```bash
git clone https://github.com/PTracana/vidDurationScraper.git
cd vidDurationScraper
pip install -r requirements.txt
```

---

## Workflow

The four scripts are designed to be run in sequence. Each script's output feeds into the next.

```
text.py  →  parser.py  →  scrapper.py  →  avg.py
(wiki)      (format)       (YouTube)      (stats)
```

### Step 1 — Scrape quest data from a wiki (`text.py`)

Fetches tables labelled "list of story quests" from a given URL and organises the rows by character name.

```bash
python text.py <URL> [-o OUTPUT_BASE]
```

**Arguments:**

| Argument | Description |
|---|---|
| `url` | URL of the wiki page to scrape |
| `-o`, `--output` | Base name for output files (optional) |
| `-c`, `--combined` | Create only a combined CSV, skip per-character files |

**Outputs:**
- `<domain>_story_quests.txt` — quest data organised by character
- `<domain>_story_quests_all.csv` — combined CSV of all quests
- `<domain>_character_<Name>.csv` — one CSV per character (unless `--combined` is used)

**Example:**
```bash
python text.py https://genshin-impact.fandom.com/wiki/Story_Quests -o genshin_quests
```

---

### Step 2 — Format search queries (`parser.py`)

Reads the CSV produced in Step 1 (one `Character,QuestName` entry per line) and converts each entry into a YouTube search query of the form:

```
<Character> quest <QuestName> Walkthrough
```

```bash
python parser.py <input_file> <output_file> [--no-print]
```

**Arguments:**

| Argument | Description |
|---|---|
| `input_file` | Path to the input text/CSV file |
| `output_file` | Path to save the formatted search queries |
| `--no-print` | Suppress console output |

**Example:**
```bash
python parser.py genshin_quests.txt output.txt
```

**Sample output (`output.txt`):**
```
Albedo quest Princeps Cretaceus Walkthrough
Alhaitham quest Vultur Volans Walkthrough
...
```

---

### Step 3 — Scrape YouTube video lengths (`scrapper.py`)

Reads the search queries from Step 2 and searches YouTube for matching walkthrough videos. For each query it records the video title, URL, duration, and relevance score, then saves everything to a CSV file.

```bash
python scrapper.py
```

The script runs interactively and prompts for:

| Prompt | Default | Description |
|---|---|---|
| Input mode | — | Single query **or** read queries from a file |
| Search term / file path | — | The query or path to `output.txt` |
| Max results per term | `5` | Upper limit: `20` (hard cap) |
| Minimum relevance | `75%` | Percentage of query words that must appear in the title |
| Minimum duration | `3 min` | Shortest video to include |

**Output:** a timestamped CSV file (e.g. `youtube_results_20240101_120000.csv`) with columns:

| Column | Description |
|---|---|
| `search_term` | The original search query |
| `title` | Video title |
| `length` | Duration in `H:MM:SS` or `M:SS` format |
| `duration_seconds` | Duration in seconds |
| `url` | Full YouTube URL |
| `relevance` | Relevance score (%) |

> **Note:** The scraper adds a 2-second delay between requests to reduce the risk of being rate-limited by YouTube.

---

### Step 4 — Calculate average durations (`avg.py`)

Reads the CSV from Step 3 and calculates the average video length for each search term.

```bash
python avg.py <input_file> [-o OUTPUT_FILE] [--console-only] [--no-print]
```

**Arguments:**

| Argument | Description |
|---|---|
| `input_file` | Path to the CSV file from Step 3 |
| `-o`, `--output-file` | Path for the output text file (optional) |
| `--console-only` | Print to console only, do not write a file |
| `--no-print` | Suppress console output |

**Example:**
```bash
python avg.py youtube_results_20240101_120000.csv -o final.txt
```

**Sample output (`final.txt`):**
```
Search Term: Albedo quest Princeps Cretaceus Walkthrough, Average Length: 65:58
Search Term: Alhaitham quest Vultur Volans Walkthrough, Average Length: 85:11
...
```

---

## Project Structure

```
vidDurationScraper/
├── text.py          # Step 1: scrape quest tables from a wiki URL
├── parser.py        # Step 2: format quest data into YouTube search queries
├── scrapper.py      # Step 3: search YouTube and record video durations
├── avg.py           # Step 4: compute average durations per search term
├── requirements.txt # Python dependencies
├── output.txt       # Sample: formatted search queries (Step 2 output)
└── final.txt        # Sample: average durations (Step 4 output)
```

---

## Notes

- YouTube's HTML structure changes frequently. If the scraper stops returning results, the parsing logic in `scrapper.py` may need to be updated.
- Requesting a large number of results in a single session increases the risk of being temporarily blocked by YouTube. The hard cap is set to 20 results per search term.
- The minimum relevance filter (default 75%) ensures that only videos whose titles contain a high proportion of the search terms are included.
