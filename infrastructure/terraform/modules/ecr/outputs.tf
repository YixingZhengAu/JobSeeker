output "server_repository_url" {
  description = "ECR repository URL for server"
  value       = aws_ecr_repository.server.repository_url
}

output "client_repository_url" {
  description = "ECR repository URL for client"
  value       = aws_ecr_repository.client.repository_url
}

output "server_repository_name" {
  description = "ECR repository name for server"
  value       = aws_ecr_repository.server.name
}

output "client_repository_name" {
  description = "ECR repository name for client"
  value       = aws_ecr_repository.client.name
}
