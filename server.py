#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI server for job recommendation system.

This server provides a REST API endpoint that accepts user descriptions
and returns job recommendations using the job_recommender module.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import logging

# Import the job recommendation function
from job_recommender import recommend_jobs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Job Recommendation API",
    description="API for recommending jobs based on user descriptions",
    version="1.0.0"
)

# Add CORS middleware to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRecommendationRequest(BaseModel):
    """
    Request model for job recommendation.
    
    Attributes:
        description (str): User's description of skills, experience, and career goals
        top_n (int): Number of job recommendations to return (default: 3, max: 10)
    """
    description: str = Field(..., min_length=10, description="User's description of skills, experience, and career goals")
    top_n: int = Field(default=3, ge=1, le=10, description="Number of job recommendations to return")

class JobRecommendationResponse(BaseModel):
    """
    Response model for job recommendation.
    
    Attributes:
        success (bool): Whether the request was successful
        jobs (List[Dict]): List of recommended jobs with details
        message (str): Additional message or error information
    """
    success: bool
    jobs: List[Dict[str, Any]]
    message: str

@app.get("/")
async def root():
    """
    Root endpoint to check if the server is running.
    
    Returns:
        dict: Simple status message
    """
    return {"message": "Job Recommendation API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status information
    """
    return {"status": "healthy", "service": "job-recommendation-api"}

@app.post("/recommend", response_model=JobRecommendationResponse)
async def get_job_recommendations(request: JobRecommendationRequest):
    """
    Get job recommendations based on user description.
    
    This endpoint accepts a user's description of their skills, experience,
    and career goals, then returns personalized job recommendations.
    
    Args:
        request (JobRecommendationRequest): The request containing user description and number of recommendations
        
    Returns:
        JobRecommendationResponse: List of recommended jobs with details
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        logger.info(f"Received job recommendation request for top_n={request.top_n}")
        
        # Call the job recommendation function
        recommended_jobs = recommend_jobs(
            description=request.description,
            top_n=request.top_n
        )
        
        # Format the response
        jobs_data = []
        for job in recommended_jobs:
            job_url, similarity_score, job_detail = job
            
            job_info = {
                "url": job_url,
                "similarity_score": float(similarity_score),
                "title": job_detail.get("job_title", "N/A"),
                "company": job_detail.get("company_name", "N/A"),
                "mandatory skills": job_detail.get("skills_mandatory", "N/A"),
                "nice to have skills": job_detail.get("skills_nice_to_have", "N/A"),
                "soft skills": job_detail.get("soft_skills", "N/A"),
                "experience industries": job_detail.get("experience_industries", "N/A"),
                "responsibilities": job_detail.get("responsibilities", "N/A")
            }
            jobs_data.append(job_info)
        
        logger.info(f"Successfully returned {len(jobs_data)} job recommendations")
        
        return JobRecommendationResponse(
            success=True,
            jobs=jobs_data,
            message=f"Successfully found {len(jobs_data)} job recommendations"
        )
        
    except Exception as e:
        logger.error(f"Error processing job recommendation request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    """
    Run the FastAPI server when the script is executed directly.
    
    The server will run on localhost:8000 by default.
    """
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
