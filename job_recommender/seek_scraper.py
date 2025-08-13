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
                print(f"Response content: {response.text[:500]}...")  # Show first 500 chars
                return None

            else:
                html_content = response.content.decode(response.encoding or 'utf-8', errors='replace')
                
                # Debug: Check if we got a browser upgrade page
                if "Browser Upgrade" in html_content or "browser" in html_content.lower():
                    print("Warning: Received browser upgrade page, may need to adjust scraper settings")
                
                # Debug: Check if we got the job content
                if "job-detail-title" in html_content or "jobDescription" in html_content:
                    print("Success: Found job content indicators")
                else:
                    print("Warning: No job content indicators found")
                
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
            
            # First, try to find the job description content specifically
            job_description = None
            
            # Look for job description in specific areas
            job_selectors = [
                '[data-automation="jobDescription"]',
                '.job-description',
                '.job-content',
                '.job-details',
                '.job-info',
            ]
            
            for selector in job_selectors:
                job_description = soup.select_one(selector)
                if job_description:
                    break
            
            # If we found job description, extract only that content
            if job_description:
                # Create a new soup with just the job description
                new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
                new_soup.body.append(job_description)
                soup = new_soup
            else:
                # If no specific job description found, try to find main content
                main_content = soup.select_one('[role="main"]') or soup.select_one('main')
                if main_content:
                    # Remove irrelevant sections from main content
                    irrelevant_sections = [
                        '[data-automation="dynamic-lmis"]',
                        '[data-automation="report-job-ad-toggle"]',
                        '[data-automation="report-job-ad-form"]',
                        '[data-automation="company-profile"]',
                        'h2:contains("Report this job advert")',
                        'h2:contains("Unlock job insights")',
                        'h2:contains("What can I earn")',
                        'h3:contains("Company profile")',
                        'h4:contains("Perks and benefits")',
                        'a[href*="/oauth/login"]',
                        'a[href*="/oauth/register"]',
                        'a:contains("Sign In")',
                        'a:contains("Register")',
                        'span:contains("Be careful")',
                        'span:contains("Don\'t provide your bank")',
                        'a:contains("Learn how to protect yourself")',
                        '.lmis-root',
                        # Additional irrelevant sections
                        'span:contains("Salary match")',
                        'span:contains("Number of applicants")',
                        'span:contains("Skills match")',
                        'span:contains("Add expected salary")',
                        'span:contains("Posted")',
                        'a:contains("Apply")',
                        'div:contains("Don\'t provide your bank")',
                    ]
                    
                    for selector in irrelevant_sections:
                        for element in main_content.select(selector):
                            element.decompose()
                    
                    # Create a new soup with just the cleaned main content
                    new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
                    new_soup.body.append(main_content)
                    soup = new_soup
            
            # Remove UI elements that are not part of job description
            ui_elements = [
                'button',
                'form',
                'select',
                'option',
                'label',
                'img',
            ]
            
            for element_name in ui_elements:
                for element in soup.find_all(element_name):
                    element.decompose()
            
            # Remove elements with specific data-automation attributes that are irrelevant
            irrelevant_automation = [
                'report-job-ad-toggle',
                'report-job-ad-form',
                'report-job-ad-reason',
                'report-job-ad-submit',
                'report-job-ad-cancel',
                'dynamic-lmis',
                'company-profile',
                'company-profile-review',
                'company-profile-review-link',
                'company-profile-profile-link',
                'job-header-company-review-link',
                'job-details-header-more-jobs',
            ]
            
            for automation in irrelevant_automation:
                for element in soup.find_all(attrs={'data-automation': automation}):
                    element.decompose()
            
            # Remove empty elements
            for element in soup.find_all():
                if element.name in ['div', 'span', 'p'] and not element.get_text(strip=True):
                    element.decompose()
            
            # Remove excessive whitespace and normalize text
            for element in soup.find_all(string=True):
                if element.parent.name not in ['script', 'style']:
                    # Normalize whitespace
                    normalized_text = ' '.join(element.strip().split())
                    if normalized_text:
                        element.replace_with(normalized_text)
            
            # Get the cleaned HTML
            cleaned_html = str(soup)
            
            # Additional text cleaning
            cleaned_html = self._clean_text_content(cleaned_html)
            
            # Remove all class attributes from remaining elements
            cleaned_html = re.sub(r'\s+class="[^"]*"', '', cleaned_html)
            
            # Remove all style attributes
            cleaned_html = re.sub(r'\s+style="[^"]*"', '', cleaned_html)
            
            # Remove all data-* attributes except data-automation="job-detail-title"
            cleaned_html = re.sub(r'\s+data-(?!automation="job-detail-title")[^=]*="[^"]*"', '', cleaned_html)
            
            # Remove all aria-* attributes
            cleaned_html = re.sub(r'\s+aria-[^=]*="[^"]*"', '', cleaned_html)
            
            # Remove all role attributes except role="main"
            cleaned_html = re.sub(r'\s+role="(?!main)[^"]*"', '', cleaned_html)
            
            # Remove all id attributes
            cleaned_html = re.sub(r'\s+id="[^"]*"', '', cleaned_html)
            
            # Remove all href attributes that are not job-related
            cleaned_html = re.sub(r'\s+href="(?!.*job)[^"]*"', '', cleaned_html)
            
            # Remove all target attributes
            cleaned_html = re.sub(r'\s+target="[^"]*"', '', cleaned_html)
            
            # Remove all rel attributes
            cleaned_html = re.sub(r'\s+rel="[^"]*"', '', cleaned_html)
            
            # Remove all tabindex attributes
            cleaned_html = re.sub(r'\s+tabindex="[^"]*"', '', cleaned_html)
            
            # Remove all placeholder attributes
            cleaned_html = re.sub(r'\s+placeholder="[^"]*"', '', cleaned_html)
            
            # Remove all disabled attributes
            cleaned_html = re.sub(r'\s+disabled="[^"]*"', '', cleaned_html)
            
            # Remove all selected attributes
            cleaned_html = re.sub(r'\s+selected="[^"]*"', '', cleaned_html)
            
            # Remove all value attributes
            cleaned_html = re.sub(r'\s+value="[^"]*"', '', cleaned_html)
            
            # Remove all type attributes
            cleaned_html = re.sub(r'\s+type="[^"]*"', '', cleaned_html)
            
            # Remove all span elements that are likely just styling
            cleaned_html = re.sub(r'<span[^>]*>\s*</span>', '', cleaned_html)
            
            # Remove all div elements that are likely just styling containers
            cleaned_html = re.sub(r'<div[^>]*>\s*</div>', '', cleaned_html)
            
            # Clean up excessive whitespace again
            cleaned_html = re.sub(r'\s+', ' ', cleaned_html)
            cleaned_html = re.sub(r'>\s+<', '><', cleaned_html)
            cleaned_html = re.sub(r'\s+>', '>', cleaned_html)
            cleaned_html = re.sub(r'>\s+', '>', cleaned_html)
            
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
    job_url = "https://www.seek.com.au/job/85848899?type=standard&ref=search-standalone&origin=cardTitle"
    # Get detailed content from a job
    job_html = scraper.get_job_content(job_url)

    print(job_html)

    # Save results
    scraper.save_job_content(job_html, 'job_html.json')


if __name__ == "__main__":
    main()
