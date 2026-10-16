# Dedicated private subnets for the CloudRAG RDS database.
resource "aws_subnet" "cloudrag_database" {
  count = length(var.private_database_subnet_cidrs)

  vpc_id                  = var.vpc_id
  cidr_block              = var.private_database_subnet_cidrs[count.index]
  availability_zone       = ["ap-south-1a", "ap-south-1b", "ap-south-1c"][count.index]
  map_public_ip_on_launch = false

  tags = {
    Name = "cloudrag-db-private-${["a", "b", "c"][count.index]}"
    Tier = "private-database"
  }
}

# Keep the database subnets separate from the public-subnet route table.
resource "aws_route_table" "cloudrag_database" {
  vpc_id = var.vpc_id

  tags = {
    Name = "cloudrag-db-private-rt"
    Tier = "private-database"
  }
}

resource "aws_route_table_association" "cloudrag_database" {
  count = length(aws_subnet.cloudrag_database)

  subnet_id      = aws_subnet.cloudrag_database[count.index].id
  route_table_id = aws_route_table.cloudrag_database.id
}

# RDS requires a DB subnet group spanning at least two Availability Zones.
resource "aws_db_subnet_group" "cloudrag" {
  name        = "cloudrag-db-subnets"
  description = "Private subnets for CloudRAG PostgreSQL"
  subnet_ids  = aws_subnet.cloudrag_database[*].id

  tags = {
    Name = "cloudrag-db-subnets"
  }
}

# Security group for database administration.
resource "aws_security_group" "cloudrag_db_admin" {
  name        = "cloudrag-db-admin-sg"
  description = "Temporary administration access to CloudRAG PostgreSQL"
  vpc_id      = var.vpc_id

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "cloudrag-db-admin-sg"
    Project = "CloudRAG"
    Purpose = "DatabaseAdministration"
  }
}

# Security group for private Systems Manager interface endpoints.
resource "aws_security_group" "cloudrag_ssm_endpoints" {
  name        = "cloudrag-ssm-endpoints-sg"
  description = "HTTPS access to private Systems Manager endpoints"
  vpc_id      = var.vpc_id

  # HTTPS from the database administration host.
  ingress {
    description     = "HTTPS from database administration host"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.cloudrag_db_admin.id]
  }

  # HTTPS from the Ollama EC2 instance for Systems Manager.
  ingress {
    description     = "HTTPS from CloudRAG Ollama EC2 for Systems Manager"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = ["sg-0af6014fbc375d61f"]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "cloudrag-ssm-endpoints-sg"
    Project = "CloudRAG"
  }
}

# Private Systems Manager VPC endpoints.
resource "aws_vpc_endpoint" "cloudrag_ssm" {
  for_each = toset([
    "ssm",
    "ssmmessages",
    "ec2messages"
  ])

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.cloudrag_database[*].id
  security_group_ids  = [aws_security_group.cloudrag_ssm_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name    = "cloudrag-${each.value}-endpoint"
    Project = "CloudRAG"
  }
}