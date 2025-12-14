# Terraform IAM Configuration for Galerly
# Creates IAM users, groups, and policies

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

# ============================================
# IAM USERS
# ============================================

resource "aws_iam_user" "galerly_cicd" {
  name = "galerly-cicd"
  path = "/galerly/"
  
  tags = {
    Application = "Galerly"
    Purpose     = "CI/CD Deployment"
    Environment = "Production"
  }
}

resource "aws_iam_user" "galerly_app_runtime" {
  name = "galerly-app-runtime"
  path = "/galerly/"
  
  tags = {
    Application = "Galerly"
    Purpose     = "Application Runtime"
    Environment = "Production"
  }
}

resource "aws_iam_user" "galerly_admin" {
  name = "galerly-admin"
  path = "/galerly/"
  
  tags = {
    Application = "Galerly"
    Purpose     = "Administrative Operations"
    Environment = "Production"
  }
}

# ============================================
# IAM GROUPS
# ============================================

resource "aws_iam_group" "galerly_cicd_group" {
  name = "galerly-cicd-group"
  path = "/galerly/"
}

resource "aws_iam_group" "galerly_app_runtime_group" {
  name = "galerly-app-runtime-group"
  path = "/galerly/"
}

resource "aws_iam_group" "galerly_admin_group" {
  name = "galerly-admin-group"
  path = "/galerly/"
}

# ============================================
# GROUP MEMBERSHIPS
# ============================================

resource "aws_iam_group_membership" "cicd_membership" {
  name  = "galerly-cicd-membership"
  users = [aws_iam_user.galerly_cicd.name]
  group = aws_iam_group.galerly_cicd_group.name
}

resource "aws_iam_group_membership" "runtime_membership" {
  name  = "galerly-runtime-membership"
  users = [aws_iam_user.galerly_app_runtime.name]
  group = aws_iam_group.galerly_app_runtime_group.name
}

resource "aws_iam_group_membership" "admin_membership" {
  name  = "galerly-admin-membership"
  users = [aws_iam_user.galerly_admin.name]
  group = aws_iam_group.galerly_admin_group.name
}

# ============================================
# POLICY: CI/CD Deployment
# ============================================

resource "aws_iam_policy" "cicd_deployment" {
  name        = "GalerlyCICDDeploymentPolicy"
  path        = "/galerly/"
  description = "CI/CD deployment permissions for GitHub Actions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LambdaDeployment"
        Effect = "Allow"
        Action = [
          "lambda:GetFunction",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:PublishVersion",
          "lambda:CreateAlias",
          "lambda:UpdateAlias",
          "lambda:GetFunctionConfiguration"
        ]
        Resource = "arn:aws:lambda:eu-central-1:*:function:galerly-*"
      },
      {
        Sid    = "S3FrontendDeployment"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "arn:aws:s3:::galerly-frontend",
          "arn:aws:s3:::galerly-frontend/*"
        ]
      },
      {
        Sid    = "CloudFrontInvalidation"
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation",
          "cloudfront:GetInvalidation",
          "cloudfront:ListInvalidations",
          "cloudfront:GetDistribution"
        ]
        Resource = "arn:aws:cloudfront::*:distribution/*"
      },
      {
        Sid    = "APIGatewayDeployment"
        Effect = "Allow"
        Action = [
          "apigateway:GET",
          "apigateway:POST",
          "apigateway:PUT",
          "apigateway:PATCH"
        ]
        Resource = "arn:aws:apigateway:eu-central-1::/restapis/*"
      },
      {
        Sid    = "IAMPassRole"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:PassRole"
        ]
        Resource = "arn:aws:iam::*:role/galerly-*"
      }
    ]
  })
}

# ============================================
# POLICY: DynamoDB Full Access
# ============================================

