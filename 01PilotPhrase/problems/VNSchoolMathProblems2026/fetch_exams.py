import requests
from bs4 import BeautifulSoup
import time
import re
import os

BASE_URL = "https://toanmath.com/de-thi-thu-thpt-mon-toan"
OUTPUT_FILE = "exam_problems.md"

def get_exam_links(page_num):
    url = f"{BASE_URL}/page/{page_num}" if page_num > 1 else BASE_URL
    print(f"Scanning page {page_num}: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        # Posts are typically inside h3 tags with class 'entry-title' or similar
        articles = soup.find_all('h3', class_='entry-title')
        if not articles:
            # Fallback for different themes
            articles = soup.find_all('h2', class_='entry-title')
            
        for article in articles:
            a_tag = article.find('a')
            if a_tag:
                title = a_tag.get_text(strip=True)
                href = a_tag['href']
                
                # Filter: Take all "đề", not "bộ đề"
                if "đề" in title.lower() and "bộ đề" not in title.lower():
                    links.append({'title': title, 'url': href})
        return links
    except Exception as e:
        print(f"Error scanning page {page_num}: {e}")
        return []

def extract_trich_dan(url):
    print(f"  Extracting content from: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_='entry-content')
        if not content_div:
            return None
            
        # We use newline as a separator for <br> and other block elements
        # to ensure problems separated by <br> are on different lines.
        text_content = content_div.get_text(separator='\n', strip=True)
        lines = text_content.split('\n')
        
        trich_dan_content = []
        found_start = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect the start of the "Trích dẫn" section
            if "Trích dẫn" in line and ("đề" in line.lower() or "Toán" in line):
                found_start = True
                trich_dan_content.append(line)
                continue
            
            if found_start:
                # Stop if we hit something that looks like "Link tải" or "File PDF"
                if "tải" in line.lower() and "xuống" in line.lower():
                    break
                if "xem thêm" in line.lower():
                    break
                if "đáp án" in line.lower() and "chi tiết" in line.lower():
                    break
                
                # Add the line if it has substantial content
                if len(line) > 10 or line.startswith('+'):
                    trich_dan_content.append(line)
        
        if len(trich_dan_content) <= 1: # Only header or nothing
            return None
            
        # Join with double newline for Markdown readability
        return "\n\n".join(trich_dan_content)
    except Exception as e:
        print(f"  Error extracting from {url}: {e}")
        return None

def main():
    # Append to existing file instead of overwriting
    # with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    #    f.write("# Tổng hợp trích dẫn đề thi thử THPT môn Toán\n\n")

    # Target specific page for appending
    target_page = 4

    links = get_exam_links(target_page)
    if links:
        for item in links:
            content = extract_trich_dan(item['url'])
            if content:
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(f"## {item['title']}\n")
                    f.write(f"Source: {item['url']}\n\n")
                    f.write(f"{content}\n\n")
                    f.write("---\n\n")

            # Rate limiting
            time.sleep(1)

    print(f"\nFinished! Data from page {target_page} appended to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
