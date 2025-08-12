#!/bin/bash

# Job Seeker Terraform Deployment Script
# This script automatically reads environment variables from .env file and deploys the infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="production"
AWS_REGION="ap-southeast-2"  # Default value, will be overridden by .env file
TERRAFORM_DIR="."

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to load environment variables from .env file
load_env_file() {
    local env_file="../../.env"
    
    if [[ ! -f "$env_file" ]]; then
        print_warning ".env file not found at $env_file"
        print_status "Creating .env file from env.example..."
        
        if [[ -f "../../env.example" ]]; then
            cp ../../env.example "$env_file"
            print_warning "Please edit $env_file and add your OpenAI API key, then run this script again."
            exit 1
        else
            print_error "env.example file not found. Please create a .env file manually."
        exit 1
        fi
    fi
    
    print_status "Loading environment variables from .env file..."
    
    # Read .env file and export variables
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ $line =~ ^[[:space:]]*# ]] || [[ -z $line ]]; then
            continue
        fi
        
        # Skip AWS credential variables to avoid overriding existing credentials
        if [[ $line =~ ^AWS_ACCESS_KEY_ID= ]] || [[ $line =~ ^AWS_SECRET_ACCESS_KEY= ]]; then
            print_warning "Skipping AWS credential variables to preserve existing credentials"
            continue
        fi
        
        # Export the variable
        export "$line"
    done < "$env_file"
    
    print_success "Environment variables loaded successfully"
    
    # Update AWS_REGION from .env file if it exists
    if [[ -n "$AWS_REGION" ]]; then
        print_status "Using AWS region from .env file: $AWS_REGION"
    else
        print_warning "AWS_REGION not found in .env file, using default: ap-southeast-2"
        AWS_REGION="ap-southeast-2"
    fi
}

# Function to validate required environment variables
validate_env_vars() {
    print_status "Validating environment variables..."
    
    local required_vars=("OPENAI_API_KEY" "OPENAI_CHAT_MODEL" "OPENAI_EMBEDDING_MODEL")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        print_error "Please check your .env file and ensure all required variables are set."
        exit 1
    fi
    
    # Check if API key is not dummy
    if [[ "$OPENAI_API_KEY" == "your_openai_api_key_here" ]] || [[ "$OPENAI_API_KEY" == "dummy-key-for-destroy" ]]; then
        print_warning "OpenAI API key appears to be a placeholder value."
        print_warning "Please set a valid OpenAI API key in your .env file for full functionality."
        print_warning "The server will not work properly without a valid API key."
        read -p "Do you want to continue with the placeholder key? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Deployment cancelled."
            exit 1
        fi
    fi
    
    print_success "Environment variables validation passed"
    print_status "OpenAI API Key: ${OPENAI_API_KEY:0:10}..."
    print_status "Chat Model: $OPENAI_CHAT_MODEL"
    print_status "Embedding Model: $OPENAI_EMBEDDING_MODEL"
}

# Function to update terraform.tfvars
update_terraform_vars() {
    print_status "Updating terraform.tfvars with environment variables..."
    
    cat > terraform.tfvars << EOF
environment = "$ENVIRONMENT"
aws_region = "$AWS_REGION"
key_pair_name = "job-seeker-key"
openai_api_key = "$OPENAI_API_KEY"
openai_chat_model = "$OPENAI_CHAT_MODEL"
openai_embedding_model = "$OPENAI_EMBEDDING_MODEL"
EOF
    
    print_success "terraform.tfvars updated successfully"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Set Docker path for macOS
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    
    # Check if required commands exist
    local required_commands=("terraform" "aws" "docker")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        print_error "Missing required commands: ${missing_commands[*]}"
        print_error "Please install the missing commands and try again."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured or invalid."
        print_error "Please run 'aws configure' or set up your AWS credentials."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Set Docker path for macOS
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    
    # Verify Docker is accessible
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker command not found. Please ensure Docker Desktop is running."
        exit 1
    fi
    
    # Verify ECR repositories exist
    print_status "Verifying ECR repositories exist..."
    if ! aws ecr describe-repositories --repository-names job-seeker-server --region "$AWS_REGION" >/dev/null 2>&1; then
        print_error "ECR repository job-seeker-server not found. Infrastructure deployment may have failed."
        exit 1
    fi
    
    if ! aws ecr describe-repositories --repository-names job-seeker-client --region "$AWS_REGION" >/dev/null 2>&1; then
        print_error "ECR repository job-seeker-client not found. Infrastructure deployment may have failed."
        exit 1
    fi
    
    print_success "ECR repositories verified"
    
    # Login to ECR
    print_status "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin 480181745914.dkr.ecr."$AWS_REGION".amazonaws.com
    
    # Build and push server image
    print_status "Building server image..."
    docker build -t 480181745914.dkr.ecr."$AWS_REGION".amazonaws.com/job-seeker-server:latest -f ../../server/Dockerfile ../../
    
    print_status "Pushing server image..."
    docker push 480181745914.dkr.ecr."$AWS_REGION".amazonaws.com/job-seeker-server:latest
    
    # Build and push client image
    print_status "Building client image..."
    docker build -t 480181745914.dkr.ecr."$AWS_REGION".amazonaws.com/job-seeker-client:latest -f ../../client/Dockerfile ../../
    
    print_status "Pushing client image..."
    docker push 480181745914.dkr.ecr."$AWS_REGION".amazonaws.com/job-seeker-client:latest
    
    print_success "Docker images built and pushed successfully"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    print_status "Planning deployment..."
    terraform plan -out=tfplan
    
    # Ask for confirmation
    echo
    print_warning "The following resources will be created/modified:"
    terraform show -no-color tfplan | grep -E "^[+-]" | head -20
    
    if [[ $(terraform show -no-color tfplan | grep -E "^[+-]" | wc -l) -gt 20 ]]; then
        print_warning "... and more resources"
    fi
    
    echo
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled."
        exit 1
    fi
    
    # Apply deployment
    print_status "Applying deployment..."
    terraform apply tfplan
    
    print_success "Infrastructure deployment completed successfully"
}

