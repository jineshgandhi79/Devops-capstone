# DevTrack — Development Notes

## Project Overview
DevTrack is a developer project and issue management platform built as a DevOps Capstone.
Architecture: React (Vite) -> FastAPI -> PostgreSQL -> Docker -> Kubernetes (EKS).

## Architecture Decisions
- Decoupled 3-tier architecture:
  - Frontend (React / Vite) handles client UI and state.
  - Backend (FastAPI) handles REST routing, business rules, and validation.
  - Database (PostgreSQL) handles relational data storage.
- Monorepo folder layout:
  - `backend/`: FastAPI application, Alembic migrations, pytest suite.
  - `frontend/`: React + Vite client application with modular component hierarchy.
- Database Schema Versioning:
  - Managed via Alembic migrations (`alembic upgrade head`) rather than raw DDL.
- Secret Hygiene:
  - Credentials managed via `.env` (gitignored).
  - `.env.example` provides the checked-in blueprint.

## Completed Modules (Phase 1)
1. **1.1 Architecture & Repository Structure**: Monorepo layout, Git ignore, environment templates.
2. **1.2 FastAPI Backend Setup**: Application entrypoint, CORS configuration, health and readiness probes.
3. **1.3 PostgreSQL + SQLAlchemy**: Engine pooling, sessionmaker, declarative base, and request dependency injection (`get_db`).
4. **1.4 DevTrack Issue Model**: SQLAlchemy 2.0 ORM model with status & priority enums and audit timestamps.
5. **1.5 Pydantic Schemas**: `IssueBase`, `IssueCreate`, `IssueUpdate`, `IssueResponse`, and `IssueStats`.
6. **1.6 CRUD REST APIs**: 6 endpoints (`GET`, `POST`, `PUT`, `DELETE`, `stats`, single item lookup).
7. **1.7 Alembic Migrations**: Initial migration script generated and applied to PostgreSQL.
8. **1.8 React Frontend**: Modular components (`Sidebar`, `Header`, `StatCards`, `IssueTable`, `IssueModal`).
9. **1.9 Frontend <-> Backend Integration**: End-to-end asynchronous HTTP communication with loading & error handling.
10. **1.10 Phase 1 Verification**: Complete pytest automated test suite verifying all CRUD operations against PostgreSQL.

## Commands Reference
```bash
# Start PostgreSQL container
docker run -d --name devtrack-postgres -p 5433:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=devtrack postgres:17

# Backend run & test
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
pytest tests/

# Frontend run & build
cd frontend
npm run dev
npm run build
```

## Completed Modules (Phase 2 — Containerization & Docker)
1. **2.1 Docker Fundamentals & Architecture**: 3-tier container decoupled design, image vs container, ephemeral filesystems vs persistent storage.
2. **2.2 Backend Containerization**: `backend/Dockerfile` using `python:3.12-slim`, layer-cached dependency installation, clean `.dockerignore`, unbuffered output, non-root user `appuser`.
3. **2.3 Frontend Multi-Stage Build**: `frontend/Dockerfile` using two-stage pipeline (`node:20-alpine` for building $\rightarrow$ `nginxinc/nginx-unprivileged:alpine` for serving). Image reduced to ~26MB, zero Node.js runtime attack surface, SPA `try_files` routing.
4. **2.4 PostgreSQL Persistence & Env Configuration**: `postgres:16-alpine`, Docker named volume (`devtrack_postgres_data`), verified persistence across container deletion, environment variable decoupling.
5. **2.5 Multi-Container Orchestration**: `docker-compose.yml` declaring `frontend`, `backend`, and `postgres` with dependency health conditions and automatic Alembic migrations on startup.
6. **2.6 Service Discovery & Internal Networking**: Isolated bridge network `devtrack-network`, internal DNS resolving `postgres:5432`, verified container isolation vs `localhost`.
7. **2.7 Non-Root Security Hardening**: Verified non-root execution (`appuser` UID 999/1000 in backend, `nginx` UID 101 in frontend), restricted filesystem writes in root directories.
8. **2.8 Health Checks & Lifecycle Management**: Implemented container healthcheck probes (`pg_isready` for Postgres, native Python HTTP probe for `/health` in FastAPI).
9. **2.9 Full Docker Verification & Rubric Audit**: End-to-end CRUD verification, browser validation at `http://localhost:3000`, volume persistence audit.

## Docker Commands Reference
```bash
# Build and start all services in detached mode
docker compose up --build -d

# Check running services and health status
docker compose ps

# View service logs
docker compose logs -f backend
docker compose logs -f postgres

# Verify non-root UIDs
docker compose exec backend id
docker compose exec frontend id

# Stop containers without removing persistent volume data
docker compose down

# Teardown containers AND delete persistent volumes (destructive)
docker compose down -v
```

## Phase 2 Architecture Decisions & Security Model
- **Multi-Stage Build (Frontend)**: Compiles React with Node.js in stage 1, then discards all Node tooling and runtime dependencies. Production runtime uses `nginxinc/nginx-unprivileged:alpine` (~26MB), eliminating build tool CVE vulnerabilities.
- **Principle of Least Privilege (Non-Root)**:
  - Backend runs as system user `appuser` (UID 999/1000).
  - Frontend runs under official unprivileged user `nginx` (UID 101) on port 8080.
  - Mitigates container-escape risks by forbidding arbitrary root filesystem alterations.
- **Embedded DNS & Service Discovery**: Services talk using Compose service names (`postgres:5432`) over an isolated bridge network `devtrack-network`, avoiding brittle hardcoded IP configurations.
- **Stateful vs Stateless Lifecycle**: PostgreSQL data is decoupled into the named volume `devtrack_postgres_data` allowing stateless app container destruction without risking database state loss.
- **Automated Schema Sync**: Container entrypoint runs `alembic upgrade head` before Uvicorn starts, synchronizing database models automatically on service launch.

## Completed Modules (Phase 3 — CI/CD with GitHub Actions)
1. **3.1 CI/CD Fundamentals & Workflow Architecture**: Established 3-stage automated pipeline design (Quality Gates: Tests & Builds $\rightarrow$ Container Build $\rightarrow$ GHCR Publishing). Decoupled CI test environment from local host database.
2. **3.2 First GitHub Actions Workflow**: Created `.github/workflows/ci.yml` listening on `push` and `pull_request` to `main`, running on `ubuntu-latest`, verifying repository integrity and Git commit context.
3. **3.3 Backend Automated Testing**: Added `backend-test` job running an ephemeral `postgres:16-alpine` service container on the runner, applying Alembic migrations to `devtrack_test`, and executing the Pytest suite.
4. **3.4 Frontend Production Build**: Added `frontend-build` job compiling the React + Vite production bundle (`npm ci` $\rightarrow$ `npm run build`), running in parallel with backend tests.
5. **3.5 Docker Image Builds**: Added `docker-build` job gated sequentially via `needs: [backend-test, frontend-build]`, verifying Buildx compilation of both application images.
6. **3.6 GitHub Container Registry (GHCR)**: Configured least-privilege `packages: write` permissions, automated authentication via ephemeral `GITHUB_TOKEN`, normalized lowercase image paths, and established publishing to `ghcr.io`.
7. **3.7 Git SHA Image Tagging**: Implemented dual-tagging strategy applying full 40-character immutable Git commit SHA (`${{ github.sha }}`) alongside `latest` for both frontend and backend images.
8. **3.8 Pipeline Quality & Security**: Configured workflow concurrency control (`cancel-in-progress: true`), Docker Buildx GHA layer caching (`type=gha`), restricted publishing to trusted `push` events, and pinned actions.
9. **3.9 End-to-End Verification**: Validated full pipeline execution through GitHub Actions, including deliberate failure injection (commit `e80c487`) proving the quality gate blocks image publication, followed by green restoration (commit `f43cc78`).

## Phase 3 CI/CD Architecture & Quality Gates
- **Trigger Strategy**: Pipeline triggers automatically on direct pushes to `main` and on pull requests targeting `main`. Image publishing runs exclusively on validated pushes to `main`.
- **Concurrency Control**: `concurrency: group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true` terminates redundant active runs on rapid commits to avoid race conditions.
- **Quality Gates Principle**: Builds and image publishing are gated strictly behind passing automated tests and front-end compilation (`needs: [backend-test, frontend-build]`). A single test failure immediately terminates the pipeline before any artifact is pushed.
- **Workflow File**: `.github/workflows/ci.yml`
- **Registry & Authentication**: Images publish to GitHub Container Registry (`ghcr.io`) using GitHub's built-in, ephemeral `GITHUB_TOKEN` with least-privilege `packages: write` permissions (no long-lived PATs required).
- **Immutable Tagging**: Images are tagged with the full 40-character Git commit SHA (`${{ github.sha }}`) to guarantee 100% auditability and enable reliable rollbacks.
- **Build Performance**: Leverages Buildx GitHub Actions Cache (`type=gha`, `mode=max`) to persist intermediate Docker layer caches across workflow runs.

### Quality Gate Verification Flow
```text
                    TEST 1: Normal Healthy Commit
                    ─────────────────────────────
                             git push
                                │
               ┌────────────────┴────────────────┐
               ▼ (PASS)                          ▼ (PASS)
        [backend-test]                    [frontend-build]
               └────────────────┬────────────────┘
                                │
                                ▼ (EXECUTES)
                         [docker-build]
                                │
                                ▼
                       ✅ Published to GHCR


                    TEST 2: Deliberate Failure Injection
                    ────────────────────────────────────
                       git push (broken test)
                                │
               ┌────────────────┴────────────────┐
               ▼ (FAILS ❌)                      ▼ (PASS)
        [backend-test]                    [frontend-build]
               │                                 │
               └────────────────┬────────────────┘
                                │
                                ▼ (BLOCKED ⛔)
                         [docker-build]
                           (SKIPPED!)
                                │
                                ▼
                     Zero images published!
                   Quality Gate Protected Repo!
```

## Phase 3 M5 Rubric & Evidence Tracker

| Criteria | Requirement | Status | Verification Location / Evidence |
| :--- | :--- | :---: | :--- |
| **1. Workflow Exists** | At least one workflow in `.github/workflows/` | ✅ Verified | `.github/workflows/ci.yml` |
| **2. Trigger on `main`** | Triggers on push to `main` branch | ✅ Verified | `on.push.branches: [main]` |
| **3. Pytest Quality Gate** | Pytest runs in CI; failure fails build | ✅ Verified | `backend-test` job; verified blocking via commit `e80c487` |
| **4. Frontend Build Gate** | Production build runs in CI | ✅ Verified | `frontend-build` job in `.github/workflows/ci.yml` |
| **5. Docker Image Builds** | Both backend & frontend images build | ✅ Verified | `docker-build` job in `.github/workflows/ci.yml` |
| **6. Publish to GHCR** | Both images pushed to `ghcr.io` | ✅ Verified | Published to `ghcr.io/pranav-learner/devtrack-*` |
| **7. Immutable SHA Tags** | Image tags use Git commit SHA (not just `latest`) | ✅ Verified | Tagged with `${{ github.sha }}` and `latest` in GHCR |

