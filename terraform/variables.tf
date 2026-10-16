variable "aws_region" {
  description = "AWS region for CloudRAG infrastructure"
  type        = string
  default     = "ap-south-1"
}

variable "aws_profile" {
  description = "AWS CLI profile used by Terraform"
  type        = string
  default     = "cloudrag-devops"
}

variable "ecr_repository_name" {
  description = "Amazon ECR repository name for the CloudRAG API"
  type        = string
  default     = "cloudrag-api"
}
variable "ecs_cluster_name" {
  description = "Name of the CloudRAG ECS cluster"
  type        = string
  default     = "cloudrag-cluster"
}

variable "ecs_task_family" {
  description = "ECS task definition family"
  type        = string
  default     = "cloudrag-api"
}

variable "container_image_tag" {
  description = "Immutable ECR image tag to deploy"
  type        = string
  default     = "592d40f"
}

variable "container_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 1024
}

variable "container_memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 3072
}
variable "vpc_id" {
  description = "Existing default VPC ID for CloudRAG"
  type        = string
  default     = "vpc-060ab62e31705a540"
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the CloudRAG ECS service"
  type        = list(string)

  default = [
    "subnet-01eed8323bc922687",
    "subnet-0420058bf11b4b558",
    "subnet-0c0e5764005d4d887"
  ]
}
variable "rds_identifier" {
  description = "Identifier for the CloudRAG RDS instance"
  type        = string
  default     = "cloudrag-postgres"
}

variable "rds_database_name" {
  description = "Initial CloudRAG PostgreSQL database name"
  type        = string
  default     = "cloudrag"
}

variable "rds_username" {
  description = "CloudRAG database administrator username"
  type        = string
  default     = "cloudrag_admin"
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version for RDS"
  type        = string
  default     = "17.11"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Initial RDS storage allocation in GiB"
  type        = number
  default     = 50
}

variable "rds_backup_retention_period" {
  description = "Automated backup retention in days"
  type        = number
  default     = 7
}

variable "private_database_subnet_cidrs" {
  description = "CIDR blocks for dedicated private database subnets"
  type        = list(string)

  default = [
    "172.31.64.0/20",
    "172.31.80.0/20",
    "172.31.96.0/20"
  ]
}
variable "ollama_base_url" {
  description = "Private Ollama API endpoint"
  type        = string
  default     = "http://172.31.28.164:11434"
}

variable "ollama_model" {
  description = "Ollama model used for CloudRAG responses"
  type        = string
  default     = "qwen3.5:2b"
}
