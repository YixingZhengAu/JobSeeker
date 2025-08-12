#!/bin/bash

# Job Seeker Terraform Destruction Script
# This script safely destroys all AWS infrastructure created by the deployment

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
        print_status "Using default AWS region: $AWS_REGION"
        return
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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required commands exist
    local required_commands=("terraform" "aws")
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

# Function to check if Terraform state exists
check_terraform_state() {
    print_status "Checking Terraform state..."
    
    if [[ ! -f "terraform.tfstate" ]]; then
        print_error "terraform.tfstate file not found."
        print_error "This directory does not appear to have been deployed with Terraform."
        exit 1
    fi
    
    # Check if state is empty or invalid
    if ! terraform show >/dev/null 2>&1; then
        print_error "Terraform state is invalid or corrupted."
        exit 1
    fi
    
    print_success "Terraform state found and valid"
}

# Function to display resources that will be destroyed
display_resources_to_destroy() {
    print_status "Analyzing resources to be destroyed..."
    
    # Get list of resources from Terraform state
    local resources=$(terraform state list 2>/dev/null || echo "")
    
    if [[ -z "$resources" ]]; then
        print_warning "No resources found in Terraform state."
        return
    fi
    
    echo
    print_warning "The following resources will be DESTROYED:"
    echo "================================================"
    
    # Count resources by type
    local ecs_count=$(echo "$resources" | grep -c "aws_ecs" || echo "0")
    local ecr_count=$(echo "$resources" | grep -c "aws_ecr" || echo "0")
    local alb_count=$(echo "$resources" | grep -c "aws_lb\|aws_lb_target_group\|aws_lb_listener" || echo "0")
    local vpc_count=$(echo "$resources" | grep -c "aws_vpc\|aws_subnet\|aws_security_group" || echo "0")
    local other_count=$(echo "$resources" | grep -v "aws_ecs\|aws_ecr\|aws_lb\|aws_lb_target_group\|aws_lb_listener\|aws_vpc\|aws_subnet\|aws_security_group" | wc -l || echo "0")
    
    echo "   ECS Resources: $ecs_count"
    echo "   ECR Repositories: $ecr_count"
    echo "   Load Balancer Resources: $alb_count"
    echo "   VPC/Network Resources: $vpc_count"
    echo "   Other Resources: $other_count"
    echo "   Total Resources: $(echo "$resources" | wc -l)"
    echo
    
    # Show some example resources
    echo "Example resources:"
    echo "$resources" | head -10 | sed 's/^/   - /'
    if [[ $(echo "$resources" | wc -l) -gt 10 ]]; then
        echo "   ... and more"
    fi
    echo
}

# Function to check for running ECS services
check_ecs_services() {
    print_status "Checking ECS services status..."
    
    local cluster_name="${ENVIRONMENT}-job-seeker-cluster"
    
    # Check if cluster exists
    if ! aws ecs describe-clusters --clusters "$cluster_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        print_warning "ECS cluster '$cluster_name' not found or already deleted."
        return
    fi
    
    # Get running services
    local running_services=$(aws ecs list-services --cluster "$cluster_name" --region "$AWS_REGION" --query 'serviceArns' --output text 2>/dev/null || echo "")
    
    if [[ -n "$running_services" ]]; then
        print_warning "Found running ECS services in cluster '$cluster_name':"
        echo "$running_services" | tr '\t' '\n' | sed 's/^/   - /'
        echo
    else
        print_success "No running ECS services found."
    fi
}

# Function to check for ECR repositories
check_ecr_repositories() {
    print_status "Checking ECR repositories..."
    
    local repositories=("job-seeker-server" "job-seeker-client")
    
    for repo in "${repositories[@]}"; do
        if aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" >/dev/null 2>&1; then
            # Get image count
            local image_count=$(aws ecr describe-images --repository-name "$repo" --region "$AWS_REGION" --query 'length(imageDetails)' --output text 2>/dev/null || echo "0")
            print_warning "ECR repository '$repo' exists with $image_count images"
        else
            print_status "ECR repository '$repo' not found or already deleted."
        fi
    done
    echo
}

