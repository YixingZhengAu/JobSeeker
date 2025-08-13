#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit client for job recommendation system.

This application provides a user-friendly web interface for users to input
their skills, experience, and career goals, then receive personalized job recommendations.
"""

import streamlit as st
import requests
import json
from typing import Dict, List, Any
import time
import os

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_ENDPOINT = f"{API_BASE_URL}/recommend"

def check_server_health() -> bool:
    """
    Check if the FastAPI server is running and healthy.
    
    Returns:
        bool: True if server is healthy, False otherwise
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_job_recommendations(description: str, top_n: int) -> Dict[str, Any]:
    """
    Send a request to the FastAPI server to get job recommendations.
    
    Args:
        description (str): User's description of skills, experience, and career goals
        top_n (int): Number of job recommendations to request
        
    Returns:
        Dict[str, Any]: Response from the server containing job URLs
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    payload = {
        "description": description,
        "top_n": top_n
    }
    
    response = requests.post(
        API_ENDPOINT,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120
    )
    
    response.raise_for_status()
    return response.json()

def get_job_detail(job_url: str) -> Dict[str, Any]:
    """
    Send a request to the FastAPI server to get job details.
    
    Args:
        job_url (str): The job URL to get details for
        
    Returns:
        Dict[str, Any]: Response from the server containing job details
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    payload = {
        "job_url": job_url
    }
    
    response = requests.post(
        f"{API_BASE_URL}/job-detail",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120
    )
    
    response.raise_for_status()
    return response.json()

def display_job_url_card(job_url: str, index: int):
    """
    Display a single job URL in a formatted card with job details functionality.
    
    Args:
        job_url (str): Job URL to display
        index (int): Index of the job in the list
    """
    with st.container():
        st.markdown("---")
        
        # Create columns for layout
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Job title display
            st.markdown(f"### {index + 1}. Job Opportunity")
            
        with col2:
            # Job URL button
            st.link_button("🔗 Open Job", job_url, type="primary", use_container_width=True)
            
        with col3:
            # View Details button - simplified approach
            if st.button("📋 View Details", key=f"details_{index}", use_container_width=True):
                # Direct API call without complex state management
                with st.spinner("🔍 Fetching job details..."):
                    try:
                        # Get job details from server
                        response = get_job_detail(job_url)
                        
                        if response.get("success"):
                            job_detail = response.get("job_detail", "")
                            
                            if job_detail:
                                # Display job details in an expandable section
                                with st.expander("📋 Job Details", expanded=True):
                                    st.markdown("### Job Information")
                                    
                                    # Try to parse and display job details in a more structured way
                                    try:
                                        # If job_detail is JSON string, try to parse it
                                        import json
                                        job_data = json.loads(job_detail)
                                        
                                        # Display structured job information
                                        if isinstance(job_data, dict):
                                            for key, value in job_data.items():
                                                if value and value != "Unknown" and value != [] and value is not None:  # Only show non-empty values
                                                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                                                    if isinstance(value, str) and len(value) > 200:
                                                        st.text_area(f"{key.replace('_', ' ').title()}", value=value, height=150, disabled=True, key=f"{key}_{index}_direct")
                                                    else:
                                                        st.write(value)
                                                    st.markdown("---")
                                        else:
                                            st.text_area("Job Details", value=job_detail, height=300, disabled=True, key=f"job_detail_text_{index}_direct")
                                    except (json.JSONDecodeError, TypeError):
                                        # If not JSON, display as plain text
                                        st.text_area("Job Details", value=job_detail, height=300, disabled=True, key=f"job_detail_text_{index}_direct")
                                    
                                    # Add a close button
                                    if st.button("❌ Close Details", key=f"close_{index}_direct"):
                                        st.rerun()
                            else:
                                st.warning("No job details available for this position.")
                        else:
                            st.error(f"Error: {response.get('message', 'Unknown error occurred')}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ **Connection Error**")
                        st.error(f"Failed to fetch job details: {str(e)}")
                        st.error("Please make sure the server is running and try again.")
                        
                    except Exception as e:
                        st.error(f"❌ **Unexpected Error**")
                        st.error(f"An error occurred while fetching job details: {str(e)}")
                
        # Add some spacing
        st.markdown("")