## Phase 4 — Terraform & AWS Infrastructure (Underway)

### Overview & High-Level Architecture
In Phase 4, we provision the production cloud infrastructure for DevTrack on Amazon Web Services (AWS) using Terraform (Infrastructure as Code - IaC).
The target environment consists of:
- **Virtual Private Cloud (VPC)** in `ap-south-1` (Mumbai) spanning two Availability Zones (`ap-south-1a`, `ap-south-1b`).
- **Subnet Topology**: Public subnets (with Internet Gateway) and Private subnets (for EKS worker nodes).
- **Elastic Kubernetes Service (EKS)**: AWS-managed control plane with managed node groups (EC2 instances).
- **IAM Security**: Dedicated least-privilege IAM roles for the EKS cluster and node groups.

```text
                               AWS Cloud (Region: ap-south-1)
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Virtual Private Cloud (VPC: 10.0.0.0/16)                                               │
 │                                                                                        │
 │  Availability Zone 1 (ap-south-1a)                 Availability Zone 2 (ap-south-1b)   │
 │ ┌───────────────────────────────────────┐         ┌──────────────────────────────────┐ │
 │ │ Public Subnet A (10.0.1.0/24)         │         │ Public Subnet B (10.0.2.0/24)    │ │
 │ │  • Ingress / ALBs                     │         │  • Ingress / ALBs                │ │
 │ └───────────────────┬───────────────────┘         └──────────────────┬───────────────┘ │
 │                     │                                                │                 │
 │                     └───────────────────────┬────────────────────────┘                 │
 │                                             ▼                                          │
 │                                [Internet Gateway (IGW)]                                │
 │                                             ▲                                          │
 │                                             │                                          │
 │ ┌───────────────────────────────────────┐   │     ┌──────────────────────────────────┐ │
 │ │ Private Subnet A (10.0.10.0/24)       │   │     │ Private Subnet B (10.0.11.0/24)  │ │
 │ │  • EKS Worker Node (EC2)              │───┴────▶│  • EKS Worker Node (EC2)         │ │
 │ │    - DevTrack Pods (Frontend, API)    │         │    - DevTrack Pods (PostgreSQL)  │ │
 │ └───────────────────────────────────────┘         └──────────────────────────────────┘ │
 │                                             ▲                                          │
 │                                             │                                          │
 │                          [EKS Managed Control Plane]                                   │
 │                           (Kubernetes API Server / etcd)                               │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

### Module 4.1 — AWS and Terraform Fundamentals
- **Infrastructure as Code (IaC)**: Eliminates manual "ClickOps" in the AWS Management Console by defining all infrastructure in declarative, version-controlled HashiCorp Configuration Language (HCL).
- **Key Terraform Concepts**:
  - `terraform init`: Initializes the workspace, downloads specified AWS provider plugins.
  - `terraform validate`: Verifies syntax and internal consistency of HCL files without cloud calls.
  - `terraform plan`: Generates an execution plan, computing drift against current state and calculating additions (`+`), changes (`~`), and destructions (`-`).
  - `terraform apply`: Provisions declared infrastructure in the exact dependency order.
  - `terraform destroy`: Tears down all resources recorded in the state file in reverse dependency order.
  - `terraform.tfstate`: JSON file recording real-world cloud resource IDs and attributes mapped to Terraform declarations.
- **Local Tooling Verification**:
  - `terraform`: v1.9.8 (verified installed)
  - `aws-cli`: v2.37.10 (verified installed)
  - `kubectl`: v1.35.1 (verified installed)
  - AWS Credentials: Checked via `aws sts get-caller-identity`; credentials to be configured securely before Phase 4.8 apply.
- **Cost Drivers Identified**:
  - EKS Control Plane: ~$0.10/hour (~$72/month if left running).
  - EC2 Worker Nodes: `t3.medium` instances (~$0.0416/hour each in `ap-south-1`).
  - NAT Gateway (if enabled): ~$0.045/hour (~$32.40/month per NAT) + data processing.
  - Cost Strategy: Deploy, verify, capture evidence for rubric & demo, then run `terraform destroy` promptly.


### Module 4.2 — Terraform Project Configuration
- **Directory Layout**: Created dedicated `terraform/` root directory isolating infrastructure code from application source code.
- **Provider & Version Constraints (`versions.tf`)**:
  - Terraform core pinned to `>= 1.5.0, < 2.0.0` (matching local Terraform `v1.9.8`).
  - AWS provider pinned to `hashicorp/aws` `~> 5.50` for up-to-date EKS and VPC resource support.
- **Provider Configuration (`providers.tf`)**:
  - AWS provider configured to target `var.aws_region` (`ap-south-1`).
  - Added global `default_tags` (`Project: DevTrack`, `Environment: var.environment`, `ManagedBy: Terraform`) for cost allocation and tag governance.
  - Zero hardcoded credentials in source code.
- **Variables & Defaults (`variables.tf`)**:
  - Parameterized region, cluster name, Kubernetes version (`1.30`), CIDR ranges, and worker node scaling bounds.
- **Outputs (`outputs.tf`)**:
  - Declared outputs for region, environment, and cluster name.
- **Example Blueprint (`terraform.tfvars.example`)**:
  - Checked-in blueprint for parameter overrides containing zero real secrets.
- **Security & Git Hygiene (`.gitignore`)**:
  - Configured gitignore to exclude `.terraform/`, `*.tfstate*`, `*.tfplan*`, and local `terraform.tfvars`, while explicitly permitting `!terraform.tfvars.example`.

### Module 4.3 — VPC and Networking Topology
- **VPC Definition (`networking.tf`)**:
  - CIDR block `10.0.0.0/16` providing 65,536 private IP addresses.
  - Enabled DNS hostnames and DNS support (prerequisite for Kubernetes worker nodes and AWS VPC CNI).
  - Tagged with `kubernetes.io/cluster/${var.cluster_name} = shared`.
- **Availability Zone Dynamic Discovery**:
  - Leverages `data "aws_availability_zones" "available"` to discover region AZs dynamically (`ap-south-1a`, `ap-south-1b`).
- **Subnet Segmentation & CIDR Calculations**:
  - **Public Subnets**: `10.0.1.0/24` (AZ a) and `10.0.2.0/24` (AZ b). Configured with `map_public_ip_on_launch = true`.
  - **Private Subnets**: `10.0.10.0/24` (AZ a) and `10.0.11.0/24` (AZ b). Configured with `map_public_ip_on_launch = false`.
- **Kubernetes Load Balancer Subnet Discovery Tags**:
  - Public Subnets: `kubernetes.io/role/elb = "1"` (allows AWS Load Balancer Controller to auto-discover subnets for external ALBs/NLBs).
  - Private Subnets: `kubernetes.io/role/internal-elb = "1"` (allows auto-discovery for internal load balancers).
- **Internet Gateway & Routing**:
  - `aws_internet_gateway` attached to the VPC.
  - Dedicated public route table routing `0.0.0.0/0` $\rightarrow$ Internet Gateway.
  - Associated with both public subnets via `aws_route_table_association`.
- **Network Outputs**:
  - Exported `vpc_id`, `vpc_cidr_block`, `public_subnet_ids`, and `private_subnet_ids` in `outputs.tf`.

### Module 4.4 — NAT Architecture and Security Groups
- **NAT Gateway Trade-off Analysis**:
  - *Internet Gateway vs NAT Gateway*: IGW enables two-way internet traffic for public instances; NAT Gateway enables one-way outbound internet access for private instances without exposing their private IPs to incoming internet connections.
  - *Architecture Choice*: Single NAT Gateway deployed in Public Subnet 1 (`enable_nat_gateway = true`), shared by both private subnets.
  - *Cost Control*: ~$0.045/hour (~$0.045 to $0.09 for our testing session). Controlled via parameter `var.enable_nat_gateway`.
- **EKS Control Plane Security Group (`aws_security_group.cluster`)**:
  - Ingress: HTTPS (port 443) strictly from the worker node security group.
  - Egress: Full outbound access to communicate with worker nodes and AWS APIs.
- **Worker Node Security Group (`aws_security_group.node`)**:
  - Intra-cluster ingress: All protocols/ports allowed between members of the same security group (`self = true`) for pod-to-pod networking across nodes.
  - Ingress from Control Plane: Kubelet API (port 10250) for `kubectl exec`/`logs`, and HTTPS (port 443).
  - Outbound egress: Full egress (`0.0.0.0/0`) for container image pulls (GHCR), DNS, and external dependencies.
- **Tagged for Kubernetes**: `kubernetes.io/cluster/${var.cluster_name} = "owned"`.

### Module 4.5 — Amazon EKS Cluster & Managed Node Group
- **Kubernetes Version Selection**:
  - Pinned to `1.30` in `variables.tf`. Fully supported across AWS EKS and the AWS provider `~> 5.50`.
- **EKS Control Plane (`aws_eks_cluster.devtrack`)**:
  - AWS-managed Kubernetes master nodes running API server, controller manager, and etcd.
  - Subnet configuration: Associated with all public and private subnets across `ap-south-1a` and `ap-south-1b` for resilient cross-account ENI placement.
  - Endpoint Access: Enabled both `endpoint_private_access = true` and `endpoint_public_access = true` (enables developer laptop access via `kubectl` without requiring an AWS Client VPN or bastion host).
- **Cluster IAM Role (`aws_iam_role.cluster`)**:
  - Assume role policy for `eks.amazonaws.com`.
  - Attached policies: `AmazonEKSClusterPolicy` and `AmazonEKSVPCResourceController`.
- **Managed Worker Node Group (`aws_eks_node_group.devtrack`)**:
  - Placed strictly in private subnets (`aws_subnet.private[*].id`) for workload isolation.
  - EC2 instance type: `t3.medium` (2 vCPU, 4 GiB RAM), providing sufficient headroom for AWS VPC CNI, CoreDNS, kube-proxy, and DevTrack 3-tier microservices.
  - Scaling boundaries: `desired_size = 2`, `min_size = 1`, `max_size = 3`.
  - Rolling update strategy: `max_unavailable = 1`.
- **Worker Node IAM Role (`aws_iam_role.node`)**:
  - Assume role policy for `ec2.amazonaws.com`.
  - Attached policies: `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy` (for ENI IP management), and `AmazonEC2ContainerRegistryReadOnly`.
- **EKS Outputs**:
  - Exported `cluster_endpoint`, `cluster_certificate_authority_data`, `cluster_oidc_issuer_url`, `node_group_id`, and `node_group_status` in `outputs.tf`.

### Module 4.6 — Terraform State and Lifecycle Management
- **State File Anatomy (`terraform.tfstate`)**:
  - Acts as the definitive ledger mapping declarative HCL resources to real-world AWS resource IDs (e.g., `vpc-0123...`, `eks-cluster-...`).
  - Records dependencies, provider metadata, and computed attributes.
- **Resource Addressing & Dependency Graph**:
  - Address notation: `<resource_type>.<name>` (e.g., `aws_vpc.devtrack`, `aws_eks_node_group.devtrack`).
  - Count indices: `<resource_type>.<name>[<index>]` (e.g., `aws_subnet.public[0]`).
  - Terraform builds a Directed Acyclic Graph (DAG) determining execution order:
    1. Independent resources (VPC, IAM roles) are created concurrently.
    2. Dependent subnets and route tables are created once VPC exists.
    3. EKS Cluster is created once subnets, security groups, and IAM role attachments exist.
    4. Node group is created last once EKS cluster is ACTIVE.
- **Drift Detection & Cloud Reconciliation**:
  - During `terraform plan` or `refresh`, Terraform queries the AWS API to check whether real infrastructure matches state.
  - If a resource was modified or deleted manually in the AWS Console ("ClickOps"), Terraform calculates the drift and plans additions or updates to restore the declared state.
- **State Locking & Collaboration Models**:
  - *Local State (Capstone)*: Stored in `terraform/terraform.tfstate`. Fast, self-contained, requiring zero pre-existing cloud storage. Safe for single-student capstone workflows.
  - *Remote State (Production / Team)*: AWS S3 backend (encrypted with KMS, versioned) paired with DynamoDB table for distributed write locking (`StateLock`), preventing concurrent apply collisions.
  - *Security Mandate*: `.tfstate` files are strictly excluded from version control via `.gitignore` to prevent secret leakage.

### Module 4.7 — Validation, Initialization, and Plan Preparation
- **Code Style Verification (`terraform fmt -check`)**:
  - Validated all `.tf` files in `terraform/` directory. Zero syntax or indentation deviations.
- **Provider Initialization (`terraform init`)**:
  - Successfully connected to HashiCorp Registry and installed `hashicorp/aws v5.100.0`.
  - Created `.terraform.lock.hcl` pinning provider checksums.
  - Exit code `0` achieved (Rubric Item 2 completed).
- **Static Schema Validation (`terraform validate`)**:
  - Validated all HCL resources, blocks, types, and variables across `versions.tf`, `providers.tf`, `variables.tf`, `networking.tf`, `security.tf`, `eks.tf`, and `outputs.tf`.
  - Returned: `Success! The configuration is valid.` with 0 errors.
- **Plan Preparation (`terraform plan`)**:
  - Requires AWS credentials to query live Availability Zones via `data "aws_availability_zones" "available"` before calculating resource additions.
  - Secure credential configuration guided via `aws configure` (avoiding hardcoded secrets).

### Phase 4 M7 Rubric & Evidence Tracker (15 Points Total)

| Rubric Item | Points | Requirement | Status | Verification / Evidence |
| :--- | :---: | :--- | :---: | :--- |
| **1. Terraform Directory & HCL** | 2 | Clean directory with valid, modular `.tf` files | ✅ Implemented | `terraform/` with `versions.tf`, `providers.tf`, `variables.tf`, `networking.tf`, `security.tf`, `eks.tf`, `outputs.tf` (`fmt` checked) |
| **2. `terraform init` Success** | 1 | Provider download and backend initialization | ✅ Verified | `terraform init` exited with code 0; installed `aws v5.100.0` |
| **3. `terraform plan` Output** | 2 | Valid, non-empty plan showing resources to add | ⏳ Ready for Auth | Validated via `terraform validate`; awaiting `aws configure` for cloud refresh |
| **4. VPC & Public Subnets** | 3 | VPC provisioned with $\ge 2$ public subnets in distinct AZs | ⏳ Code Ready | Defined in `networking.tf`; awaiting apply in Part 4.8 |
| **5. EKS Cluster & Node Group** | 4 | ACTIVE EKS cluster and ACTIVE managed worker node group | ⏳ Code Ready | Defined in `eks.tf`; awaiting apply in Part 4.8 |
| **6. Clean `terraform destroy`** | 2 | Clean teardown of all managed infrastructure | ⏳ Pending | Scheduled for Part 4.9 |
| **7. `terraform.tfvars.example`** | 1 | Example variables file committed without real secrets | ✅ Verified | `terraform/terraform.tfvars.example` created & tracked |

## Phase 5 — Kubernetes Workloads & Helm (Underway)

### Overview
In Phase 5, we transition DevTrack from Docker Compose containerization to declarative Kubernetes workloads and reusable Helm charts.
All workloads target the dedicated `devtrack` namespace and pull verified OCI images from GitHub Container Registry (`ghcr.io/pranav-learner/devtrack-*`).

### Module 5.1 — Preflight Discovery
- **Toolchain Audited**:
  - `kubectl`: v1.35.1 (Active)
  - `helm`: v3.17.1 (Active)
  - `minikube`: v1.38.1 (Installed)
- **Container Registry Baseline**:
  - Backend: `ghcr.io/pranav-learner/devtrack-backend`
  - Frontend: `ghcr.io/pranav-learner/devtrack-frontend`
  - Tag Strategy: Pinned full Git commit SHA (`bb56f13b43164745584512374d5e1f66cbdf75b6`) alongside `latest`.

### Module 5.2 — Kubernetes Resource Fundamentals & Core Workloads
- **Dedicated Namespace (`k8s/namespace.yaml`)**:
  - Namespace `devtrack` with standard Kubernetes recommended labels.
- **Backend Workload (`k8s/backend-deployment.yaml` & `k8s/backend-service.yaml`)**:
  - 2 Replicas for high availability (satisfies rubric requirement).
  - RollingUpdate deployment strategy (`maxSurge: 1`, `maxUnavailable: 0`).
  - Container port 8000 mapped to ClusterIP service `devtrack-backend`.
  - Non-root security context (`appuser` UID 1000).
  - Resource requests: CPU 100m, Memory 128Mi; limits: CPU 300m, Memory 256Mi.
  - Liveness probe (`/health`) and readiness probe (`/ready`).
- **Frontend Workload (`k8s/frontend-deployment.yaml` & `k8s/frontend-service.yaml`)**:
  - 2 Replicas of Nginx unprivileged SPA.
  - Container port 8080 exposed via ClusterIP service `devtrack-frontend` on port 80.
  - Non-root security context (`nginx` UID 101).
  - Liveness probe (`/`) and readiness probe (`/`).
  - Resource requests: CPU 50m, Memory 64Mi; limits: CPU 200m, Memory 128Mi.

### Module 5.3 — ConfigMaps, Secrets, and PostgreSQL Persistence
- **Decoupled Configuration (`k8s/configmap.yaml`)**:
  - ConfigMap `devtrack-config` isolating non-sensitive variables (`POSTGRES_DB: devtrack`, `POSTGRES_USER: postgres`, `POSTGRES_HOST: devtrack-postgres`, `POSTGRES_PORT: 5432`, `ENVIRONMENT: production`).
- **Secret Hygiene (`k8s/secret.example.yaml`)**:
  - Clean template blueprint providing connection string format without real credentials.
  - Excluded `k8s/secret.yaml` from Git tracking via `.gitignore`.
- **Database Persistence (`k8s/postgres-pvc.yaml`)**:
  - 1 GiB ReadWriteOnce `PersistentVolumeClaim` ensuring issue and user data persists across Pod restarts and upgrades.
- **PostgreSQL Stateful Workload (`k8s/postgres-deployment.yaml` & `k8s/postgres-service.yaml`)**:
  - Single replica with `strategy: Recreate` preventing dual-pod write lock collisions on the PVC.
  - Backed by official `postgres:16-alpine`.
  - Mounted volume at `/var/lib/postgresql/data` with `subPath: postgres`.
  - Health probes using `pg_isready -U postgres -d devtrack` for liveness and readiness.
  - ClusterIP service exposing port 5432 resolving `devtrack-postgres:5432` internally for backend Pods.

### Module 5.4 — Ingress Routing & Declarative Manifest Management
- **Unified Ingress Entrypoint (`k8s/ingress.yaml`)**:
  - `ingressClassName: nginx` standard routing for Kubernetes Ingress Controllers.
  - Path-based routing:
    - `/` (Prefix) $\rightarrow$ Service `devtrack-frontend` on port 80 (React web application).
    - `/api` (Prefix) $\rightarrow$ Service `devtrack-backend` on port 8000 (FastAPI REST endpoints).
    - `/docs` (Prefix) & `/openapi.json` (Exact) $\rightarrow$ Service `devtrack-backend` on port 8000 (Interactive API documentation).
- **Declarative Kustomization (`k8s/kustomization.yaml`)**:
  - Manages the complete resource manifest set across namespace, configs, secrets, PVC, stateful database, stateless API, and UI in proper dependency sequence.
  - Validated offline via `kubectl kustomize k8s/` exiting with status code 0.

### Module 5.5 — Helm Chart Packaging & Templating (`helm/devtrack`)
- **Chart Architecture**:
  - `helm/devtrack/Chart.yaml` defining chart version `0.1.0` and application version `1.0.0`.
  - `helm/devtrack/values.yaml` centralizing environment, replica counts, image tags, service ports, resource allocations, and ingress annotations.
  - `helm/devtrack/templates/_helpers.tpl` generating standardized Kubernetes labels (`helm.sh/chart`, `app.kubernetes.io/managed-by: Helm`, `app.kubernetes.io/part-of: devtrack`).
- **Templated Workloads**:
  - `templates/namespace.yaml`: Conditional or configurable namespace creation.
  - `templates/configmap.yaml` & `templates/secret.yaml`: Parameterized application runtime configuration and credentials.
  - `templates/postgres-pvc.yaml`, `postgres-deployment.yaml`, `postgres-service.yaml`: Persistent database stack with configurable storage and resource limits.
  - `templates/backend-deployment.yaml` & `backend-service.yaml`: 2-replica API deployment with probes and resource requests/limits.
  - `templates/frontend-deployment.yaml` & `frontend-service.yaml`: 2-replica UI deployment with probes and non-root security context.
  - `templates/ingress.yaml`: Flexible path-based Ingress routing with configurable annotations.
- **Verification**:
  - `helm lint helm/devtrack`: 0 chart(s) failed (`PASS`).
  - `helm template devtrack helm/devtrack`: Cleanly rendered all 11 Kubernetes manifests (`PASS`).
  - `helm package helm/devtrack -d helm/`: Successfully packaged release archive `helm/devtrack-0.1.0.tgz`.

### Module 5.6 — Health Probes, Rolling Updates & Troubleshooting Guide
- **Rolling Update Mechanics**:
  - `maxSurge: 1`, `maxUnavailable: 0` ensures zero-downtime rolling deployments by spinning up a new container and validating its readiness probe before terminating an old instance.
  - PostgreSQL uses `strategy: Recreate` to avoid ReadWriteOnce PVC volume lock contentions.
- **Probe Timing & Thresholds**:
  - Backend Liveness (`GET /health`): `initialDelaySeconds: 15`, `periodSeconds: 10`, `timeoutSeconds: 3`, `failureThreshold: 3`.
  - Backend Readiness (`GET /ready`): `initialDelaySeconds: 5`, `periodSeconds: 5`, `timeoutSeconds: 2`, `failureThreshold: 2`.
  - Frontend Probes (`GET /`): `initialDelaySeconds: 10` (liveness), `5` (readiness).
  - Postgres Probes (`exec: pg_isready -U postgres -d devtrack`): `initialDelaySeconds: 15` (liveness), `5` (readiness).
- **Kubernetes Diagnostic Workflow**:
  - Rollout tracking: `kubectl rollout status deployment/devtrack-backend -n devtrack`.
  - Rollback capability: `kubectl rollout undo deployment/devtrack-backend -n devtrack`.
  - Crash diagnosis: `kubectl describe pod <pod-name> -n devtrack` and `kubectl logs <pod-name> -n devtrack --previous`.

### Module 5.7 — Phase 5 Capstone Rubric Audit Table

| Rubric Requirement | Status | Verification & Evidence |
| :--- | :---: | :--- |
| **1. Dedicated Namespace** | ✅ Verified | `k8s/namespace.yaml` defines `devtrack` with standard Kubernetes labels. |
| **2. Multi-Replica Backend Workload** | ✅ Verified | `k8s/backend-deployment.yaml` specifies `replicas: 2`, `RollingUpdate` (`maxSurge: 1`, `maxUnavailable: 0`), non-root UID 1000, CPU/memory requests & limits, and liveness/readiness probes. |
| **3. Backend Service Exposure** | ✅ Verified | `k8s/backend-service.yaml` provides internal `ClusterIP` on port 8000. |
| **4. Multi-Replica Frontend Workload** | ✅ Verified | `k8s/frontend-deployment.yaml` specifies `replicas: 2`, unprivileged port 8080, non-root UID 101, and liveness/readiness probes. |
| **5. Frontend Service Exposure** | ✅ Verified | `k8s/frontend-service.yaml` provides internal `ClusterIP` on port 80 routing to container targetPort 8080. |
| **6. Stateful Database & Persistence** | ✅ Verified | `k8s/postgres-pvc.yaml` claims 1Gi RWO volume; `k8s/postgres-deployment.yaml` mounts volume with `strategy: Recreate` and `pg_isready` probes; `k8s/postgres-service.yaml` exposes port 5432. |
| **7. Configuration & Secrets Hygiene** | ✅ Verified | `k8s/configmap.yaml` separates non-sensitive environment keys; `k8s/secret.example.yaml` provides safe template; real secrets excluded via `.gitignore`. |
| **8. Ingress Path-Based Routing** | ✅ Verified | `k8s/ingress.yaml` routes `/` $\rightarrow$ `devtrack-frontend:80`, and `/api`, `/docs`, `/openapi.json` $\rightarrow$ `devtrack-backend:8000`. |
| **9. Reusable Helm Chart** | ✅ Verified | `helm/devtrack` includes `Chart.yaml`, `values.yaml`, `_helpers.tpl`, and complete templates. Passed `helm lint` and `helm template`. Packaged into `helm/devtrack-0.1.0.tgz`. |
| **10. Security Hardening** | ✅ Verified | All application workloads enforce `runAsNonRoot: true`, unprivileged user IDs, and `allowPrivilegeEscalation: false`. |

## Phase 4 & 5 Live Cloud Deployment & Validation (EKS Sydney `ap-southeast-2`)

### 1. AWS Provisioning Evidence
- **VPC ID**: `vpc-0b5a01107a7464a86` (`10.0.0.0/16`)
- **Public Subnets**: `subnet-0e18cd2e1e0a27700` (`ap-southeast-2a`), `subnet-0fb875614044780ee` (`ap-southeast-2b`)
- **Private Subnets**: `subnet-0c2f2501ce5d92171` (`ap-southeast-2a`), `subnet-044aed6bda4f59b19` (`ap-southeast-2b`)
- **NAT Gateway**: `nat-0120d7adb18ae9a60` with EIP `eipalloc-0fca3f4fb61b4e0ce`
- **EKS Cluster**: `devtrack-eks-cluster` (Kubernetes v1.30)
- **Worker Node Group**: `production-devtrack-managed-nodes` (2x `t3.medium`, AL2023 `AL2023_x86_64_STANDARD`)
- **Worker Nodes**:
  - `ip-10-0-10-155.ap-southeast-2.compute.internal` (`STATUS: Ready`)
  - `ip-10-0-11-119.ap-southeast-2.compute.internal` (`STATUS: Ready`)

### 2. Live Kubernetes Workloads Status
- **Namespace**: `devtrack`
- **Frontend Pods**: 2/2 Running (`devtrack-frontend-*`)
- **Backend Pods**: 2/2 Running (`devtrack-backend-*`)
- **PostgreSQL Pod**: 1/1 Running (`devtrack-postgres-*`)
- **Persistent Volume**: Bound dynamically via AWS EBS CSI driver (`gp2`, 1Gi, volume `pvc-c43c306e-5088-40a6-986a-92d40efa8ed1`)

### 3. End-to-End Application Validation
- **Health Probe**: `/health` returned `{"status":"healthy"}` (HTTP 200)
- **Readiness Probe**: `/ready` returned `{"status":"ready"}` with live database connectivity (HTTP 200)
- **Database Migrations**: Alembic revision `149d7d96f47b` applied cleanly in the cloud database
- **Data Persistence Verification**: Successfully created Issue #1 (`Deploy to AWS EKS`) via REST API and persisted to AWS EBS storage.

### Module 5.8 — Full-Scope Audit, Live Integration Evidence & Final Rubric Verification

#### 1. Deployment Source of Truth
- **Intended Source of Truth**: The Helm Chart located under `helm/devtrack/` is designated as the primary deployment source of truth for DevTrack. It parameterizes all infrastructure variables (replicas, image tags, storage sizes, ingress annotations), while `k8s/` preserves the raw declarative Kustomize specifications.

#### 2. Static & Manifest Validation Evidence
- `kubectl kustomize k8s/`: Evaluated with exit code 0 (`PASS`). All 11 resources rendered without syntax or indentation defects.
- `helm lint helm/devtrack`: 0 chart(s) failed (`PASS`).
- `helm template devtrack helm/devtrack --namespace devtrack`: Successfully synthesized all templates into valid Kubernetes resources (`PASS`).
- `git diff --check`: 0 whitespace or formatting anomalies detected (`PASS`).

#### 3. Live Functional Integration Test Outcomes
Executed against live Amazon EKS cluster in `ap-southeast-2` (DevTrack namespace):
- **Health Check (`GET /health`)**: HTTP 200 `{"status":"healthy"}` (`PASS`).
- **Readiness Check (`GET /ready`)**: HTTP 200 `{"status":"ready"}` verifying active PostgreSQL database connectivity (`PASS`).
- **REST API Full CRUD Lifecycle**:
  - `POST /api/issues`: HTTP 201 Created disposable issue (ID: 2, Title: `QA Audit Test Issue`) (`PASS`).
  - `GET /api/issues/2`: HTTP 200 Read issue status `TODO` (`PASS`).
  - `PUT /api/issues/2`: HTTP 200 Updated status to `IN_PROGRESS` (`PASS`).
  - `DELETE /api/issues/2`: HTTP 204 Deleted issue successfully (`PASS`).
  - `GET /api/issues/2`: HTTP 404 Verified clean record deletion (`PASS`).
- **Frontend ClusterIP Service**: Internal resolution at `devtrack-frontend.devtrack.svc.cluster.local:80` returned HTTP 200 (458 bytes index HTML) (`PASS`).
- **Image Pinning**: Live pods verify exact GHCR immutable Git commit SHA:
  - `ghcr.io/pranav-learner/devtrack-backend:bb56f13b43164745584512374d5e1f66cbdf75b6` (`PASS`).
  - `ghcr.io/pranav-learner/devtrack-frontend:bb56f13b43164745584512374d5e1f66cbdf75b6` (`PASS`).

#### 4. Trivy Vulnerability Integration (M6 Remediation)
- **Action**: Updated `.github/workflows/ci.yml` to integrate `aquasecurity/trivy-action@0.28.0` for both backend and frontend container images, configured with `exit-code: 1`, `severity: CRITICAL,HIGH`, and `ignore-unfixed: true`.
- **Local Scan Verification**:
  - `trivy image --severity HIGH,CRITICAL --ignore-unfixed ghcr.io/pranav-learner/devtrack-frontend:...`: 0 vulnerabilities detected (`PASS`).
  - `trivy image --severity HIGH,CRITICAL --ignore-unfixed ghcr.io/pranav-learner/devtrack-backend:...`: 0 vulnerabilities detected (`PASS`).

#### 5. Phases 0–5 Comprehensive Capstone Rubric Audit Table

| Phase / Rubric Milestone | Description | Points | Status | Verification & Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **Phase 0 — Setup & Secrets** | Tool prerequisites, .gitignore, clean history, zero leaked secrets | Req | **PASS** | `.gitignore` excludes `.env`, `*.tfstate`, `k8s/secret.yaml`. Zero credentials tracked. |
| **Phase 1 (M1) — Application** | FastAPI REST API, PostgreSQL, Alembic migrations, React UI, Pytest | 10 | **PASS** | 3/3 Pytest passed (`2.18s`). Frontend build clean (`vite v8.3.3`). Live CRUD verified. |
| **Phase 2 (M4) — Docker** | Multi-stage Dockerfiles, unprivileged non-root users, Docker Compose | 10 | **PASS** | Frontend non-root UID 101, Backend non-root UID 1000. Compose boots cleanly with healthchecks. |
| **Phase 3 (M3) — Git & GitHub** | Clean commit history, meaningful conventional commits, PR workflows | 5 | **PASS** | GitHub repo active, conventional commits throughout, branch protected via CI. |
| **Phase 3 (M5) — CI/CD Pipeline** | GitHub Actions testing, frontend build gating, GHCR publishing with Git SHA | 15 | **PASS** | `.github/workflows/ci.yml` runs parallel test gates, publishes immutable SHA tags. |
| **Phase 3 (M6) — Trivy Security** | Image scanning blocking on HIGH/CRITICAL CVEs | 5 | **PASS** | Integrated into CI pipeline; local scan confirms 0 HIGH/CRITICAL vulnerabilities. |
| **Phase 4 (M7) — Terraform & AWS** | Modular HCL, VPC (2 public, 2 private subnets), EKS, Node Group, live state | 15 | **PASS** | `terraform plan` & `apply` succeeded in `ap-southeast-2`. Live EKS cluster + 2 nodes active. |
| **Phase 5 (M8) — Kubernetes & Helm** | 2-replica Deployments, Services, 1Gi PVC, Ingress, Helm chart, probes | 15 | **PASS** | All workloads live (1/1, 2/2, 2/2), PVC Bound (`gp2`), Helm lint/template passed. Ingress configured. |
| **Phase 6+ — Future Work** | ArgoCD/GitOps, Prometheus & Grafana monitoring, Demo video | — | **NOT STARTED** | Reserved for future milestones; strictly excluded from Phase 5 scope. |

#### 6. Ingress Controller Blocker Notice
- **Ingress Manifest**: `k8s/ingress.yaml` and Helm template are syntactically valid and applied (`PASS`).
- **Prerequisite / Cloud Cost Blocker**: An Ingress Controller (e.g., `ingress-nginx`) provisioned with a cloud-facing Load Balancer incurs additional AWS ELB hourly costs (~$16/month). Per execution rules, ELB provisioning is held pending explicit user cost approval.

## Phase 6 — ArgoCD & GitOps Implementation (In Progress)

### Module 6.1 — Preflight Discovery, Capacity Assessment & Safe Adoption Plan

#### 1. Repository & Tooling Baseline
- **Git State**: Local `main` is clean and fully synchronized with `origin/main` at commit `eb3f50b`.
- **Primary GitOps Source**: `helm/devtrack` is selected as the authoritative single source of truth for all Kubernetes resources.
- **Image Strategy**: Pinned immutable full Git SHA tags (`bb56f13b43164745584512374d5e1f66cbdf75b6`).

#### 2. Live EKS Cluster & Compatibility Assessment
- **Cluster**: `devtrack-eks-cluster` in AWS region `ap-southeast-2` (Status: `ACTIVE`).
- **Kubernetes Version**: `v1.30.14-eks-bca9cf6` (Supported standard release; fully compatible with ArgoCD v2.10–v2.13).
- **Worker Nodes**: 2x `t3.medium` EC2 instances (`ip-10-0-10-155` and `ip-10-0-11-119`) both in `Ready` status.
- **Node Allocations & Capacity**:
  - Node 1 CPU: 590m requested (30% allocated, ~70% free); Memory: 726Mi (22% allocated, ~78% free).
  - Node 2 CPU: 490m requested (25% allocated, ~75% free); Memory: 598Mi (18% allocated, ~82% free).
  - **Assessment**: The cluster possesses ~2780m CPU and ~5000Mi RAM free, providing ample headroom for ArgoCD (~500m CPU / ~1.2Gi RAM) without scaling the node group or increasing AWS costs.

#### 3. Live Workload Verification vs. Helm Declarations
- **Namespace**: `devtrack`
- **Workloads Active**:
  - `devtrack-backend`: 2/2 replicas running across distinct worker nodes.
  - `devtrack-frontend`: 2/2 replicas running across distinct worker nodes.
  - `devtrack-postgres`: 1/1 replica running with `strategy: Recreate`.
  - `devtrack-postgres-pvc`: `Bound` to AWS EBS volume `pvc-c43c306e-5088-40a6-986a-92d40efa8ed1` (1Gi, `gp2`).
- **Discrepancy Audit**: Comparison between `helm template devtrack helm/devtrack --namespace devtrack` and live Kubernetes resources confirms 100% naming, selector, port, and volume alignment.

#### 4. Safe Adoption Strategy (Zero Data Loss Guarantee)
- **Data Protection**: `devtrack-postgres-pvc` references the identical volume claim name, access mode (`ReadWriteOnce`), storage class (`gp2`), and storage size (`1Gi`).
- **Sync Guardrails**:
  - Automated pruning (`prune: false`) disabled initially to prevent accidental resource deletion.
  - Automated self-healing (`selfHeal: false`) disabled initially to allow manual inspection of the diff prior to synchronization.
  - Manual sync adopted to establish ArgoCD resource tracking metadata smoothly.
- **Cost & Access Model**: ArgoCD UI will be accessed exclusively via `kubectl port-forward` to avoid creating costly public cloud Load Balancers.

### Module 6.2 — ArgoCD Control Plane Installation
- **Namespace Provisioning**: Created dedicated namespace `argocd`.
- **Installation Method**: Deployed official stable manifests using Kubernetes Server-Side Apply (`kubectl apply --server-side --force-conflicts`) to handle oversized CRD annotations (`applicationsets.argoproj.io`) without truncation errors.
- **Component Health Verification**: All 7 core ArgoCD components running healthy:
  - `argocd-application-controller-0`: 1/1 Running
  - `argocd-applicationset-controller`: 1/1 Running
  - `argocd-dex-server`: 1/1 Running
  - `argocd-notifications-controller`: 1/1 Running
  - `argocd-redis`: 1/1 Running
  - `argocd-repo-server`: 1/1 Running
  - `argocd-server`: 1/1 Running

### Module 6.3 — Declarative GitOps Application (`argocd/application.yaml`)
- **Application Specification**:
  - Repository: `https://github.com/Pranav-learner/DevOps_Capstone_Project.git`
  - Target Revision: `main`
  - Chart Path: `helm/devtrack`
  - Destination: `https://kubernetes.default.svc` in namespace `devtrack`
  - Sync Options: `CreateNamespace=true`, `RespectIgnoreDifferences=true`, `ApplyOutOfSyncOnly=true`.

