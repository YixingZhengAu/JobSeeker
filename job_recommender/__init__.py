"""
Job Recommender Package

This package provides job recommendation functionality based on user skills and experience.
"""

import config
from .job_recommender import JobRecommender

def recommend_jobs(description: str, top_n: int = 3):
    """
    Main interface for job recommendations.
    
    Args:
        description (str): A description of the person's skills, experience, and career goals
        top_n (int): Number of top jobs to return (default: 3)
        api_key (str): OpenAI API key (optional, will use environment variable if not provided)
    
    Returns:
        List[Tuple[str, float, Dict]]: Top N jobs sorted by similarity. List of tuples containing (url, similarity_score, job_detail)
    """
    recommender = JobRecommender(api_key=config.OPENAI_API_KEY, 
                                openai_chat_model=config.OPENAI_CHAT_MODEL, 
                                openai_embedding_model=config.OPENAI_EMBEDDING_MODEL)
    return recommender.recommend_jobs(description, top_n)

__all__ = ['recommend_jobs', 'JobRecommender']
