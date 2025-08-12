# Job Seeker - AI-Powered Job Recommendation System

A comprehensive job recommendation system that uses AI to match users with relevant job opportunities based on their skills, experience, and career goals.

## Features

- 🤖 **AI-Powered Recommendations**: Uses OpenAI's GPT models for intelligent job matching
- 🌐 **Web Interface**: User-friendly Streamlit frontend
- 🔧 **RESTful API**: FastAPI backend for job recommendations
- 📊 **Detailed Job Information**: Comprehensive job details including skills, responsibilities, and requirements
- 🚀 **High Availability**: Deployed on AWS with auto-scaling and load balancing
- 🔄 **Automated CI/CD**: GitHub Actions for continuous deployment
- 🏗️ **Infrastructure as Code**: Terraform for reliable and reproducible deployments

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Job Data      │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Client)      │    │   (Server)      │    │   (JSON Files)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Deployment

### Prerequisites

Before deploying, ensure you have the following installed:
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [Terraform](https://www.terraform.io/downloads.html) (v1.0+)
- [Docker](https://www.docker.com/products/docker-desktop/) Desktop
- [OpenAI API Key](https://platform.openai.com/api-keys)

### Quick Deployment (Recommended)

1. **Set up environment variables:**
```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env file and add your OpenAI API key
   nano .env
   ```

2. **Configure your .env file:**
   ```bash
   # Required: Your OpenAI API key
   OPENAI_API_KEY=your_actual_openai_api_key_here
   
   # Optional: Customize models (defaults are good for most use cases)
   OPENAI_CHAT_MODEL=gpt-4o-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   ```

3. **Run the automated deployment:**
   ```bash
   cd infrastructure/terraform
   ./deploy.sh
   ```

The deployment script will:
- ✅ Automatically read your OpenAI API key from `.env` file
- ✅ Validate all required environment variables
- ✅ Build and push Docker images to ECR
- ✅ Deploy infrastructure with Terraform
- ✅ Wait for services to be ready
- ✅ Display access URLs and monitoring links


### Post-Deployment

After successful deployment, you'll see output similar to:

```
🎉 Deployment completed successfully!

📋 Deployment Information:
   Environment: production
   AWS Region: ap-southeast-2
   OpenAI Model: gpt-4o-mini

🌐 Access URLs:
   Client (Streamlit): http://production-job-seeker-alb-xxxxx.ap-southeast-2.elb.amazonaws.com:8501
   Server API: http://production-job-seeker-alb-xxxxx.ap-southeast-2.elb.amazonaws.com
   Health Check: http://production-job-seeker-alb-xxxxx.ap-southeast-2.elb.amazonaws.com/health
```

### Environment Variables

The following environment variables can be configured in your `.env` file:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | ✅ Yes |
| `OPENAI_CHAT_MODEL` | OpenAI chat model for recommendations | `gpt-4o-mini` | No |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` | No |
| `AWS_REGION` | AWS region for deployment | `ap-southeast-2` | No |
| `ENVIRONMENT` | Environment name | `production` | No |

### Troubleshooting

**Common Issues:**

1. **"OpenAI API key appears to be a placeholder value"**
   - Solution: Update your `.env` file with a valid OpenAI API key

2. **"AWS credentials not configured"**
   - Solution: Run `aws configure` and set up your AWS credentials

3. **"Docker is not installed"**
   - Solution: Install Docker Desktop and ensure it's running

4. **"Terraform is not installed"**
   - Solution: Install Terraform from the official website

**Getting Help:**
- Check the deployment logs for detailed error messages
- Verify all prerequisites are installed and configured
- Ensure your OpenAI API key is valid and has sufficient credits
  

## System Cleanup and Destruction

⚠️ **IMPORTANT**: To prevent AWS billing charges, always destroy the infrastructure when you're done testing or using the system.

### Method 1: Using Terraform Destroy Script (Recommended)

The project includes a comprehensive destroy script that safely removes all resources:

```bash
# Navigate to the terraform directory first
cd infrastructure/terraform

# Run the destroy script
./destroy.sh
```

This script will:
- Check if infrastructure exists
- Display resources to be destroyed
- Ask for confirmation
- Destroy all AWS resources in the correct order
- Clean up ECR repositories with force delete
- Remove all associated data and configurations

**Note**: The destroy script must be run from the `infrastructure/terraform` directory, not from the project root.


### What Gets Destroyed

The destruction process removes all AWS resources including:

- **ECS Services**: `production-job-seeker-server`, `production-job-seeker-client`
- **ECS Cluster**: `production-job-seeker-cluster`
- **ECR Repositories**: `job-seeker-server`, `job-seeker-client`
- **Application Load Balancer**: `production-job-seeker-alb`
- **Target Groups**: Server and client target groups
- **VPC**: Complete VPC with all subnets
- **Security Groups**: ALB and ECS security groups
- **NAT Gateway**: With associated Elastic IP
- **Internet Gateway**: VPC internet gateway
- **Route Tables**: Public and private route tables
- **CloudWatch Log Groups**: Application logs
- **IAM Roles**: ECS task execution role

### Verification

After destruction, verify all resources are removed:

```bash
# Check ECS services
aws ecs list-services --cluster production-job-seeker-cluster --region ap-southeast-2

# Check ECR repositories
aws ecr describe-repositories --region ap-southeast-2 | grep job-seeker

# Check ALB
aws elbv2 describe-load-balancers --region ap-southeast-2 | grep job-seeker

# Check VPC
aws ec2 describe-vpcs --region ap-southeast-2 | grep job-seeker
```

### Cost Savings

Destroying the infrastructure will stop all AWS charges:

- **ECS Fargate**: ~$40-80/month (stopped)
- **ALB**: ~$20-30/month (stopped)
- **NAT Gateway**: ~$45/month (stopped)
- **Data Transfer**: ~$10-20/month (stopped)
- **Total Savings**: ~$115-175/month


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
│   └── terraform/                   # Terraform configuration
│       ├── main.tf                  # Main Terraform configuration
│       ├── variables.tf             # Variable definitions
│       ├── outputs.tf               # Output values
│       ├── terraform.tfvars         # Variable values
│       ├── deploy.sh                # Deployment script
│       ├── destroy.sh               # Destruction script
│       ├── test.sh                  # Testing script
│       └── modules/                 # Terraform modules
│           ├── vpc/                 # VPC module
│           ├── ecr/                 # ECR module
│           ├── ecs/                 # ECS module
│           └── alb/                 # ALB module
├── .github/                         # GitHub Actions
│   └── workflows/
│       └── deploy.yml               # CI/CD pipeline
├── docker-compose.yml               # Local development
├── env.example                      # Environment template
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

### Terraform Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | Environment name | `production` |
| `aws_region` | AWS region | `ap-southeast-2` |
| `openai_api_key` | OpenAI API key | Required |
| `openai_chat_model` | OpenAI chat model | `gpt-4o-mini` |
| `openai_embedding_model` | OpenAI embedding model | `text-embedding-3-small` |

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

### Monthly AWS Costs (ap-southeast-2)
- **ECS Fargate**: $40-80 (2 tasks running 24/7)
- **ALB**: $20-30
- **NAT Gateway**: $45
- **CloudWatch**: $10-20
- **Data Transfer**: $10-20
- **Total**: $125-195/month

*Costs may vary based on usage and region*

---

**Built with ❤️ using FastAPI, Streamlit, Terraform, and AWS**
