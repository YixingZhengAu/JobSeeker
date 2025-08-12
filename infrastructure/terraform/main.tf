terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Use local backend for testing, can be changed to S3 for production
  # backend "s3" {
  #   bucket = "job-seeker-terraform-state-480181745914"
  #   key    = "terraform.tfstate"
  #   region = "ap-southeast-2"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "job-seeker"
      ManagedBy   = "terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  azs         = var.availability_zones
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"
  
  environment = var.environment
}

# ALB Module
module "alb" {
  source = "./modules/alb"
  
  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  public_subnet_ids    = module.vpc.public_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  ecs_security_group_id = module.vpc.ecs_security_group_id
  
  depends_on = [module.vpc]
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"
  
  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  public_subnet_ids    = module.vpc.public_subnet_ids
  private_subnet_ids   = module.vpc.private_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  ecs_security_group_id = module.vpc.ecs_security_group_id
  
  # Repository URLs
  server_repository_url = module.ecr.server_repository_url
  client_repository_url = module.ecr.client_repository_url
  
  # Environment variables
  openai_api_key       = var.openai_api_key
  openai_chat_model    = var.openai_chat_model
  openai_embedding_model = var.openai_embedding_model
  
  # ALB DNS name
  alb_dns_name         = module.alb.load_balancer_dns
  
  # Target group ARNs from ALB module
  server_target_group_arn = module.alb.server_target_group_arn
  client_target_group_arn = module.alb.client_target_group_arn
  
  depends_on = [module.vpc, module.ecr, module.alb]
}
