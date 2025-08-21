import re
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify
from urllib.parse import quote, urljoin
import time

monster_jobs_bp = Blueprint('monster_jobs', __name__)

def parse_query(query):
    """Parse the user query to extract job title, location, and distance."""
    # Default values
    job_title = ""
    location = ""
    distance = 5
    
    # Remove common words and extract meaningful parts
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
    
    # Extract job title (remaining text after removing location and distance)
    job_title = re.sub(r'\s+', ' ', query_lower.strip())
    job_title = re.sub(r'\b(jobs?|job)\b', '', job_title).strip()
    
    return job_title, location, distance

def construct_search_url(job_title, location, distance):
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

def extract_job_summary(job_url):
    """Extract job summary from the job detail page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try multiple selectors for job description
        selectors = [
            '#__next > div.main-layout-styles__Layout-sc-86e48e0f-0.ceQSkJ > div.job-openings-style__SmallJobViewWrapper-sc-b9f61078-0.iWRvKv > div',
            '[data-testid="job-description"]',
            '.job-description',
            '.job-details'
        ]
        
        for selector in selectors:
            description_element = soup.select_one(selector)
            if description_element:
                # Extract text and limit to first 200 characters
                text = description_element.get_text(strip=True)
                if text:
                    return text[:200] + "..." if len(text) > 200 else text
        
        return "Job description not available"
    except Exception as e:
        return f"Unable to fetch job description: {str(e)}"

def scrape_monster_jobs(search_url, max_jobs=10):
    """Scrape job listings from Monster.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the job cards container
        jobs_container = soup.select_one('#card-scroll-container')
        if not jobs_container:
            return []
        
        # Find all job cards
        job_cards = jobs_container.select('div.job-search-results-style__JobCardWrap-sc-30547e5b-4')
        
        jobs = []
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                # Extract job title and link
                title_element = card.select_one('a[data-testid="jobTitle"]')
                if not title_element:
                    continue
                
                title = title_element.get_text(strip=True)
                relative_link = title_element.get('href', '')
                job_link = urljoin('https://www.monster.com', relative_link) if relative_link else ''
                
                # Extract company name
                company_element = card.select_one('span[data-testid="company"]')
                company = company_element.get_text(strip=True) if company_element else 'Company not specified'
                
                # Extract location
                location_element = card.select_one('span[data-testid="jobDetailLocation"]')
                location = location_element.get_text(strip=True) if location_element else 'Location not specified'
                
                # For now, use a simple summary instead of fetching from detail page
                summary = f"Position available in {location}. Click the link for full job details and requirements."
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'summary': summary,
                    'link': job_link
                })
                
                # Add a small delay to be respectful to the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing job card {i}: {str(e)}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"Error scraping Monster jobs: {str(e)}")
        return []

@monster_jobs_bp.route('/search', methods=['POST'])
def search_jobs():
    """Search for jobs on Monster.com based on user query."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        query = data['query']
        max_jobs = data.get('max_jobs', 10)
        
        # Parse the query
        job_title, location, distance = parse_query(query)
        
        # Construct search URL
        search_url = construct_search_url(job_title, location, distance)
        
        # Scrape jobs
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

@monster_jobs_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'Monster Jobs MCP Server'})

