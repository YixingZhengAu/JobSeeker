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
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import the JobRecommender class
from job_recommender.job_recommender import JobRecommender
import config

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

# Initialize JobRecommender
try:
    recommender = JobRecommender(
        api_key=config.OPENAI_API_KEY,
        openai_chat_model=config.OPENAI_CHAT_MODEL,
        openai_embedding_model=config.OPENAI_EMBEDDING_MODEL
    )
    logger.info("JobRecommender initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize JobRecommender: {e}")
    recommender = None

class JobRecommendationRequest(BaseModel):
    """
    Request model for job recommendation.
    
    Attributes:
        description (str): User's description of skills, experience, and career goals
        top_n (int): Number of job recommendations to return (default: 10, max: 20)
    """
    description: str = Field(..., min_length=10, description="User's description of skills, experience, and career goals")
    top_n: int = Field(default=10, ge=1, le=20, description="Number of job recommendations to return")

class JobRecommendationResponse(BaseModel):
    """
    Response model for job recommendation.
    
    Attributes:
        success (bool): Whether the request was successful
        job_urls (List[str]): List of recommended job URLs
        message (str): Additional message or error information
    """
    success: bool
    job_urls: List[str]
    message: str

class JobDetailRequest(BaseModel):
    """
    Request model for job detail.
    
    Attributes:
        job_url (str): The job URL to get details for
    """
    job_url: str = Field(..., description="The job URL to get details for")

class JobDetailResponse(BaseModel):
    """
    Response model for job detail.
    
    Attributes:
        success (bool): Whether the request was successful
        job_detail (str): The job detail content
        message (str): Additional message or error information
    """
    success: bool
    job_detail: str
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
    and career goals, then returns personalized job URLs.
    
    Args:
        request (JobRecommendationRequest): The request containing user description and number of recommendations
        
    Returns:
        JobRecommendationResponse: List of recommended job URLs
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    if not recommender:
        raise HTTPException(
            status_code=500,
            detail="JobRecommender is not properly initialized"
        )
    
    try:
        logger.info(f"Received job recommendation request for top_n={request.top_n}")
        
        # Call the job recommendation function
        job_urls = recommender.recommend_jobs_urls(
            description=request.description,
            top_n=request.top_n
        )
        
        logger.info(f"Successfully returned {len(job_urls)} job URLs")
        
        return JobRecommendationResponse(
            success=True,
            job_urls=job_urls,
            message=f"Successfully found {len(job_urls)} job recommendations"
        )
        
    except Exception as e:
        logger.error(f"Error processing job recommendation request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/job-detail", response_model=JobDetailResponse)
async def get_job_detail(request: JobDetailRequest):
    """
    Get detailed information for a specific job URL.
    
    This endpoint accepts a job URL and returns detailed information about the job,
    including job description, requirements, and other relevant details.
    
    Args:
        request (JobDetailRequest): The request containing the job URL
        
    Returns:
        JobDetailResponse: Detailed job information
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    logger.info(f"=== Job Detail Endpoint Called ===")
    logger.info(f"Request received: {request.job_url}")
    
    if not recommender:
        logger.error("JobRecommender is not initialized")
        raise HTTPException(
            status_code=500,
            detail="JobRecommender is not properly initialized"
        )
    
    try:
        logger.info(f"Calling recommender.get_job_detail for URL: {request.job_url}")
        
        # Call the job detail function
        job_detail = recommender.get_job_detail(request.job_url)
        
        logger.info(f"Successfully retrieved job detail for URL: {request.job_url}")
        logger.info(f"Job detail length: {len(str(job_detail))}")
        
        # Convert job_detail to string if it's a dict
        if isinstance(job_detail, dict):
            import json
            job_detail_str = json.dumps(job_detail, ensure_ascii=False, indent=2)
        else:
            job_detail_str = str(job_detail)
        
        return JobDetailResponse(
            success=True,
            job_detail=job_detail_str,
            message="Successfully retrieved job details"
        )
        
    except Exception as e:
        logger.error(f"Error processing job detail request: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    """
    Run the FastAPI server when the script is executed directly.
    
    The server will run on localhost:8000 by default.
    """
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
