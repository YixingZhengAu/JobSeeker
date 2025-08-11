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

# Configuration
API_BASE_URL = "http://localhost:8000"
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
        Dict[str, Any]: Response from the server containing job recommendations
        
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
        timeout=30
    )
    
    response.raise_for_status()
    return response.json()

def display_job_card(job: Dict[str, Any], index: int):
    """
    Display a single job recommendation in a formatted card.
    
    Args:
        job (Dict[str, Any]): Job information dictionary
        index (int): Index of the job in the list
    """
    with st.container():
        st.markdown("---")
        
        # Create columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Job title and company
            title = job.get('title', 'N/A')
            company = job.get('company', 'N/A')
            
            st.markdown(f"### {index + 1}. {title}")
            if company != 'N/A':
                st.markdown(f"**Company:** {company}")
            
        with col2:
            # Job URL button
            if job.get('url'):
                st.link_button("View Job", job['url'], type="primary")
        
        # Display all available job information fields
        fields_to_display = [
            ('mandatory skills', '🔧 Mandatory Skills'),
            ('nice to have skills', '✨ Nice to Have Skills'),
            ('soft skills', '🤝 Soft Skills'),
            ('experience industries', '🏭 Experience Industries'),
            ('responsibilities', '📋 Responsibilities')
        ]
        
        for field_key, field_label in fields_to_display:
            field_value = job.get(field_key, 'N/A')
            if field_value and field_value != 'N/A':
                with st.expander(field_label):
                    st.markdown(field_value)

def main():
    """
    Main function to run the Streamlit application.
    
    This function sets up the Streamlit interface, handles user input,
    and displays job recommendations.
    """
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
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">💼 Job Seeker</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Job Recommendations</p>', unsafe_allow_html=True)
    
    # Check server health
    if not check_server_health():
        st.error("⚠️ **Server Connection Error**")
        st.error("The job recommendation server is not running. Please start the server first by running:")
        st.code("python server.py")
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
            max_value=10,
            value=3,
            help="Choose between 1 and 10 job recommendations"
        )
        
        # Submit button
        submit_button = st.button("🚀 Get Recommendations", type="primary", use_container_width=True)
        
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
                    jobs = response.get("jobs", [])
                    
                    if jobs:
                        st.success(f"✅ Found {len(jobs)} job recommendations for you!")
                        
                        # Display jobs
                        for i, job in enumerate(jobs):
                            display_job_card(job, i)
                        
                        # Summary
                        st.markdown("---")
                        st.markdown(f"**Total recommendations found:** {len(jobs)}")
                        
                        # Export option
                        if st.button("📥 Export Results"):
                            # Create export data
                            export_data = {
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "user_description": description,
                                "recommendations_requested": top_n,
                                "jobs": jobs
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
                        st.warning("No job recommendations found. Try adjusting your description or preferences..")
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