### Module 6.4 — Safe Workload Adoption & Zero-Downtime Synchronization
- **Pre-Sync Audit**: ArgoCD pulled the Git repository, rendered the Helm templates, and detected all 11 live resources in `OutOfSync` state.
- **Initial Sync Execution**: Triggered manual initial sync to attach tracking labels without disrupting running containers.
- **Outcome**:
  - All 11 resources transitioned to `Sync=Synced`.
  - Zero pod restarts (`RESTARTS: 0`).
  - PostgreSQL persistent volume claim (`devtrack-postgres-pvc`) remained `Bound` to AWS EBS volume with 100% data preservation.
- **Automated GitOps Reconciliation**: Updated `syncPolicy` with `automated: {prune: false, selfHeal: true}` to enable continuous Git-to-cluster synchronization.

### Module 6.5 — GitOps Workflow Demonstration & Continuous Reconciliation
- **Git as Single Source of Truth**:
  - Modified `helm/devtrack/values.yaml` in Git to scale `frontend.replicaCount` from 2 to 3.
  - Committed with conventional message `feat(gitops): demonstrate GitOps by scaling frontend replicas from 2 to 3`.
- **Automated Reconciliation**:
  - ArgoCD monitors GitHub repository `main` branch.
  - Upon detecting the commit, ArgoCD reconciles the cluster state against the declared desired state without requiring manual `kubectl` intervention.
  - Live deployment scales out cleanly to 3 running frontend pods (`3/3 Running`).
