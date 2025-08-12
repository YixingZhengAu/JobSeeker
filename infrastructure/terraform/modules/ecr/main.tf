# ECR Repository for Server
resource "aws_ecr_repository" "server" {
  name                 = "job-seeker-server"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name = "${var.environment}-job-seeker-server"
  }
}

# ECR Repository for Client
resource "aws_ecr_repository" "client" {
  name                 = "job-seeker-client"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name = "${var.environment}-job-seeker-client"
  }
}

# ECR Lifecycle Policy for Server
resource "aws_ecr_lifecycle_policy" "server" {
  repository = aws_ecr_repository.server.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Lifecycle Policy for Client
resource "aws_ecr_lifecycle_policy" "client" {
  repository = aws_ecr_repository.client.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
