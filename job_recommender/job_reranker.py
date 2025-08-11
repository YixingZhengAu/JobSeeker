from typing import List, Dict, Tuple
import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from .utils import save_json, read_json


class JobReranker:
    """
    A class to rerank job details based on user description using OpenAI embeddings.
    
    This class takes a user's description of their skills and experience, along with
    job details from job recommendations, and ranks the jobs by similarity to the
    user's profile using OpenAI embeddings.
    
    Features:
    - Caching of embeddings in local JSON file to avoid redundant API calls
    - Cosine similarity calculation between user description and job details
    - Efficient ranking of job opportunities based on relevance
    """
    
    def __init__(self, api_key: str = None, openai_embedding_model: str = None):
        """
        Initialize the JobReranker
        
        Args:
            api_key (str): OpenAI API key. If not provided, will try to get from environment variables
        """
        self.api_key = api_key
        self.openai_embedding_model = openai_embedding_model
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please provide it as parameter or set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the job embedding database directory and files"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_dir = os.path.join(current_dir, "job_urls_database")
        
        # Create database directory if it doesn't exist
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        # Initialize job_embedding_table.json if it doesn't exist
        self.embedding_table_path = os.path.join(self.db_dir, "job_embedding_table.json")
        if not os.path.exists(self.embedding_table_path):
            save_json(self.embedding_table_path, {})
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a given text using OpenAI API
        
        Args:
            text (str): The text to get embedding for
            
        Returns:
            List[float]: The embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.openai_embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Error getting embedding: {str(e)}")
    
    def _get_cached_embedding(self, text: str, url: str = None) -> List[float]:
        """
        Get embedding for text, using cache if available
        
        Args:
            text (str): The text to get embedding for
            url (str): The URL to use as cache key (optional, for job details)
            
        Returns:
            List[float]: The embedding vector
        """
        # Use URL as key if provided, otherwise use text hash
        cache_key = url if url else str(hash(text))
        
        try:
            embedding_table = read_json(self.embedding_table_path)
            
            # Check if embedding exists in cache
            if cache_key in embedding_table:
                print(f"Found cached embedding for: {cache_key[:50]}...")
                return embedding_table[cache_key]
            
            # If not in cache, get from API and save
            print(f"Getting new embedding for: {cache_key[:50]}...")
            embedding = self._get_embedding(text)
            embedding_table[cache_key] = embedding
            save_json(self.embedding_table_path, embedding_table)
            
            return embedding
            
        except Exception as e:
            print(f"Error accessing embedding cache: {e}")
            # Fallback to direct API call
            return self._get_embedding(text)
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1 (List[float]): First vector
            vec2 (List[float]): Second vector
            
        Returns:
            float: Cosine similarity score between 0 and 1
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _extract_job_text(self, job_detail: Dict) -> str:
        """
        Extract relevant text from job detail for embedding
        
        Args:
            job_detail (Dict): Job detail dictionary
            
        Returns:
            str: Concatenated relevant text from job detail
        """
        text_parts = []
        
        for key, value in job_detail.items():
            if value is None or value == "":
                continue
                
            # Handle different data types
            if isinstance(value, list):
                if value:  # Only add non-empty lists
                    text_parts.append(f"{key.replace('_', ' ').title()}: {', '.join(str(item) for item in value)}")
            elif isinstance(value, (str, int, float)):
                text_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            else:
                # For other types, convert to string
                text_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
        
        return " | ".join(text_parts)
    
    def rerank_jobs(self, user_description: str, job_data: Dict[str, Dict]) -> List[Tuple[str, float, Dict, str]]:
        """
        Rerank job details based on similarity to user description
        
        Args:
            user_description (str): User's description of skills and experience
            job_data (Dict[str, Dict]): Dictionary with URL as key and job detail dict as value
                                  
        Returns:
            List[Tuple[str, float, Dict]]: List of tuples containing (url, similarity_score, job_detail)
                                              sorted by similarity score in descending order
        """
        if not user_description or not user_description.strip():
            raise ValueError("User description cannot be empty")
        
        if not job_data:
            return []
        
        print(f"Reranking {len(job_data)} jobs based on user description...")
        
        # Get embedding for user description (always call OpenAI API directly)
        user_embedding = self._get_embedding(user_description.strip())
        
        # Calculate similarities for all jobs
        job_similarities = []
        
        for job_url, job_detail in job_data.items():
            try:
                # Extract text from job detail
                job_text = self._extract_job_text(job_detail)
                
                if not job_text.strip():
                    print(f"Warning: No extractable text found for job: {job_url[:50]}...")
                    job_similarities.append((job_url, 0.0, job_detail))
                    continue
                
                # Get embedding for job text (use URL as cache key)
                job_embedding = self._get_cached_embedding(job_text, job_url)
                
                # Calculate similarity
                similarity = self._calculate_cosine_similarity(user_embedding, job_embedding)
                
                job_similarities.append((job_url, similarity, job_detail))
                
            except Exception as e:
                print(f"Error processing job {job_url[:50]}...: {e}")
                job_similarities.append((job_url, 0.0, job_detail))
        
        # Sort by similarity score in descending order
        job_similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Reranking completed. Top similarity score: {job_similarities[0][1]:.4f}")
        
        return job_similarities
    
    def get_top_jobs(self, user_description: str, job_data: Dict[str, Dict], top_n: int = 5) -> List[Tuple[str, float, Dict, str]]:
        """
        Get top N most similar jobs to user description
        
        Args:
            user_description (str): User's description of skills and experience
            job_data (Dict[str, Dict]): Dictionary with URL as key and job detail dict as value
            top_n (int): Number of top jobs to return
            
        Returns:
            List[Tuple[str, float, Dict]]: Top N jobs sorted by similarity. sorted by similarity score in descending order.
                                                List of tuples containing (url, similarity_score, job_detail)
        """
        reranked_jobs = self.rerank_jobs(user_description, job_data)
        return reranked_jobs[:top_n]


