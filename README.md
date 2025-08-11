# Job Seeker - AI-Powered Job Recommendation System

A comprehensive job recommendation system that uses AI to match users with relevant job opportunities based on their skills, experience, and career goals.

## 🚀 Features

- **AI-Powered Recommendations**: Uses OpenAI's language models to analyze user profiles and job descriptions
- **Web Interface**: Beautiful Streamlit frontend for easy interaction
- **REST API**: FastAPI backend for scalable and efficient job recommendations
- **Real-time Processing**: Get instant job recommendations based on your profile
- **Export Functionality**: Download your recommendations as JSON files
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Prerequisites

Before running this application, make sure you have:

1. **Python 3.8+** installed on your system
2. **OpenAI API Key** - You'll need to set up an OpenAI account and get an API key
3. **Internet Connection** - Required for API calls and job data retrieval

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd JobSeeker
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory with your OpenAI API key:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Important**: Replace `your_openai_api_key_here` with your actual OpenAI API key.

## 🚀 How to Use

### Step 1: Start the Backend Server

First, start the FastAPI server that handles job recommendations:

```bash
python server.py
```

The server will start on `http://localhost:8000`. You should see output like:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 2: Start the Frontend Client

In a new terminal window, start the Streamlit frontend:

```bash
streamlit run client.py
```

The Streamlit app will open in your default browser at `http://localhost:8501`.

### Step 3: Get Job Recommendations

1. **Enter Your Profile**: In the sidebar, describe your skills, experience, and career goals
2. **Choose Number of Recommendations**: Use the slider to select how many jobs you want (1-10)
3. **Get Recommendations**: Click the "🚀 Get Recommendations" button
4. **Review Results**: Browse through the recommended jobs with detailed information
5. **Export (Optional)**: Download your recommendations as a JSON file

## 📁 Project Structure

```
JobSeeker/
├── client.py                 # Streamlit frontend application
├── server.py                 # FastAPI backend server
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── test.py                   # Test script for job recommender
└── job_recommender/          # Core job recommendation module
    ├── __init__.py
    ├── job_recommender.py
    ├── job_description_analyzer.py
    ├── job_reranker.py
    ├── seek_scraper.py
    ├── utils.py
    ├── prompts/              # AI prompt templates
    └── job_urls_database/    # Job data storage
```

## 🔧 Configuration

### Environment Variables

The following environment variables can be configured in your `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_CHAT_MODEL`: OpenAI chat model to use (default: gpt-4o-mini)
- `OPENAI_EMBEDDING_MODEL`: OpenAI embedding model to use (default: text-embedding-3-small)

### API Endpoints

The FastAPI server provides the following endpoints:

- `GET /`: Health check and server status
- `GET /health`: Detailed health information
- `POST /recommend`: Get job recommendations (main endpoint)

## 💡 Usage Examples

### Example User Descriptions

Here are some example descriptions you can use to test the system:

**Software Engineer:**
```
I am a software engineer with 3 years of experience in Python, JavaScript, and React. 
I have worked on full-stack web applications and have experience with cloud platforms like AWS. 
I'm passionate about clean code and agile development practices.
```

**Data Scientist:**
```
I am a data scientist with 4 years of experience in Python, R, and SQL. 
I have expertise in machine learning, statistical analysis, and data visualization. 
I have worked with large datasets and have experience with tools like TensorFlow, scikit-learn, and Tableau.
```

**Product Manager:**
```
I am a product manager with 6 years of experience in software product development. 
I have successfully launched multiple products and have experience with agile methodologies, 
user research, and market analysis. I'm passionate about creating user-centric solutions.
```

## 🔍 How It Works

1. **User Input**: Users provide their skills, experience, and career goals through the web interface
2. **AI Analysis**: The system uses OpenAI's language models to analyze the user's profile
3. **Job Matching**: The system compares the user's profile with available job descriptions
4. **Ranking**: Jobs are ranked based on similarity scores and relevance
5. **Results**: Users receive personalized job recommendations with detailed information

## 🛠️ Troubleshooting

### Common Issues

**1. Server Connection Error**
- Make sure the FastAPI server is running (`python server.py`)
- Check that the server is running on port 8000
- Verify your firewall settings

**2. OpenAI API Error**
- Ensure your OpenAI API key is correctly set in the `.env` file
- Check that you have sufficient API credits
- Verify the API key has the necessary permissions

**3. No Job Recommendations Found**
- Try being more specific in your description
- Include relevant skills, experience, and location preferences
- Check that the job database has been populated

**4. Import Errors**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're using Python 3.8 or higher

### Getting Help

If you encounter any issues:

1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Ensure both server and client are running
4. Check the logs in the terminal for detailed error information

## 📊 API Documentation

When the server is running, you can access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔒 Security Notes

- Keep your OpenAI API key secure and never commit it to version control
- In production, use proper authentication and authorization
- Consider rate limiting for API endpoints
- Use HTTPS in production environments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the language models
- Streamlit for the web framework
- FastAPI for the backend framework
- The open-source community for various dependencies

---

**Happy Job Hunting! 🎯**
