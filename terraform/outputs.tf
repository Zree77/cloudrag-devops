output "ecr_repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.cloudrag_api.name
}

output "ecr_repository_url" {
  description = "Full ECR repository URL"
  value       = aws_ecr_repository.cloudrag_api.repository_url
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}
output "ecs_cluster_name" {
  description = "CloudRAG ECS cluster name"
  value       = aws_ecs_cluster.cloudrag.name
}

output "cloudwatch_log_group" {
  description = "CloudRAG application log group"
  value       = aws_cloudwatch_log_group.cloudrag.name
}

output "ecs_task_family" {
  description = "CloudRAG ECS task definition family"
  value       = aws_ecs_task_definition.cloudrag_api.family
}
output "ecs_security_group_id" {
  description = "Security group ID for CloudRAG ECS tasks"
  value       = aws_security_group.cloudrag_ecs.id
}
