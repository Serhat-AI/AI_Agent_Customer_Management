# RSD Analysis Agent - AI-Powered Customer Solution Matching

An intelligent agent that analyzes incoming Software Requirement Specifications (RSD) from customers and identifies similar solutions from your company's archive of 1000+ completed projects.

## 🎯 Features

- **Automated Email Monitoring** – Monitors Gmail inbox for incoming RSDs
- **RAG-Based Similarity Search** – Uses semantic search to find similar past solutions
- **AI-Powered Analysis** – Extracts key requirements and generates insights using LLM
- **Intelligent Reporting** – Sends detailed HTML email reports with recommendations
- **Multiple Document Formats** – Supports PDF, DOCX, and TXT files
- **Configurable LLM** – Works with OpenAI GPT or local Ollama models
- **Scheduled Execution** – Run continuously or on a schedule via Windows Task Scheduler

## 📋 Prerequisites

- Python 3.11+
- Google Gmail account with API access
- Project documents archive (local folder with historical RSD/SoW/Spec documents)
- OpenAI API key OR local Ollama installation

## 🚀 Setup Instructions

### 1. Clone and Install

```bash
cd C:\Users\Admin\Documents\PythonProjects\RAG_LangChain_Local.worktrees\agents-ai-agent-customer-management
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

Edit `.env`:

```
# Gmail Configuration
GMAIL_USER_EMAIL=your-company@gmail.com
SUMMARY_RECIPIENT_EMAIL=team-lead@company.com

# Document Archive
PROJECT_DOCS_PATH=C:\path\to\your\project\documents

# LLM Configuration (choose one)
# Option A: Use OpenAI
OPENAI_API_KEY=sk-your-api-key-here
USE_OLLAMA=false

# Option B: Use Ollama (local)
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

### 3. Setup Gmail API

#### Step A: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project: "RSD Analysis Agent"
3. Enable Gmail API:
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application"
   - Download JSON and save as `credentials.json` in project root

#### Step B: First-Time Authentication

Run the agent to generate token:

```bash
python main.py
```

A browser window will open for Gmail authentication. Click "Allow" to grant permissions.

Token will be saved as `token.json` (keep this secure).

### 4. Prepare Project Documents

Organize your historical project documents in a folder structure:

```
C:\path\to\project\documents\
├── Project_1\
│   ├── RSD.pdf
│   ├── SoW.docx
│   └── Specification.pdf
├── Project_2\
│   ├── RSD.txt
│   └── Scope.pdf
└── ...
```

### 5. Index Your Project Archive

Before running the agent, index all project documents:

```bash
# Initial indexing
python main.py --init

# Force reindexing (rebuild vector DB)
python main.py --init --force
```

This creates a vector database with embeddings for fast similarity search.

## 🔄 Running the Agent

### Manual Run (One-Time)

```bash
python main.py
```

This will:
1. Fetch all unread emails with "RSD" in subject
2. Analyze each RSD against your project archive
3. Send detailed HTML reports to the configured recipient
4. Mark emails as read

### Automated Scheduling (Windows Task Scheduler)

#### Option A: Run Every Hour

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task:
   - **Name**: RSD Analysis Agent - Hourly
   - **Trigger**: Daily, repeat every 1 hour, for a duration of 24 hours
3. Action:
   - **Program**: `C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe`
   - **Arguments**: `C:\full\path\to\main.py`
   - **Start in**: `C:\Users\Admin\Documents\PythonProjects\RAG_LangChain_Local.worktrees\agents-ai-agent-customer-management`

#### Option B: Run Every Morning at 8 AM

1. Open Task Scheduler
2. Create Basic Task:
   - **Name**: RSD Analysis Agent - Daily Morning
   - **Trigger**: Daily at 8:00 AM
3. Action:
   - **Program**: Python executable path
   - **Arguments**: `C:\full\path\to\main.py`
   - **Start in**: Project root directory

#### Option C: Run on Login

1. Open Task Scheduler
2. Create Basic Task:
   - **Name**: RSD Analysis Agent - On Login
   - **Trigger**: At log on
3. Action: Same as above

**Note**: For scheduled tasks to work properly:
- Ensure user account has permission to access project files
- Test the manual run first before scheduling
- Check Task Scheduler logs if agent doesn't run

### Continuous Daemon (Optional Advanced)

For always-on monitoring, create `scheduler.py`:

```bash
# scheduler.py not included in base - request if needed
# Runs agent every 10 minutes in background
```

## 📧 Email Report Format

The agent sends HTML reports containing:

