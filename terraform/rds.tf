resource "aws_db_instance" "cloudrag" {
  identifier = var.rds_identifier

  engine         = "postgres"
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.rds_database_name
  username = var.rds_username
  password = random_password.cloudrag_db.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.cloudrag.name
  vpc_security_group_ids = [aws_security_group.cloudrag_rds.id]
  publicly_accessible    = false

  multi_az                = false
  backup_retention_period = var.rds_backup_retention_period
  deletion_protection     = false
  skip_final_snapshot     = true
  apply_immediately       = true

  auto_minor_version_upgrade = true

  tags = {
    Name = "cloudrag-postgres"
    Tier = "private-database"
  }
}
