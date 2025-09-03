# VPN Infrastructure Variables
# Configuration variables for AWS VPN infrastructure

variable "aws_region" {
  description = "AWS region for VPN infrastructure"
  type        = string
  default     = "us-west-2"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "environment" {
  description = "Environment name (e.g., production, staging, development)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging", "development", "testing"], var.environment)
    error_message = "Environment must be one of: production, staging, development, testing."
  }
}

variable "instance_type" {
  description = "EC2 instance type for VPN servers"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition     = can(regex("^[a-z0-9]+\\.[a-z0-9]+$", var.instance_type))
    error_message = "Instance type must be a valid AWS instance type."
  }
}

variable "min_instances" {
  description = "Minimum number of VPN instances in Auto Scaling Group"
  type        = number
  default     = 1
  
  validation {
    condition     = var.min_instances >= 1 && var.min_instances <= 10
    error_message = "Minimum instances must be between 1 and 10."
  }
}

variable "max_instances" {
  description = "Maximum number of VPN instances in Auto Scaling Group"
  type        = number
  default     = 3
  
  validation {
    condition     = var.max_instances >= var.min_instances && var.max_instances <= 20
    error_message = "Maximum instances must be >= minimum instances and <= 20."
  }
}

variable "desired_instances" {
  description = "Desired number of VPN instances in Auto Scaling Group"
  type        = number
  default     = 2
  
  validation {
    condition     = var.desired_instances >= var.min_instances && var.desired_instances <= var.max_instances
    error_message = "Desired instances must be between min and max instances."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  validation {
    condition = alltrue([
      for cidr in var.public_subnet_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "Public subnet CIDRs must be valid CIDR blocks."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  
  validation {
    condition = alltrue([
      for cidr in var.private_subnet_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "Private subnet CIDRs must be valid CIDR blocks."
  }
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in VPC"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for VPN infrastructure"
  type        = string
  default     = ""
  
  validation {
    condition     = var.domain_name == "" || can(regex("^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\\.[a-zA-Z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid domain or empty."
  }
}

variable "certificate_arn" {
  description = "ARN of existing ACM certificate (optional)"
  type        = string
  default     = ""
  
  validation {
    condition     = var.certificate_arn == "" || can(regex("^arn:aws:acm:", var.certificate_arn))
    error_message = "Certificate ARN must be a valid ACM certificate ARN or empty."
  }
}

variable "key_name" {
  description = "Name of EC2 key pair for SSH access"
  type        = string
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring for EC2 instances"
  type        = bool
  default     = true
}

variable "enable_termination_protection" {
  description = "Enable termination protection for ALB"
  type        = bool
  default     = false
}

variable "health_check_path" {
  description = "Path for ALB health checks"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Interval for ALB health checks (seconds)"
  type        = number
  default     = 30
  
  validation {
    condition     = var.health_check_interval >= 5 && var.health_check_interval <= 300
    error_message = "Health check interval must be between 5 and 300 seconds."
  }
}

variable "health_check_timeout" {
  description = "Timeout for ALB health checks (seconds)"
  type        = number
  default     = 5
  
  validation {
    condition     = var.health_check_timeout >= 2 && var.health_check_timeout <= 60
    error_message = "Health check timeout must be between 2 and 60 seconds."
  }
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive successful health checks before considering target healthy"
  type        = number
  default     = 2
  
  validation {
    condition     = var.health_check_healthy_threshold >= 2 && var.health_check_healthy_threshold <= 10
    error_message = "Healthy threshold must be between 2 and 10."
  }
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks before considering target unhealthy"
  type        = number
  default     = 2
  
  validation {
    condition     = var.health_check_unhealthy_threshold >= 2 && var.health_check_unhealthy_threshold <= 10
    error_message = "Unhealthy threshold must be between 2 and 10."
  }
}

variable "enable_stickiness" {
  description = "Enable session stickiness for ALB"
  type        = bool
  default     = true
}

variable "stickiness_duration" {
  description = "Duration of session stickiness (seconds)"
  type        = number
  default     = 86400
  
  validation {
    condition     = var.stickiness_duration >= 1 && var.stickiness_duration <= 604800
    error_message = "Stickiness duration must be between 1 and 604800 seconds (7 days)."
  }
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling policies"
  type        = bool
  default     = true
}

variable "scale_up_threshold" {
  description = "CPU threshold for scaling up (percentage)"
  type        = number
  default     = 80
  
  validation {
    condition     = var.scale_up_threshold >= 50 && var.scale_up_threshold <= 95
    error_message = "Scale up threshold must be between 50 and 95 percent."
  }
}

variable "scale_down_threshold" {
  description = "CPU threshold for scaling down (percentage)"
  type        = number
  default     = 20
  
  validation {
    condition     = var.scale_down_threshold >= 5 && var.scale_down_threshold <= 50
    error_message = "Scale down threshold must be between 5 and 50 percent."
  }
}

variable "scale_cooldown" {
  description = "Cooldown period between scaling actions (seconds)"
  type        = number
  default     = 300
  
  validation {
    condition     = var.scale_cooldown >= 60 && var.scale_cooldown <= 3600
    error_message = "Scale cooldown must be between 60 and 3600 seconds."
  }
}

variable "enable_logging" {
  description = "Enable ALB access logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
  
  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 365
    error_message = "Log retention must be between 1 and 365 days."
  }
}

variable "enable_encryption" {
  description = "Enable encryption for EBS volumes"
  type        = bool
  default     = true
}

variable "volume_size" {
  description = "Size of EBS volume in GB"
  type        = number
  default     = 20
  
  validation {
    condition     = var.volume_size >= 8 && var.volume_size <= 1000
    error_message = "Volume size must be between 8 and 1000 GB."
  }
}

variable "volume_type" {
  description = "Type of EBS volume"
  type        = string
  default     = "gp3"
  
  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2", "st1", "sc1"], var.volume_type)
    error_message = "Volume type must be one of: gp2, gp3, io1, io2, st1, sc1."
  }
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 1 and 365 days."
  }
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
  
  validation {
    condition = alltrue([
      for key, value in var.tags : length(key) <= 128 && length(value) <= 256
    ])
    error_message = "Tag keys must be <= 128 characters and values <= 256 characters."
  }
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access VPN infrastructure"
  type        = list(string)
  default     = ["0.0.0.0/0"]
  
  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "Allowed CIDR blocks must be valid CIDR blocks."
  }
}

variable "enable_ssh_access" {
  description = "Enable SSH access to instances"
  type        = bool
  default     = false
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for cidr in var.ssh_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "SSH CIDR blocks must be valid CIDR blocks."
  }
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
  
  validation {
    condition     = var.alarm_email == "" || can(regex("^[^@]+@[^@]+\\.[^@]+$", var.alarm_email))
    error_message = "Alarm email must be a valid email address or empty."
  }
}

variable "enable_sns_notifications" {
  description = "Enable SNS notifications for alarms"
  type        = bool
  default     = false
}

variable "sns_topic_arn" {
  description = "ARN of SNS topic for notifications"
  type        = string
  default     = ""
  
  validation {
    condition     = var.sns_topic_arn == "" || can(regex("^arn:aws:sns:", var.sns_topic_arn))
    error_message = "SNS topic ARN must be a valid SNS topic ARN or empty."
  }
}

variable "enable_waf" {
  description = "Enable WAF for ALB protection"
  type        = bool
  default     = false
}

variable "waf_rules" {
  description = "List of WAF rule names to apply"
  type        = list(string)
  default     = []
}

variable "enable_shield" {
  description = "Enable AWS Shield Advanced (requires subscription)"
  type        = bool
  default     = false
}

variable "enable_guardduty" {
  description = "Enable Amazon GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "config_recorder_role_arn" {
  description = "ARN of IAM role for Config recorder"
  type        = string
  default     = ""
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for API logging"
  type        = bool
  default     = true
}

variable "cloudtrail_log_group_name" {
  description = "Name of CloudWatch log group for CloudTrail"
  type        = string
  default     = ""
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services"
  type        = bool
  default     = false
}

variable "vpc_endpoint_services" {
  description = "List of AWS services for VPC endpoints"
  type        = list(string)
  default     = ["s3", "ec2", "ec2messages", "ssm", "ssmmessages"]
  
  validation {
    condition = alltrue([
      for service in var.vpc_endpoint_services : contains(["s3", "ec2", "ec2messages", "ssm", "ssmmessages", "logs", "monitoring"], service)
    ])
    error_message = "VPC endpoint services must be valid AWS service names."
  }
}

variable "enable_network_acl" {
  description = "Enable custom Network ACLs"
  type        = bool
  default     = false
}

variable "network_acl_rules" {
  description = "List of Network ACL rules"
  type = list(object({
    rule_number = number
    egress      = bool
    protocol    = string
    rule_action = string
    cidr_block  = string
    from_port   = number
    to_port     = number
  }))
  default = []
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for network monitoring"
  type        = bool
  default     = true
}

variable "flow_log_retention_days" {
  description = "Number of days to retain VPC Flow Logs"
  type        = number
  default     = 7
  
  validation {
    condition     = var.flow_log_retention_days >= 1 && var.flow_log_retention_days <= 365
    error_message = "Flow log retention must be between 1 and 365 days."
  }
}

variable "enable_route53_health_checks" {
  description = "Enable Route53 health checks"
  type        = bool
  default     = true
}

variable "health_check_failure_threshold" {
  description = "Number of consecutive health check failures before marking unhealthy"
  type        = number
  default     = 3
  
  validation {
    condition     = var.health_check_failure_threshold >= 1 && var.health_check_failure_threshold <= 10
    error_message = "Health check failure threshold must be between 1 and 10."
  }
}

variable "enable_route53_failover" {
  description = "Enable Route53 failover routing"
  type        = bool
  default     = false
}

variable "failover_region" {
  description = "AWS region for failover infrastructure"
  type        = string
  default     = ""
  
  validation {
    condition     = var.failover_region == "" || can(regex("^[a-z0-9-]+$", var.failover_region))
    error_message = "Failover region must be a valid AWS region identifier or empty."
  }
}

variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "enable_spot_instances" {
  description = "Enable Spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_max_price" {
  description = "Maximum price for Spot instances (percentage of On-Demand price)"
  type        = number
  default     = 50
  
  validation {
    condition     = var.spot_max_price >= 1 && var.spot_max_price <= 100
    error_message = "Spot max price must be between 1 and 100 percent."
  }
}

variable "enable_scheduled_actions" {
  description = "Enable scheduled scaling actions"
  type        = bool
  default     = false
}

variable "scheduled_actions" {
  description = "List of scheduled scaling actions"
  type = list(object({
    name                   = string
    schedule               = string
    min_size               = number
    max_size               = number
    desired_capacity       = number
    time_zone              = string
    recurrence             = string
  }))
  default = []
}

variable "enable_maintenance_window" {
  description = "Enable maintenance windows for updates"
  type        = bool
  default     = true
}

variable "maintenance_window_schedule" {
  description = "Cron expression for maintenance window"
  type        = string
  default     = "cron(0 2 ? * SUN *)"  # Every Sunday at 2 AM UTC
  
  validation {
    condition     = can(regex("^cron\\(.*\\)$", var.maintenance_window_schedule))
    error_message = "Maintenance window schedule must be a valid cron expression."
  }
}

variable "maintenance_window_duration" {
  description = "Duration of maintenance window (hours)"
  type        = number
  default     = 2
  
  validation {
    condition     = var.maintenance_window_duration >= 1 && var.maintenance_window_duration <= 24
    error_message = "Maintenance window duration must be between 1 and 24 hours."
  }
}

variable "enable_patch_management" {
  description = "Enable automated patch management"
  type        = bool
  default     = true
}

variable "patch_schedule" {
  description = "Cron expression for patch schedule"
  type        = string
  default     = "cron(0 3 ? * SUN *)"  # Every Sunday at 3 AM UTC
  
  validation {
    condition     = can(regex("^cron\\(.*\\)$", var.patch_schedule))
    error_message = "Patch schedule must be a valid cron expression."
  }
}

variable "enable_vulnerability_scanning" {
  description = "Enable vulnerability scanning"
  type        = bool
  default     = true
}

variable "scan_schedule" {
  description = "Cron expression for vulnerability scan schedule"
  type        = string
  default     = "cron(0 4 ? * SUN *)"  # Every Sunday at 4 AM UTC
  
  validation {
    condition     = can(regex("^cron\\(.*\\)$", var.scan_schedule))
    error_message = "Scan schedule must be a valid cron expression."
  }
}

variable "enable_compliance_reporting" {
  description = "Enable compliance reporting"
  type        = bool
  default     = true
}

variable "compliance_frameworks" {
  description = "List of compliance frameworks to monitor"
  type        = list(string)
  default     = ["CIS", "PCI-DSS", "SOC"]
  
  validation {
    condition = alltrue([
      for framework in var.compliance_frameworks : contains(["CIS", "PCI-DSS", "SOC", "ISO27001", "NIST"], framework)
    ])
    error_message = "Compliance frameworks must be valid framework names."
  }
}

variable "enable_performance_monitoring" {
  description = "Enable detailed performance monitoring"
  type        = bool
  default     = true
}

variable "monitoring_interval" {
  description = "Interval for performance monitoring (seconds)"
  type        = number
  default     = 60
  
  validation {
    condition     = var.monitoring_interval >= 10 && var.monitoring_interval <= 300
    error_message = "Monitoring interval must be between 10 and 300 seconds."
  }
}

variable "enable_log_aggregation" {
  description = "Enable centralized log aggregation"
  type        = bool
  default     = true
}

variable "log_retention_policy" {
  description = "Log retention policy"
  type = object({
    access_logs    = number
    error_logs     = number
    security_logs  = number
    performance_logs = number
  })
  default = {
    access_logs    = 30
    error_logs     = 90
    security_logs  = 365
    performance_logs = 90
  }
}

variable "enable_backup_encryption" {
  description = "Enable encryption for backups"
  type        = bool
  default     = true
}

variable "backup_kms_key_arn" {
  description = "ARN of KMS key for backup encryption"
  type        = string
  default     = ""
  
  validation {
    condition     = var.backup_kms_key_arn == "" || can(regex("^arn:aws:kms:", var.backup_kms_key_arn))
    error_message = "Backup KMS key ARN must be a valid KMS key ARN or empty."
  }
}

variable "enable_disaster_recovery" {
  description = "Enable disaster recovery features"
  type        = bool
  default     = false
}

variable "dr_region" {
  description = "AWS region for disaster recovery"
  type        = string
  default     = ""
  
  validation {
    condition     = var.dr_region == "" || can(regex("^[a-z0-9-]+$", var.dr_region))
    error_message = "DR region must be a valid AWS region identifier or empty."
  }
}

variable "dr_rpo" {
  description = "Recovery Point Objective in minutes"
  type        = number
  default     = 60
  
  validation {
    condition     = var.dr_rpo >= 15 && var.dr_rpo <= 1440
    error_message = "DR RPO must be between 15 and 1440 minutes."
  }
}

variable "dr_rto" {
  description = "Recovery Time Objective in minutes"
  type        = number
  default     = 120
  
  validation {
    condition     = var.dr_rto >= 30 && var.dr_rto <= 2880
    error_message = "DR RTO must be between 30 and 2880 minutes."
  }
}
