"""
Terraform Infrastructure-as-Code Generator for Multi-Cloud Solutions
Addresses operational complexity by generating unified IaC templates
"""

from typing import Dict, List, Any
from backend.models import Solution

class TerraformGenerator:
    """Generate Terraform configurations for multi-cloud solutions"""
    
    def __init__(self):
        self.provider_configs = {
            'AWS': self._aws_provider_config,
            'Azure': self._azure_provider_config, 
            'GCP': self._gcp_provider_config
        }
        
        self.service_mappings = {
            # API Gateway
            'AWS API Gateway': 'aws_api_gateway_rest_api',
            'Azure API Management': 'azurerm_api_management',
            'GCP API Gateway': 'google_api_gateway_api',
            
            # Compute
            'AWS EC2': 'aws_instance',
            'Azure VM': 'azurerm_linux_virtual_machine',
            'GCP Compute Engine': 'google_compute_instance',
            
            # Database
            'AWS RDS': 'aws_db_instance',
            'Azure SQL': 'azurerm_mssql_server',
            'GCP Cloud SQL': 'google_sql_database_instance',
            
            # Storage
            'AWS S3': 'aws_s3_bucket',
            'Azure Storage': 'azurerm_storage_account',
            'GCP Cloud Storage': 'google_storage_bucket',
            
            # Container Orchestration
            'AWS EKS': 'aws_eks_cluster',
            'Azure AKS': 'azurerm_kubernetes_cluster',
            'GCP GKE': 'google_container_cluster',
        }

    def generate_terraform_config(self, solution: Solution) -> str:
        """Generate complete Terraform configuration for a solution"""
        config_parts = []
        
        # Add provider configurations
        providers = self._get_providers_from_solution(solution)
        config_parts.append(self._generate_providers_block(providers))
        
        # Add variable definitions
        config_parts.append(self._generate_variables_block())
        
        # Add resources for each service
        for component, service in solution.configuration.items():
            resource_config = self._generate_resource_config(component, service)
            if resource_config:
                config_parts.append(resource_config)
        
        # Add networking configuration for multi-cloud
        if len(providers) > 1:
            config_parts.append(self._generate_networking_config(providers))
        
        # Add monitoring and tagging
        config_parts.append(self._generate_common_config(solution))
        
        return '\n\n'.join(config_parts)

    def _get_providers_from_solution(self, solution: Solution) -> List[str]:
        """Extract unique providers from solution configuration"""
        providers = set()
        for service in solution.configuration.values():
            provider = service.split(' ')[0]
            providers.add(provider)
        return list(providers)

    def _generate_providers_block(self, providers: List[str]) -> str:
        """Generate Terraform provider configurations"""
        provider_blocks = []
        
        for provider in providers:
            if provider in self.provider_configs:
                provider_blocks.append(self.provider_configs[provider]())
        
        return '\n\n'.join(provider_blocks)

    def _aws_provider_config(self) -> str:
        return '''terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}'''

    def _azure_provider_config(self) -> str:
        return '''terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}'''

    def _gcp_provider_config(self) -> str:
        return '''terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}'''

    def _generate_variables_block(self) -> str:
        return '''# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "cloud-migration"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "azure_location" {
  description = "Azure location"
  type        = string
  default     = "East US"
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-east1"
}'''

    def _generate_resource_config(self, component: str, service: str) -> str:
        """Generate Terraform resource configuration for a service"""
        provider = service.split(' ')[0]
        resource_name = f"{component.replace('_', '-')}-{provider.lower()}"
        
        if service == 'AWS EC2':
            return f'''# {component.title()} - {service}
resource "aws_instance" "{resource_name}" {{
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.medium"
  
  tags = {{
    Name = "${{var.project_name}}-{component}"
    Component = "{component}"
  }}
}}

data "aws_ami" "amazon_linux" {{
  most_recent = true
  owners      = ["amazon"]
  
  filter {{
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }}
}}'''
        
        elif service == 'Azure AKS':
            return f'''# {component.title()} - {service}
resource "azurerm_resource_group" "aks_rg" {{
  name     = "${{var.project_name}}-{component}-rg"
  location = var.azure_location
}}

resource "azurerm_kubernetes_cluster" "{resource_name}" {{
  name                = "${{var.project_name}}-{component}"
  location            = azurerm_resource_group.aks_rg.location
  resource_group_name = azurerm_resource_group.aks_rg.name
  dns_prefix          = "${{var.project_name}}-{component}"

  default_node_pool {{
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2_v2"
  }}

  identity {{
    type = "SystemAssigned"
  }}

  tags = {{
    Environment = var.environment
    Component   = "{component}"
  }}
}}'''
        
        elif service == 'GCP Cloud Storage':
            return f'''# {component.title()} - {service}
resource "google_storage_bucket" "{resource_name}" {{
  name     = "${{var.project_name}}-{component}-${{random_id.bucket_suffix.hex}}"
  location = var.gcp_region
  
  uniform_bucket_level_access = true
  
  labels = {{
    environment = var.environment
    component   = "{component.replace('_', '-')}"
  }}
}}

resource "random_id" "bucket_suffix" {{
  byte_length = 4
}}'''
        
        # Add more service mappings as needed
        return f'''# {component.title()} - {service}
# TODO: Add specific configuration for {service}'''

    def _generate_networking_config(self, providers: List[str]) -> str:
        """Generate cross-cloud networking configuration"""
        config = '''# Cross-Cloud Networking Configuration
# VPC Peering and VPN connections for multi-cloud setup'''
        
        if 'AWS' in providers and 'Azure' in providers:
            config += '''

# AWS-Azure VPN Connection
resource "aws_vpn_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${var.project_name}-vpn-gateway"
  }
}

# Azure VPN Gateway (requires virtual network)
resource "azurerm_virtual_network_gateway" "main" {
  name                = "${var.project_name}-vpn-gateway"
  location            = var.azure_location
  resource_group_name = azurerm_resource_group.main.name
  
  type     = "Vpn"
  vpn_type = "RouteBased"
  
  active_active = false
  enable_bgp    = false
  sku           = "VpnGw1"
  
  ip_configuration {
    public_ip_address_id          = azurerm_public_ip.vpn.id
    private_ip_address_allocation = "Dynamic"
    subnet_id                     = azurerm_subnet.gateway.id
  }
}'''
        
        return config

    def _generate_common_config(self, solution: Solution) -> str:
        """Generate common configuration (monitoring, tagging, etc.)"""
        return f'''# Common Configuration
# Estimated monthly cost: ${solution.cost:.2f}
# Expected latency: {solution.latency:.1f}ms
# Providers: {solution.providers}

# Output values
output "solution_summary" {{
  value = {{
    cost      = {solution.cost}
    latency   = {solution.latency}
    providers = {solution.providers}
    score     = {getattr(solution, 'score', 0)}
  }}
}}

# Local values for consistent naming
locals {{
  common_tags = {{
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    CostCenter  = "cloud-migration"
  }}
}}'''

def generate_terraform_for_solution(solution: Solution) -> str:
    """Main function to generate Terraform configuration for a solution"""
    generator = TerraformGenerator()
    return generator.generate_terraform_config(solution)

def generate_deployment_script(solution: Solution) -> str:
    """Generate deployment script for the Terraform configuration"""
    providers = set(service.split(' ')[0] for service in solution.configuration.values())
    
    script = '''#!/bin/bash
# Deployment script for multi-cloud solution
set -e

echo "Deploying multi-cloud solution..."
echo "Estimated cost: $''' + f'{solution.cost:.2f}' + '''/month"
echo "Expected latency: ''' + f'{solution.latency:.1f}' + '''ms"
echo "Providers: ''' + ', '.join(providers) + '''"

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply with confirmation
echo "Review the plan above. Continue? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    terraform apply tfplan
    echo "Deployment completed successfully!"
else
    echo "Deployment cancelled."
    exit 1
fi
'''
    
    return script