resource "aws_iam_policy" "dynamodb_access" {
  name        = "GalerlyDynamoDBFullAccessPolicy"
  path        = "/galerly/"
  description = "Full access to all Galerly DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBTableAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DescribeTable",
          "dynamodb:ConditionCheckItem"
        ]
        Resource = "arn:aws:dynamodb:eu-central-1:*:table/galerly-*"
      },
      {
        Sid    = "DynamoDBIndexAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = "arn:aws:dynamodb:eu-central-1:*:table/galerly-*/index/*"
      }
    ]
  })
}

# ============================================
# POLICY: S3 Storage
# ============================================

resource "aws_iam_policy" "s3_storage" {
  name        = "GalerlyS3StoragePolicy"
  path        = "/galerly/"
  description = "S3 storage permissions for photos and renditions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          "arn:aws:s3:::galerly-images-storage",
          "arn:aws:s3:::galerly-renditions",
          "arn:aws:s3:::galerly-frontend"
        ]
      },
      {
        Sid    = "S3ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:PutObjectAcl",
          "s3:GetObjectAcl",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          "arn:aws:s3:::galerly-images-storage/*",
          "arn:aws:s3:::galerly-renditions/*"
        ]
      }
    ]
  })
}

# ============================================
# POLICY: SES Email
# ============================================

resource "aws_iam_policy" "ses_email" {
  name        = "GalerlySESEmailPolicy"
  path        = "/galerly/"
  description = "SES email sending permissions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SESEmailSending"
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail",
          "ses:SendTemplatedEmail"
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "ses:FromAddress" = [
              "noreply@galerly.com",
              "support@galerly.com"
            ]
          }
        }
      },
      {
        Sid    = "SESQuotaChecking"
        Effect = "Allow"
        Action = [
          "ses:GetSendQuota",
          "ses:GetSendStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================
# POLICY: CloudWatch Logs
# ============================================

resource "aws_iam_policy" "cloudwatch_logs" {
  name        = "GalerlyCloudWatchLogsPolicy"
  path        = "/galerly/"
  description = "CloudWatch Logs write permissions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogsAccess"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:eu-central-1:*:log-group:/aws/lambda/galerly-*",
          "arn:aws:logs:eu-central-1:*:log-group:/aws/lambda/galerly-*:*"
        ]
      }
    ]
  })
}

# ============================================
# POLICY: Admin
# ============================================

resource "aws_iam_policy" "admin" {
  name        = "GalerlyAdminPolicy"
  path        = "/galerly/"
  description = "Administrative permissions for manual operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "FullGalerlyAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:*",
          "s3:*",
          "lambda:*",
          "cloudfront:*",
          "apigateway:*",
          "ses:*",
          "logs:*",
          "cloudwatch:*",
          "acm:*"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMLimitedAccess"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:PassRole",
          "iam:ListRoles"
        ]
        Resource = "arn:aws:iam::*:role/galerly-*"
      }
    ]
  })
}

# ============================================
# ATTACH POLICIES TO GROUPS
# ============================================

# CI/CD Group Policies
resource "aws_iam_group_policy_attachment" "cicd_deployment" {
  group      = aws_iam_group.galerly_cicd_group.name
  policy_arn = aws_iam_policy.cicd_deployment.arn
}

# Runtime Group Policies
resource "aws_iam_group_policy_attachment" "runtime_dynamodb" {
  group      = aws_iam_group.galerly_app_runtime_group.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

resource "aws_iam_group_policy_attachment" "runtime_s3" {
  group      = aws_iam_group.galerly_app_runtime_group.name
  policy_arn = aws_iam_policy.s3_storage.arn
}

resource "aws_iam_group_policy_attachment" "runtime_ses" {
  group      = aws_iam_group.galerly_app_runtime_group.name
  policy_arn = aws_iam_policy.ses_email.arn
}

resource "aws_iam_group_policy_attachment" "runtime_logs" {
  group      = aws_iam_group.galerly_app_runtime_group.name
  policy_arn = aws_iam_policy.cloudwatch_logs.arn
}

# Admin Group Policies
resource "aws_iam_group_policy_attachment" "admin_policy" {
  group      = aws_iam_group.galerly_admin_group.name
  policy_arn = aws_iam_policy.admin.arn
}

# ============================================
# OUTPUTS
# ============================================

output "cicd_user_arn" {
  description = "ARN of CI/CD IAM user"
  value       = aws_iam_user.galerly_cicd.arn
}

output "runtime_user_arn" {
  description = "ARN of runtime IAM user"
  value       = aws_iam_user.galerly_app_runtime.arn
}

output "admin_user_arn" {
  description = "ARN of admin IAM user"
  value       = aws_iam_user.galerly_admin.arn
}

output "policy_arns" {
  description = "ARNs of created policies"
  value = {
    cicd_deployment = aws_iam_policy.cicd_deployment.arn
    dynamodb_access = aws_iam_policy.dynamodb_access.arn
    s3_storage      = aws_iam_policy.s3_storage.arn
    ses_email       = aws_iam_policy.ses_email.arn
    cloudwatch_logs = aws_iam_policy.cloudwatch_logs.arn
    admin           = aws_iam_policy.admin.arn
  }
}
