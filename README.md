# Job Seeker - AI-Powered Job Recommendation System

A comprehensive job recommendation system that uses AI to match users with relevant job opportunities based on their skills, experience, and career goals.

## Features

- 🤖 **AI-Powered Recommendations**: Uses OpenAI's GPT models for intelligent job matching
- 🌐 **Web Interface**: User-friendly Streamlit frontend
- 🔧 **RESTful API**: FastAPI backend for job recommendations
- 📊 **Detailed Job Information**: Comprehensive job details including skills, responsibilities, and requirements
- 🚀 **High Availability**: Deployed on AWS with auto-scaling and load balancing
- 🔄 **Automated CI/CD**: GitHub Actions for continuous deployment

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Job Data      │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Client)      │    │   (Server)      │    │   (JSON Files)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Local Development

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
   # Edit .env and add your OpenAI API key
   ```

4. **Run the application**
   ```bash
   # Terminal 1: Start the server
   python server/main.py
   
   # Terminal 2: Start the client
   streamlit run client/app.py
   ```

### Docker Development

1. **Build and run with Docker Compose**
```bash
   docker compose up --build
   ```

2. **Access the application**
   - Client: http://localhost:8501
   - Server API: http://localhost:8000

## AWS Deployment

This project includes a complete AWS deployment solution with high availability and auto-scaling.

### Deployment Features

- ✅ **ECS EC2**: Container orchestration with EC2 instances
- ✅ **Application Load Balancer**: Traffic distribution
- ✅ **VPC with Private/Public Subnets**: Network security
- ✅ **Auto Scaling**: CPU-based scaling (2-4 instances)
- ✅ **Health Checks**: Automatic health monitoring
- ✅ **CloudWatch Logging**: Centralized logging
- ✅ **CloudFormation**: Infrastructure as Code
- ✅ **GitHub Actions**: Automated CI/CD

### Quick Deployment

1. **Set up AWS credentials**
   ```bash
   aws configure
   ```

2. **Deploy to AWS**
   ```bash
   OPENAI_API_KEY=your_key_here ./infrastructure/scripts/deploy.sh
   ```

3. **Access your application**
   - The deployment script will output the URLs
   - Client: `http://your-alb-dns:8501`
   - Server Health: `http://your-alb-dns/health`

### Automated CI/CD

1. **Push to GitHub**
```bash
   git push origin main
   ```

2. **Automatic deployment**
   - GitHub Actions will automatically deploy to AWS
   - No manual intervention required

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Project Structure

```
JobSeeker/
├── server/                          # FastAPI server
│   ├── main.py                      # Server application
│   ├── requirements.txt             # Server dependencies
│   └── Dockerfile                   # Server container
├── client/                          # Streamlit client
│   ├── app.py                       # Client application
│   ├── requirements.txt             # Client dependencies
│   └── Dockerfile                   # Client container
├── job_recommender/                 # Core recommendation engine
│   ├── job_recommender.py           # Main recommendation logic
│   ├── job_description_analyzer.py  # Job analysis
│   ├── job_reranker.py              # Job ranking
│   ├── seek_scraper.py              # Job scraping
│   └── job_urls_database/           # Job data storage
├── infrastructure/                  # AWS infrastructure
│   ├── cloudformation/              # CloudFormation templates
│   │   ├── main.yaml                # Main stack
│   │   ├── vpc.yaml                 # VPC configuration
│   │   ├── ecs.yaml                 # ECS configuration
│   │   └── alb.yaml                 # Load balancer configuration
│   └── scripts/                     # Deployment scripts
│       └── deploy.sh                # Manual deployment script
├── .github/                         # GitHub Actions
│   └── workflows/
│       └── deploy.yml               # CI/CD pipeline
├── docker-compose.yml               # Local development
├── env.example                      # Environment template
├── DEPLOYMENT.md                    # Deployment guide
└── README.md                        # This file
```

## API Documentation

### Server Endpoints

- `GET /health` - Health check
- `POST /recommend` - Get job recommendations

### Request Format

```json
{
  "description": "I am a software engineer with 5 years of experience...",
  "top_n": 3
}
```

### Response Format

```json
{
  "success": true,
  "jobs": [
    {
      "url": "https://example.com/job",
      "title": "Senior Software Engineer",
      "company": "Tech Company",
      "mandatory skills": "Python, JavaScript, React",
      "nice to have skills": "AWS, Docker, Kubernetes",
      "soft skills": "Communication, Leadership",
      "experience industries": "Technology, Finance",
      "responsibilities": "Lead development team..."
    }
  ],
  "message": "Successfully found 3 job recommendations"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_CHAT_MODEL` | Chat model name | `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model name | `text-embedding-3-small` |
| `API_BASE_URL` | Server API URL | `http://localhost:8000` |

### AWS Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `Environment` | Environment name | `production` |
| `ServerCpu` | Server CPU units | `256` |
| `ServerMemory` | Server memory (MiB) | `512` |
| `ClientCpu` | Client CPU units | `256` |
| `ClientMemory` | Client memory (MiB) | `512` |
| `ServerDesiredCount` | Server task count | `2` |
| `ClientDesiredCount` | Client task count | `2` |

## Monitoring and Logging

### CloudWatch Logs
- Server logs: `/ecs/{environment}-job-seeker-server`
- Client logs: `/ecs/{environment}-job-seeker-client`

### Health Checks
- Server: `GET /health` every 30 seconds
- Client: `GET /_stcore/health` every 30 seconds

### Auto Scaling
- CPU utilization threshold: 70%
- Scale-out cooldown: 60 seconds
- Scale-in cooldown: 60 seconds

## Cost Estimation

### Monthly AWS Costs (us-east-1)
- **EC2 Instances**: $30-50 (2 t3.medium instances)
- **ALB**: $20-30
- **NAT Gateway**: $45
- **CloudWatch**: $10-20
- **Data Transfer**: $10-20
- **Total**: $115-165/month

*Costs may vary based on usage and region*

## Development

### Running Tests
```bash
# Test local setup
python test_local_setup.py

# Test deployment
python test_deployment.py
```

### Local Testing
```bash
# Test server
curl http://localhost:8000/health

# Test client
curl http://localhost:8501/_stcore/health

# Test job recommendation
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"description": "Software engineer with Python experience", "top_n": 2}'
```

## Troubleshooting

### Common Issues

1. **Server not starting**
   - Check OpenAI API key is set
   - Verify all dependencies are installed
   - Check port 8000 is available

2. **Client not connecting to server**
   - Verify server is running on port 8000
   - Check `API_BASE_URL` environment variable
   - Ensure CORS is properly configured

3. **AWS deployment failures**
   - Check AWS credentials and permissions
   - Verify CloudFormation template syntax
   - Review CloudWatch logs for errors

### Debug Commands

```bash
# Check ECS services
aws ecs list-services --cluster production-job-seeker-cluster

# Check service logs
aws logs tail /ecs/production-job-seeker-server --follow

# Check ALB health
aws elbv2 describe-target-health --target-group-arn your-target-group-arn
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
2. Review CloudWatch logs for application errors
3. Open an issue on GitHub

---

**Built with ❤️ using FastAPI, Streamlit, and AWS**
