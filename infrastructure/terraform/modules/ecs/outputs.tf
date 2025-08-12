output "cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "server_service_name" {
  description = "Server service name"
  value       = aws_ecs_service.server.name
}

output "client_service_name" {
  description = "Client service name"
  value       = aws_ecs_service.client.name
}

output "server_task_definition_arn" {
  description = "Server task definition ARN"
  value       = aws_ecs_task_definition.server.arn
}

output "client_task_definition_arn" {
  description = "Client task definition ARN"
  value       = aws_ecs_task_definition.client.arn
}
