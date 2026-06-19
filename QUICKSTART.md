# Quick Start Deployment Guide

Choose your deployment method below:

## 🖥️ Option 1: Local Windows Machine (5 min setup)

**Best for**: Single office, small team, testing

```powershell
# Run as Administrator

# Step 1: Clone or download the project
cd C:\Users\Admin\Documents\PythonProjects\RAG_LangChain_Local.worktrees\agents-ai-agent-customer-management

# Step 2: Run automated setup
.\setup.bat

# Step 3: Download credentials.json from Google Cloud Console
# Save to project root directory

# Step 4: Initialize document index
python main.py --init

# Step 5: Test the agent
python main.py

# Step 6: Schedule with Task Scheduler (run as Admin)
.\deploy.ps1 -Action schedule -ScheduleType hourly
```

**Verify it works**:
```powershell
# Check scheduled task
.\deploy.ps1 -Action logs
```

---

## ☁️ Option 2: Azure VM (15 min setup)

**Best for**: Enterprise, cloud-native, scalable

```bash
# Prerequisites: Azure CLI installed, authenticated with 'az login'

# Step 1: Run deployment script
chmod +x deploy-azure.sh
./deploy-azure.sh "rsd-agent-rg" "rsd-agent-vm" "westeurope"

# Step 2: Connect to VM
mstsc /v:<VM_IP_ADDRESS>

# Step 3: Inside VM, run PowerShell as Administrator
cd C:\rsd-agent
.\deploy.ps1 -Action setup
.\deploy.ps1 -Action schedule

# Step 4: Upload project documents
az storage blob upload-batch \
  -s "C:\path\to\documents" \
  -d "project-documents" \
  -a "rsddocsXXXXXX" \
  --account-key "<storage-key>"

# Step 5: Configure agent to sync documents on startup
# (See DEPLOYMENT.md for details)
```

**Monitor in Azure**:
```bash
az vm get-instance-view \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm
```

---

## 🐳 Option 3: Docker Container (10 min setup)

**Best for**: Containerized, scalable, easy updates

```bash
# Step 1: Build Docker image
docker build -t rsd-analysis-agent:latest .

# Step 2: Create environment file
cp .env.example .env.docker
# Edit .env.docker with your settings

# Step 3: Prepare volumes
mkdir -p ~/docker-volumes/project_docs
mkdir -p ~/docker-volumes/vector_db
cp -r /path/to/project/documents/* ~/docker-volumes/project_docs/

# Step 4: Run with docker-compose
docker-compose up -d

# Step 5: Verify it's running
docker-compose logs -f rsd-agent
```

**Scale with Kubernetes**:
```bash
# Push to registry
docker tag rsd-analysis-agent:latest yourusername/rsd-analysis-agent:1.0
docker push yourusername/rsd-analysis-agent:1.0

# Deploy to Kubernetes
kubectl apply -f rsd-agent-deployment.yaml
```

---

## 📋 Pre-Deployment Checklist

Before you start, ensure you have:

- [ ] **Gmail Setup**
  - [ ] Google Cloud project created
  - [ ] Gmail API enabled
  - [ ] OAuth credentials downloaded (`credentials.json`)
  - [ ] Email recipient configured

- [ ] **Project Documents**
  - [ ] Historical project documents folder prepared
  - [ ] Documents organized in accessible location
  - [ ] File permissions verified

- [ ] **LLM Configuration**
  - [ ] OpenAI API key OR Ollama installed locally
  - [ ] API keys/models tested

- [ ] **Infrastructure**
  - [ ] Python 3.11+ (local/Windows)
  - [ ] Docker installed (for containerization)
  - [ ] Azure subscription (for cloud deployment)

---

## 🔧 Configuration Reference

### Essential Environment Variables

