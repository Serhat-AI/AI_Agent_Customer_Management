# Deployment Guides for RSD Analysis Agent

## 📋 Deployment Options Overview

This document covers three deployment strategies for the RSD Analysis Agent:
1. **Local Windows Machine** - Simplest, for single-user/small team
2. **Azure VM** - Cloud-based, managed by Microsoft
3. **Docker Container** - Containerized, portable across platforms

---

## 1️⃣ Local Windows Machine Deployment

### Recommended For:
- Single office location
- <50 incoming RSDs per week
- Development/testing phase

### Installation Steps

#### Step 1: Install Python 3.11+

```bash
# Download from https://www.python.org/downloads/
# Run installer, check "Add Python to PATH"
python --version  # Verify installation
```

#### Step 2: Clone Repository

```bash
cd C:\Users\Admin\Documents\PythonProjects\RAG_LangChain_Local.worktrees\agents-ai-agent-customer-management
```

#### Step 3: Setup Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 4: Configure Environment

```bash
# Copy and edit .env
copy .env.example .env
notepad .env
```

Update these values:
```
GMAIL_USER_EMAIL=your-company@gmail.com
GMAIL_CREDENTIALS_PATH=credentials.json
PROJECT_DOCS_PATH=C:\your\project\documents
SUMMARY_RECIPIENT_EMAIL=team@company.com
OPENAI_API_KEY=sk-your-key-here
```

#### Step 5: Setup Gmail API

1. Download `credentials.json` from Google Cloud Console
2. Place in project root directory
3. Run once to authenticate:
   ```bash
   python main.py
   ```

#### Step 6: Index Documents

```bash
python main.py --init
```

#### Step 7: Schedule with Task Scheduler

Create automated task:

**PowerShell (as Administrator):**

```powershell
$taskName = "RSD-Analysis-Agent-Hourly"
$action = New-ScheduledTaskAction -Execute "C:\path\to\venv\Scripts\python.exe" `
    -Argument "C:\full\path\to\main.py" `
    -WorkingDirectory "C:\full\path\to\project"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -RunLevel Highest
```

**Or manually via GUI:**

1. Open Task Scheduler (`taskschd.msc`)
2. Click "Create Basic Task"
3. Name: "RSD Analysis Agent"
4. Trigger: "Daily" → Repeat every 1 hour
5. Action:
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\full\path\to\main.py`
   - Start in: `C:\full\path\to\project`

### Monitoring Local Deployment

Check logs:
```bash
# View recent runs
Get-EventLog -LogName System -Source TaskScheduler | Select-Object -First 10

# Or run manually to see output
python main.py
```

---

## 2️⃣ Azure VM Deployment

### Recommended For:
- Enterprise deployment
- Multiple offices/regions
- High availability requirements
- 100+ RSDs per week

### Architecture

```
Azure Subscription
├── Resource Group (rsd-agent-rg)
├── VM (Windows Server 2022)
│   ├── Python environment
│   ├── RSD Agent service
│   └── Vector database
├── Storage Account (project documents)
└── Keyvault (credentials storage)
```

### Prerequisites

- Azure subscription
- Azure CLI installed
- Global admin or contributor role

### Step-by-Step Deployment

#### Step 1: Create Resource Group

```bash
az group create \
  --name rsd-agent-rg \
  --location westeurope
```

#### Step 2: Create Windows VM

```bash
az vm create \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm \
  --image Win2022Datacenter \
  --size Standard_B2s \
  --admin-username azureuser \
  --admin-password <YOUR_PASSWORD> \
  --public-ip-address-allocation static
```

Get VM IP:
```bash
az vm show -d \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm \
  --query publicIps -o tsv
```

#### Step 3: Open Network Ports

```bash
az vm open-port \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm \
  --port 3389  # RDP
```

#### Step 4: Connect via RDP

```bash
# Get public IP
$ip = az vm show -d --resource-group rsd-agent-rg --name rsd-agent-vm --query publicIps -o tsv

# Connect (Windows)
mstsc /v:$ip
```

#### Step 5: Setup on VM

Inside the VM, open PowerShell:

```powershell
# Install Python 3.11
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" `
  -OutFile "$env:TEMP\python-3.11.9-amd64.exe"

& "$env:TEMP\python-3.11.9-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1

# Clone repository
cd C:\
git clone https://github.com/your-org/rsd-agent.git

cd rsd-agent

# Setup Python environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Step 6: Create Azure Storage Account

