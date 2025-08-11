#!/bin/bash

# Job Seeker AWS Deployment Script
# This script deploys the Job Seeker application to AWS using CloudFormation

set -e

# Configuration
STACK_NAME="job-seeker-production"
ENVIRONMENT="production"
AWS_REGION="us-east-1"
KEY_PAIR_NAME="job-seeker-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
}

# Function to check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
}

# Function to create ECR repositories
create_ecr_repositories() {
    print_status "Creating ECR repositories..."
    
    # Create server repository
    if ! aws ecr describe-repositories --repository-names job-seeker-server --region $AWS_REGION &> /dev/null; then
        aws ecr create-repository --repository-name job-seeker-server --region $AWS_REGION
        print_status "Created ECR repository: job-seeker-server"
    else
        print_warning "ECR repository job-seeker-server already exists"
    fi
    
    # Create client repository
    if ! aws ecr describe-repositories --repository-names job-seeker-client --region $AWS_REGION &> /dev/null; then
        aws ecr create-repository --repository-name job-seeker-client --region $AWS_REGION
        print_status "Created ECR repository: job-seeker-client"
    else
        print_warning "ECR repository job-seeker-client already exists"
    fi
}

# Function to create EC2 key pair
create_key_pair() {
    print_status "Creating EC2 key pair..."
    
    if ! aws ec2 describe-key-pairs --key-names $KEY_PAIR_NAME --region $AWS_REGION &> /dev/null; then
        aws ec2 create-key-pair --key-name $KEY_PAIR_NAME --region $AWS_REGION --query 'KeyMaterial' --output text > $KEY_PAIR_NAME.pem
        chmod 400 $KEY_PAIR_NAME.pem
        print_status "Created EC2 key pair: $KEY_PAIR_NAME"
        print_warning "Key pair file saved as $KEY_PAIR_NAME.pem - keep it secure!"
    else
        print_warning "EC2 key pair $KEY_PAIR_NAME already exists"
    fi
}

# Function to build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get ECR login token
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Build and push server image
    print_status "Building server image..."
    cd server
    docker build -t job-seeker-server:latest .
    docker tag job-seeker-server:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/job-seeker-server:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/job-seeker-server:latest
    cd ..
    
    # Build and push client image
    print_status "Building client image..."
    cd client
    docker build -t job-seeker-client:latest .
    docker tag job-seeker-client:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/job-seeker-client:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/job-seeker-client:latest
    cd ..
    
    print_status "Docker images built and pushed successfully"
}

# Function to deploy CloudFormation stack
deploy_cloudformation() {
    print_status "Deploying CloudFormation stack..."
    
    # Check if environment variables are set
    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "OPENAI_API_KEY environment variable is not set"
        exit 1
    fi
    
    # Deploy the stack
    aws cloudformation deploy \
        --template-file infrastructure/cloudformation/main.yaml \
        --stack-name $STACK_NAME \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            KeyPairName=$KEY_PAIR_NAME \
            OpenAIApiKey=$OPENAI_API_KEY \
            OpenAIChatModel=${OPENAI_CHAT_MODEL:-gpt-4o-mini} \
            OpenAIEmbeddingModel=${OPENAI_EMBEDDING_MODEL:-text-embedding-3-small} \
        --capabilities CAPABILITY_IAM \
        --no-fail-on-empty-changeset \
        --region $AWS_REGION
    
    print_status "CloudFormation stack deployed successfully"
}

# Function to wait for ECS services to be stable
wait_for_services() {
    print_status "Waiting for ECS services to be stable..."
    
    # Wait for server service
    aws ecs wait services-stable \
        --cluster $ENVIRONMENT-job-seeker-cluster \
        --services $ENVIRONMENT-job-seeker-server \
        --region $AWS_REGION
    
    # Wait for client service
    aws ecs wait services-stable \
        --cluster $ENVIRONMENT-job-seeker-cluster \
        --services $ENVIRONMENT-job-seeker-client \
        --region $AWS_REGION
    
    print_status "ECS services are stable"
}

# Function to get deployment URLs
get_deployment_urls() {
    print_status "Getting deployment URLs..."
    
    # Get ALB DNS name
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`ClientServiceURL`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    print_status "Deployment completed successfully!"
    print_status "Client URL: $ALB_DNS"
    print_status "Server Health Check: ${ALB_DNS%:8501}/health"
}

# Function to perform health checks
health_check() {
    print_status "Performing health checks..."
    
    # Wait a bit for services to be fully ready
    sleep 30
    
    # Get ALB DNS name
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`ClientServiceURL`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    # Health check server
    SERVER_URL="${ALB_DNS%:8501}/health"
    print_status "Checking server health at: $SERVER_URL"
    if curl -f "$SERVER_URL"; then
        print_status "Server health check passed"
    else
        print_error "Server health check failed"
        exit 1
    fi
    
    # Health check client
    print_status "Checking client health at: $ALB_DNS"
    if curl -f "$ALB_DNS"; then
        print_status "Client health check passed"
    else
        print_error "Client health check failed"
        exit 1
    fi
    
    print_status "All health checks passed!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -s, --skip-build        Skip building and pushing Docker images"
    echo "  -e, --environment       Environment name (default: production)"
    echo "  -r, --region           AWS region (default: us-east-1)"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY         OpenAI API key (required)"
    echo "  OPENAI_CHAT_MODEL      OpenAI chat model (default: gpt-4o-mini)"
    echo "  OPENAI_EMBEDDING_MODEL OpenAI embedding model (default: text-embedding-3-small)"
    echo ""
    echo "Example:"
    echo "  OPENAI_API_KEY=your_key_here $0"
}

# Main script
main() {
    # Parse command line arguments
    SKIP_BUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -s|--skip-build)
                SKIP_BUILD=true
                shift
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Update stack name based on environment
    STACK_NAME="job-seeker-$ENVIRONMENT"
    
    print_status "Starting deployment for environment: $ENVIRONMENT"
    print_status "AWS Region: $AWS_REGION"
    print_status "Stack Name: $STACK_NAME"
    
    # Pre-flight checks
    check_aws_cli
    check_docker
    check_aws_credentials
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_status "AWS Account ID: $AWS_ACCOUNT_ID"
    
    # Create ECR repositories
    create_ecr_repositories
    
    # Create EC2 key pair
    create_key_pair
    
    # Build and push images (unless skipped)
    if [ "$SKIP_BUILD" = false ]; then
        build_and_push_images
    else
        print_warning "Skipping Docker build and push"
    fi
    
    # Deploy CloudFormation stack
    deploy_cloudformation
    
    # Wait for services to be stable
    wait_for_services
    
    # Get deployment URLs
    get_deployment_urls
    
    # Perform health checks
    health_check
    
    print_status "Deployment completed successfully!"
}

# Run main function
main "$@"
