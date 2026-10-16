# Data source to fetch available Availability Zones in the selected AWS region
data "aws_availability_zones" "available" {
  state = "available"
}

# 1. Virtual Private Cloud (VPC)
resource "aws_vpc" "devtrack" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                                        = "${var.environment}-devtrack-vpc"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# 2. Internet Gateway (IGW) for public internet access
resource "aws_internet_gateway" "devtrack" {
  vpc_id = aws_vpc.devtrack.id

  tags = {
    Name = "${var.environment}-devtrack-igw"
  }
}

# 3. Public Subnets (across at least 2 distinct Availability Zones)
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.devtrack.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                        = "${var.environment}-devtrack-public-subnet-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
  }
}

# 4. Private Subnets (across at least 2 distinct Availability Zones)
resource "aws_subnet" "private" {
  count                   = length(var.private_subnet_cidrs)
  vpc_id                  = aws_vpc.devtrack.id
  cidr_block              = var.private_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = false

  tags = {
    Name                                        = "${var.environment}-devtrack-private-subnet-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }
}

# 5. Public Route Table (direct route to Internet Gateway)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.devtrack.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.devtrack.id
  }

  tags = {
    Name = "${var.environment}-devtrack-public-rt"
  }
}

# 6. Route Table Associations for Public Subnets
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# 7. Elastic IP for NAT Gateway (only created if NAT Gateway is enabled)
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"

  tags = {
    Name = "${var.environment}-devtrack-nat-eip"
  }
}

# 8. NAT Gateway (placed in Public Subnet 1 for outbound internet access from private nodes)
resource "aws_nat_gateway" "devtrack" {
  count         = var.enable_nat_gateway ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.environment}-devtrack-nat-gw"
  }

  depends_on = [aws_internet_gateway.devtrack]
}

# 9. Private Route Table (routes outbound traffic through NAT Gateway if enabled)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.devtrack.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.devtrack[0].id
    }
  }

  tags = {
    Name = "${var.environment}-devtrack-private-rt"
  }
}

# 10. Route Table Associations for Private Subnets
resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
