variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "streamline-cluster"
}

variable "db_identifier" {
  description = "RDS instance identifier"
  type        = string
  default     = "streamline-db"
}

variable "redis_cluster_id" {
  description = "ElastiCache cluster ID"
  type        = string
  default     = "streamline-redis"
}
