from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import date
import json
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os

try:
    from .utils import load_prompt
except ImportError:
    from utils import load_prompt
from dotenv import load_dotenv


class JobDescriptionRecord(BaseModel):
    """
    Purpose: Structured extraction of Analyst job descriptions from recruitment websites (such as Seek) 
    and serves as the output parsing target for LangChain.
    Parsing requirements (strict guidance for models/parsers):
    - Only fill in information that is "explicitly mentioned or can be reasonably inferred" from the job description; 
      do not fabricate information that is not present in the JD.
    - If a field does not exist or is uncertain, fill in None (scalar) or [] (list).
    - For list fields, use "concise, reusable phrases/keywords", avoid copying entire paragraphs from the original text.
    - Dates use ISO-8601 format (YYYY-MM-DD); salary amounts use numbers (without currency symbols); 
      currency uses ISO codes (such as AUD).
    - All text should remove excess whitespace and line breaks; preserve key terminology with original spelling (such as SQL, Power BI).
    - This model favors the minimal sufficient field set for two downstream tasks: "job matching + market analysis".
    """

    # 1) Basic job information
    job_title: Optional[str] = Field(
        None, description="Job title (such as 'Data Analyst', 'Senior Business Analyst'). if JD does not specify, fill in 'Unknown'"
    )
    seniority_level: Optional[Literal["Junior", "Mid", "Senior", "Lead", "Manager", "Director", "Unknown"]] = Field(
        "Unknown", description="Job seniority level; if JD does not specify, fill in 'Unknown'."
    )
    company_name: Optional[str] = Field(None, description="Company name; None if not disclosed.")
    company_description: Optional[str] = Field(None, description="Description of the company, if available. if JD does not specify, fill in 'Unknown'")
    is_remote: Optional[bool] = Field(None, description="Whether explicitly marked as remote; None if not specified.")
    employment_type: Optional[Literal["Full-time", "Part-time", "Contract", "Temporary", "Casual", "Internship", "Other"]] \
        = Field(None, description="Employment type.")
    posting_date: Optional[date] = Field(None, description="Job posting date (YYYY-MM-DD).")
    close_date: Optional[date] = Field(None, description="Job closing/expiry date (if any).")

    # 3) Skill requirements
    skills_mandatory: List[str] = Field(
        default_factory=list,
        description="Required skill keywords (such as 'SQL', 'Power BI', 'Tableau', 'Python')."
    )
    skills_nice_to_have: List[str] = Field(
        default_factory=list,
        description="Preferred skill keywords (such as 'AWS', 'Azure', 'GCP', 'Statistics', 'Machine Learning')."
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Soft skills (such as 'stakeholder communication', 'problem solving')."
    )
    domain_knowledge: List[str] = Field(
        default_factory=list,
        description="Domain/industry knowledge (such as 'banking', 'retail', 'healthcare')."
    )

    # 4) Responsibilities and deliverables
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Key points list of daily job responsibilities (phrases, such as 'build dashboards', 'define KPIs')."
    )

    # 5) Experience and education
    experience_years_min: Optional[float] = Field(None, description="Minimum years requirement (such as 2 or 3.0).")
    experience_years_max: Optional[float] = Field(None, description="Maximum years (if JD provides a range).")
    experience_industries: List[str] = Field(
        default_factory=list, description="Required or preferred previous industry experience."
    )
    education_requirements: Optional[str] = Field(
        None, description="Education background requirement summary (such as 'Bachelor in Statistics or related')."
    )

    # 6) Recruiter and signals
    risk_flags: List[str] = Field(
        default_factory=list,
        description="Potential risk signals (such as 'broad responsibilities', 'frequent hiring for same role')."
    )

    # 7) Matching/keywords
    keywords: List[str] = Field(
        default_factory=list,
        description="Key theme words extracted from JD (for retrieval/clustering)."
    )

class JobDescriptionAnalyzer(object):
    """
    JobDescriptionAnalyzer is responsible for extracting structured information from raw HTML job descriptions.
    It uses a language model (LLM) and a Pydantic schema to parse and format the extracted data.
    
    Main responsibilities:
    - Initialize the LLM and output parser for job description extraction.
    - Define and use a prompt template for instructing the LLM.
    - Provide a method to parse HTML job content and return structured data as a dictionary.
    """

    def __init__(self,api_key: str = None, openai_chat_model: str = None):
        """
        Initialize the JobDescriptionAnalyzer.
        
       Args:
            api_key (str): OpenAI API key. If not provided, will try to get from environment variables
        """

        self.api_key = api_key
        self.openai_chat_model = openai_chat_model
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please provide it as parameter or set OPENAI_API_KEY environment variable.")
        
        # Initialize the language model with specified parameters
        llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=self.openai_chat_model,
            temperature=0.1,
            max_tokens=10000)

        # Create the output parser using the JobDescriptionRecord Pydantic model
        parser = PydanticOutputParser(pydantic_object=JobDescriptionRecord)
        
        # Define the prompt template for the LLM, including format instructions
        prompt_template = PromptTemplate(
            input_variables=["html_content"],
            template=load_prompt("job_description_analyzer"),
            partial_variables={"format_instructions": parser.get_format_instructions()})
        
        # Create the processing chain: prompt -> LLM -> parser
        chain = prompt_template | llm | parser
        self.chain = chain
        self.format_instructions = parser.get_format_instructions()

    def parse_job_html_to_json(self, html_content: str) -> dict:
        """
        Parse HTML job posting content and extract structured information according to the JobDescriptionRecord schema.
        
        Args:
            html_content (str): HTML string containing job posting information.
        
        Returns:
            dict: Structured job information in JSON format matching the JobDescriptionRecord schema.
        """
        try:
            # Execute the processing chain with the provided HTML content
            result = self.chain.invoke({
                "html_content": html_content,
                "format_instructions": self.format_instructions
            })
            
            # Convert the result to a dictionary and return
            return result.dict()
            
        except Exception as e:
            print(f"Error parsing job HTML: {str(e)}")
            # Return the default dict of the Pydantic model (all default values) in case of error
            return JobDescriptionRecord().model_dump()

def main():
    """
    Test function using the job_html.json file
    """

    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config

        from seek_scraper import SeekJobScraper
        job_url = "https://www.seek.com.au/job/86406417?type=promoted&ref=search-standalone&origin=cardTitle"
        scraper = SeekJobScraper()
        analyzer = JobDescriptionAnalyzer(config.OPENAI_API_KEY, config.OPENAI_CHAT_MODEL)
        
        job_content = scraper.get_job_content(job_url)
        job_detail = analyzer.parse_job_html_to_json(job_content)
        
        # Print the result
        print(job_content)
        print("--------------------------------")
        print("Parsed Job Information:")
        print(json.dumps(job_detail, indent=2, ensure_ascii=False, default=str))
        
        return job_detail
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return None


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    main()
