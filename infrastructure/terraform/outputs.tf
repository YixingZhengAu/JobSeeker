output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = module.alb.load_balancer_dns
}

output "server_service_url" {
  description = "URL to access the server application"
  value       = "http://${module.alb.load_balancer_dns}:80"
}

output "client_service_url" {
  description = "URL to access the client application"
  value       = "http://${module.alb.load_balancer_dns}:8501"
}

output "server_health_check_url" {
  description = "URL to check server health"
  value       = "http://${module.alb.load_balancer_dns}/health"
}

output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = module.ecs.cluster_name
}

output "server_repository_url" {
  description = "ECR repository URL for server"
  value       = module.ecr.server_repository_url
}

output "client_repository_url" {
  description = "ECR repository URL for client"
  value       = module.ecr.client_repository_url
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}
