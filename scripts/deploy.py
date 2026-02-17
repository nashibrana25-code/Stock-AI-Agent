#!/usr/bin/env python3
"""
Deployment script for ASX AI Investment Platform

Deploys to AWS/Azure/GCP with all necessary services
"""
import subprocess
import sys
import os
from pathlib import Path


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stderr)
        return None


def deploy_to_aws():
    """Deploy to AWS ECS/EKS"""
    print_header("Deploying to AWS")
    
    # Check AWS CLI
    if not run_command("aws --version", "Checking AWS CLI"):
        print("Please install AWS CLI first")
        return False
    
    # Build and push Docker images
    print("\n📦 Building Docker images...")
    
    images = [
        ("api-gateway", "services/api-gateway"),
        ("ai-agent", "services/ai-agent"),
        ("data-ingestion", "services/data-ingestion"),
    ]
    
    aws_account = run_command("aws sts get-caller-identity --query Account --output text", "Getting AWS account")
    if not aws_account:
        return False
    
    aws_account = aws_account.strip()
    region = "ap-southeast-2"  # Sydney region for ASX
    ecr_url = f"{aws_account}.dkr.ecr.{region}.amazonaws.com"
    
    # Login to ECR
    run_command(
        f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {ecr_url}",
        "Logging into ECR"
    )
    
    # Build and push each image
    for name, path in images:
        repo_name = f"asx-platform-{name}"
        
        # Create ECR repository if doesn't exist
        run_command(
            f"aws ecr create-repository --repository-name {repo_name} --region {region} || true",
            f"Creating ECR repository for {name}"
        )
        
        # Build image
        if not run_command(
            f"docker build -t {repo_name} -f {path}/Dockerfile .",
            f"Building {name} image"
        ):
            continue
        
        # Tag and push
        run_command(f"docker tag {repo_name}:latest {ecr_url}/{repo_name}:latest", f"Tagging {name}")
        run_command(f"docker push {ecr_url}/{repo_name}:latest", f"Pushing {name} to ECR")
    
    # Deploy with CloudFormation or Terraform
    print("\n🚀 Deploying infrastructure...")
    
    # Option 1: Use AWS CDK
    if os.path.exists("infrastructure/aws-cdk"):
        os.chdir("infrastructure/aws-cdk")
        run_command("npm install", "Installing CDK dependencies")
        run_command("cdk deploy --all --require-approval never", "Deploying with CDK")
    
    # Option 2: Use Terraform
    elif os.path.exists("infrastructure/terraform"):
        os.chdir("infrastructure/terraform")
        run_command("terraform init", "Initializing Terraform")
        run_command("terraform plan", "Planning Terraform deployment")
        run_command("terraform apply -auto-approve", "Applying Terraform configuration")
    
    print("\n✅ AWS deployment complete!")
    print(f"\nYour platform is deploying to AWS...")
    print(f"Region: {region}")
    print(f"\nNext steps:")
    print("1. Configure domain name in Route 53")
    print("2. Set up SSL certificate in ACM")
    print("3. Update environment variables in ECS/EKS")
    
    return True


def deploy_to_azure():
    """Deploy to Azure Container Apps"""
    print_header("Deploying to Azure")
    
    # Check Azure CLI
    if not run_command("az --version", "Checking Azure CLI"):
        print("Please install Azure CLI first")
        return False
    
    resource_group = "asx-platform-rg"
    location = "australiaeast"  # Sydney region
    
    # Create resource group
    run_command(
        f"az group create --name {resource_group} --location {location}",
        "Creating resource group"
    )
    
    # Create container registry
    registry_name = "asxplatformregistry"
    run_command(
        f"az acr create --resource-group {resource_group} --name {registry_name} --sku Basic",
        "Creating Azure Container Registry"
    )
    
    # Build and push images
    run_command(
        f"az acr build --registry {registry_name} --image api-gateway:latest -f services/api-gateway/Dockerfile .",
        "Building API Gateway image"
    )
    
    run_command(
        f"az acr build --registry {registry_name} --image ai-agent:latest -f services/ai-agent/Dockerfile .",
        "Building AI Agent image"
    )
    
    # Create Container App environment
    env_name = "asx-platform-env"
    run_command(
        f"az containerapp env create --name {env_name} --resource-group {resource_group} --location {location}",
        "Creating Container App environment"
    )
    
    # Deploy containers
    run_command(
        f"az containerapp create --name api-gateway --resource-group {resource_group} "
        f"--environment {env_name} --image {registry_name}.azurecr.io/api-gateway:latest "
        f"--target-port 8000 --ingress external --registry-server {registry_name}.azurecr.io",
        "Deploying API Gateway"
    )
    
    print("\n✅ Azure deployment complete!")
    return True


def deploy_to_vercel_netlify():
    """Deploy frontend to Vercel/Netlify"""
    print_header("Deploying Frontend")
    
    frontend_path = "frontend"
    
    if not os.path.exists(frontend_path):
        print("Frontend not built yet. Please run: cd frontend && npm run build")
        return False
    
    # Deploy to Vercel
    if run_command("vercel --version", "Checking Vercel CLI"):
        os.chdir(frontend_path)
        run_command("vercel --prod", "Deploying to Vercel")
        return True
    
    # Or deploy to Netlify
    elif run_command("netlify --version", "Checking Netlify CLI"):
        os.chdir(frontend_path)
        run_command("netlify deploy --prod --dir=build", "Deploying to Netlify")
        return True
    
    print("Please install Vercel or Netlify CLI")
    return False


def setup_domain_ssl():
    """Setup custom domain and SSL"""
    print_header("Domain & SSL Setup")
    
    print("""
To make your platform accessible at your custom domain:

1. Register a domain (e.g., mysmartstocks.com)
2. Point DNS to your cloud provider:
   - AWS: Use Route 53 or update nameservers
   - Azure: Use Azure DNS
   - Vercel/Netlify: Follow their custom domain guide

3. SSL is automatically provisioned by:
   - AWS: ACM (AWS Certificate Manager)
   - Azure: Managed certificates
   - Vercel/Netlify: Automatic Let's Encrypt

4. Update CORS settings in .env with your domain
""")


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      ASX AI Investment Platform - Deployment Tool       ║
║                                                          ║
║     Deploy your 24/7 AI agent to the cloud              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")
    
    print("\nSelect deployment option:")
    print("1. Deploy to AWS (ECS/EKS)")
    print("2. Deploy to Azure (Container Apps)")
    print("3. Deploy Frontend (Vercel/Netlify)")
    print("4. Full deployment (All services)")
    print("5. Setup domain & SSL")
    print("6. Exit")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        deploy_to_aws()
    elif choice == "2":
        deploy_to_azure()
    elif choice == "3":
        deploy_to_vercel_netlify()
    elif choice == "4":
        deploy_to_aws()
        deploy_to_vercel_netlify()
        setup_domain_ssl()
    elif choice == "5":
        setup_domain_ssl()
    elif choice == "6":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice")
        main()


if __name__ == "__main__":
    main()