def main():
    """Example usage and test of JobReranker"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the JobReranker
    reranker = JobReranker(api_key=config.OPENAI_API_KEY)
    
    # Example user description
    user_description = """
    I am a software engineer with 5 years of experience in Python, JavaScript, and React. 
    I have worked on full-stack web applications and have experience with cloud platforms like AWS. 
    I'm passionate about machine learning and have completed several projects using TensorFlow and scikit-learn. 
    I'm looking for opportunities that combine my software engineering skills with AI/ML applications. 
    I have a strong background in data analysis and enjoy working on projects that have real-world impact.
    """
    
    # Example job data (new format with URL as key and job detail as value)
    example_job_data = {
        "https://www.seek.com.au/job/example1": {
            "job_title": "Senior Software Engineer - Machine Learning",
            "company_name": "TechCorp",
            "skills_mandatory": ["Python", "Machine Learning", "TensorFlow", "AWS"],
            "skills_nice_to_have": ["React", "JavaScript", "scikit-learn"],
            "responsibilities": ["Develop ML models", "Build scalable systems", "Lead technical projects"],
            "keywords": ["AI", "ML", "Python", "AWS"]
        },
        "https://www.seek.com.au/job/example2": {
            "job_title": "Frontend Developer",
            "company_name": "WebSolutions",
            "skills_mandatory": ["JavaScript", "React", "HTML", "CSS"],
            "skills_nice_to_have": ["TypeScript", "Node.js"],
            "responsibilities": ["Build user interfaces", "Optimize performance", "Collaborate with designers"],
            "keywords": ["Frontend", "React", "JavaScript"]
        },
        "https://www.seek.com.au/job/example3": {
            "job_title": "Data Scientist",
            "company_name": "DataAnalytics Inc",
            "skills_mandatory": ["Python", "Statistics", "SQL", "Machine Learning"],
            "skills_nice_to_have": ["TensorFlow", "scikit-learn", "AWS"],
            "responsibilities": ["Analyze data", "Build predictive models", "Present insights"],
            "keywords": ["Data Science", "ML", "Python", "Statistics"]
        }
    }
    
    try:
        print("=== Testing JobReranker ===")
        
        # Test reranking
        print("\n1. Testing reranking functionality...")
        reranked_jobs = reranker.rerank_jobs(user_description, example_job_data)
        
        print("\nReranked Jobs (by similarity):")
        for i, (job_url, similarity, job_detail) in enumerate(reranked_jobs, 1):
            print(f"{i}. {job_detail['job_title']} at {job_detail['company_name']}")
            print(f"   Similarity Score: {similarity:.4f}")
            print(f"   URL: {job_url}")
            print()
        
        # Test getting top jobs
        print("\n2. Testing get_top_jobs functionality...")
        top_jobs = reranker.get_top_jobs(user_description, example_job_data, top_n=2)
        
        print("\nTop 2 Jobs:")
        for i, (job_url, similarity, job_detail) in enumerate(top_jobs, 1):
            print(f"{i}. {job_detail['job_title']} at {job_detail['company_name']}")
            print(f"   Similarity Score: {similarity:.4f}")
            print(f"   URL: {job_url}")
            print()
        
        # Test caching functionality
        print("\n3. Testing caching functionality...")
        print("Running reranking again to test cache...")
        reranked_jobs_cached = reranker.rerank_jobs(user_description, example_job_data)
        print("Cache test completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")


if __name__ == "__main__":
    main()




