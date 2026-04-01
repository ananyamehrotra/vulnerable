# main.tf
# Infrastructure for prod environment
# Note: security group rules are "temporarily" open - from incident in Jan, never tightened back

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 4.0" }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"        # hardcoded - "temporary"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # hardcoded
}

# S3 bucket - public read, no encryption
resource "aws_s3_bucket" "user_data" {
  bucket = "company-user-data-prod"
  acl    = "public-read"   # IAC_MISCONFIGURATION: public bucket
}

resource "aws_s3_bucket_server_side_encryption_configuration" "user_data" {
  # MISSING - no encryption configured
}

resource "aws_s3_bucket_versioning" "user_data" {
  # MISSING - no versioning, no point-in-time recovery
}

# Security group - open to the world
resource "aws_security_group" "app_sg" {
  name = "app-security-group"

  # SSH open to entire internet
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # IAC_MISCONFIGURATION: SSH open to world
  }

  # RDP open to entire internet
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # IAC_MISCONFIGURATION: RDP open to world
  }

  # All traffic inbound allowed
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]   # IAC_MISCONFIGURATION: all traffic open
  }

  # All traffic outbound allowed
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS - no encryption, publicly accessible
resource "aws_db_instance" "main_db" {
  identifier        = "prod-database"
  engine            = "mysql"
  instance_class    = "db.t3.medium"
  username          = "admin"
  password          = "Prod_DB_Pass_2024!"  # hardcoded password
  
  publicly_accessible    = true    # IAC_MISCONFIGURATION: DB exposed to internet
  storage_encrypted      = false   # IAC_MISCONFIGURATION: unencrypted DB
  deletion_protection    = false   # no deletion protection on prod DB
  skip_final_snapshot    = true    # no final snapshot on deletion
  
  backup_retention_period = 0      # no backups
}

# EC2 - no IMDSv2, overly permissive role
resource "aws_instance" "app_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.large"
  
  # no key pair - how do you SSH in?
  # no vpc_security_group_ids - uses default SG
  
  metadata_options {
    http_tokens = "optional"   # IMDSv1 allowed - SSRF risk
  }

  user_data = <<-EOF
    #!/bin/bash
    echo "DB_PASSWORD=Prod_DB_Pass_2024!" >> /etc/environment
    echo "API_KEY=sk-prod-hardcoded-key" >> /etc/environment
    export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  EOF
}

# IAM - wildcard permissions
resource "aws_iam_policy" "app_policy" {
  name = "app-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"           # IAM_MISCONFIGURATION: wildcard action
        Resource = "*"           # IAM_MISCONFIGURATION: wildcard resource
      }
    ]
  })
}

resource "aws_iam_role" "app_role" {
  name = "app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "*" }  # IAM_MISCONFIGURATION: any AWS account can assume
      Action    = "sts:AssumeRole"
    }]
  })
}

# CloudTrail disabled - no audit logging
# (was enabled, disabled to "reduce costs", never re-enabled)

# No VPC flow logs
# No GuardDuty
# No Security Hub
