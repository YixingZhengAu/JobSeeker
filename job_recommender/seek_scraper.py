#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merged Seek Job Scraper
Combines job URL scraping and job content scraping into a single class
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import random
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import cloudscraper
from fake_useragent import UserAgent
import re


class SeekJobScraper:
    def __init__(self, use_proxy: bool = False):
        """
        Initialize merged seek job scraper
        
        Args:
            use_proxy: Whether to use proxy, default False
        """
        self.use_proxy = use_proxy
        self.scraper = None
        self.session = None
        self.setup_scraper()
    
    def setup_scraper(self):
        """Setup scraper with cloudscraper and fallback"""
        try:
            # Use cloudscraper to bypass Cloudflare protection
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'darwin',
                    'desktop': True
                }
            )
            
            # Set more realistic request headers
            ua = UserAgent()
            self.scraper.headers.update({
                'User-Agent': ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
            })
            
            # Add cookies
            self.scraper.cookies.update({
                'country': 'au',
                'language': 'en',
                'timezone': 'Australia/Melbourne',
            })
            
            print("✅ Cloudscraper initialized successfully")
            
        except Exception as e:
            print(f"❌ Cloudscraper initialization failed: {e}")
            print("Falling back to regular requests")
            self.setup_fallback()
    
    def setup_fallback(self):
        """Setup fallback solution with regular requests"""
        self.session = requests.Session()
        
        # Set request headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        self.session.headers.update(headers)
        
        # Add cookies
        self.session.cookies.update({
            'country': 'au',
            'language': 'en',
        })
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Send request with retry logic"""
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                # Random delay
                time.sleep(random.uniform(2, 5))
                
                # Update User-Agent
                if self.scraper:
                    ua = UserAgent()
                    self.scraper.headers['User-Agent'] = ua.random
                    response = self.scraper.get(url, timeout=15)
                else:
                    response = self.session.get(url, timeout=15)
                
                response.raise_for_status()
                return response
                
            except Exception as e:
                print(f"Request failed (attempt {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(random.uniform(10, 20))
                else:
                    return None
        
        return None
    
    def get_job_urls(self, url: str, max_pages: int = 3) -> List[str]:
        """
        Scrape job URL list from Seek website
        
        Args:
            url: Seek website job search page URL
            max_pages: Maximum number of pages to scrape, default 3 pages
            
        Returns:
            List of job URLs
        """
        job_urls = []
        current_page = 1
        
        print(f"Starting to scrape job URLs from: {url}")
        
        while current_page <= max_pages:
            try:
                # Build pagination URL
                if current_page == 1:
                    page_url = url
                else:
                    separator = '&' if '?' in url else '?'
                    page_url = f"{url}{separator}page={current_page}"
                
                print(f"Scraping page {current_page}: {page_url}")
                
                # Send request
                response = self._make_request(page_url)
                
                if not response:
                    print(f"Page {current_page} request failed")
                    break
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job links
                page_job_urls = self._extract_job_urls(soup, url)
                
                if not page_job_urls:
                    print(f"No job links found on page {current_page}, stopping scraping")
                    break
                
                job_urls.extend(page_job_urls)
                print(f"Found {len(page_job_urls)} jobs on page {current_page}")
                
                # Check if there's a next page
                if not self._has_next_page(soup):
                    print("No more pages, stopping scraping")
                    break
                
                current_page += 1
                
                # Random delay
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.1f} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"Error scraping page {current_page}: {e}")
                break
        
        print(f"Found {len(job_urls)} job URLs in total")
        return job_urls
    
    def _extract_job_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract job URLs from page"""
        job_urls = []
        
        # Job link selectors
        selectors = [
            'a[data-automation="jobTitle"]',
            'a[href*="/job/"]',
            'a[data-testid="job-title"]',
            'h2 a',
            '.job-title a',
            '[data-automation="normalJob"] a',
            'a[data-automation="job-link"]',
            '.yvsb870 a',
            '[data-testid="job-card"] a',
            'a[href*="seek.com.au/job/"]',
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if self._is_job_url(full_url):
                            job_urls.append(full_url)
                
                if job_urls:
                    break
        
        # Remove duplicates
        return list(set(job_urls))
    
    def _is_job_url(self, url: str) -> bool:
        """Check if URL is a job detail page"""
        return '/job/' in url and 'seek.com.au' in url
    
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page"""
        next_selectors = [
            'a[aria-label="Next"]',
            'a[data-automation="page-next"]',
            '.pagination a[rel="next"]',
            'a:contains("Next")',
            'a:contains("下一页")',
            '[data-automation="page-next"]',
        ]
        
        for selector in next_selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get('href'):
                return True
        
        return False
    
    def get_job_content(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed content from a Seek job page
        
        Args:
            job_url: The URL of the job page
            
        Returns:
            if success, return the response content of raw html
            if failed, return None
        """
        print(f"Scraping job content from: {job_url}")
        
        try:
            # Send request
            response = self._make_request(job_url)
            
            if not response:
                print("Failed to get response from job page")
                return None
            
            if response.status_code != 200:
                print(f"Failed to get response from job page: {response.status_code}")
                print(f"Response content: {response.text}")
                return None

            else:
                html_content = response.content.decode(response.encoding or 'utf-8', errors='replace')
                
                # Clean the HTML content
                cleaned_html = self._clean_html_content(html_content)
                
                return cleaned_html
                
        except Exception as e:
            print(f"Error scraping job content: {e}")
            return None

    def _clean_html_content(self, html_content: str) -> str:
        """
        Clean HTML content by removing irrelevant elements while preserving job information
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned HTML content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'noscript']):
                element.decompose()
            
            # Remove common irrelevant elements
            irrelevant_selectors = [
                # Navigation and header elements
                'header', 'nav', '.header', '.navigation', '.navbar',
                # Footer elements
                'footer', '.footer', '.site-footer',
                # Sidebar and ads
                '.sidebar', '.advertisement', '.ads', '[class*="ad-"]',
                # Social media and sharing
                '.social', '.share', '.social-media',
                # Breadcrumbs
                '.breadcrumb', '.breadcrumbs',
                # Search and filter elements
                '.search', '.filter', '.filters',
                # Pagination (not needed for single job page)
                '.pagination', '.pager',
                # Related jobs section
                '.related-jobs', '.similar-jobs',
                # Cookie notices and popups
                '.cookie-notice', '.popup', '.modal',
                # Analytics and tracking
                '[data-analytics]', '[data-tracking]',
                # Common irrelevant classes
                '.hidden', '.invisible', '.sr-only',
                # Comments
                'comment',
            ]
            
            for selector in irrelevant_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Remove elements with specific attributes that are usually irrelevant
            for element in soup.find_all(attrs={
                'data-testid': lambda x: x and any(keyword in x.lower() for keyword in ['ad', 'tracking', 'analytics', 'cookie'])
            }):
                element.decompose()
            
            # Remove empty elements
            for element in soup.find_all():
                if element.name in ['div', 'span', 'p'] and not element.get_text(strip=True):
                    element.decompose()
            
            # Keep only the main job content area
            main_content_selectors = [
                '[data-automation="jobDescription"]',
                '.job-description',
                '.job-content',
                'main',
                '.main-content',
                '[role="main"]',
                '.job-details',
                '.job-info',
            ]
            
            # Try to find the main content area
            main_content = None
            for selector in main_content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If we found main content, keep only that
            if main_content:
                # Create a new soup with just the main content
                new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
                new_soup.body.append(main_content)
                soup = new_soup
            
            # Remove excessive whitespace and normalize text
            for element in soup.find_all(text=True):
                if element.parent.name not in ['script', 'style']:
                    # Normalize whitespace
                    normalized_text = ' '.join(element.strip().split())
                    if normalized_text:
                        element.replace_with(normalized_text)
            
            # Get the cleaned HTML
            cleaned_html = str(soup)
            
            # Additional text cleaning
            cleaned_html = self._clean_text_content(cleaned_html)
            
            print(f"HTML cleaned: Original size: {len(html_content)}, Cleaned size: {len(cleaned_html)}")
            
            return cleaned_html
            
        except Exception as e:
            print(f"Error cleaning HTML content: {e}")
            return html_content
    
    def _clean_text_content(self, html_content: str) -> str:
        """
        Clean text content by removing common irrelevant text patterns
        
        Args:
            html_content: HTML content to clean
            
        Returns:
            Cleaned HTML content
        """
        # Remove common irrelevant text patterns
        patterns_to_remove = [
            # Cookie notices
            r'This website uses cookies.*?\.',
            r'We use cookies.*?\.',
            r'By continuing to use this site.*?\.',
            
            # Common irrelevant text
            r'Loading\.\.\.',
            r'Please wait\.\.\.',
            r'Click here to.*?\.',
            r'Read more.*?\.',
            r'Show more.*?\.',
            r'View all.*?\.',
            
            # Social media text
            r'Share this job.*?\.',
            r'Follow us.*?\.',
            r'Like us.*?\.',
            
            # Navigation text
            r'Back to.*?\.',
            r'Return to.*?\.',
            r'Go to.*?\.',
            
            # Common irrelevant phrases
            r'Advertisement',
            r'Sponsored',
            r'Advertise with us',
            r'Partner with us',
        ]
        
        for pattern in patterns_to_remove:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove excessive whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        
        return html_content.strip()
    
    def save_job_urls(self, job_urls: List[str], filename: str = 'seek_jobs_merged.json'):
        """Save job URLs to JSON file"""
        data = {
            'total_jobs': len(job_urls),
            'job_urls': job_urls,
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Job URLs saved to: {filename}")
    
    def save_job_content(self, job_html: str, filename: str = 'seek_job_content_merged.json'):
        """Save job content to JSON file"""
        data = {
            'job_html': job_html,
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Job content saved to: {filename}")


def main():
    # Initialize scraper
    scraper = SeekJobScraper()

    # Get job URLs from search page
    job_urls = scraper.get_job_urls("https://www.seek.com.au/data-scientist-jobs/in-Melbourne-VIC-3000", max_pages=2)

    # Get detailed content from a job
    job_html = scraper.get_job_content(job_urls[0])

    # Save results
    scraper.save_job_urls(job_urls, 'job_urls.json')
    scraper.save_job_content(job_html, 'job_html.json')


if __name__ == "__main__":
    main()