- **Customer Request** – Subject and sender information
- **Key Requirements** – Extracted from RSD using AI
- **Similar Solutions** – Ranked list with similarity scores
- **Recommendations** – Actionable suggestions for reusing components

Example similarity scores:
- 0.95+ = Highly similar, strong reuse potential
- 0.80-0.95 = Similar, some components reusable  
- 0.60-0.80 = Moderately similar, architecture patterns applicable
- <0.60 = Not similar (filtered out by default)

## ⚙️ Configuration Details

### RAG Parameters

```
CHUNK_SIZE=1000           # Words per chunk for embedding
CHUNK_OVERLAP=200         # Overlap between chunks
SIMILARITY_THRESHOLD=0.6  # Minimum similarity to report
```

### Supported File Types

```
.pdf    – PDF documents
.docx   – Microsoft Word documents  
.txt    – Plain text files
```

### Embedding Model

Uses `all-MiniLM-L6-v2` (fast, accurate for technical documents):
- 384 dimensions
- ~100MB model size
- Downloaded automatically on first run

## 🔧 Troubleshooting

### "Gmail API not enabled"
- Ensure Gmail API is enabled in Google Cloud Console
- Delete `token.json` and re-run `python main.py` to re-authenticate

### "No documents loaded"
- Check `PROJECT_DOCS_PATH` in `.env` is correct
- Verify files have supported extensions (.pdf, .docx, .txt)
- Run: `python -c "from config import PROJECT_DOCS_PATH; print(PROJECT_DOCS_PATH)"`

### "API Rate Limit Exceeded"
- Gmail API has rate limits
- Space out agent runs (don't run more than every 5 minutes)
- Check Gmail API quotas in Google Cloud Console

### "OPENAI_API_KEY not found"
- Ensure `.env` file is in project root (same directory as `main.py`)
- Verify `OPENAI_API_KEY` is set to valid key (starts with `sk-`)
- Alternatively, set `USE_OLLAMA=true` to use local model

### Scheduled Task Not Running
- Check "Run with highest privileges" checkbox in Task Scheduler
- Verify "Run whether user is logged in or not" is checked
- Check Windows Event Viewer for error logs
- Test manual run first: `python main.py`

## 📊 Vector Database

The agent creates a persistent vector database in `./vector_db/`:

```
vector_db/
├── chroma.sqlite3      # Chroma database
├── index/
│   └── index_metadata/ # Embeddings metadata
```

To reset the database:
```bash
rm -r vector_db
python main.py --init
```

## 🔒 Security Considerations

1. **Gmail Token** – `token.json` has sensitive credentials. Add to `.gitignore`:
   ```
   token.json
   credentials.json
   .env
   downloads/
   vector_db/
   ```

2. **API Keys** – Never commit `.env` to version control

3. **Email Access** – Scoped to read-only + send for reports only

## 📈 Performance

- **Indexing**: ~1000 documents takes 2-5 minutes (one-time)
- **Search**: <1 second per query
- **Analysis**: 5-30 seconds per email (depends on LLM response time)
- **Total per email**: ~10-60 seconds

## 🛠️ Advanced Usage

### Custom Prompt Engineering

Edit `analysis_engine.py`:
- Modify `_extract_requirements()` prompt for different requirement extraction
- Adjust `_generate_recommendations()` prompt for different recommendation style

### Multiple LLM Models

Change in `config.py`:
```python
OLLAMA_MODEL=mistral     # Fast, lightweight
OLLAMA_MODEL=neural-chat # Good balance
OLLAMA_MODEL=llama2      # Higher quality
```

### Adjust Similarity Threshold

In `.env`:
```
SIMILARITY_THRESHOLD=0.7  # Stricter matching (fewer results)
SIMILARITY_THRESHOLD=0.5  # Looser matching (more results)
```

## 📝 Logs

View agent execution logs:
- **Windows Event Viewer** – For scheduled tasks
- **Console output** – When running manually

To redirect to file:
```bash
python main.py >> agent.log 2>&1
```

## 🚀 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Configure `.env` with your settings
3. ✅ Setup Gmail API credentials
4. ✅ Prepare project documents folder
5. ✅ Run initial indexing: `python main.py --init`
6. ✅ Test with: `python main.py`
7. ✅ Schedule with Windows Task Scheduler

## 📞 Support

For issues or questions:
- Check **Troubleshooting** section above
- Review Google Cloud Console for API errors
- Check `agent.log` for detailed error messages

## 📄 License

Internal use only

---

Created by: Serhat Yilmaz - AI Automation   
Version: 1.0  
