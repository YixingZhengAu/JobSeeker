# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-job-seeker-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids
  
  enable_deletion_protection = false
  
  tags = {
    Name = "${var.environment}-job-seeker-alb"
  }
}

# Target Group for Server
resource "aws_lb_target_group" "server" {
  name        = "${var.environment}-server-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "${var.environment}-server-target-group"
  }
}

# Target Group for Client
resource "aws_lb_target_group" "client" {
  name        = "${var.environment}-client-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/_stcore/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "${var.environment}-client-target-group"
  }
}

# Listener for Server (Port 80)
resource "aws_lb_listener" "server" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.server.arn
  }
}

# Listener for Client (Port 8501)
resource "aws_lb_listener" "client" {
  load_balancer_arn = aws_lb.main.arn
  port              = "8501"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.client.arn
  }
}