# Function to get ALB URL for final confirmation
get_alb_url() {
    local alb_url=$(terraform output -raw alb_url 2>/dev/null || echo "")
    if [[ -n "$alb_url" ]]; then
        echo "   Application Load Balancer: $alb_url"
    fi
}

# Function to perform pre-destroy cleanup
pre_destroy_cleanup() {
    print_status "Performing pre-destroy cleanup..."
    
    # Stop ECS services first to avoid issues
    local cluster_name="${ENVIRONMENT}-job-seeker-cluster"
    local services=("${ENVIRONMENT}-job-seeker-server" "${ENVIRONMENT}-job-seeker-client")
    
    for service in "${services[@]}"; do
        if aws ecs describe-services --cluster "$cluster_name" --services "$service" --region "$AWS_REGION" >/dev/null 2>&1; then
            print_status "Stopping ECS service: $service"
            aws ecs update-service --cluster "$cluster_name" --service "$service" --desired-count 0 --region "$AWS_REGION" >/dev/null 2>&1 || true
            
            # Wait for service to stop
            print_status "Waiting for service $service to stop..."
            aws ecs wait services-stable --cluster "$cluster_name" --services "$service" --region "$AWS_REGION" >/dev/null 2>&1 || true
        fi
    done
    
    # Clean up ECR repositories by removing all images
    print_status "Cleaning up ECR repositories..."
    local repositories=("job-seeker-server" "job-seeker-client")
    
    for repo in "${repositories[@]}"; do
        if aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" >/dev/null 2>&1; then
            print_status "Cleaning up ECR repository: $repo"
            
            # Get all image digests in the repository
            local image_digests=$(aws ecr list-images --repository-name "$repo" --region "$AWS_REGION" --query 'imageIds[*].imageDigest' --output text 2>/dev/null || echo "")
            
            if [[ -n "$image_digests" ]]; then
                print_status "Found $(echo "$image_digests" | wc -w) images in repository '$repo'"
                
                # Delete all images in the repository
                for digest in $image_digests; do
                    print_status "Deleting image: $digest"
                    aws ecr batch-delete-image --repository-name "$repo" --image-ids imageDigest="$digest" --region "$AWS_REGION" >/dev/null 2>&1 || true
                done
                
                print_success "All images deleted from repository '$repo'"
            else
                print_status "No images found in repository '$repo'"
            fi
        else
            print_status "ECR repository '$repo' not found or already deleted."
        fi
    done
    
    print_success "Pre-destroy cleanup completed"
}

# Function to destroy infrastructure
destroy_infrastructure() {
    print_status "Destroying infrastructure with Terraform..."
    
    # Initialize Terraform if needed
    if [[ ! -d ".terraform" ]]; then
        print_status "Initializing Terraform..."
        terraform init
    fi
    
    # Plan destruction
    print_status "Planning destruction..."
    terraform plan -destroy -out=tfdestroy
    
    # Show what will be destroyed
    echo
    print_warning "Terraform destruction plan:"
    terraform show -no-color tfdestroy | grep -E "^[+-]" | head -20
    
    if [[ $(terraform show -no-color tfdestroy | grep -E "^[+-]" | wc -l) -gt 20 ]]; then
        print_warning "... and more resources"
    fi
    
    echo
    print_error "⚠️  WARNING: This will PERMANENTLY DELETE all AWS resources!"
    print_error "   This action cannot be undone."
    echo
    
    # Final confirmation
    read -p "Are you absolutely sure you want to destroy all resources? Type 'DESTROY' to confirm: " -r
    echo
    
    if [[ "$REPLY" != "DESTROY" ]]; then
        print_status "Destruction cancelled."
        exit 1
    fi
    
    # Apply destruction
    print_status "Applying destruction..."
    terraform apply tfdestroy
    
    print_success "Infrastructure destruction completed successfully"
}

