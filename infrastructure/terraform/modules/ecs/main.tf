# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-job-seeker-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name        = "${var.environment}-job-seeker-cluster"
    Environment = var.environment
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.environment}-ecs-task-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach ECS Task Execution Role Policy
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "server" {
  name              = "/ecs/${var.environment}-job-seeker-server"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.environment}-job-seeker-server-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "client" {
  name              = "/ecs/${var.environment}-job-seeker-client"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.environment}-job-seeker-client-logs"
    Environment = var.environment
  }
}

# ECS Task Definition for Server
resource "aws_ecs_task_definition" "server" {
  family                   = "${var.environment}-job-seeker-server"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name  = "server"
      image = "${var.server_repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "OPENAI_API_KEY"
          value = var.openai_api_key
        },
        {
          name  = "OPENAI_CHAT_MODEL"
          value = var.openai_chat_model
        },
        {
          name  = "OPENAI_EMBEDDING_MODEL"
          value = var.openai_embedding_model
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.server.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = {
    Name        = "${var.environment}-job-seeker-server-task"
    Environment = var.environment
  }
}

# ECS Task Definition for Client
resource "aws_ecs_task_definition" "client" {
  family                   = "${var.environment}-job-seeker-client"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name  = "client"
      image = "${var.client_repository_url}:latest"
      
      environment = [
        {
          name  = "API_BASE_URL"
          value = "http://${var.alb_dns_name}"
        }
      ]
      
      portMappings = [
        {
          containerPort = 8501
          protocol      = "tcp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.client.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
  
  tags = {
    Name        = "${var.environment}-job-seeker-client-task"
    Environment = var.environment
  }
}

# ECS Service for Server
resource "aws_ecs_service" "server" {
  name            = "${var.environment}-job-seeker-server"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.server.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = var.server_target_group_arn
    container_name   = "server"
    container_port   = 8000
  }
  
  health_check_grace_period_seconds = 60
  
  depends_on = [aws_ecs_task_definition.server]
  
  tags = {
    Name        = "${var.environment}-job-seeker-server-service"
    Environment = var.environment
  }
}

# ECS Service for Client
resource "aws_ecs_service" "client" {
  name            = "${var.environment}-job-seeker-client"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.client.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = var.client_target_group_arn
    container_name   = "client"
    container_port   = 8501
  }
  
  health_check_grace_period_seconds = 60
  
  depends_on = [aws_ecs_task_definition.client]
  
  tags = {
    Name        = "${var.environment}-job-seeker-client-service"
    Environment = var.environment
  }
}

# Data source for current region
data "aws_region" "current" {}
