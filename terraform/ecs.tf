resource "aws_ecs_cluster" "cloudrag" {
  name = var.ecs_cluster_name
}

resource "aws_cloudwatch_log_group" "cloudrag" {
  name              = "/ecs/cloudrag-api"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "cloudrag_api" {
  family                   = var.ecs_task_family
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory

  execution_role_arn = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "cloudrag-api"
      image     = "${aws_ecr_repository.cloudrag_api.repository_url}:${var.container_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "APP_NAME"
          value = "CloudRAG API"
        },
        {
          name  = "APP_VERSION"
          value = "0.2.0"
        },
        {
          name  = "POSTGRES_DB"
          value = var.rds_database_name
        },
        {
          name  = "POSTGRES_USER"
          value = var.rds_username
        },
        {
          name  = "POSTGRES_HOST"
          value = aws_db_instance.cloudrag.address
        },
        {
          name  = "POSTGRES_PORT"
          value = "5432"
        },
        {
          name  = "OLLAMA_BASE_URL"
          value = var.ollama_base_url
        },
        {
          name  = "OLLAMA_MODEL"
          value = var.ollama_model
        }
      ]

      secrets = [
        {
          name      = "POSTGRES_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.cloudrag_db.arn}:password::"
        }
      ]

      healthCheck = {
        command = [
          "CMD-SHELL",
          "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)\" || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.cloudrag.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution,
    aws_iam_role_policy.cloudrag_secrets_access
  ]
}