```bash
az storage account create \
  --name rsddocuments$(Get-Random) \
  --resource-group rsd-agent-rg \
  --kind StorageV2 \
  --access-tier Hot
```

Upload project documents to Azure Blob Storage

#### Step 7: Create Keyvault for Secrets

```bash
az keyvault create \
  --name rsd-agent-kv \
  --resource-group rsd-agent-rg

# Store API keys
az keyvault secret set \
  --vault-name rsd-agent-kv \
  --name openai-api-key \
  --value "sk-your-key-here"
```

#### Step 8: Configure Agent on VM

Inside VM PowerShell:

```powershell
# Create .env file
$env_content = @"
GMAIL_USER_EMAIL=your-company@gmail.com
OPENAI_API_KEY=$(az keyvault secret show --vault-name rsd-agent-kv --name openai-api-key -o tsv --query value)
PROJECT_DOCS_PATH=C:\project_documents
SUMMARY_RECIPIENT_EMAIL=team@company.com
"@

$env_content | Out-File -FilePath C:\rsd-agent\.env -Encoding UTF8
```

#### Step 9: Create Windows Service

```powershell
# Create service wrapper script
$script = @"
`$venv = 'C:\rsd-agent\venv\Scripts\python.exe'
`$script = 'C:\rsd-agent\main.py'
`$workdir = 'C:\rsd-agent'