# Function to wait for services to be ready
wait_for_services() {
    print_status "Waiting for ECS services to be ready..."
    
    aws ecs wait services-stable \
        --cluster "production-job-seeker-cluster" \
        --services "production-job-seeker-server" "production-job-seeker-client" \
        --region "$AWS_REGION"
    
    print_success "ECS services are ready"
}

# Function to test service connectivity
test_service_connectivity() {
    print_status "Testing service connectivity..."
    
    # Get ALB URL
    local alb_url=$(terraform output -raw alb_url 2>/dev/null || echo "")
    
    if [[ -z "$alb_url" ]]; then
        print_warning "ALB URL not available yet, skipping connectivity test"
        return
    fi
    
    # Test server health endpoint
    print_status "Testing server health endpoint..."
    local health_response=$(curl -s -o /dev/null -w "%{http_code}" "http://$alb_url/health" || echo "000")
    
    if [[ "$health_response" == "200" ]]; then
        print_success "✅ Server health check passed"
    else
        print_warning "⚠️  Server health check failed (HTTP $health_response)"
    fi
    
    # Test client endpoint
    print_status "Testing client endpoint..."
    local client_response=$(curl -s -o /dev/null -w "%{http_code}" "http://$alb_url:8501" || echo "000")
    
    if [[ "$client_response" == "200" ]]; then
        print_success "✅ Client endpoint accessible"
    else
        print_warning "⚠️  Client endpoint test failed (HTTP $client_response)"
    fi
    
    # Test server-client communication
    print_status "Testing server-client communication..."
    local api_response=$(curl -s -o /dev/null -w "%{http_code}" "http://$alb_url/" || echo "000")
    
    if [[ "$api_response" == "200" ]]; then
        print_success "✅ Server API endpoint accessible"
    else
        print_warning "⚠️  Server API endpoint test failed (HTTP $api_response)"
    fi
}

# Function to display deployment information
display_deployment_info() {
    print_status "Getting deployment information..."
    
    # Get ALB URL
    local alb_url=$(terraform output -raw alb_url 2>/dev/null || echo "Not available yet")
    
    echo
    print_success "🎉 Deployment completed successfully!"
    echo
    echo "📋 Deployment Information:"
    echo "   Environment: $ENVIRONMENT"
    echo "   AWS Region: $AWS_REGION"
    echo "   OpenAI Model: $OPENAI_CHAT_MODEL"
    echo
    echo "🌐 Access URLs:"
    echo "   Client (Streamlit): $alb_url:8501"
    echo "   Server API: $alb_url"
    echo "   Health Check: $alb_url/health"
    echo
    echo "📊 Monitoring:"
    echo "   ECS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/production-job-seeker-cluster"
    echo "   CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups"
    echo
    print_warning "Note: If you used a placeholder OpenAI API key, the AI features will not work."
    print_warning "To enable AI features, update your .env file with a valid OpenAI API key and redeploy."
    
    # Test connectivity
    test_service_connectivity
}

# Main execution
main() {
    echo "🚀 Job Seeker Infrastructure Deployment"
    echo "======================================"
    echo
    
    # Change to terraform directory
    cd "$TERRAFORM_DIR"
    
    # Run deployment steps
    check_prerequisites
    load_env_file
    validate_env_vars
    update_terraform_vars
    
    # Deploy infrastructure first (including ECR repositories)
    print_status "Deploying infrastructure first..."
    deploy_infrastructure
    
    # Then build and push Docker images
    print_status "Building and pushing Docker images..."
    build_and_push_images
    
    # Wait for services to be ready
    wait_for_services
    display_deployment_info
}

# Run main function
main "$@"