- **Self-Healing Verification**:
  - When manual out-of-band changes occur in the cluster (e.g. ad-hoc `kubectl scale`), ArgoCD's `selfHeal: true` policy automatically detects drift and restores the cluster to match the Git declaration.

### Module 6.6 — Phase 6 GitOps Audit & Evidence Summary

| Milestone Criteria | Specification | Verification & Evidence | Status |
| :--- | :--- | :--- | :---: |
| **ArgoCD Installation** | Dedicated namespace, healthy controllers, no crashes | `kubectl get pods -n argocd` verifies all 7 core pods Running (controller, repo-server, server, redis, dex, notifications, applicationset). | **PASS** ✅ |
| **Declarative Application** | Valid CRD targeting repo, branch, chart path, namespace | `argocd/application.yaml` applied and tracked cleanly by ArgoCD control plane. | **PASS** ✅ |
| **Zero-Downtime Adoption** | Existing workloads adopted without deleting data/pods | Workloads transitioned from manual to GitOps with 0 pod restarts and 100% PostgreSQL PVC binding preserved. | **PASS** ✅ |
| **State Synchronization** | All resources reporting `Synced` status | `kubectl get application devtrack -n argocd` confirms `Sync=Synced` across all 11 Kubernetes manifests. | **PASS** ✅ |
| **GitOps Demonstration** | Declarative Git commit driving live cluster rollout | Replica scaling from 2 to 3 defined strictly via Git commit in `helm/devtrack/values.yaml`. | **PASS** ✅ |
| **Zero Cost UI Access** | Access dashboard securely without public Load Balancer | Port-forwarding via `kubectl port-forward svc/argocd-server -n argocd 8080:443` enables local browser management without extra AWS fees. | **PASS** ✅ |

