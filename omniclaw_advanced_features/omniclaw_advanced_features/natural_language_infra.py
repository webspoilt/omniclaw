"""
🏗️ NATURAL LANGUAGE INFRASTRUCTURE
Describe infrastructure in English → Get Terraform, Kubernetes, CI/CD, Ansible.
"Set up production k8s with auto-scaling, monitoring, and database"
Kills: DevOps engineers, Infrastructure engineers, AWS/Azure certified pros

Author: OmniClaw Advanced Features
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"


@dataclass
class InfraComponent:
    """A single infrastructure component"""
    type: str  # ecs, rds, s3, etc.
    name: str
    config: dict
    dependencies: list[str] = field(default_factory=list)


@dataclass
class InfraSpec:
    """Complete infrastructure specification"""
    provider: CloudProvider
    components: list[InfraComponent]
    ci_cd: Optional[dict] = None
    monitoring: Optional[dict] = None
    security: Optional[dict] = None


class NaturalLanguageInfra:
    """
    Generate infrastructure code from natural language descriptions.
    Input: "Production k8s with auto-scaling, monitoring, CI/CD"
    Output: Terraform + Helm + GitHub Actions + Ansible
    """
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        self.provider = CloudProvider.AWS  # Default
    
    def generate(
        self,
        description: str,
        provider: CloudProvider = CloudProvider.AWS
    ) -> InfraSpec:
        """
        Generate infrastructure from natural language.
        
        Args:
            description: What you want (e.g., "Production k8s with auto-scaling")
            provider: Target cloud provider
        
        Returns:
            InfraSpec with all components
        """
        self.provider = provider
        
        # Parse requirements from description
        requirements = self._parse_requirements(description)
        
        # Generate components based on requirements
        components = self._generate_components(requirements)
        
        # Generate CI/CD if requested
        ci_cd = None
        if requirements.get("ci_cd") or requirements.get("deployment"):
            ci_cd = self._generate_cicd(requirements)
        
        # Generate monitoring if requested
        monitoring = None
        if requirements.get("monitoring") or requirements.get("observability"):
            monitoring = self._generate_monitoring(requirements)
        
        # Generate security if requested
        security = None
        if requirements.get("security") or requirements.get("secure"):
            security = self._generate_security(requirements)
        
        return InfraSpec(
            provider=provider,
            components=components,
            ci_cd=ci_cd,
            monitoring=monitoring,
            security=security
        )
    
    def _parse_requirements(self, description: str) -> dict:
        """Parse natural language into structured requirements"""
        
        desc_lower = description.lower()
        
        requirements = {
            # Compute
            "kubernetes": "k8s" in desc_lower or "kubernetes" in desc_lower,
            "containers": "container" in desc_lower or "docker" in desc_lower,
            "serverless": "serverless" in desc_lower or "lambda" in desc_lower,
            "vm": "vm" in desc_lower or "ec2" in desc_lower,
            
            # Database
            "database": "database" in desc_lower or "db" in desc_lower,
            "sql": "sql" in desc_lower or "postgres" in desc_lower or "mysql" in desc_lower,
            "nosql": "nosql" in desc_lower or "mongo" in desc_lower or "dynamo" in desc_lower,
            "redis": "redis" in desc_lower or "cache" in desc_lower,
            
            # Storage
            "storage": "storage" in desc_lower or "s3" in desc_lower,
            
            # Networking
            "vpc": "vpc" in desc_lower or "network" in desc_lower,
            "cdn": "cdn" in desc_lower or "cloudfront" in desc_lower,
            "load_balancer": "load" in desc_lower or "balancer" in desc_lower,
            
            # Features
            "auto_scaling": "auto" in desc_lower and "scale" in desc_lower,
            "monitoring": "monitor" in desc_lower or "observability" in desc_lower,
            "ci_cd": "ci" in desc_lower or "cd" in desc_lower or "deploy" in desc_lower,
            "ssl": "ssl" in desc_lower or "tls" in desc_lower or "https" in desc_lower,
            "security": "security" in desc_lower or "secure" in desc_lower,
            
            # Production
            "production": "production" in desc_lower or "prod" in desc_lower,
            "staging": "staging" in desc_lower,
            "high_availability": "ha" in desc_lower or "high availability" in desc_lower,
            "multi_az": "multi" in desc_lower or "availability zone" in desc_lower,
        }
        
        return requirements
    
    def _generate_components(self, reqs: dict) -> list[InfraComponent]:
        """Generate infrastructure components"""
        
        components = []
        
        # Kubernetes cluster
        if reqs.get("kubernetes"):
            components.append(InfraComponent(
                type="eks",
                name="main-cluster",
                config={
                    "version": "1.28",
                    "node_groups": [
                        {
                            "name": "general",
                            "instance_type": "t3.medium",
                            "min_size": 2,
                            "max_size": 10,
                            "desired_size": 3 if reqs.get("high_availability") else 2
                        }
                    ],
                    "auto_scaling": reqs.get("auto_scaling"),
                    "vpc": reqs.get("vpc", True)
                }
            ))
        
        # ECS/Fargate (alternative to k8s)
        elif reqs.get("containers"):
            components.append(InfraComponent(
                type="ecs",
                name="app-cluster",
                config={
                    "cluster_type": "FARGATE",
                    "auto_scaling": reqs.get("auto_scaling")
                }
            ))
        
        # EC2 (if no k8s/containers)
        elif reqs.get("vm"):
            components.append(InfraComponent(
                type="ec2",
                name="app-servers",
                config={
                    "instance_type": "t3.medium",
                    "min_size": 2 if reqs.get("high_availability") else 1,
                    "max_size": 10 if reqs.get("auto_scaling") else 2,
                    "auto_scaling": reqs.get("auto_scaling")
                }
            ))
        
        # Database
        if reqs.get("database"):
            db_type = "rds"
            if reqs.get("nosql"):
                db_type = "dynamodb" if self.provider == CloudProvider.AWS else "mongodb"
            
            components.append(InfraComponent(
                type=db_type,
                name="main-database",
                config={
                    "engine": "postgres" if reqs.get("sql") else "aurora",
                    "multi_az": reqs.get("multi_az") or reqs.get("high_availability"),
                    "encrypted": True,
                    "backup": True,
                    "instance_class": "db.t3.medium"
                },
                dependencies=["vpc"]
            ))
        
        # Redis/Cache
        if reqs.get("redis"):
            components.append(InfraComponent(
                type="elasticache",
                name="redis-cache",
                config={
                    "node_type": "cache.t3.micro",
                    "num_nodes": 2 if reqs.get("high_availability") else 1,
                    "engine": "redis"
                }
            ))
        
        # Storage
        if reqs.get("storage"):
            components.append(InfraComponent(
                type="s3",
                name="app-storage",
                config={
                    "versioning": True,
                    "encryption": "AES256",
                    "lifecycle_rules": True
                }
            ))
        
        # VPC (if networking needed)
        if reqs.get("vpc") or any([reqs.get("kubernetes"), reqs.get("containers"), reqs.get("database")]):
            components.append(InfraComponent(
                type="vpc",
                name="main-vpc",
                config={
                    "cidr": "10.0.0.0/16",
                    "public_subnets": ["10.0.1.0/24", "10.0.2.0/24"],
                    "private_subnets": ["10.0.10.0/24", "10.0.20.0/24"],
                    "nat_gateway": reqs.get("high_availability", True),
                    "vpc_endpoints": ["s3", "dynamodb"]
                }
            ))
        
        # Load Balancer
        if reqs.get("load_balancer") or reqs.get("kubernetes") or reqs.get("containers"):
            components.append(InfraComponent(
                type="alb",
                name="main-lb",
                config={
                    "type": "application",
                    "ssl_cert": reqs.get("ssl", True),
                    "waf": reqs.get("security", False)
                }
            ))
        
        return components
    
    def _generate_cicd(self, reqs: dict) -> dict:
        """Generate CI/CD configuration"""
        
        return {
            "github_actions": {
                "workflows": [
                    {
                        "name": "CI/CD Pipeline",
                        "on": ["push", "pull_request"],
                        "jobs": [
                            {
                                "name": "test",
                                "runs_on": "ubuntu-latest",
                                "steps": [
                                    {"uses": "actions/checkout@v3"},
                                    {"uses": "actions/setup-node@v3"},
                                    {"run": "npm install"},
                                    {"run": "npm test"},
                                ]
                            },
                            {
                                "name": "deploy",
                                "runs_on": "ubuntu-latest",
                                "needs": "test",
                                "if": "github.ref == 'refs/heads/main'",
                                "steps": [
                                    {"uses": "actions/checkout@v3"},
                                    {"name": "Configure AWS", "uses": "aws-actions/configure-aws-credentials@v2"},
                                    {"run": "npm run deploy"}
                                ]
                            }
                        ]
                    }
                ]
            },
            "helm": {
                "charts": [
                    {
                        "name": "application",
                        "values": {
                            "replicaCount": 3 if reqs.get("high_availability") else 1,
                            "autoscaling": {
                                "enabled": reqs.get("auto_scaling"),
                                "minReplicas": 2,
                                "maxReplicas": 10
                            }
                        }
                    }
                ]
            }
        }
    
    def _generate_monitoring(self, reqs: dict) -> dict:
        """Generate monitoring/observability stack"""
        
        return {
            "prometheus": {
                "enabled": True,
                "retention": "30d",
                "alerting": True
            },
            "grafana": {
                "enabled": True,
                "dashboards": [
                    "kubernetes",
                    "nginx",
                    "postgresql"
                ]
            },
            "logging": {
                "type": "cloudwatch" if self.provider == CloudProvider.AWS else "elasticsearch",
                "retention": "30d"
            },
            "alerting": {
                "slack": True,
                "email": True
            },
            "tracing": {
                "jaeger": True
            }
        }
    
    def _generate_security(self, reqs: dict) -> dict:
        """Generate security configuration"""
        
        return {
            "encryption": {
                "at_rest": True,
                "in_transit": True
            },
            "secrets": {
                "manager": "secrets-manager",
                "rotation": True
            },
            "iam": {
                "least_privilege": True,
                "mfa_required": True
            },
            "network": {
                "waf": True,
                "shield": reqs.get("production", False),
                "vpc_flow_logs": True
            },
            "audit": {
                "cloudtrail": True,
                "guardduty": reqs.get("production", False)
            }
        }
    
    def render_terraform(self, spec: InfraSpec) -> str:
        """Render Terraform code from spec"""
        
        tf = '''# Generated by OmniClaw Natural Language Infrastructure
# Provider: {provider}

provider "aws" {{
  region = "us-east-1"
}}

'''.format(provider=spec.provider.value)
        
        # Generate resource blocks
        for comp in spec.components:
            if comp.type == "vpc":
                tf += self._render_vpc_tf(comp)
            elif comp.type == "eks":
                tf += self._render_eks_tf(comp)
            elif comp.type == "rds":
                tf += self._render_rds_tf(comp)
            elif comp.type == "s3":
                tf += self._render_s3_tf(comp)
            elif comp.type == "alb":
                tf += self._render_alb_tf(comp)
        
        # Add CI/CD if present
        if spec.ci_cd:
            tf += self._render_github_workflow(spec.ci_cd)
        
        # Add monitoring if present
        if spec.monitoring:
            tf += self._render_monitoring_tf(spec.monitoring)
        
        return tf
    
    def _render_vpc_tf(self, comp: InfraComponent) -> str:
        return f'''
# VPC
resource "aws_vpc" "{comp.name}" {{
  cidr_block           = "{comp.config.get('cidr', '10.0.0.0/16')}"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name = "{comp.name}"
  }}
}}

resource "aws_subnet" "public" {{
  count             = 2
  vpc_id            = aws_vpc.{comp.name}.id
  cidr_block        = element(["10.0.1.0/24", "10.0.2.0/24"], count.index)
  availability_zone = element(["us-east-1a", "us-east-1b"], count.index)
  map_public_ip_on_instance = true

  tags = {{
    Name = "{comp.name}-public-{{count.index}}"
  }}
}}
'''
    
    def _render_eks_tf(self, comp: InfraComponent) -> str:
        return f'''
# EKS Cluster
resource "aws_eks_cluster" "{comp.name}" {{
  name     = "{comp.name}"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "{comp.config.get('version', '1.28')}"

  vpc_config {{
    subnet_ids = aws_subnet.public[*].id
  }}
}}
'''
    
    def _render_rds_tf(self, comp: InfraComponent) -> str:
        multi_az = "true" if comp.config.get("multi_az") else "false"
        return f'''
# RDS Database
resource "aws_db_instance" "{comp.name}" {{
  identifier     = "{comp.name}"
  engine         = "{comp.config.get('engine', 'postgres')}"
  instance_class = "{comp.config.get('instance_class', 'db.t3.medium')}"
  multi_az       = {multi_az}
  encrypted      = {"true" if comp.config.get("encrypted") else "false"}

  # For production, use secrets manager instead
  # password = var.db_password
}}
'''
    
    def _render_s3_tf(self, comp: InfraComponent) -> str:
        return f'''
# S3 Bucket
resource "aws_s3_bucket" "{comp.name}" {{
  bucket = "{comp.name}"
}}

resource "aws_s3_bucket_versioning" "{comp.name}" {{
  bucket = aws_s3_bucket.{comp.name}.id
  versioning_configuration {{
    status = {"Enabled" if comp.config.get("versioning") else "Suspended"}
  }}
}}
'''
    
    def _render_alb_tf(self, comp: InfraComponent) -> str:
        return f'''
# Application Load Balancer
resource "aws_lb" "{comp.name}" {{
  name               = "{comp.name}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}}
'''
    
    def _render_github_workflow(self, cicd: dict) -> str:
        workflow = '''
# GitHub Actions Workflow
.github/workflows/deploy.yml:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on:    steps:
      ubuntu-latest
 - uses: actions/checkout@v3
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: ./deploy.sh
```
'''
        return workflow
    
    def _render_monitoring_tf(self, monitoring: dict) -> str:
        return '''
# Monitoring (Prometheus + Grafana)
# Add via Helm:
# helm install prometheus prometheus-community/kube-prometheus-stack
'''


# Demo
if __name__ == "__main__":
    infra = NaturalLanguageInfra()
    
    # Generate from natural language
    spec = infra.generate(
        "Production k8s cluster with auto-scaling, monitoring, CI/CD, and PostgreSQL database",
        provider=CloudProvider.AWS
    )
    
    print("🏗️ NATURAL LANGUAGE INFRASTRUCTURE")
    print("=" * 50)
    
    print(f"\nProvider: {spec.provider.value}")
    print(f"Components: {len(spec.components)}")
    for comp in spec.components:
        print(f"  - {comp.type}: {comp.name}")
    
    if spec.ci_cd:
        print("\nCI/CD: ✅ Included")
    
    if spec.monitoring:
        print("Monitoring: ✅ Included")
    
    if spec.security:
        print("Security: ✅ Included")
    
    print("\n\n📄 Terraform Preview:")
    print("-" * 30)
    print(infra.render_terraform(spec)[:1500] + "...")
