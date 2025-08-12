variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "ALB security group ID"
  type        = string
}

variable "ecs_security_group_id" {
  description = "ECS security group ID"
  type        = string
}

# Server configuration
variable "server_repository_url" {
  description = "Server container repository URL"
  type        = string
}

# Client configuration
variable "client_repository_url" {
  description = "Client container repository URL"
  type        = string
}

# Environment variables
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

# ALB DNS name
variable "alb_dns_name" {
  description = "ALB DNS name"
  type        = string
}

# Target group ARNs (will be provided by ALB module)
variable "server_target_group_arn" {
  description = "Server target group ARN"
  type        = string
  default     = ""
}

variable "client_target_group_arn" {
  description = "Client target group ARN"
  type        = string
  default     = ""
}
