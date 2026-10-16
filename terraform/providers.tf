provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DevTrack"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
