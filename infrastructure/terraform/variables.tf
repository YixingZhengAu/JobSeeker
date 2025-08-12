variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use"
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b"]
}

# Environment Variables
variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "openai_chat_model" {
  description = "OpenAI Chat Model"
  type        = string
  default     = "gpt-4o-mini"
}

variable "openai_embedding_model" {
  description = "OpenAI Embedding Model"
  type        = string
  default     = "text-embedding-3-small"
}

variable "key_pair_name" {
  description = "EC2 Key Pair name"
  type        = string
  default     = "job-seeker-key"
}
