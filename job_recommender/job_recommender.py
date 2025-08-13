from typing import List
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

# Use relative imports when imported as module
try:
    from .seek_scraper import SeekJobScraper
    from .utils import load_prompt, save_json, read_json
    from .job_description_analyzer import JobDescriptionAnalyzer
    from .job_reranker import JobReranker
except ImportError:
    # Fallback to absolute imports if relative imports fail
    from seek_scraper import SeekJobScraper
    from utils import load_prompt, save_json, read_json
    from job_description_analyzer import JobDescriptionAnalyzer
    from job_reranker import JobReranker


class JobTitleRecord(BaseModel):
    """Model for job title recommendations"""
    job_titles: List[str] = Field(
        description="A list of exactly 2 job titles that are most relevant to the person's skills and career description",
        min_items=2,
        max_items=2
    )
    location: str = Field(description="The desired work location mentioned in the person's description. If no location is specified, set to 'none'")
    reasoning: str = Field(
        description="Brief explanation of why these job titles were selected based on the person's skills and experience"
    )

class JobRecommender(object):
    """A class to recommend job titles based on skills and career description"""
    
    def __init__(self, api_key: str = None, openai_chat_model: str = None, openai_embedding_model: str = None):
        """
        Initialize the JobRecommender
        
        Args:
            api_key (str): OpenAI API key. If not provided, will try to get from environment variables
        """
        self.api_key = api_key
        self.openai_chat_model = openai_chat_model
        self.openai_embedding_model = openai_embedding_model

        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please provide it as parameter or set OPENAI_API_KEY environment variable.")
        
        self.llm = ChatOpenAI(
            api_key=self.api_key, 
            model_name=self.openai_chat_model,
            temperature=0.1,
            max_tokens=10000
        )
        self.parser = PydanticOutputParser(pydantic_object=JobTitleRecord)
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["description"],
            template=load_prompt("job_recommender"),
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        self.scraper = SeekJobScraper()
        self.analyzer = JobDescriptionAnalyzer(api_key=self.api_key, 
            openai_chat_model=self.openai_chat_model)
        self.reranker = JobReranker(api_key=self.api_key, 
            openai_embedding_model=self.openai_embedding_model)
        
        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize the job URLs database directory and files"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_dir = os.path.join(current_dir, "job_urls_database")
        
        # Create database directory if it doesn't exist
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        # Initialize search_url_table.json if it doesn't exist
        self.search_url_table_path = os.path.join(self.db_dir, "search_url_table.json")
        if not os.path.exists(self.search_url_table_path):
            save_json(self.search_url_table_path, {})

        # Initialize job_details_table.json if it doesn't exist
        self.job_detail_table_path = os.path.join(self.db_dir, "job_detail_table.json")
        if not os.path.exists(self.job_detail_table_path):
            save_json(self.job_detail_table_path, {})

    def search_url_database(self, search_url: str) -> List[str]:
        """
        Search for job URLs in the local database
        
        Args:
            search_url (str): The search URL to look up
            
        Returns:
            List[str]: List of job URLs if found, empty list otherwise
        """
        try:
            search_url_table = read_json(self.search_url_table_path)
            return search_url_table.get(search_url, [])
        except Exception as e:
            print(f"Error reading from database: {e}")
            return []

    def save_job_urls_to_database(self, search_url: str, data):
        """
        Save job URLs to the local database
        
        Args:
            search_url (str): The search URL as key
            data: data to save
        """
        try:
            search_url_table = read_json(self.search_url_table_path)
            search_url_table[search_url] = data
            save_json(self.search_url_table_path, search_url_table)
        except Exception as e:
            print(f"Error saving to database: {e}")

    
    def save_job_detail_to_database(self, job_url: str, data):
        """
        Save job detail data to the local database

        Args:
            job_url (str): The job URL as the key
            data: The job detail data to save
        """
        try:
            job_url_table = read_json(self.job_detail_table_path)
            job_url_table[job_url] = data
            save_json(self.job_detail_table_path, job_url_table)
        except Exception as e:
            print(f"Error saving to database: {e}")
    
    def recommend_titles(self, description: str) -> JobTitleRecord:
        """
        Generate job title recommendations based on a person's description
        
        Args:
            description (str): A description of the person's skills, experience, and career goals
                             This should include information from their resume and personal description
        
        Returns:
            JobTitleRecord: Object containing 3 recommended job titles and reasoning
        
        Raises:
            ValueError: If description is empty or invalid
            Exception: If there's an error in the API call or parsing
        """
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        
        try:
            # Create the prompt with the description
            prompt = self.prompt_template.format(description=description.strip())
            
            # Generate response from LLM using ChatOpenAI format
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse the response using Pydantic
            result = self.parser.parse(response.content)
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating job recommendations: {str(e)}")


    def get_job_urls_by_recommds(self, job_recommends: JobTitleRecord) -> List[str]:
        """
        Get job URLs by job titles
        
        Args:
            job_recommends (JobTitleRecord): Job recommendations object
            
        Returns:
            List[str]: List of all job URLs found for the recommended job titles
        """
        location = job_recommends.location
        if str(location).lower() == 'none':
            location = None
        else:
            location = str(location)

        all_job_urls = []
        for job_title in job_recommends.job_titles:
            # Clean job title for URL
            job_title = '-'.join(job_title.lower().split())
            search_url = f"https://www.seek.com.au/{job_title}-jobs"
            
            # Clean location for URL if provided
            if location and location.strip():
                # Handle multiple locations (e.g., "Sydney or Melbourne")
                if ' or ' in location.lower():
                    # For multiple locations, just use the first one
                    first_location = location.split(' or ')[0].strip()
                    location_clean = '-'.join(first_location.lower().split())
                else:
                    location_clean = '-'.join(location.lower().split())
                
                # Only add location if it's not empty after cleaning
                if location_clean:
                    search_url = f"{search_url}/in-{location_clean}"
            
            job_urls = self.get_job_urls_by_recommd(search_url)
            all_job_urls.extend(job_urls)
            
        return all_job_urls

    def get_job_details_by_urls(self, job_urls: List[str]) -> List[str]:
        """
        Retrieve job details for a list of job URLs. If details are missing from the database, scrape and store them.

        Args:
            job_urls (List[str]): List of job URLs.

        Returns:
            Dict[str, dict]: Dictionary mapping job URLs to their job detail dictionaries.
        """
        all_job_details = {}
        for job_url in job_urls:
            job_details = self.get_job_detail(job_url)
            all_job_details[job_url] = job_details
        return all_job_details

    def get_job_detail(self, job_url: str) -> str:
        """
        Get job detail by job URL. If job detail is not in the database, scrape and save to database.
        """
        job_detail = self.search_job_detail_database(job_url)
        if job_detail:
            return job_detail
        else:
            job_content = self.scraper.get_job_content(job_url)
            job_detail = self.analyzer.parse_job_html_to_json(job_content)
            self.save_job_detail_to_database(job_url, job_detail)
            return job_detail

    def search_job_detail_database(self, job_url):
        """
        Search for job details in the local database
        
        Args:
            job_url (str): The job URL to look up
            
        Returns:
            dict: Dict of job details
        """
        try:
            job_detail_table = read_json(self.job_detail_table_path)
            return job_detail_table.get(job_url, {})
        except Exception as e:
            print(f"Error reading from database: {e}")
            return {}


            
    def get_job_urls_by_recommd(self, search_url: str) -> List[str]:
        """
        Get job URLs by search URL with caching functionality
        
        Args:
            search_url (str): The search URL to get job URLs for
            
        Returns:
            List[str]: List of job URLs
        """
        # First, try to get from database
        job_urls = self.search_url_database(search_url)
        
        if job_urls:
            print(f"Found {len(job_urls)} job URLs in database for: {search_url}")
            return job_urls
        
        # If not in database, scrape and save
        print(f"Scraping job URLs for: {search_url}")
        job_urls = self.scraper.get_job_urls(search_url, max_pages=2)
        
        # Save to database for future use
        self.save_job_urls_to_database(search_url, job_urls)
        
        return job_urls


    def recommend_jobs_urls(self, description: str, top_n: int = 10) -> List[str]:
        """
        Recommend jobs urls based on a person's description

        Args:
            description (str): A description of the person's skills, experience, and career goals
            top_n (int): Number of top job urls to return

        Returns:
            List[str]: A list of job URLs recommended for the user, sorted by relevance.
        """
        recommendations = self.recommend_titles(description)

        job_urls = self.get_job_urls_by_recommds(recommendations)
        
        # Limit the number of URLs returned based on top_n parameter
        return job_urls[:top_n]


def main():
    """Example usage of JobRecommender"""
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config
    # Initialize the JobRecommender
    # You can either provide the API key directly or set it in your .env file
    recommender = JobRecommender(api_key=config.OPENAI_API_KEY, 
        openai_chat_model=config.OPENAI_CHAT_MODEL, 
        openai_embedding_model=config.OPENAI_EMBEDDING_MODEL)
    
    # Example description of a person's skills and career goals
    description = """
    I am a software engineer with 5 years of experience in Python, JavaScript, and React. 
    I have worked on full-stack web applications and have experience with cloud platforms like AWS. 
    I'm passionate about machine learning and have completed several projects using TensorFlow and scikit-learn. 
    I'm looking for opportunities that combine my software engineering skills with AI/ML applications. 
    I have a strong background in data analysis and enjoy working on projects that have real-world impact.
    """
    
    try:
        # Get job recommendations
        print("Generating job recommendations...")
        jobs = recommender.recommend_jobs_urls(description)
        print(jobs) 

        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    main()



