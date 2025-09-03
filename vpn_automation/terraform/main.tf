# VPN Infrastructure Terraform Configuration
# Complete AWS VPN Infrastructure with Auto-Scaling

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket = "vpn-terraform-state"
    key    = "vpn-infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "vpn-infrastructure"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.environment}-vpn-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  enable_dns_hostnames = true
  enable_dns_support = true
  
  # NAT Gateway configuration
  single_nat_gateway = false
  one_nat_gateway_per_az = true
  
  # VPC Flow Logs
  enable_flow_log = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role = true
  
  tags = {
    Environment = var.environment
    Project     = "vpn-infrastructure"
  }
}

# Security Groups
resource "aws_security_group" "vpn_server" {
  name_prefix = "${var.environment}-vpn-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for VPN servers"
  
  # HTTPS/TLS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS/TLS traffic"
  }
  
  # HTTP (for ACME challenges)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for ACME challenges"
  }
  
  # SSH access (restricted to VPC)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
    description = "SSH access from VPC"
  }
  
  # 3X-UI Panel
  ingress {
    from_port   = 2053
    to_port     = 2053
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "3X-UI Panel access"
  }
  
  # DNS-over-TLS
  ingress {
    from_port   = 853
    to_port     = 853
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "DNS-over-TLS"
  }
  
  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = {
    Name = "${var.environment}-vpn-sg"
  }
}

# Data sources
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# IAM Role for VPN servers
resource "aws_iam_role" "vpn_server" {
  name = "${var.environment}-vpn-server-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "vpn_server" {
  name = "${var.environment}-vpn-server-profile"
  role = aws_iam_role.vpn_server.name
}

# Launch Template
resource "aws_launch_template" "vpn_server" {
  name_prefix   = "${var.environment}-vpn-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  
  vpc_security_group_ids = [aws_security_group.vpn_server.id]
  iam_instance_profile {
    name = aws_iam_instance_profile.vpn_server.name
  }
  
  user_data = base64encode(templatefile("${path.module}/scripts/install-xray.sh", {
    domain = "vpn.${var.environment}.com"
    environment = var.environment
  }))
  
  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = 20
      volume_type = "gp3"
      encrypted   = true
      delete_on_termination = true
    }
  }
  
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 1
  }
  
  monitoring {
    enabled = true
  }
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.environment}-vpn-server"
      Environment = var.environment
    }
  }
  
  tag_specifications {
    resource_type = "volume"
    tags = {
      Name = "${var.environment}-vpn-server-volume"
      Environment = var.environment
    }
  }
}

# Application Load Balancer
resource "aws_lb" "vpn" {
  name               = "${var.environment}-vpn-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.vpn_server.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = false
  
  access_logs {
    bucket  = aws_s3_bucket.vpn_logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }
  
  tags = {
    Environment = var.environment
  }
}

# ALB Target Group
resource "aws_lb_target_group" "vpn" {
  name     = "${var.environment}-vpn-tg"
  port     = 443
  protocol = "HTTPS"
  vpc_id   = module.vpc.vpc_id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "443"
    protocol            = "HTTPS"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
}

# ALB Listener
resource "aws_lb_listener" "vpn" {
  load_balancer_arn = aws_lb.vpn.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.vpn.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.vpn.arn
  }
}

# HTTP to HTTPS redirect
resource "aws_lb_listener" "vpn_http" {
  load_balancer_arn = aws_lb.vpn.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "vpn_servers" {
  name                = "${var.environment}-vpn-asg"
  vpc_zone_identifier = module.vpc.public_subnets
  target_group_arns   = [aws_lb_target_group.vpn.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300
  
  min_size         = var.min_instances
  max_size         = var.max_instances
  desired_capacity = var.desired_instances
  
  launch_template {
    id      = aws_launch_template.vpn_server.id
    version = "$Latest"
  }
  
  # Scaling policies
  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
  
  tag {
    key                 = "Name"
    value               = "${var.environment}-vpn-server"
    propagate_at_launch = true
  }
  
  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }
}

# Auto Scaling Policies
resource "aws_autoscaling_policy" "vpn_cpu_scale_up" {
  name                   = "${var.environment}-vpn-cpu-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.vpn_servers.name
}

resource "aws_autoscaling_policy" "vpn_cpu_scale_down" {
  name                   = "${var.environment}-vpn-cpu-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.vpn_servers.name
}

# CloudWatch Alarms for Auto Scaling
resource "aws_cloudwatch_metric_alarm" "vpn_cpu_high" {
  alarm_name          = "${var.environment}-vpn-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "CPUUtilization"
  namespace          = "AWS/EC2"
  period             = "120"
  statistic          = "Average"
  threshold          = "80"
  alarm_description  = "Scale up if CPU > 80% for 4 minutes"
  alarm_actions      = [aws_autoscaling_policy.vpn_cpu_scale_up.arn]
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.vpn_servers.name
  }
}

resource "aws_cloudwatch_metric_alarm" "vpn_cpu_low" {
  alarm_name          = "${var.environment}-vpn-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "CPUUtilization"
  namespace          = "AWS/EC2"
  period             = "120"
  statistic          = "Average"
  threshold          = "20"
  alarm_description  = "Scale down if CPU < 20% for 4 minutes"
  alarm_actions      = [aws_autoscaling_policy.vpn_cpu_scale_down.arn]
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.vpn_servers.name
  }
}

# S3 Bucket for logs
resource "aws_s3_bucket" "vpn_logs" {
  bucket = "${var.environment}-vpn-logs-${random_string.bucket_suffix.result}"
}

resource "aws_s3_bucket_versioning" "vpn_logs" {
  bucket = aws_s3_bucket.vpn_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "vpn_logs" {
  bucket = aws_s3_bucket.vpn_logs.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "vpn_logs" {
  bucket = aws_s3_bucket.vpn_logs.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Random string for bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ACM Certificate
resource "aws_acm_certificate" "vpn" {
  domain_name       = "vpn.${var.environment}.com"
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = {
    Environment = var.environment
  }
}

# Route53 Zone (if not exists)
resource "aws_route53_zone" "vpn" {
  name = "${var.environment}.com"
  
  tags = {
    Environment = var.environment
  }
}

# Route53 Record for ALB
resource "aws_route53_record" "vpn" {
  zone_id = aws_route53_zone.vpn.zone_id
  name    = "vpn.${var.environment}.com"
  type    = "A"
  
  alias {
    name                   = aws_lb.vpn.dns_name
    zone_id                = aws_lb.vpn.zone_id
    evaluate_target_health = true
  }
}

# Outputs
output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.vpn.dns_name
}

output "vpn_domain" {
  description = "The VPN domain name"
  value       = "vpn.${var.environment}.com"
}

output "asg_name" {
  description = "The name of the Auto Scaling Group"
  value       = aws_autoscaling_group.vpn_servers.name
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "The IDs of the public subnets"
  value       = module.vpc.public_subnets
}