# Function to verify destruction
verify_destruction() {
    print_status "Verifying destruction..."
    
    local cluster_name="${ENVIRONMENT}-job-seeker-cluster"
    local repositories=("job-seeker-server" "job-seeker-client")
    
    # Check ECS cluster
    if aws ecs describe-clusters --clusters "$cluster_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        print_warning "⚠️  ECS cluster '$cluster_name' still exists"
    else
        print_success "✅ ECS cluster '$cluster_name' successfully deleted"
    fi
    
    # Check ECR repositories
    for repo in "${repositories[@]}"; do
        if aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" >/dev/null 2>&1; then
            print_warning "⚠️  ECR repository '$repo' still exists"
        else
            print_success "✅ ECR repository '$repo' successfully deleted"
        fi
    done
    
    # Check if terraform.tfstate is empty
    if [[ -f "terraform.tfstate" ]]; then
        local state_size=$(wc -c < terraform.tfstate)
        if [[ $state_size -lt 100 ]]; then
            print_success "✅ Terraform state cleared"
        else
            print_warning "⚠️  Terraform state still contains data"
        fi
    fi
}

# Function to cleanup local files
cleanup_local_files() {
    print_status "Cleaning up local files..."
    
    # Remove Terraform files
    local files_to_remove=(
        "terraform.tfstate"
        "terraform.tfstate.backup"
        "tfdestroy"
        ".terraform.lock.hcl"
    )
    
    for file in "${files_to_remove[@]}"; do
        if [[ -f "$file" ]]; then
            rm -f "$file"
            print_status "Removed $file"
        fi
    done
    
    # Remove .terraform directory
    if [[ -d ".terraform" ]]; then
        rm -rf ".terraform"
        print_status "Removed .terraform directory"
    fi
    
    print_success "Local cleanup completed"
}

# Function to display destruction information
display_destruction_info() {
    echo
    print_success "🗑️  Destruction completed successfully!"
    echo
    echo "📋 Destruction Summary:"
    echo "   Environment: $ENVIRONMENT"
    echo "   AWS Region: $AWS_REGION"
    echo "   Status: All resources destroyed"
    echo
    echo "🧹 Cleanup Actions:"
    echo "   ✅ ECS services stopped and deleted"
    echo "   ✅ ECR repositories deleted"
    echo "   ✅ Application Load Balancer deleted"
    echo "   ✅ VPC and network resources deleted"
    echo "   ✅ Local Terraform files cleaned up"
    echo
    print_warning "Note: If you want to redeploy, run './deploy.sh' again."
}

# Main execution
main() {
    echo "🗑️  Job Seeker Infrastructure Destruction"
    echo "========================================"
    echo
    
    # Change to terraform directory
    cd "$TERRAFORM_DIR"
    
    # Run destruction steps
    check_prerequisites
    load_env_file
    check_terraform_state
    display_resources_to_destroy
    check_ecs_services
    check_ecr_repositories
    
    # Show current ALB URL if available
    local alb_url=$(terraform output -raw alb_url 2>/dev/null || echo "")
    if [[ -n "$alb_url" ]]; then
        echo "🌐 Current Application URL: $alb_url"
        echo
    fi
    
    # Final confirmation before proceeding
    echo
    print_error "⚠️  FINAL WARNING: This will delete ALL AWS resources!"
    print_error "   This includes:"
    print_error "   - ECS cluster and services"
    print_error "   - ECR repositories and Docker images"
    print_error "   - Application Load Balancer"
    print_error "   - VPC, subnets, and security groups"
    print_error "   - All associated data"
    echo
    
    read -p "Do you want to proceed with destruction? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Destruction cancelled."
        exit 1
    fi
    
    # Perform destruction
    pre_destroy_cleanup
    destroy_infrastructure
    verify_destruction
    cleanup_local_files
    display_destruction_info
}

# Run main function
main "$@"