while (`$true) {
    Write-Host "Starting RSD Agent..."
    & `$venv `$script
    Start-Sleep -Seconds 300  # Wait 5 minutes before retry
}
"@

$script | Out-File -FilePath C:\rsd-agent\run-agent.ps1 -Encoding UTF8

# Create scheduled task (runs at startup)
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\rsd-agent\run-agent.ps1"

$trigger = New-ScheduledTaskTrigger -AtStartup

Register-ScheduledTask -TaskName "RSD-Agent-Service" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest `
    -Force
```

#### Step 10: Enable VM AutoShutdown (Optional - Cost Saving)

```bash
az vm auto-shutdown \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm \
  --time 1900  # Shutdown at 7 PM
```

### Monitoring Azure Deployment

```bash
# Check VM status
az vm get-instance-view \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm \
  --query "instanceView.statuses[?contains(code, 'ProvisioningState')].displayStatus" \
  --output table

# View metrics (CPU, memory)
az monitor metrics list \
  --resource /subscriptions/{subscription}/resourceGroups/rsd-agent-rg/providers/Microsoft.Compute/virtualMachines/rsd-agent-vm \
  --metric "Percentage CPU" \
  --start-time $(Get-Date).AddHours(-1)
```

### Cost Estimation (Azure)

- **VM (Standard_B2s)**: ~$40/month
- **Storage (100GB documents)**: ~$2/month
- **Keyvault**: ~$0.70/secret/month
- **Total**: ~$45/month

---

## 3️⃣ Docker Container Deployment

### Recommended For:
- Microservices architecture
- Multi-environment deployment (dev/staging/prod)
- Kubernetes orchestration
- Easy scaling and updates

### Prerequisites

- Docker Desktop installed
- Docker Hub account (optional, for private registry)
- docker-compose (included in Docker Desktop)

### Quick Start (Local Docker)

#### Step 1: Build Image

```bash
cd C:\Users\Admin\Documents\PythonProjects\RAG_LangChain_Local.worktrees\agents-ai-agent-customer-management

docker build -t rsd-analysis-agent:latest .
```

#### Step 2: Create .env.docker

```bash
copy .env.example .env.docker
notepad .env.docker
```

#### Step 3: Prepare Volumes

Create directories for persistent data:

```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "C:\docker-volumes\project_docs"
New-Item -ItemType Directory -Force -Path "C:\docker-volumes\vector_db"

# Copy project documents
Copy-Item "C:\path\to\project\documents\*" "C:\docker-volumes\project_docs" -Recurse
```

#### Step 4: Run Container

```bash
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f rsd-agent
```

### Docker Hub Registry (Push Image)

```bash
# Login
docker login

# Tag image
docker tag rsd-analysis-agent:latest yourusername/rsd-analysis-agent:1.0

# Push
docker push yourusername/rsd-analysis-agent:1.0
```

### Kubernetes Deployment

Create `rsd-agent-deployment.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rsd-agent-config
data:
  GMAIL_USER_EMAIL: "your-company@gmail.com"
  OPENAI_API_KEY: "sk-your-key"
  PROJECT_DOCS_PATH: "/app/project_documents"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rsd-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rsd-agent
  template:
    metadata:
      labels:
        app: rsd-agent
    spec:
      containers:
      - name: rsd-agent
        image: yourusername/rsd-analysis-agent:1.0
        envFrom:
        - configMapRef:
            name: rsd-agent-config
        volumeMounts:
        - name: project-docs
          mountPath: /app/project_documents
          readOnly: true
        - name: vector-db
          mountPath: /app/vector_db
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
      volumes:
      - name: project-docs
        persistentVolumeClaim:
          claimName: project-docs-pvc
      - name: vector-db
        persistentVolumeClaim:
          claimName: vector-db-pvc
```

Deploy:
```bash
kubectl apply -f rsd-agent-deployment.yaml
```

### Docker Security Best Practices

1. **Use secrets for sensitive data**:
```bash
docker secret create gmail_creds credentials.json
```

2. **Non-root user in Dockerfile**:
```dockerfile
RUN useradd -m agent
USER agent
```

3. **Scan for vulnerabilities**:
```bash
docker scan rsd-analysis-agent:latest
```

4. **Registry authentication**:
```bash
docker login registry.azurecr.io
```

---

## 🔄 Deployment Comparison Matrix

| Feature | Local Windows | Azure VM | Docker |
|---------|--------------|----------|--------|
| **Setup Time** | 30 min | 1-2 hours | 15 min |
| **Scalability** | Limited | High | Very High |
| **Cost** | $0 | $40-100/mo | $20-50/mo |
| **Reliability** | Medium | High | Very High |
| **Maintenance** | Manual | Managed | Automated |
| **Multi-region** | No | Yes | Yes |
| **CI/CD Ready** | No | Yes | Yes |

---

## 🚀 Post-Deployment Checklist

- [ ] Verify agent runs successfully
- [ ] Index all project documents
- [ ] Send test RSD email
- [ ] Confirm report received
- [ ] Setup monitoring/logging
- [ ] Document configuration
- [ ] Backup credentials securely
- [ ] Setup disaster recovery plan
- [ ] Configure auto-scaling (if cloud)
- [ ] Setup alerting for failures

---

## 📊 Monitoring & Logging

### Local Windows
```powershell
# View Task Scheduler history
Get-EventLog -LogName System -Source TaskScheduler | Select-Object -First 10

# Manual run with logging
python main.py > log.txt 2>&1
```

### Azure VM
```bash
# Monitor via Azure portal
# Or use Azure CLI:
az vm list-ip-addresses --resource-group rsd-agent-rg

# SSH into VM for logs
ssh -i key.pem azureuser@<ip>
```

### Docker
```bash
# View logs
docker-compose logs -f rsd-agent

# Monitor resource usage
docker stats rsd-analysis-agent

# Check health
docker inspect rsd-analysis-agent --format='{{.State.Health.Status}}'
```

---

## 🔐 Security Hardening

### Credentials Management

1. **Never commit secrets**:
```bash
# .gitignore includes:
credentials.json
token.json
.env
```

2. **Use cloud secret management**:
   - Azure Keyvault
   - AWS Secrets Manager
   - HashiCorp Vault

3. **Rotate credentials regularly**:
```bash
# Re-authenticate Gmail every 90 days
rm token.json
python main.py  # Will prompt for re-auth
```

### Network Security

- Use VPN for cloud deployments
- Whitelist Gmail API IPs
- Enable firewall rules
- Use HTTPS/TLS for all communication

---

## 💡 Troubleshooting by Deployment Type

### Local Windows Issues
- Task not running → Check "Run with highest privileges"
- Python not found → Add to PATH or use full path
- Permission denied → Run as Administrator

### Azure VM Issues
- Connection timeout → Check Network Security Group rules
- Out of memory → Resize VM (Standard_B2s → Standard_B4ms)
- Slow performance → Check Azure Metrics in portal

### Docker Issues
- Container exits → Check `docker logs container_name`
- Volume mount failed → Verify path exists on host
- Out of space → Check `docker system df`

---

## 📞 Support & Resources

- [Python Official Docs](https://docs.python.org)
- [Azure VMs Documentation](https://docs.microsoft.com/en-us/azure/virtual-machines/)
- [Docker Documentation](https://docs.docker.com)
- [Google Cloud Console](https://console.cloud.google.com)

