output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "server_target_group_arn" {
  description = "Server target group ARN"
  value       = aws_lb_target_group.server.arn
}

output "client_target_group_arn" {
  description = "Client target group ARN"
  value       = aws_lb_target_group.client.arn
}