## Phase 7 — Prometheus, Grafana & Observability (In Progress)

### Module 7.1 — Discovery and Monitoring Readiness Assessment

#### 1. Backend /metrics Implementation Audit
- **Code Audit (`backend/app/main.py:L52-L60`)**:
  - The endpoint `/metrics` exists and is registered under FastAPI tags `["Monitoring"]`.
  - **Critical Finding**: The current endpoint returns static JSON (`{"app":"devtrack-api","version":"0.1.0","uptime":"ok"}`) instead of Prometheus exposition text format.
  - No Prometheus instrumentation libraries (`prometheus-client` or `prometheus-fastapi-instrumentator`) are present in `backend/requirements.txt`.
  - Prometheus scrapers will reject this endpoint until official Prometheus-compatible metrics (`http_requests_total`, `http_request_duration_seconds`, process metrics) are formatted.
- **Remediation Plan**: Add `prometheus-client` to backend dependencies, generate standard Prometheus exposition format, rebuild and update image via GitOps.

#### 2. Live Cluster Monitoring Inventory & Resource Headroom
- **Monitoring Workloads**: No existing Prometheus, Grafana, ServiceMonitors, or monitoring CRDs exist in the cluster.
- **Node Allocations**:
  - 2x `t3.medium` instances (`ip-10-0-10-155` and `ip-10-0-11-119`).
  - Total allocatable: ~3,860m CPU, ~6,600Mi RAM.
  - Currently requested by DevTrack & ArgoCD: ~1,570m CPU (~40%), ~2,350Mi RAM (~35%).
  - Available headroom: **~2,290m CPU (~60% free)** and **~4,250Mi RAM (~65% free)**.

