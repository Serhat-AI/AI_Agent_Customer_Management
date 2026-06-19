#!/usr/bin/env python
"""
Setup and testing script for RSD Analysis Agent
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python 3.11+ is installed"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"   Current version: {sys.version}")
        return False
    print("✅ Python version OK")
    return True

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("   Creating from .env.example...")
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("   Created .env - please edit with your settings")
            return False
        return False
    print("✅ .env file found")
    return True

def check_credentials():
    """Check if Gmail credentials exist"""
    if not os.path.exists('credentials.json'):
        print("⚠️  credentials.json not found")
        print("   You need to download this from Google Cloud Console")
        return False
    print("✅ credentials.json found")
    return True

def check_imports():
    """Check if required packages are installed"""
    required_packages = [
        'google.auth',
        'google.oauth2',
        'google_auth_oauthlib',
        'google_auth_httplib2',
        'googleapiclient',
        'langchain',
        'langchain_openai',
        'chromadb',
        'sentence_transformers',
        'PyPDF2',
        'docx',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages installed")
    return True

def check_project_docs():
    """Check if project documents path is configured"""
    try:
        from config import PROJECT_DOCS_PATH
        if os.path.exists(PROJECT_DOCS_PATH):
            num_files = len(list(Path(PROJECT_DOCS_PATH).rglob('*')))
            print(f"✅ Project docs path found: {num_files} files")
            return True
        else:
            print(f"⚠️  Project docs path not found: {PROJECT_DOCS_PATH}")
            return False
    except Exception as e:
        print(f"⚠️  Could not check project docs: {e}")
        return False

def test_gmail_connection():
    """Test Gmail API connection"""
    try:
        from gmail_client import GmailClient
        print("   Testing Gmail connection...")
        client = GmailClient()
        print("✅ Gmail API connection successful")
        return True
    except Exception as e:
        print(f"❌ Gmail API connection failed: {e}")
        return False

def test_rag_engine():
    """Test RAG engine initialization"""
    try:
        from rag_engine import RAGEngine
        print("   Testing RAG engine...")
        rag = RAGEngine()
        info = rag.get_collection_info()
        print(f"✅ RAG engine initialized (Status: {info['status']})")
        return True
    except Exception as e:
        print(f"❌ RAG engine failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("RSD Analysis Agent - Setup Check")
    print("="*60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Gmail Credentials", check_credentials),
        ("Required Packages", check_imports),
        ("Project Documents", check_project_docs),
        ("Gmail Connection", test_gmail_connection),
        ("RAG Engine", test_rag_engine),
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n🔍 {name}...")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error: {e}")
            results[name] = False
    
    print("\n" + "="*60)
    print("Setup Check Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to run:")
        print("   python main.py --init    # Index documents")
        print("   python main.py            # Run agent")
    else:
        print("\n⚠️  Please fix the failures above before running the agent")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
