output "aws_region" {
  description = "Target AWS region for DevTrack infrastructure"
  value       = var.aws_region
}

output "environment" {
  description = "Deployment environment name"
  value       = var.environment
}

output "cluster_name" {
  description = "Configured Amazon EKS cluster name"
  value       = var.cluster_name
}

output "vpc_id" {
  description = "The ID of the DevTrack VPC"
  value       = aws_vpc.devtrack.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the DevTrack VPC"
  value       = aws_vpc.devtrack.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "cluster_security_group_id" {
  description = "Security group ID for the EKS control plane"
  value       = aws_security_group.cluster.id
}

output "node_security_group_id" {
  description = "Security group ID for the EKS worker nodes"
  value       = aws_security_group.node.id
}

output "cluster_endpoint" {
  description = "Endpoint URL for Amazon EKS control plane API server"
  value       = aws_eks_cluster.devtrack.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.devtrack.certificate_authority[0].data
  sensitive   = true
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = aws_eks_cluster.devtrack.identity[0].oidc[0].issuer
}

output "node_group_id" {
  description = "EKS managed Node Group ID"
  value       = aws_eks_node_group.devtrack.id
}

output "node_group_status" {
  description = "Status of the EKS managed Node Group"
  value       = aws_eks_node_group.devtrack.status
}
