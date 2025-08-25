#!/usr/bin/env python3
"""
Monster Jobs Search API
A simple Flask API for searching jobs on Monster.com
"""

import os
import re
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
from typing import List, Dict, Tuple

# Create Flask app
app = Flask(__name__)
CORS(app)

def parse_query(query: str) -> Tuple[str, str, int]:
    """Parse the user query to extract job title, location, and distance."""
    job_title = ""
    location = ""
    distance = 5

    query_lower = query.lower()

    # Extract distance if specified
    distance_match = re.search(r'within\s+(\d+)\s+miles?', query_lower)
    if distance_match:
        distance = int(distance_match.group(1))
        query_lower = re.sub(r'within\s+\d+\s+miles?', '', query_lower)

    # Extract location if "near" is present
    near_match = re.search(r'near\s+([^,]+)', query_lower)
    if near_match:
        location = near_match.group(1).strip()
        query_lower = re.sub(r'near\s+[^,]+', '', query_lower)

    # Extract job title
    job_title = re.sub(r'\s+', ' ', query_lower.strip())
    job_title = re.sub(r'\b(jobs?|job)\b', '', job_title).strip()

    return job_title, location, distance

def construct_search_url(job_title: str, location: str, distance: int) -> str:
    """Construct the Monster.com search URL."""
    base_url = "https://www.monster.com/jobs/search"
    params = []

    if job_title:
        params.append(f"q={quote(job_title)}")
    if location:
        params.append(f"where={quote(location)}")
    if distance:
        params.append(f"rd={distance}")

    params.append("page=1")
    params.append("so=m.h.sh")

    return f"{base_url}?{'&'.join(params)}"

def scrape_monster_jobs(search_url: str, max_jobs: int = 10) -> List[Dict[str, str]]:
    """Scrape job listings from Monster.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        jobs_container = soup.select_one('#card-scroll-container')
        if not jobs_container:
            return []

        job_cards = jobs_container.select('div.job-search-results-style__JobCardWrap-sc-30547e5b-4')

        jobs = []
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                title_element = card.select_one('a[data-testid="jobTitle"]')
                if not title_element:
                    continue

                title = title_element.get_text(strip=True)
                relative_link = title_element.get('href', '')
                job_link = urljoin('https://www.monster.com', relative_link) if relative_link else ''

                company_element = card.select_one('span[data-testid="company"]')
                company = company_element.get_text(strip=True) if company_element else 'Company not specified'

                location_element = card.select_one('span[data-testid="jobDetailLocation"]')
                location = location_element.get_text(strip=True) if location_element else 'Location not specified'

                summary = f"Position available in {location}. Click the link for full job details and requirements."

                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'summary': summary,
                    'link': job_link
                })

                time.sleep(0.5)

            except Exception as e:
                print(f"Error processing job card {i}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Error scraping Monster jobs: {str(e)}")
        return []

@app.route('/search', methods=['POST'])
def search_jobs():
    """Search for jobs on Monster.com based on user query."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter is required'}), 400

        query = data['query']
        max_jobs = data.get('max_jobs', 10)

        job_title, location, distance = parse_query(query)
        search_url = construct_search_url(job_title, location, distance)
        jobs = scrape_monster_jobs(search_url, max_jobs)

        return jsonify({
            'query': query,
            'parsed': {
                'job_title': job_title,
                'location': location,
                'distance': distance
            },
            'search_url': search_url,
            'jobs': jobs,
            'total_found': len(jobs)
        })

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'Monster Jobs API'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
