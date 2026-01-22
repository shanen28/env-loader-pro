"""Auto-detection utilities for runtime environment."""

import os
from typing import Optional


def detect_aws_environment() -> bool:
    """Detect if running in AWS environment.
    
    Checks for:
    - AWS_EXECUTION_ENV
    - AWS_LAMBDA_FUNCTION_NAME
    - ECS metadata endpoint
    - EC2 metadata endpoint
    
    Returns:
        True if running in AWS environment
    """
    # Check environment variables
    if os.getenv("AWS_EXECUTION_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return True
    
    # Check for ECS metadata endpoint
    if os.getenv("ECS_CONTAINER_METADATA_URI_V4"):
        return True
    
    # Check for EC2 metadata endpoint (simplified check)
    # In production, you might want to actually try to reach the endpoint
    if os.path.exists("/sys/hypervisor/uuid"):
        try:
            with open("/sys/hypervisor/uuid", "r") as f:
                uuid = f.read().strip()
                # EC2 UUIDs start with "ec2"
                if uuid.startswith("ec2"):
                    return True
        except Exception:
            pass
    
    return False


def detect_azure_environment() -> bool:
    """Detect if running in Azure environment.
    
    Checks for:
    - WEBSITE_INSTANCE_ID (Azure App Service)
    - MSI_ENDPOINT (Managed Identity)
    - Azure Functions environment variables
    
    Returns:
        True if running in Azure environment
    """
    # Azure App Service
    if os.getenv("WEBSITE_INSTANCE_ID"):
        return True
    
    # Azure Managed Identity
    if os.getenv("MSI_ENDPOINT") or os.getenv("IDENTITY_ENDPOINT"):
        return True
    
    # Azure Functions
    if os.getenv("FUNCTIONS_WORKER_RUNTIME"):
        return True
    
    # Azure Container Instances
    if os.getenv("ACI_CONTAINER_GROUP"):
        return True
    
    return False


def detect_kubernetes_environment() -> bool:
    """Detect if running in Kubernetes environment.
    
    Checks for:
    - KUBERNETES_SERVICE_HOST
    - Service account token mount
    
    Returns:
        True if running in Kubernetes
    """
    # Kubernetes service host
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return True
    
    # Service account token (mounted in pods)
    if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
        return True
    
    return False


def detect_docker_environment() -> bool:
    """Detect if running in Docker environment.
    
    Checks for:
    - /.dockerenv file
    - Docker cgroup
    
    Returns:
        True if running in Docker
    """
    # Docker environment file
    if os.path.exists("/.dockerenv"):
        return True
    
    # Check cgroup (simplified)
    try:
        if os.path.exists("/proc/self/cgroup"):
            with open("/proc/self/cgroup", "r") as f:
                content = f.read()
                if "docker" in content or "containerd" in content:
                    return True
    except Exception:
        pass
    
    return False


def detect_environment() -> dict:
    """Detect the runtime environment.
    
    Returns:
        Dictionary with environment detection results
    """
    return {
        "aws": detect_aws_environment(),
        "azure": detect_azure_environment(),
        "kubernetes": detect_kubernetes_environment(),
        "docker": detect_docker_environment(),
    }


def get_recommended_providers() -> list:
    """Get recommended providers based on detected environment.
    
    Returns:
        List of recommended provider class names (not instances)
    """
    env = detect_environment()
    providers = []
    
    if env["azure"]:
        providers.append("AzureKeyVaultProvider")
    
    if env["aws"]:
        providers.append("AWSSecretsManagerProvider")
        providers.append("AWSSSMProvider")
    
    if env["kubernetes"]:
        providers.append("KubernetesSecretsProvider")
    
    if env["docker"]:
        providers.append("DockerSecretsProvider")
    
    return providers
