resource "aws_security_group" "cloudrag_ecs" {
  name        = "cloudrag-ecs-sg"
  description = "Security group for CloudRAG ECS Fargate tasks"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow HTTP from within the VPC"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["172.31.0.0/16"]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cloudrag-ecs-sg"
  }
}

resource "aws_security_group" "cloudrag_rds" {
  name        = "cloudrag-rds-sg"
  description = "Allow PostgreSQL access only from CloudRAG ECS tasks"
  vpc_id      = var.vpc_id

  # PostgreSQL ingress rules are managed separately below.

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cloudrag-rds-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "cloudrag_rds_ecs" {
  security_group_id            = aws_security_group.cloudrag_rds.id
  referenced_security_group_id = aws_security_group.cloudrag_ecs.id

  description = "PostgreSQL from CloudRAG ECS tasks"
  ip_protocol = "tcp"
  from_port   = 5432
  to_port     = 5432
}

resource "aws_vpc_security_group_ingress_rule" "cloudrag_rds_admin" {
  security_group_id            = aws_security_group.cloudrag_rds.id
  referenced_security_group_id = aws_security_group.cloudrag_db_admin.id

  description = "PostgreSQL access from CloudRAG administration host"
  ip_protocol = "tcp"
  from_port   = 5432
  to_port     = 5432
}