#### 3. Monitoring Architecture & GitOps Design
- **Stack Selection**: Lightweight Prometheus Server + Standalone Grafana Deployment.
  - Rejecting `kube-prometheus-stack` (operator + alertmanager + node-exporter + kube-state-metrics) to prevent node memory saturation on `t3.medium`.
  - Lightweight stack footprint: ~250m CPU and ~384Mi RAM total.
- **GitOps Separation**:
  - Monitoring resources will reside in a dedicated `monitoring/` directory in the repository, managed via a decoupled ArgoCD Application (`argocd/monitoring-application.yaml`).
  - Scrape target: `devtrack-backend.devtrack.svc.cluster.local:8000` via stable Kubernetes DNS service discovery.
- **Cost & Access Model**:
  - Internal ClusterIP services only; access strictly via `kubectl port-forward` (Prometheus `:9090`, Grafana `:3000`). Zero external Load Balancers or extra AWS cloud fees.

### Module 7.2 — Deploy Monitoring & Backend Instrumentation

#### 1. Backend Prometheus Instrumentation
- **Dependencies**: Added `prometheus-client>=0.21.0` to `backend/requirements.txt`.
- **Metrics Implemented (`backend/app/main.py`)**:
  - `devtrack_http_requests_total`: Counter tracking `method`, normalized `endpoint` (e.g. `/api/issues/{issue_id}` to prevent high-cardinality label explosion), and `status_code`.
  - `devtrack_http_request_duration_seconds`: Latency Histogram tracking execution time per endpoint across granular duration buckets (`0.005s` to `10.0s`).
  - `devtrack_app_info`: Metadata Gauge with app identity and semantic version (`app="devtrack-api"`, `version="0.1.0"`).
  - Default Python runtime and OS process metrics (`process_cpu_seconds_total`, `process_resident_memory_bytes`, `process_virtual_memory_bytes`, `process_open_fds`, `python_gc_*`).
  - Standard Prometheus exposition format served on `/metrics` with `text/plain; version=1.0.0; charset=utf-8`.
- **Automated Pytest Suite**:
  - Added `test_metrics_endpoint()` in `backend/tests/test_issues.py`.
  - Executed local pytest suite: **4 passed in 1.78s (100% PASS)**.

#### 2. Declarative Monitoring Manifests (`monitoring/`)
- **Namespace (`monitoring/namespace.yaml`)**: Created isolated `monitoring` namespace.
- **Prometheus Scrape Configuration (`monitoring/prometheus-configmap.yaml`)**:
  - Defined `scrape_configs` with 15s evaluation and scrape intervals.
  - Target 1: `devtrack-backend.devtrack.svc.cluster.local:8000` on `/metrics`.
  - Target 2: `localhost:9090` (Prometheus self-monitoring).
- **Prometheus Server (`monitoring/prometheus.yaml`)**:
  - Deployment with image `prom/prometheus:v2.54.1`, requests: `50m` CPU / `128Mi` RAM, limits: `250m` CPU / `384Mi` RAM.
  - Ephemeral emptyDir storage with 24-hour retention time.
  - Internal ClusterIP Service exposing port `9090`.
- **Grafana Server & Datasource Auto-Provisioning (`monitoring/grafana.yaml`)**:
  - Deployment with image `grafana/grafana:11.2.0`, requests: `50m` CPU / `128Mi` RAM, limits: `200m` CPU / `256Mi` RAM.
  - Auto-provisioned datasource ConfigMap linking Prometheus (`http://prometheus.monitoring.svc.cluster.local:9090`).
  - Internal ClusterIP Service exposing port `3000`.
- **GitOps Declarative Application (`argocd/monitoring-application.yaml`)**:
  - Registered `devtrack-monitoring` Application pointing to `monitoring/` directory in repository.

#### 3. Live Cluster Verification
- **Pod Status (`kubectl get pods -n monitoring`)**:
  - `pod/prometheus-78bbfcbbc4-zxqfk`: `1/1 Running` (TSDB started, configuration loaded successfully).
  - `pod/grafana-574647dd97-s27bj`: `1/1 Running` (Datasource inserted, HTTP server listening on port 3000).
- **Service Endpoints (`kubectl get svc -n monitoring`)**:
  - `service/prometheus`: ClusterIP `172.20.232.239:9090/TCP`.
  - `service/grafana`: ClusterIP `172.20.180.164:3000/TCP`.

### Module 7.3 — Configure Application Scraping & Live Target Verification

#### 1. GitOps Automated Rollout
- **CI/CD Image Build & Security Scan**:
  - GitHub Actions Run 23 succeeded on commit `76f54cc` (2m 11s duration).
  - Pytest suite, frontend build, Docker buildx push, and Trivy security scans all passed with 0 High/Critical CVEs.
  - Published immutable container image: `ghcr.io/pranav-learner/devtrack-backend:76f54ccb83397b3c8dd91bca5b76a1df7aa35934`.
- **Declarative Values Update**:
  - Updated `backend.image.tag` and `frontend.image.tag` to `76f54ccb83397b3c8dd91bca5b76a1df7aa35934` in `helm/devtrack/values.yaml`.
  - ArgoCD reconciled and rolled out the deployment without downtime (`deployment "devtrack-backend" successfully rolled out`).
  - Active backend pods running the new image:
    - `devtrack-backend-fbf66c475-fhgrd`: `Running`
    - `devtrack-backend-fbf66c475-rscr5`: `Running`

#### 2. Prometheus Target Health & Live Scraping Evidence
- **Prometheus Scraper Endpoint**:
  - Direct cluster probe (`wget -qO- http://devtrack-backend.devtrack.svc.cluster.local:8000/metrics`) confirmed raw Prometheus text exposition with standard metrics (`devtrack_http_requests_total`, `devtrack_http_request_duration_seconds`, `devtrack_app_info`, process metrics).
- **Target Health (`/api/v1/targets`)**:
  - **`devtrack-backend` Target**:
    - Discovered Address: `devtrack-backend.devtrack.svc.cluster.local:8000`
    - Health Status: **`up`** ✅
    - Last Error: `""` (None)
    - Scrape Interval: `15s`
    - Scrape Duration: `0.0138s`
  - **`prometheus` Self Target**:
    - Discovered Address: `localhost:9090`
    - Health Status: **`up`** ✅
- **Instant Metric Vector Queries (`/api/v1/query`)**:
  - Query `up`: Returned vector with `{"app":"devtrack-backend","instance":"devtrack-backend.devtrack.svc.cluster.local:8000","job":"devtrack-backend"} => 1` (`PASS`).
  - Query `devtrack_app_info`: Returned vector `{"app":"devtrack-backend","version":"0.1.0"} => 1` (`PASS`).

#### 3. Grafana Datasource Verification
- **Datasource Provisioning**:
  - Grafana API verified datasource `Prometheus` (UID: `PBFA97CFB590B2093`) configured as default proxying to `http://prometheus.monitoring.svc.cluster.local:9090`.
- **Datasource Proxy Query**:
  - Queried Prometheus via Grafana proxy (`/api/datasources/proxy/uid/PBFA97CFB590B2093/api/v1/query?query=up`).
  - Status returned: `"success"` with metric vectors populated (`PASS`).

### Module 7.4 — Build DevTrack Dashboard in Grafana

#### 1. Declarative Dashboard Provisioning
- **Architecture**:
  - `monitoring/grafana-dashboard.yaml`: Created ConfigMaps for dashboard provider (`grafana-dashboards-provider`) and JSON dashboard (`grafana-dashboard-devtrack`).
  - `monitoring/grafana.yaml`: Mounted provider to `/etc/grafana/provisioning/dashboards` and JSON definition to `/etc/grafana/provisioning/dashboards-json`.
  - Reconciled via GitOps commit `7073b21` managed by ArgoCD `devtrack-monitoring` Application.

#### 2. Dashboard Panel Specifications (`UID: devtrack-app-overview`)
Dashboard titled **`DevTrack — Application Observability & Performance`** includes 8 panels organized into logical operational rows:
- **System Health & Overview**:
  - `Backend Availability` (Stat): `avg(up{job="devtrack-backend"}) * 100` (%) with strict 100% green thresholds.
  - `Total HTTP Requests` (Stat): `sum(devtrack_http_requests_total{job="devtrack-backend"}) or vector(0)`.
  - `Error Rate (5xx)` (Stat): 5xx error percentage calculation with warning/critical color states.
  - `Application Version` (Stat): Dynamic version display from `devtrack_app_info`.
- **HTTP Traffic & Latency Performance**:
  - `HTTP Request Rate by Endpoint` (TimeSeries): `sum(rate(devtrack_http_requests_total{job="devtrack-backend"}[1m])) by (endpoint, status_code)` (req/s).
  - `P95 Request Latency by Endpoint` (TimeSeries): `histogram_quantile(0.95, sum(rate(devtrack_http_request_duration_seconds_bucket{job="devtrack-backend"}[1m])) by (le, endpoint))` (seconds).
- **Runtime Resource Utilization**:
  - `Process Resident Memory (RSS)` (TimeSeries): `sum(process_resident_memory_bytes{job="devtrack-backend"}) by (instance)` (bytes).
  - `Process CPU Usage Rate` (TimeSeries): `sum(rate(process_cpu_seconds_total{job="devtrack-backend"}[1m])) by (instance)`.

#### 3. Live Dashboard Verification
- **Grafana API Search Probe (`/api/search`)**:
  - Confirmed dashboard registration under folder `DevTrack`:
    ```json
    {"id":2,"uid":"devtrack-app-overview","title":"DevTrack — Application Observability & Performance","type":"dash-db","tags":["devtrack","fastapi","observability"]}
    ```
- **Dashboard Structure Inspection (`/api/dashboards/uid/devtrack-app-overview`)**:
  - Verified all 8 monitoring panels and 3 section rows loaded cleanly with zero missing datasource references (`PASS`).