def main():
    """
    Main function to run the Streamlit application.
    
    This function sets up the Streamlit interface, handles user input,
    and displays job URLs.
    """
    # Initialize session state for job details
    if 'job_details_loaded' not in st.session_state:
        st.session_state.job_details_loaded = False
    
    # Page configuration
    st.set_page_config(
        page_title="Job Seeker - AI Job Recommendations",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .job-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .button-container {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">💼 Job Seeker</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Job Recommendations</p>', unsafe_allow_html=True)
    
    # Check server health
    if not check_server_health():
        st.error("⚠️ **Server Connection Error**")
        st.error("The job recommendation server is not running. Please start the server first by running:")
        st.code("python server/main.py")
        st.stop()
    
    # Sidebar for input
    with st.sidebar:
        st.header("📝 Your Profile")
        
        # User description input
        st.subheader("Tell us about yourself")
        description = st.text_area(
            "Describe your skills, experience, and career goals:",
            height=200,
            placeholder="Example: I am a software engineer with 5 years of experience in Python, JavaScript, and React. I have worked on full-stack web applications and have experience with cloud platforms like AWS. I'm passionate about machine learning and have completed several projects using TensorFlow and scikit-learn. I'm looking for opportunities that combine my software engineering skills with AI/ML applications. I have a strong background in data analysis and enjoy working on projects that have real-world impact. I'm based in Melbourne and prefer remote or hybrid work arrangements.",
            help="Be specific about your skills, experience, location preferences, and career goals for better recommendations."
        )
        
        # Number of recommendations
        st.subheader("Number of Recommendations")
        top_n = st.slider(
            "How many job recommendations would you like?",
            min_value=1,
            max_value=20,
            value=10,
            help="Choose between 1 and 20 job recommendations"
        )
        
        # Submit button
        submit_button = st.button("🚀 Get Recommendations", key="submit_recommendations", type="primary", use_container_width=True)
        
        # Example descriptions
        st.subheader("💡 Need inspiration?")
        example_descriptions = {
            "Software Engineer": "I am a software engineer with 3 years of experience in Python, JavaScript, and React. I have worked on full-stack web applications and have experience with cloud platforms like AWS. I'm passionate about clean code and agile development practices.",
            "Data Scientist": "I am a data scientist with 4 years of experience in Python, R, and SQL. I have expertise in machine learning, statistical analysis, and data visualization. I have worked with large datasets and have experience with tools like TensorFlow, scikit-learn, and Tableau.",
            "Product Manager": "I am a product manager with 6 years of experience in software product development. I have successfully launched multiple products and have experience with agile methodologies, user research, and market analysis. I'm passionate about creating user-centric solutions."
        }
        
        selected_example = st.selectbox("Choose an example:", ["None"] + list(example_descriptions.keys()))
        if selected_example != "None":
            description = example_descriptions[selected_example]
            st.session_state.description = description
    
    # Main content area
    if submit_button and description.strip():
        # Show loading spinner
        with st.spinner("🔍 Finding the best jobs for you..."):
            try:
                # Get recommendations
                response = get_job_recommendations(description.strip(), top_n)
                
                if response.get("success"):
                    job_urls = response.get("job_urls", [])
                    
                    if job_urls:
                        st.success(f"✅ Found {len(job_urls)} job recommendations for you!")
                        
                        # Store job URLs in session state for persistence
                        st.session_state.job_urls = job_urls
                        st.session_state.user_description = description
                        st.session_state.recommendations_requested = top_n
                        
                        # Display job URLs
                        for i, job_url in enumerate(job_urls):
                            display_job_url_card(job_url, i)
                        
                        # Summary
                        st.markdown("---")
                        st.markdown(f"**Total recommendations found:** {len(job_urls)}")
                        
                        # Export option
                        if st.button("📥 Export Results", key="export_results"):
                            # Create export data
                            export_data = {
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "user_description": description,
                                "recommendations_requested": top_n,
                                "job_urls": job_urls
                            }
                            
                            # Convert to JSON
                            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                            
                            # Download button
                            st.download_button(
                                label="📄 Download JSON",
                                data=json_str,
                                file_name=f"job_recommendations_{time.strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                    else:
                        st.warning("No job recommendations found. Try adjusting your description or preferences.")
                else:
                    st.error(f"Error: {response.get('message', 'Unknown error occurred')}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ **Connection Error**")
                st.error(f"Failed to connect to the server: {str(e)}")
                st.error("Please make sure the server is running.")
                
            except Exception as e:
                st.error(f"❌ **Unexpected Error**")
                st.error(f"An error occurred: {str(e)}")
    
    elif submit_button and not description.strip():
        st.warning("⚠️ Please enter a description of your skills and experience.")
    
    # Display job URLs from session state (persistent display)
    elif st.session_state.get('job_urls'):
        st.success(f"✅ Found {len(st.session_state.job_urls)} job recommendations for you!")
        
        # Display job URLs
        for i, job_url in enumerate(st.session_state.job_urls):
            display_job_url_card(job_url, i)
        
        # Summary
        st.markdown("---")
        st.markdown(f"**Total recommendations found:** {len(st.session_state.job_urls)}")
        
        # Export option
        if st.button("📥 Export Results", key="export_results_persistent"):
            # Create export data
            export_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_description": st.session_state.get('user_description', ''),
                "recommendations_requested": st.session_state.get('recommendations_requested', 0),
                "job_urls": st.session_state.job_urls
            }
            
            # Convert to JSON
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Download button
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name=f"job_recommendations_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>Built with ❤️ using Streamlit and FastAPI</p>
        <p>Powered by AI Job Recommendation System</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
