# Security Group for EKS Control Plane
resource "aws_security_group" "cluster" {
  name        = "${var.environment}-devtrack-cluster-sg"
  description = "Security group for EKS control plane communication"
  vpc_id      = aws_vpc.devtrack.id

  egress {
    description = "Allow control plane to communicate with worker nodes"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-devtrack-cluster-sg"
  }
}

# Security Group for EKS Worker Nodes
resource "aws_security_group" "node" {
  name        = "${var.environment}-devtrack-node-sg"
  description = "Security group for all worker nodes in the DevTrack EKS cluster"
  vpc_id      = aws_vpc.devtrack.id

  # 1. Pod-to-Pod and Node-to-Node Intra-Cluster Communication
  ingress {
    description = "Allow intra-cluster node-to-node communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # 2. Inbound communication from the EKS Control Plane
  ingress {
    description     = "Allow control plane to reach worker node kubelets"
    from_port       = 10250
    to_port         = 10250
    protocol        = "tcp"
    security_groups = [aws_security_group.cluster.id]
  }

  ingress {
    description     = "Allow control plane to reach worker pods via HTTPS"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.cluster.id]
  }

  # 3. Allow Control Plane to receive API requests from Worker Nodes
  egress {
    description = "Allow worker nodes outbound access to the internet and AWS APIs"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name                                        = "${var.environment}-devtrack-node-sg"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }
}

# Rule allowing Control Plane to accept inbound HTTPS from worker nodes
resource "aws_security_group_rule" "cluster_ingress_nodes" {
  description              = "Allow worker nodes to communicate with the EKS API server"
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.node.id
  security_group_id        = aws_security_group.cluster.id
}
