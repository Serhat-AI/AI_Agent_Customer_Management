#!/bin/bash
# Azure Deployment Script for RSD Analysis Agent
# Requires: Azure CLI installed and authenticated

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP=${1:-"rsd-agent-rg"}
VM_NAME=${2:-"rsd-agent-vm"}
LOCATION=${3:-"westeurope"}
VM_SIZE="Standard_B2s"  # 2 vCPUs, 4GB RAM

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Azure RSD Analysis Agent Deployment${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Step 1: Check Azure CLI
echo -e "${YELLOW}Step 1: Checking Azure CLI...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}ERROR: Azure CLI not found. Install from: https://aka.ms/azcli${NC}"
    exit 1
fi

az version

# Step 2: Check authentication
echo ""
echo -e "${YELLOW}Step 2: Checking Azure authentication...${NC}"
CURRENT_USER=$(az account show --query user.name -o tsv 2>/dev/null)
if [ -z "$CURRENT_USER" ]; then
    echo -e "${YELLOW}Not authenticated. Running: az login${NC}"
    az login
fi
echo -e "${GREEN}Logged in as: $CURRENT_USER${NC}"

# Step 3: Create Resource Group
echo ""
echo -e "${YELLOW}Step 3: Creating Resource Group: $RESOURCE_GROUP in $LOCATION${NC}"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

echo -e "${GREEN}Resource Group created${NC}"

# Step 4: Create VM
echo ""
echo -e "${YELLOW}Step 4: Creating Windows VM: $VM_NAME (size: $VM_SIZE)${NC}"
echo "(This may take 3-5 minutes...)"

az vm create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --image Win2022Datacenter \
    --size "$VM_SIZE" \
    --public-ip-sku Standard \
    --output none

echo -e "${GREEN}VM created${NC}"

# Step 5: Get VM info
echo ""
echo -e "${YELLOW}Step 5: Retrieving VM details...${NC}"
VM_IP=$(az vm show -d \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --query publicIps -o tsv)

echo -e "${GREEN}Public IP: $VM_IP${NC}"

# Step 6: Open RDP port
echo ""
echo -e "${YELLOW}Step 6: Opening RDP port (3389)...${NC}"
az vm open-port \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --port 3389 \
    --output none

echo -e "${GREEN}RDP port opened${NC}"

# Step 7: Create Storage Account
echo ""
echo -e "${YELLOW}Step 7: Creating Storage Account for project documents...${NC}"
STORAGE_ACCOUNT="rsddocs$(date +%s | tail -c 10)"

az storage account create \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --kind StorageV2 \
    --access-tier Hot \
    --output none

echo -e "${GREEN}Storage Account created: $STORAGE_ACCOUNT${NC}"

# Step 8: Create Storage Container
echo ""
echo -e "${YELLOW}Step 8: Creating storage container for documents...${NC}"
STORAGE_KEY=$(az storage account keys list \
    --resource-group "$RESOURCE_GROUP" \
    --account-name "$STORAGE_ACCOUNT" \
    --query '[0].value' -o tsv)

az storage container create \
    --name "project-documents" \
    --account-name "$STORAGE_ACCOUNT" \
    --account-key "$STORAGE_KEY" \
    --output none

echo -e "${GREEN}Storage container created${NC}"

# Step 9: Create Keyvault
echo ""
echo -e "${YELLOW}Step 9: Creating Azure Keyvault...${NC}"
KEYVAULT_NAME="rsd-agent-kv-$(date +%s | tail -c 6)"

az keyvault create \
    --name "$KEYVAULT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

echo -e "${GREEN}Keyvault created: $KEYVAULT_NAME${NC}"

# Step 10: Store secrets
echo ""
echo -e "${YELLOW}Step 10: Storing secrets in Keyvault...${NC}"
read -sp "Enter OpenAI API Key (sk-...): " OPENAI_KEY
echo ""

az keyvault secret set \
    --vault-name "$KEYVAULT_NAME" \
    --name "openai-api-key" \
    --value "$OPENAI_KEY" \
    --output none

echo -e "${GREEN}Secret stored${NC}"

# Step 11: Create Managed Identity
echo ""
echo -e "${YELLOW}Step 11: Creating Managed Identity for VM...${NC}"
IDENTITY_NAME="rsd-agent-identity"

az identity create \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --output none

IDENTITY_ID=$(az identity show \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query id -o tsv)

PRINCIPAL_ID=$(az identity show \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId -o tsv)

echo -e "${GREEN}Managed Identity created${NC}"

# Step 12: Grant permissions
echo ""
echo -e "${YELLOW}Step 12: Granting Keyvault access to Managed Identity...${NC}"
az keyvault set-policy \
    --name "$KEYVAULT_NAME" \
    --object-id "$PRINCIPAL_ID" \
    --secret-permissions get list \
    --output none

echo -e "${GREEN}Permissions granted${NC}"

# Summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "VM Name: $VM_NAME"
echo "VM IP Address: $VM_IP"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Keyvault Name: $KEYVAULT_NAME"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Connect to VM via RDP:"
echo "   mstsc /v:$VM_IP"
echo ""
echo "2. On the VM, download and run the agent setup:"
echo "   git clone https://github.com/your-org/rsd-agent.git"
echo "   cd rsd-agent"
echo "   .\deploy.ps1 -Action setup"
echo ""
echo "3. Upload project documents to storage:"
echo "   az storage blob upload-batch -s <local-path> -d project-documents -a $STORAGE_ACCOUNT -k $STORAGE_KEY"
echo ""
echo "4. Configure VM to download documents from storage on startup"
echo ""

# Optional: Enable autoshutdown
read -p "Enable Auto-Shutdown at 7 PM? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Enabling auto-shutdown...${NC}"
    az vm auto-shutdown \
        --resource-group "$RESOURCE_GROUP" \
        --name "$VM_NAME" \
        --time 1900 \
        --output none
    echo -e "${GREEN}Auto-shutdown enabled at 7 PM${NC}"
fi

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
