# Job Seeker - AI-Powered Job Recommendation System

An intelligent job recommendation system that uses AI to analyze user skills and experience, then provides personalized job URLs from Seek.com.au.

## 🚀 Features

- **AI-Powered Recommendations**: Uses OpenAI's GPT models to analyze user descriptions and recommend relevant job titles
- **Smart URL Generation**: Automatically generates and scrapes job URLs from Seek.com.au based on recommended job titles
- **Clickable Job Links**: Users can directly click on job URLs to view and apply for positions
- **Caching System**: Implements local database caching to avoid repeated scraping
- **Modern Web Interface**: Clean Streamlit-based user interface
- **RESTful API**: FastAPI backend for scalable job recommendation services

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Internet connection for job scraping

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd JobSeeker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_CHAT_MODEL=gpt-4o-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   ```

## 🚀 Usage

### Starting the Server

1. **Start the FastAPI server**
   ```bash
   python server/main.py
   ```
   
   The server will run on `http://localhost:8000`

2. **Verify server is running**
   ```bash
   curl http://localhost:8000/health
   ```

### Running the Client

1. **Start the Streamlit client**
   ```bash
   streamlit run client/app.py
   ```
   
   The client will open in your browser at `http://localhost:8501`

2. **Use the application**
   - Enter your skills, experience, and career goals in the text area
   - Choose the number of job recommendations (1-20)
   - Click "Get Recommendations" to receive personalized job URLs
   - Click on any job URL to open it in your browser

## 🔧 API Endpoints

### Health Check
```
GET /health
```
Returns server health status.

### Job Recommendations
```
POST /recommend
```

**Request Body:**
```json
{
  "description": "Your skills and experience description",
  "top_n": 10
}
```

**Response:**
```json
{
  "success": true,
  "job_urls": [
    "https://www.seek.com.au/job/123456",
    "https://www.seek.com.au/job/789012"
  ],
  "message": "Successfully found 10 job recommendations"
}
```

## 🏗️ Architecture

### Components

1. **JobRecommender** (`job_recommender/job_recommender.py`)
   - Core AI logic for job title recommendations
   - URL generation and scraping functionality
   - Local database caching system

2. **FastAPI Server** (`server/main.py`)
   - RESTful API endpoints
   - Request/response handling
   - Integration with JobRecommender

3. **Streamlit Client** (`client/app.py`)
   - User-friendly web interface
   - Real-time job URL display
   - Export functionality

### Data Flow

1. User enters description in Streamlit client
2. Client sends request to FastAPI server
3. Server calls JobRecommender to get job titles
4. JobRecommender generates search URLs and scrapes job listings
5. Server returns job URLs to client
6. Client displays clickable job links

## 🧪 Testing

Run the integration test to verify everything is working:

```bash
python test_integration.py
```

## 📁 Project Structure

```
JobSeeker/
├── job_recommender/          # Core AI recommendation logic
│   ├── job_recommender.py    # Main recommendation class
│   ├── seek_scraper.py       # Web scraping functionality
│   ├── job_description_analyzer.py
│   ├── job_reranker.py
│   └── job_urls_database/    # Local caching database
├── server/                   # FastAPI backend
│   ├── main.py              # API server
│   └── requirements.txt
├── client/                   # Streamlit frontend
│   ├── app.py               # Web interface
│   └── requirements.txt
├── infrastructure/           # Terraform deployment
├── config.py                # Configuration settings
├── requirements.txt         # Main dependencies
└── README.md
```

## 🔒 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_CHAT_MODEL` | OpenAI chat model name | `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` |
| `API_BASE_URL` | Server URL for client | `http://localhost:8000` |

## 🐛 Troubleshooting

### Common Issues

1. **Server not starting**
   - Check if OpenAI API key is set correctly
   - Verify all dependencies are installed
   - Check port 8000 is not in use

2. **No job recommendations**
   - Ensure internet connection is available
   - Check if Seek.com.au is accessible
   - Verify the description is detailed enough

3. **Import errors**
   - Make sure you're in the correct directory
   - Install all requirements: `pip install -r requirements.txt`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the AI models
- Seek.com.au for job listings
- FastAPI and Streamlit communities for excellent frameworks
