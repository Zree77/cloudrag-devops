resource "random_password" "cloudrag_db" {
  length           = 32
  special          = false
  override_special = ""
}

resource "aws_secretsmanager_secret" "cloudrag_db" {
  name                    = "cloudrag/database-credentials"
  description             = "CloudRAG PostgreSQL credentials"
  recovery_window_in_days = 7

  tags = {
    Name = "cloudrag-database-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "cloudrag_db" {
  secret_id = aws_secretsmanager_secret.cloudrag_db.id

  secret_string = jsonencode({
    username = var.rds_username
    password = random_password.cloudrag_db.result
  })
}