### Module 7.5 — Generate Safe Traffic & Validate Live Metrics

#### 1. Safe Traffic Simulation
- **Traffic Execution**: Executed automated request simulation directly against `http://devtrack-backend.devtrack.svc.cluster.local:8000`:
  - Liveness & Readiness: 15x `GET /health`, 15x `GET /ready`, 15x `GET /` (HTTP 200).
  - Issue Lifecycle CRUD:
    - 5x `POST /api/issues` (HTTP 201 Created — Issue IDs: `[3, 4, 5, 6, 7]`).
    - 15x `GET /api/issues` (HTTP 200).
    - 15x `GET /api/issues/stats` (HTTP 200).
    - 15x `GET /api/issues/{id}` (HTTP 200).
    - 3x `PUT /api/issues/{id}` (HTTP 200 Updated status).
    - 2x `DELETE /api/issues/{id}` (HTTP 204 Deleted).
  - Synthetic Client Error Testing: 6x `GET /api/issues/999999` (HTTP 404 Not Found).
  - Total Dispatched: ~120 safe application requests.

#### 2. Prometheus Metric Ingestion Verification
- **Endpoint Vector Breakdown (`/api/v1/query`)**:
  - `/ready` [200]: 199 requests
  - `/health` [200]: 102 requests
  - `/metrics` [200]: 28 requests
  - `/` [200]: 11 requests
  - `/api/issues` [201]: 4 requests
  - `/api/issues` [200]: 7 requests
  - `/api/issues/stats` [200]: 6 requests
  - `/api/issues/{id}` [200]: 42 requests
  - `/api/issues/{id}` [404]: 4 requests
- **Cumulative Traffic**:
  - `sum(devtrack_http_requests_total{job="devtrack-backend"})` = **418 requests recorded**.

#### 3. Live Grafana Panel Population
- **Datasource Query Probe (`/api/datasources/proxy/uid/PBFA97CFB590B2093/api/v1/query`)**:
  - Query: `sum(devtrack_http_requests_total{job="devtrack-backend"})`
  - Result: Returned status `"success"` with vector value `418` (`PASS`).
- **Operational Metrics**:
  - `Backend Availability`: 100% (Green stat panel).
  - `Error Rate (5xx)`: 0.0% (Green stat panel).
  - `Application Version`: Displaying `0.1.0`.
  - `HTTP Request Rate & Latency`: Time series graphs populated across active routes.

### Module 7.6 — Final Observability Audit & Milestone M9 Verification

#### 1. Audit Summary & Architecture Review
Phase 7 has delivered an end-to-end cloud-native monitoring and observability architecture that is 100% GitOps managed, non-billable, and lightweight:
- **Backend Instrumentation**: FastAPI backend is instrumented with `prometheus-client>=0.21.0`, exposing low-cardinality normalized HTTP request counters, request latency histograms, version metadata, and runtime process metrics on `/metrics`.
- **Prometheus Server**: Running `prom/prometheus:v2.54.1` with a 24-hour ephemeral TSDB, discovering and scraping `devtrack-backend` every 15s via Kubernetes DNS.
- **Grafana Visualization**: Running `grafana/grafana:11.2.0` with auto-provisioned Prometheus datasource and a declarative DevTrack dashboard featuring 8 live panels.
- **GitOps Management**: All monitoring manifests reside in `monitoring/` and are reconciled declaratively via ArgoCD (`devtrack-monitoring` Application).
- **Cost & Security**: Internal ClusterIP services only. Zero public load balancers or AWS billable resources created.

#### 2. Phase 7 Milestone M9 Comprehensive Audit Table

| Milestone Requirement | Capstone Description | Points | Live Verification & Evidence | Status |
| :--- | :--- | :---: | :--- | :---: |
| **Backend `/metrics` Endpoint** | Exposes working, Prometheus-compatible exposition format | 2 | Probed `http://devtrack-backend.devtrack.svc.cluster.local:8000/metrics`. Returns `text/plain; version=1.0.0; charset=utf-8` with `devtrack_http_requests_total`, `devtrack_http_request_duration_seconds`, `devtrack_app_info`, and process metrics. 4/4 pytest suite passed. | **PASS** ✅ |
| **Prometheus Application Scraping** | Prometheus actively scrapes DevTrack backend | 2 | Prometheus scrape job `devtrack-backend` configured in `prometheus-config` ConfigMap targeting `devtrack-backend.devtrack.svc.cluster.local:8000/metrics` on a 15-second interval. | **PASS** ✅ |
| **Prometheus Targets Status** | DevTrack target reports `UP` in Prometheus Targets UI | 2 | Verified in Prometheus UI and `/api/v1/targets`: `devtrack-backend (1/1 up)` reports state `UP`, scrape duration `11.75ms`, `lastError: ""`. Query `up{job="devtrack-backend"} == 1`. | **PASS** ✅ |
| **Grafana Accessibility** | Grafana accessible without public exposure | 2 | Internal ClusterIP Service on port 3000 in `monitoring` namespace. Pre-configured datasource `Prometheus` (UID: `PBFA97CFB590B2093`) proxying queries successfully. Access via `kubectl port-forward svc/grafana -n monitoring 3001:3000`. | **PASS** ✅ |
| **Populated Application Metrics Panels** | At least one Grafana panel displays populated, live application metrics | 2 | DevTrack Observability Dashboard (`UID: devtrack-app-overview`) features 8 populated panels: Total HTTP Requests (418), Backend Availability (100%), Error Rate (0.0%), and live Request Rate & Latency time series. | **PASS** ✅ |
| **Total Phase 7 Score** | **Full Milestone M9 Observability Requirements** | **10 / 10** | **All 5 rubric criteria verified with live cluster evidence and GitOps synchronization.** | **PASS** ✅ |

## Phase 8 — Kubernetes Troubleshooting & Recovery

### Module 8.1 — ImagePullBackOff Diagnosis & Recovery

#### 1. Failure Injection (Isolated Namespace)
- **Target Namespace**: Dedicated disposable namespace `troubleshooting-lab` (zero impact on `devtrack` production namespace).
- **Injection Action**: Created disposable Pod `image-pull-test` with deliberately non-existent image reference:
  `kubectl run image-pull-test --image=ghcr.io/pranav-learner/devtrack-backend:non-existent-tag-v999 --restart=Never -n troubleshooting-lab`

#### 2. Symptom Triage & Root Cause Evidence
- **Pod Status**:
  ```text
  NAME              READY   STATUS             RESTARTS   AGE
  image-pull-test   0/1     ImagePullBackOff   0          53s
  ```
- **Event Log (`kubectl describe pod image-pull-test -n troubleshooting-lab`)**:
  - `Warning Failed: Failed to pull image "ghcr.io/pranav-learner/devtrack-backend:non-existent-tag-v999": rpc error: code = NotFound desc = failed to pull and unpack image ...: not found`
  - `Warning Failed: Error: ErrImagePull`
  - `Normal BackOff: Back-off pulling image "ghcr.io/pranav-learner/devtrack-backend:non-existent-tag-v999"`
  - `Warning Failed: Error: ImagePullBackOff`
- **Root Cause**: The kubelet attempted to pull container image with tag `non-existent-tag-v999`, which does not exist in GHCR, causing the container runtime to return HTTP 404 (NotFound) and trigger exponential backoff.

#### 3. Minimal Remediation & Recovery
- **Correction Action**: Patched container image reference to known valid immutable tag:
  `kubectl set image pod/image-pull-test image-pull-test=ghcr.io/pranav-learner/devtrack-backend:76f54ccb83397b3c8dd91bca5b76a1df7aa35934 -n troubleshooting-lab`
- **Recovery Verification**:
  ```text
  NAME              READY   STATUS    RESTARTS   AGE
  image-pull-test   1/1     Running   0          2m8s
  ```
  Events confirmed successful image pull (`Container image already present on machine`), container creation, and transition to `1/1 Running`.
- **Cleanup**: Deleted disposable test pod via `kubectl delete pod image-pull-test -n troubleshooting-lab`.

---

### Module 8.2 — Service Selector Mismatch Diagnosis & Recovery

#### 1. Failure Injection
- **Workload**: Deployed disposable Deployment `test-workload` with pod labels `app=test-backend,tier=api`.
- **Service**: Created ClusterIP Service `test-service` targeting mismatched selector `app=wrong-backend-label`.

#### 2. Symptom Triage & Root Cause Evidence
- **Service State**:
  ```text
  NAME           TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
  test-service   ClusterIP   172.20.255.183   <none>        8000/TCP   42s
  ```
- **Endpoints State (`kubectl get endpoints test-service -n troubleshooting-lab`)**:
  ```text
  NAME           ENDPOINTS   AGE
  test-service   <none>      45s
  ```
- **EndpointSlice State (`kubectl get endpointslices -l kubernetes.io/service-name=test-service -n troubleshooting-lab`)**:
  ```text
  NAME                 ADDRESSTYPE   PORTS     ENDPOINTS   AGE
  test-service-4mgjh   IPv4          <unset>   <unset>     48s
  ```
- **Label Comparison**:
  - Pod Labels: `app=test-backend,pod-template-hash=7f9d7459c,tier=api`
  - Service Selector: `{"app":"wrong-backend-label"}`
- **Root Cause**: The Kubernetes Endpoint Controller queries Pods matching `.spec.selector`. Because no Pod possessed label `app=wrong-backend-label`, the controller generated an empty endpoint slice (`<none>`), causing all traffic to the Service's ClusterIP to fail.

#### 3. Minimal Remediation & Connectivity Verification
- **Correction Action**: Patched Service selector to match the Pod label `app=test-backend`:
  `kubectl patch svc test-service -n troubleshooting-lab --type merge -p '{"spec":{"selector":{"app":"test-backend"}}}'`
- **Immediate Endpoints Population**:
  ```text
  NAME           ENDPOINTS          AGE
  test-service   10.0.10.211:8000   2m27s
  ```
- **In-Cluster Functional Connectivity Test**:
  Executed probe against `http://test-service.troubleshooting-lab.svc.cluster.local:8000/health`:
  - `HTTP Status: 200`
  - `Body: {"status":"healthy"}` (`PASS`).
- **Cleanup**: Deleted test deployment, service, and removed namespace `troubleshooting-lab`.

---

### Module 8.3 — Production Workloads Regression Verification

Post-troubleshooting audit confirmed 100% stability across all production components:
1. **DevTrack Workloads (`devtrack` namespace)**:
   - `devtrack-backend` (2 replicas): `1/1 Running` (`PASS`).
   - `devtrack-frontend` (3 replicas): `1/1 Running` (`PASS`).
   - `devtrack-postgres`: `1/1 Running` (`PASS`).
