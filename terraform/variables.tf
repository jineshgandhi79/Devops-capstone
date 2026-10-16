variable "aws_region" {
  description = "Target AWS region for DevTrack infrastructure"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Deployment environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "Name of the Amazon EKS cluster"
  type        = string
  default     = "devtrack-eks-cluster"
}

variable "cluster_version" {
  description = "Kubernetes control plane version for EKS"
  type        = string
  default     = "1.30"
}

variable "vpc_cidr" {
  description = "CIDR block for the DevTrack Virtual Private Cloud"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (must be at least 2 across distinct AZs)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (must be at least 2 across distinct AZs)"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "node_instance_types" {
  description = "EC2 instance types for the EKS managed worker node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes in the managed node group"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of worker nodes in the managed node group"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of worker nodes in the managed node group"
  type        = number
  default     = 3
}

variable "enable_nat_gateway" {
  description = "Whether to provision a NAT Gateway for outbound internet access from private subnets (costs ~$0.045/hr)"
  type        = bool
  default     = true
}