```bash
# Gmail
GMAIL_USER_EMAIL=your-company@gmail.com
SUMMARY_RECIPIENT_EMAIL=team@company.com

# Documents
PROJECT_DOCS_PATH=/path/to/documents

# LLM (choose one)
OPENAI_API_KEY=sk-your-key-here
# OR
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434

# RAG
SIMILARITY_THRESHOLD=0.6
```

---

## ✅ Post-Deployment Verification

### 1. Verify Installation

```bash
# Test imports
python -c "from gmail_client import GmailClient; print('OK')"

# Check vector DB
python -c "from rag_engine import RAGEngine; rag = RAGEngine(); print(rag.get_collection_info())"

# Test Gmail connection
python main.py  # Should connect without errors
```

### 2. Send Test Email

1. From your test email, send an email with:
   - **Subject**: "RSD - Test Project"
   - **Body**: Project requirements text

2. Run agent:
   ```bash
   python main.py
   ```

3. Check for report email in your inbox (at `SUMMARY_RECIPIENT_EMAIL`)

### 3. Monitor Execution

**Local Windows**:
```powershell
Get-EventLog -LogName System -Source TaskScheduler | head -10
```

**Docker**:
```bash
docker-compose logs -f rsd-agent
```

**Azure**:
```bash
az vm run-command invoke \
  --resource-group rsd-agent-rg \
  --name rsd-agent-vm \
  --command-id RunPowerShellScript \
  --scripts "Get-EventLog -LogName System -Source TaskScheduler | head -10"
```

---

## 🆘 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.11+ from python.org |
| "Gmail API error" | Re-authenticate: `rm token.json && python main.py` |
| "No documents indexed" | Check `PROJECT_DOCS_PATH` exists and has files |
| "Container won't start" | Check logs: `docker-compose logs rsd-agent` |
| "VM connection timeout" | Check Azure NSG rules allow RDP (port 3389) |
| "Low memory" | Increase VM size: `az vm resize --size Standard_B4ms` |

---

## 📞 Support Resources

- **Gmail API Issues**: https://console.cloud.google.com/apis/
- **Python Help**: https://docs.python.org/3.11/
- **Docker Docs**: https://docs.docker.com/
- **Azure Docs**: https://docs.microsoft.com/en-us/azure/
- **LangChain**: https://python.langchain.com/

---

## 🎯 Next Steps After Deployment

1. **Monitor first week** - Check logs daily, adjust similarity threshold if needed
2. **Optimize prompts** - Refine requirement extraction and recommendations
3. **Scale if needed** - Start with local, move to cloud if volume increases
4. **Backup strategy** - Regular backups of vector DB and credentials
5. **Team training** - Show team how to interpret reports
6. **Metrics tracking** - Monitor accuracy and time-to-report

---

## 📊 Deployment Comparison

| Aspect | Local | Azure VM | Docker |
|--------|-------|----------|--------|
| Setup Time | 5 min | 20 min | 10 min |
| Cost | $0 | $40+/mo | $20+/mo |
| Scalability | ❌ | ✅✅ | ✅✅✅ |
| Reliability | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Maintenance | Manual | Managed | Container |

---

## 📝 Deployment Status Tracker

Use this to track your deployment progress:

```
[ ] Pre-deployment checklist completed
[ ] Environment configured (.env file)
[ ] Gmail credentials downloaded
[ ] Project documents prepared
[ ] Deployment method chosen

# Local Windows:
[ ] Python installed
[ ] Virtual environment created
[ ] Dependencies installed
[ ] Agent tested locally
[ ] Task Scheduler configured

# Azure VM:
[ ] Resource group created
[ ] VM provisioned
[ ] Storage account created
[ ] Keyvault setup
[ ] Agent deployed on VM

# Docker:
[ ] Docker installed
[ ] Image built
[ ] docker-compose configured
[ ] Container running
[ ] Persistent volumes created

[ ] First test email sent and processed
[ ] Report email received
[ ] Performance acceptable
[ ] Monitoring setup
[ ] Documentation updated
```

---

**Ready to deploy? Pick your option above and get started!** 🚀