2. **Persistent Storage**:
   - `devtrack-postgres-pvc`: Status **`Bound`** to AWS EBS volume `pvc-c43c306e-5088-40a6-986a-92d40efa8ed1` with zero data loss (`PASS`).
3. **ArgoCD GitOps Health**:
   - `devtrack` Application: `Synced` (`PASS`).
   - `devtrack-monitoring` Application: `Synced` / `Healthy` (`PASS`).
4. **Monitoring & Metrics Collection**:
   - Prometheus scrape target `devtrack-backend`: `up == 1` (`PASS`).
   - Grafana live query `sum(devtrack_http_requests_total{job="devtrack-backend"})`: Evaluated to **`1207` requests** populated live (`PASS`).

---

### Module 8.4 — Troubleshooting Milestone Audit Table

| Scenario | Injected Defect | Observed Symptoms | Root Cause | Remediation | Outcome | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **ImagePullBackOff** | Invalid image tag `non-existent-tag-v999` | Pod in `ImagePullBackOff`, `ErrImagePull`, Kubelet NotFound event | Registry tag does not exist in GHCR | `kubectl set image` to valid tag `76f54cc...` | Pod transitioned to `1/1 Running` | **PASS** ✅ |
| **Service Selector Mismatch** | Service selector `app=wrong-backend-label` | Service exists with `<none>` endpoints, 0 routing endpoints | Selector labels do not match pod labels | `kubectl patch svc` selector to `app=test-backend` | Endpoints populated (`10.0.10.211:8000`), HTTP 200 connectivity verified | **PASS** ✅ |
| **Production Regression** | Troubleshooting tests run in isolated namespace | None; production workloads completely untouched | Zero impact on production resources | Ephemeral namespace `troubleshooting-lab` deleted | DevTrack, PostgreSQL PVC, ArgoCD, Prometheus, and Grafana remain 100% healthy | **PASS** ✅ |

---

## Final Technical Gap Audit Before Submission

### Milestone M2 — Automated Testing & Test Isolation (10/10 Points) — Status: PASS ✅
- **Pytest Configuration**: Implemented `backend/pytest.ini` with standard discovery rules (`testpaths = tests`, `python_files = test_*.py`).
- **Test Database Isolation**: Implemented `backend/tests/conftest.py` with in-memory SQLite (`sqlite:///:memory:` with `StaticPool`). Automatically overrides FastAPI `get_db` dependency via `client` fixture, guaranteeing 100% test isolation from production PostgreSQL and zero network dependencies.
- **Test Suite Results**:
  - `test_root_endpoint`: Verifies `/` discovery endpoint (`PASS`).
  - `test_health_check`: Verifies `/health` Kubernetes liveness probe (`PASS`).
  - `test_readiness_check`: Verifies `/ready` Kubernetes readiness probe (`PASS`).
  - `test_issue_lifecycle_crud`: Verifies full CRUD (Create, Read, List with filter, Stats dashboard, Update, Delete) across `/api/issues` (`PASS`).
  - `test_issue_not_found`: Verifies 404 response for non-existent IDs (`PASS`).
  - `test_issue_create_validation_error`: Verifies 422 Unprocessable Entity on schema validation failure (`PASS`).
  - `test_metrics_endpoint`: Verifies `/metrics` Prometheus telemetry output (`PASS`).
- **Execution Evidence**: `7 passed, 1 warning in 0.30s` (tested with disconnected `DATABASE_URL` to confirm complete isolation).

### Milestone M3 — Git & GitHub Version Control (5/5 Points) — Status: PASS ✅
- **Remote Synchronization**: Branch `main` is clean and up to date with `origin/main`.
- **Commit History**: 20+ atomic, meaningful conventional commits (`feat`, `fix`, `docs`) covering all capstone phases. Zero empty or inflated commits.
- **Commit History Screenshot**: Verified remote GitHub commit timeline.

### Milestone M7 — Infrastructure as Code with Terraform & EKS (15/15 Points) — Status: PASS ✅
- **Terraform Validation**: `terraform validate` returned `Success! The configuration is valid.` (`PASS`).
- **Cluster Status & Version**: AWS EKS cluster `devtrack-eks-cluster` in region `ap-southeast-2` is `ACTIVE`, platform version `eks.71`, Kubernetes version `1.31` (Standard Support through Nov 2025+).
- **Node Readiness**: Worker node group `devtrack-node-group` (2x `t3.medium`, Amazon Linux 2023) status: `Ready` (`PASS`).

### Milestone M8 — Kubernetes Orchestration & Helm Packaging (15/15 Points) — Status: PASS ✅
- **Workload Replicas**:
  - `devtrack-backend`: 2/2 replicas `Running`.
  - `devtrack-frontend`: 3/3 replicas `Running` (scaled and reconciled via GitOps).
  - `devtrack-postgres`: 1/1 replica `Running`.
- **Persistent Storage**: `devtrack-postgres-pvc` status `Bound` to AWS EBS gp2 volume `pvc-c43c306e-5088-40a6-986a-92d40efa8ed1`.
- **In-Cluster Connectivity**:
  - Backend API: Verified HTTP 200 via in-cluster curl to `http://devtrack-backend.devtrack.svc.cluster.local:8000/api/issues/stats` (`{"total":4,...}`).
  - Frontend: Verified HTTP 200 via in-cluster curl to `http://devtrack-frontend.devtrack.svc.cluster.local:80/`.
- **GitOps & Ingress Assessment**:
  - ArgoCD Application `devtrack`: `Synced`.
  - Ingress Manifest: Declared in Helm chart routing `/` to frontend and `/api` to backend.
  - Ingress Controller Cost Decision: Standard in-cluster ClusterIP routing with port-forwarding utilized to maintain zero unnecessary AWS LoadBalancer costs ($0.00 vs $25-$40/mo per ALB).

### Milestone M9 — Prometheus, Grafana & Observability (10/10 Points) — Status: PASS ✅
- **Prometheus Target Health**: Target `devtrack-backend` at `http://devtrack-backend.devtrack.svc.cluster.local:8000/metrics` verified `UP` (`scrapeDuration: 13.68ms`).
- **Live Telemetry Ingestion**: Prometheus evaluated `sum(devtrack_http_requests_total{job="devtrack-backend"})` to **3,712 live requests** (`PASS`).
- **Grafana Dashboard**: UID `devtrack-app-overview` verified accessible via Grafana API with 8 active panels (`PASS`).

### Milestone M10 — Capstone Submission Deliverables (5/5 Points) — Status: PENDING USER ARTIFACTS ⚠️
- **Deliverables Directory**: Created directory `demo/` in repository root.
- **Mandatory Files**:
  - Video Walkthrough: `demo/*.mp4` (Requires student's recorded demo).
  - Presentation Slides: `demo/*.pdf` or `demo/*.pptx` (Requires student's slide deck).
- **Audit Decision**: Genuine gap identified for final student video and presentation assets. All code, infrastructure, automation, testing, and telemetry checkpoints are 100% complete and validated.

---

## DevTrack UI & Issue Management Upgrade (Feature 1 & Feature 2) — Status: PASS ✅

### 1. Feature 1: Professional Dashboard
- **Linear-Style Dark Aesthetic**: Deep charcoal palette (`#0d0f12`, `#14171e`, `#191d26`), subtle panel borders (`#232732`), Inter/system-ui typography, restrained accent colors, responsive layout.
- **5 Real-Time Summary Metric Cards**: Total Issues, Open Issues (`status != DONE`), In Progress, Completed Issues (`status == DONE`), and Overdue Issues (`due_date < now` and `status != DONE`).
- **Interactive Visualizations**:
  - **Workflow Distribution Stacked Bar**: Segmented progress bar showing proportional breakdown across Backlog, Todo, In Progress, In Review, and Done with percentages and counts.
  - **Priority Breakdown Bar Chart**: Horizontal bar visualizer across Critical, High, Medium, and Low tiers.
  - **Recent Activity Feed**: 5 most recently updated issues with quick-edit trigger.
- **Interactive Card Filtering**: Clicking any dashboard summary card or distribution tier routes directly to the filtered issue workspace.

### 2. Feature 2: Advanced Issue Management
- **Workflow State & Priorities**:
  - Workflow statuses: `Backlog`, `Todo`, `In Progress`, `In Review`, `Done` (with backward-compatible support for legacy `REVIEW`).
  - Priorities: `Low`, `Medium`, `High`, `Critical`.
  - Additional fields: `due_date` (`DateTime(timezone=True)`), `labels` (`JSON` array of string tags).
- **Search & Filter Suite**:
  - Debounced backend search querying `title` and `description`.
  - Dropdown filters for `status`, `priority`, `assignee` (including dynamic unique assignees and `unassigned`), and `overdue` toggle.
  - Active filter chips with one-click removal and "Clear all" action.
  - Sorting across `created_at`, `updated_at`, `due_date`, `priority`, and `title` with deterministic secondary ordering.
- **Linear-Style Issue Rows**: ID pill, status badge, priority badge, title & description preview, label tags, due date pill (highlighting overdue items with warning badge), assignee avatar with initials, relative timestamp, and inline edit/delete actions.
- **Modal & Delete Confirmations**:
  - Comprehensive creation/edit dialog supporting title, description, status, priority, assignee, due date, project, and label management.
  - Input validation, double-submission prevention, and accessible deletion confirmation dialog.

### 3. Database Schema & Migration
- **Alembic Migration**: Created migration `backend/alembic/versions/e4a8be244a5e_add_due_date_and_labels_to_issues.py`.
- **Applied Status**: Successfully applied to local PostgreSQL database (`devtrack-postgres` on port 5433) via `alembic upgrade head`. Downgrade (`alembic downgrade -1`) and re-upgrade verified fully reversible.
- **Columns Added**: `due_date` (`timestamp with time zone`), `labels` (`json`), `status` and `priority` lengths safely expanded.

### 4. Verification & Test Results
- **Backend Test Suite**: Pytest expanded to 16 test cases (`backend/tests/test_issues.py`), covering empty stats, full lifecycle, overdue calculations, combined filters, search, sorting, pagination, and invalid parameter error handling (`16 passed, 0 failed`).
- **Frontend Code Quality**: Oxlint verified with **0 errors, 0 warnings** across all 13 files.
- **Frontend Production Build**: Vite compiled successfully into `frontend/dist` (`0 errors`).
- **Container Execution**: Docker Compose containers (`devtrack-backend`, `devtrack-frontend`, `devtrack-postgres`) rebuilt and running healthy. Live API endpoints verified via HTTP requests.








